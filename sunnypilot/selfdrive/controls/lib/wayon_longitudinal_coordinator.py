"""Traverse-specific longitudinal coordination and bounded response learning."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import json
import math
import os
import time

import numpy as np

from openpilot.common.constants import CV

DT_CTRL = 0.01


RESPONSE_PROFILE_PATH = "/data/wayon/longitudinal_response.json"
PROFILE_VERSION = 1
SPEED_BIN_EDGES_KPH = (10.0, 30.0, 60.0)


def speed_bin_index(v_ego: float) -> int:
  speed_kph = max(0.0, v_ego) * CV.MS_TO_KPH
  return sum(speed_kph >= edge for edge in SPEED_BIN_EDGES_KPH)


def empty_response_profile(default_delay: float) -> dict:
  return {
    "version": PROFILE_VERSION,
    "updatedAt": 0,
    "bins": [
      {"samples": 0, "delaySamples": 0, "delay": default_delay, "gasGain": 1.0, "brakeGain": 1.0}
      for _ in range(4)
    ],
  }


def load_response_profile(profile_path: str, default_delay: float) -> dict:
  profile = empty_response_profile(default_delay)
  try:
    with open(profile_path, encoding="utf-8") as profile_file:
      parsed = json.load(profile_file)
    if not isinstance(parsed, dict) or parsed.get("version") != PROFILE_VERSION:
      return profile
    bins = parsed.get("bins")
    if not isinstance(bins, list) or len(bins) != 4:
      return profile
    for index, learned in enumerate(bins):
      if not isinstance(learned, dict):
        continue
      target = profile["bins"][index]
      target["samples"] = max(0, int(learned.get("samples", 0)))
      target["delaySamples"] = max(0, int(learned.get("delaySamples", 0)))
      target["delay"] = float(np.clip(float(learned.get("delay", default_delay)), 0.08, 0.9))
      target["gasGain"] = float(np.clip(float(learned.get("gasGain", 1.0)), 0.65, 1.35))
      target["brakeGain"] = float(np.clip(float(learned.get("brakeGain", 1.0)), 0.65, 1.35))
    profile["updatedAt"] = int(parsed.get("updatedAt", 0))
  except (OSError, TypeError, ValueError, json.JSONDecodeError):
    pass
  return profile


def learned_delay_for_speed(profile: dict, v_ego: float, default_delay: float) -> float:
  try:
    learned = profile["bins"][speed_bin_index(v_ego)]
    if int(learned.get("delaySamples", 0)) < 6:
      return default_delay
    return float(np.clip(float(learned["delay"]), 0.08, 0.9))
  except (KeyError, IndexError, TypeError, ValueError):
    return default_delay


@dataclass
class CoastDecision:
  active: bool = False
  enter_frames: int = 0


class WayonCoastController:
  """Select a true zero-gas/zero-brake state with hysteresis."""

  ENTER_FRAMES = round(0.6 / DT_CTRL)
  LOW_SPEED_ENTER_FRAMES = round(0.3 / DT_CTRL)
  NATURAL_ACCEL_TAU = 0.8
  MAX_DOWNHILL_ALLOWANCE = 0.28
  HIGH_SPEED_MIN = 40.0 * CV.KPH_TO_MS
  HIGH_SPEED_ENTER_ACCEL = 0.10
  HIGH_SPEED_STAY_ACCEL = 0.16

  def __init__(self):
    self.state = CoastDecision()
    self.natural_accel = 0.0
    self.natural_accel_initialized = False

  def reset(self) -> None:
    self.state = CoastDecision()
    self.natural_accel = 0.0
    self.natural_accel_initialized = False

  def update(self, active: bool, v_ego: float, v_target: float, requested_accel: float,
             pitch: float, automatic_control: bool, lead=None, cutin_risk=None,
             measured_accel: float = 0.0, previous_accel: float = 0.0) -> bool:
    if active and abs(previous_accel) <= 0.08 and math.isfinite(measured_accel) and abs(measured_accel) < 1.5:
      if not self.natural_accel_initialized:
        self.natural_accel = measured_accel
        self.natural_accel_initialized = True
      else:
        alpha = DT_CTRL / (self.NATURAL_ACCEL_TAU + DT_CTRL)
        self.natural_accel += alpha * (measured_accel - self.natural_accel)

    speed_error = v_target - v_ego
    lead_urgent = bool(lead is not None and getattr(lead, "status", False) and (
      (float(getattr(lead, "dRel", 1000.0)) < max(12.0, v_ego * 1.8) and float(getattr(lead, "vRel", 0.0)) < -0.8) or
      float(getattr(lead, "dRel", 1000.0)) < 7.0
    ))
    cutin_urgent = bool(cutin_risk is not None and bool(getattr(cutin_risk, "status", False)) and
                        float(getattr(cutin_risk, "score", 0.0)) > 0.35)
    radar_lead = bool(lead is not None and getattr(lead, "status", False) and getattr(lead, "radar", False))
    stable_low_speed_lead = bool(
      1.0 <= v_ego < 5.0 and radar_lead and
      float(getattr(lead, "dRel", 0.0)) > max(7.0, v_ego * 1.8) and
      -0.25 < float(getattr(lead, "vRel", 0.0)) < 0.90 and
      abs(float(getattr(lead, "aLeadK", 0.0))) < 0.60
    )
    gravity_allowance = float(np.clip(-math.sin(pitch) * 9.81 * 0.75, 0.0, self.MAX_DOWNHILL_ALLOWANCE))
    observed_allowance = float(np.clip(self.natural_accel, 0.0, 0.25)) if self.natural_accel_initialized else 0.0
    free_roll_allowance = max(gravity_allowance, observed_allowance)
    base_valid = (active and (v_ego >= 5.0 or stable_low_speed_lead) and
                  abs(pitch) <= math.radians(4.0) and not automatic_control and
                  not lead_urgent and not cutin_urgent)
    if stable_low_speed_lead:
      enter_valid = (base_valid and -0.30 <= speed_error <= 0.75 and
                     -0.12 <= requested_accel <= 0.08 + free_roll_allowance)
      stay_valid = (base_valid and -0.40 <= speed_error <= 0.90 and
                    -0.20 <= requested_accel <= 0.15 + free_roll_allowance)
      enter_frames = self.LOW_SPEED_ENTER_FRAMES
    else:
      enter_accel_max = self.HIGH_SPEED_ENTER_ACCEL if v_ego >= self.HIGH_SPEED_MIN else 0.05
      stay_accel_max = self.HIGH_SPEED_STAY_ACCEL if v_ego >= self.HIGH_SPEED_MIN else 0.12
      enter_valid = base_valid and -0.35 <= speed_error <= 0.75 and -0.30 <= requested_accel <= enter_accel_max
      stay_valid = base_valid and -0.55 <= speed_error <= 0.95 and -0.45 <= requested_accel <= stay_accel_max
      enter_frames = self.ENTER_FRAMES

    if self.state.active:
      self.state.active = stay_valid
      if not self.state.active:
        self.state.enter_frames = 0
    elif enter_valid:
      self.state.enter_frames += 1
      self.state.active = self.state.enter_frames >= enter_frames
    else:
      self.state.enter_frames = 0
    return self.state.active


@dataclass
class LeadTrendDecision:
  active: bool = False
  enter_frames: int = 0
  exit_frames: int = 0
  track_id: int | None = None
  relative_accel: float = 0.0
  initialized: bool = False


class LeadTrendAnticipator:
  """Release throttle before a shrinking positive relative speed becomes closing."""

  ENTER_FRAMES = round(0.20 / DT_CTRL)
  EXIT_FRAMES = round(0.30 / DT_CTRL)
  FILTER_TAU = 0.25
  MIN_EGO_SPEED = 2.0
  MIN_REL_SPEED = 0.15
  MIN_REL_ACCEL = -0.25
  MAX_ZERO_CROSSING_TIME = 3.0

  def __init__(self):
    self.state = LeadTrendDecision()

  def reset(self) -> None:
    self.state = LeadTrendDecision()

  def update(self, active: bool, v_ego: float, requested_accel: float,
             measured_accel: float, lead=None) -> bool:
    valid_lead = bool(lead is not None and getattr(lead, "status", False) and getattr(lead, "radar", False))
    track_id = int(getattr(lead, "radarTrackId", -1)) if valid_lead else None
    if not active or not valid_lead or v_ego < self.MIN_EGO_SPEED:
      self.reset()
      return False

    if self.state.track_id is not None and track_id != self.state.track_id:
      self.reset()
    self.state.track_id = track_id

    raw_relative_accel = float(getattr(lead, "aLeadK", 0.0)) - measured_accel
    if not math.isfinite(raw_relative_accel):
      self.reset()
      return False
    if not self.state.initialized:
      self.state.relative_accel = raw_relative_accel
      self.state.initialized = True
    else:
      alpha = DT_CTRL / (self.FILTER_TAU + DT_CTRL)
      self.state.relative_accel += alpha * (raw_relative_accel - self.state.relative_accel)

    d_rel = float(getattr(lead, "dRel", 0.0))
    v_rel = float(getattr(lead, "vRel", 0.0))
    max_distance = max(35.0, v_ego * 2.5)
    zero_crossing_time = v_rel / max(-self.state.relative_accel, 1e-3)
    trend_valid = (
      requested_accel > 0.05 and 4.0 < d_rel < max_distance and
      v_rel > self.MIN_REL_SPEED and self.state.relative_accel < self.MIN_REL_ACCEL and
      zero_crossing_time <= self.MAX_ZERO_CROSSING_TIME
    )

    if self.state.active:
      # Once armed, hold zero throttle until the planner requests deceleration.
      if requested_accel <= 0.0:
        self.reset()
        return False
      if trend_valid or (v_rel <= self.MIN_REL_SPEED and self.state.relative_accel < -0.05):
        self.state.exit_frames = 0
      else:
        self.state.exit_frames += 1
        if self.state.exit_frames >= self.EXIT_FRAMES:
          self.reset()
    elif trend_valid:
      self.state.enter_frames += 1
      if self.state.enter_frames >= self.ENTER_FRAMES:
        self.state.active = True
        self.state.exit_frames = 0
    else:
      self.state.enter_frames = 0

    return self.state.active


class LowSpeedStopController:
  """Taper residual braking only in the final fraction of a stop."""

  TAPER_START = 1.5 * CV.KPH_TO_MS
  STOP_EPSILON = 0.015
  HOLD_CONFIRM_FRAMES = round(0.2 / DT_CTRL)
  MIN_LEAD_RESERVE = 4.2
  MAX_CLOSING_SPEED = -0.8

  def __init__(self):
    self.phase = "inactive"
    self.output_accel = None
    self.hold_confirm_frames = 0

  def reset(self) -> None:
    self.phase = "inactive"
    self.output_accel = None
    self.hold_confirm_frames = 0

  def update(self, requested_accel: float, v_ego: float, a_ego: float, standstill: bool,
             should_stop: bool, lead=None) -> float:
    filtered_stopped = standstill and v_ego <= self.STOP_EPSILON
    self.hold_confirm_frames = self.hold_confirm_frames + 1 if filtered_stopped else 0
    if self.hold_confirm_frames >= self.HOLD_CONFIRM_FRAMES:
      self.phase = "hold"
      self.output_accel = requested_accel
      return requested_accel
    if not should_stop or v_ego >= self.TAPER_START:
      self.phase = "approach"
      self.output_accel = requested_accel
      return requested_accel

    if not filtered_stopped:
      valid_lead = lead is not None and bool(getattr(lead, "status", False))
      if valid_lead:
        d_rel = float(getattr(lead, "dRel", 1000.0))
        v_rel = float(getattr(lead, "vRel", 0.0))
        if d_rel <= self.MIN_LEAD_RESERVE or v_rel < self.MAX_CLOSING_SPEED:
          self.phase = "safety"
          self.output_accel = requested_accel
          return requested_accel
      else:
        # Without a measured stopping reserve, preserve the planner's braking.
        self.phase = "unverified"
        self.output_accel = requested_accel
        return requested_accel

    self.phase = "settle" if filtered_stopped else "taper"
    desired_accel = -0.02 if filtered_stopped else float(np.interp(
      v_ego,
      [self.STOP_EPSILON, 0.15 * CV.KPH_TO_MS, 0.4 * CV.KPH_TO_MS,
       0.8 * CV.KPH_TO_MS, self.TAPER_START],
      [0.0, -0.02, -0.06, -0.16, -0.38],
    ))

    if self.output_accel is None:
      self.output_accel = requested_accel
    # Release quickly enough to shed residual hydraulic pressure before the
    # wheel-speed zero bin, then let GM Auto Hold build stationary pressure.
    release_step = 4.5 * DT_CTRL
    self.output_accel += float(np.clip(desired_accel - self.output_accel, 0.0, release_step))
    return self.output_accel


class LongitudinalResponseLearner:
  """Learn bounded delay and command response by speed bin during normal driving."""

  SAVE_INTERVAL_S = 60.0
  SAMPLE_EVERY_FRAMES = round(0.1 / DT_CTRL)

  def __init__(self, default_delay: float, profile_path: str = RESPONSE_PROFILE_PATH, enabled: bool = True):
    self.profile_path = profile_path
    self.default_delay = float(np.clip(default_delay, 0.08, 0.9))
    self.profile = load_response_profile(self.profile_path, self.default_delay) if enabled else empty_response_profile(self.default_delay)
    self.enabled = enabled
    self.frame = 0
    self.last_save = time.monotonic()
    self.last_command = 0.0
    self.probe_command = 0.0
    self.pending_onset = None
    self.history = deque(maxlen=round(1.5 / DT_CTRL))

  def reset_transient(self) -> None:
    self.pending_onset = None
    self.history.clear()
    self.last_command = 0.0
    self.probe_command = 0.0

  def response_delay(self, v_ego: float) -> float:
    return learned_delay_for_speed(self.profile, v_ego, self.default_delay)

  def correction(self, command: float, v_ego: float) -> float:
    learned = self.profile["bins"][speed_bin_index(v_ego)]
    if int(learned["samples"]) < 300 or abs(command) < 0.12:
      return command
    gain = float(learned["gasGain"] if command > 0.0 else learned["brakeGain"])
    correction = float(np.clip(1.0 / gain, 0.85, 1.15))
    return command * correction

  def update(self, command: float, measured_accel: float, v_ego: float, active: bool,
             pitch: float, gas_pressed: bool, brake_pressed: bool, urgent: bool) -> None:
    self.frame += 1
    now = time.monotonic()
    self.history.append((now, command, measured_accel))
    valid = (self.enabled and active and not gas_pressed and not brake_pressed and not urgent and
             v_ego > 1.0 and abs(pitch) <= math.radians(1.5) and
             math.isfinite(command) and math.isfinite(measured_accel))
    if not valid:
      self.pending_onset = None
      self.last_command = command
      self.probe_command = command
      return

    bin_data = self.profile["bins"][speed_bin_index(v_ego)]
    command_delta = command - self.last_command
    if self.frame % self.SAMPLE_EVERY_FRAMES == 0:
      probe_delta = command - self.probe_command
      if abs(probe_delta) >= 0.12:
        self.pending_onset = (now, measured_accel, math.copysign(1.0, probe_delta), speed_bin_index(v_ego))
      self.probe_command = command
    self.last_command = command

    if self.pending_onset is not None:
      onset_time, baseline, direction, onset_bin = self.pending_onset
      elapsed = now - onset_time
      response = (measured_accel - baseline) * direction
      if 0.08 <= elapsed <= 0.9 and response >= 0.08:
        learned = self.profile["bins"][onset_bin]
        alpha = 0.12 if learned["delaySamples"] < 10 else 0.04
        learned["delay"] = float((1.0 - alpha) * learned["delay"] + alpha * elapsed)
        learned["delaySamples"] += 1
        self.pending_onset = None
      elif elapsed > 0.9:
        self.pending_onset = None

    if self.frame % self.SAMPLE_EVERY_FRAMES == 0 and abs(command) >= 0.18 and abs(command_delta) < 0.03:
      gain_sample = measured_accel / command
      if 0.5 <= gain_sample <= 1.5:
        key = "gasGain" if command > 0.0 else "brakeGain"
        alpha = 0.02 if bin_data["samples"] < 300 else 0.005
        bin_data[key] = float((1.0 - alpha) * bin_data[key] + alpha * gain_sample)
        bin_data["samples"] += 1

    if now - self.last_save >= self.SAVE_INTERVAL_S:
      self.save()

  def save(self) -> None:
    self.profile["updatedAt"] = int(time.time())
    try:
      os.makedirs(os.path.dirname(self.profile_path), exist_ok=True)
      temporary_path = f"{self.profile_path}.tmp"
      with open(temporary_path, "w", encoding="utf-8") as profile_file:
        json.dump(self.profile, profile_file, separators=(",", ":"))
        profile_file.flush()
        os.fsync(profile_file.fileno())
      os.replace(temporary_path, self.profile_path)
    except OSError:
      pass
    self.last_save = time.monotonic()
