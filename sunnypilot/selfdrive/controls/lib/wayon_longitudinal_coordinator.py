"""Traverse-specific longitudinal coordination and bounded response learning."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import json
import math
import time
from typing import Any

import numpy as np

from openpilot.common.constants import CV

DT_CTRL = 0.01


RESPONSE_PROFILE_PARAM = "WayonLongitudinalResponse"
RESPONSE_LEARNING_PARAM = "WayonLongitudinalLearning"
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


def load_response_profile(params: Any, default_delay: float) -> dict:
  profile = empty_response_profile(default_delay)
  try:
    raw = params.get(RESPONSE_PROFILE_PARAM)
    parsed = raw if isinstance(raw, dict) else json.loads(raw) if raw else None
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

  def __init__(self):
    self.state = CoastDecision()

  def reset(self) -> None:
    self.state = CoastDecision()

  def update(self, active: bool, v_ego: float, v_target: float, requested_accel: float,
             pitch: float, automatic_control: bool, lead=None, cutin_risk=None) -> bool:
    speed_error = v_target - v_ego
    lead_urgent = bool(lead is not None and getattr(lead, "status", False) and (
      (float(getattr(lead, "dRel", 1000.0)) < max(12.0, v_ego * 1.8) and float(getattr(lead, "vRel", 0.0)) < -0.8) or
      float(getattr(lead, "dRel", 1000.0)) < 7.0
    ))
    cutin_urgent = bool(cutin_risk is not None and bool(getattr(cutin_risk, "status", False)) and
                        float(getattr(cutin_risk, "score", 0.0)) > 0.35)
    base_valid = (active and v_ego >= 5.0 and abs(pitch) <= math.radians(2.0) and
                  not automatic_control and not lead_urgent and not cutin_urgent)
    enter_valid = base_valid and -0.35 <= speed_error <= 0.75 and -0.30 <= requested_accel <= 0.05
    stay_valid = base_valid and -0.55 <= speed_error <= 0.95 and -0.45 <= requested_accel <= 0.12

    if self.state.active:
      self.state.active = stay_valid
      if not self.state.active:
        self.state.enter_frames = 0
    elif enter_valid:
      self.state.enter_frames += 1
      self.state.active = self.state.enter_frames >= self.ENTER_FRAMES
    else:
      self.state.enter_frames = 0
    return self.state.active


class LowSpeedStopController:
  """Release near walking speed, then recapture before GM hydraulic hold."""

  RELEASE_START = 3.0 * CV.KPH_TO_MS
  CAPTURE_START = 1.0 * CV.KPH_TO_MS
  STOP_EPSILON = 0.08

  def __init__(self):
    self.phase = "inactive"
    self.output_accel = None

  def reset(self) -> None:
    self.phase = "inactive"
    self.output_accel = None

  def update(self, requested_accel: float, v_ego: float, a_ego: float, standstill: bool,
             should_stop: bool, lead=None) -> float:
    if standstill or v_ego <= self.STOP_EPSILON:
      self.phase = "hold"
      self.output_accel = requested_accel
      return requested_accel
    if not should_stop or v_ego >= self.RELEASE_START:
      self.phase = "approach"
      self.output_accel = requested_accel
      return requested_accel

    valid_lead = lead is not None and bool(getattr(lead, "status", False))
    if valid_lead:
      d_rel = float(getattr(lead, "dRel", 1000.0))
      v_rel = float(getattr(lead, "vRel", 0.0))
      if d_rel <= 3.5 or v_rel < -1.0:
        self.phase = "safety"
        self.output_accel = requested_accel
        return requested_accel
    else:
      # Without a measured stopping reserve, preserve the planner's braking.
      self.phase = "unverified"
      self.output_accel = requested_accel
      return requested_accel

    if v_ego >= self.CAPTURE_START:
      self.phase = "release"
      soft_target = float(np.interp(v_ego, [self.CAPTURE_START, self.RELEASE_START], [-0.20, -0.55]))
    else:
      self.phase = "capture"
      soft_target = float(np.interp(v_ego, [self.STOP_EPSILON, self.CAPTURE_START], [-0.55, -0.20]))

    available_m = max(float(getattr(lead, "dRel", 1000.0)) - 3.0, 0.25)
    required_accel = -(v_ego ** 2) / (2.0 * available_m)
    # Never relax beyond the acceleration needed to retain a 3 m stopping reserve.
    desired_accel = min(soft_target, required_accel)
    if a_ego > -0.05 and v_ego < self.CAPTURE_START:
      desired_accel = min(desired_accel, -0.25)

    if self.output_accel is None:
      self.output_accel = requested_accel
    release_step = 0.8 * DT_CTRL
    build_step = 1.2 * DT_CTRL
    self.output_accel += float(np.clip(desired_accel - self.output_accel, -build_step, release_step))
    return self.output_accel


class LongitudinalResponseLearner:
  """Learn bounded delay and command response by speed bin during normal driving."""

  SAVE_INTERVAL_S = 60.0
  SAMPLE_EVERY_FRAMES = round(0.1 / DT_CTRL)

  def __init__(self, default_delay: float, params: Any | None = None):
    if params is None:
      from openpilot.common.params import Params
      params = Params()
    self.params = params
    self.default_delay = float(np.clip(default_delay, 0.08, 0.9))
    self.profile = load_response_profile(self.params, self.default_delay)
    self.enabled = self.params.get_bool(RESPONSE_LEARNING_PARAM)
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
    self.params.put(RESPONSE_PROFILE_PARAM, self.profile)
    self.last_save = time.monotonic()
