import math
from time import monotonic

import numpy as np
from cereal import car
from openpilot.common.realtime import DT_CTRL
from openpilot.common.swaglog import cloudlog
from openpilot.selfdrive.controls.lib.drive_helpers import CONTROL_N
from openpilot.common.pid import PIDController
from openpilot.selfdrive.modeld.constants import ModelConstants
from openpilot.sunnypilot.selfdrive.controls.lib.gm_manual_resume import manual_resume_eligible, manual_resume_obstacle_clear
from openpilot.sunnypilot.selfdrive.controls.lib.wayon_carrot_long_profile import (
  MOVING_STOPPING_DECEL_RATE,
  PID_KF,
  PID_KI,
  PID_KP,
  apply_uphill_accel_compensation,
  get_grade_adjusted_max_accel,
  is_enabled,
)
from openpilot.sunnypilot.selfdrive.controls.lib.adaptive_longitudinal_smoother import AdaptiveLongitudinalSmoother
from openpilot.sunnypilot.selfdrive.controls.lib.radar_lead_helpers import cutin_risk_for_control
from openpilot.sunnypilot.selfdrive.controls.lib.wayon_longitudinal_coordinator import (
  LeadApproachController,
  LeadTrendAnticipator,
  LongitudinalResponseLearner,
  LowSpeedStopController,
  QueueCreepController,
  WayonCoastController,
  icbm_blocks_coast,
)

CONTROL_N_T_IDX = ModelConstants.T_IDXS[:CONTROL_N]

LongCtrlState = car.CarControl.Actuators.LongControlState

SNG_STOP_CONFIRM_FRAMES = round(0.5 / DT_CTRL)
SNG_LEAD_CONFIRM_FRAMES = round(0.2 / DT_CTRL)
SNG_LEAD_MIN_DISTANCE = 1.5
SNG_LEAD_MAX_DISTANCE = 25.0
SNG_LEAD_MIN_REL_SPEED = 0.35
SNG_LEAD_MIN_DISTANCE_DELTA = 0.4
SNG_RESUME_TIMEOUT_FRAMES = round(2.0 / DT_CTRL)
SNG_PRESTOP_TRACK_SPEED = 1.5
SNG_STARTED_CONFIRM_FRAMES = round(0.2 / DT_CTRL)
SNG_MANUAL_RELEASE_TIMEOUT = 4.0
SNG_MANUAL_CREEP_MIN_SPEED = 0.1
SNG_MANUAL_CREEP_MAX_SPEED = 1.0
SNG_MANUAL_CREEP_MAX_DISTANCE = 1.5
QUEUE_CREEP_MAX_ACCEL = 0.0
QUEUE_CREEP_MAX_DECEL = -0.55
QUEUE_CREEP_SPEED_KP = 0.9
QUEUE_CREEP_ACCEL_DAMPING = 0.75
QUEUE_CREEP_MEASURED_ACCEL_LIMIT = 0.4
QUEUE_CREEP_BRAKE_BUILD_RATE = 1.5
QUEUE_CREEP_BRAKE_RELEASE_RATE = 1.5


def get_queue_creep_accel(v_target: float, v_ego: float, a_ego: float) -> float:
  """Track crawl speed with brake release only and damp torque-converter surge."""
  if not all(math.isfinite(value) for value in (v_target, v_ego, a_ego)):
    return QUEUE_CREEP_MAX_DECEL

  measured_accel = float(np.clip(a_ego, -QUEUE_CREEP_MEASURED_ACCEL_LIMIT,
                                 QUEUE_CREEP_MEASURED_ACCEL_LIMIT))
  requested_accel = QUEUE_CREEP_SPEED_KP * (v_target - v_ego) - \
                    QUEUE_CREEP_ACCEL_DAMPING * measured_accel
  return float(np.clip(requested_accel, QUEUE_CREEP_MAX_DECEL, QUEUE_CREEP_MAX_ACCEL))


def rate_limit_queue_creep_accel(requested_accel: float, previous_accel: float) -> float:
  """Move brake command promptly but continuously in both directions."""
  rate = QUEUE_CREEP_BRAKE_RELEASE_RATE if requested_accel > previous_accel else QUEUE_CREEP_BRAKE_BUILD_RATE
  step = rate * DT_CTRL
  return float(previous_accel + np.clip(requested_accel - previous_accel, -step, step))


def use_gm_auto_hold_sng(CP) -> bool:
  return getattr(CP, "brand", "") == "gm" and bool(getattr(CP, "autoResumeSng", False))


def use_traverse_unacked_follow(CP) -> bool:
  return use_gm_auto_hold_sng(CP) and getattr(CP, "carFingerprint", "") == "CHEVROLET_TRAVERSE"


def gm_cruise_active(CS) -> bool:
  # Traverse CarState only marks raw ACTIVE/STANDSTILL as enabled. In
  # particular, OFF, FAULTED and unknown PCM states are not resume ACKs.
  return CS.canValid and CS.cruiseState.enabled and not CS.cruiseState.standstill and not CS.accFaulted


def gm_resume_motion_confirmed(CS) -> bool:
  motion_speed = max(abs(CS.vEgoRaw), abs(CS.vEgo))
  return gm_cruise_active(CS) and not CS.standstill and motion_speed >= SNG_MANUAL_CREEP_MIN_SPEED


def long_control_state_trans(CP, CP_SP, active, long_control_state, v_ego,
                             should_stop, brake_pressed, cruise_standstill,
                             sng_resume=False, unacked_follow=False, vehicle_standstill=None):
  # Gas Interceptor
  cruise_standstill = cruise_standstill and not CP_SP.enableGasInterceptor

  stopping_condition = should_stop
  # The Traverse can report PCM standstill before the wheels have stopped. Do
  # not turn a rolling stop into Auto Hold after the planner clears shouldStop.
  if use_gm_auto_hold_sng(CP):
    physically_stopped = abs(v_ego) <= 0.05 if vehicle_standstill is None else vehicle_standstill
    launch_latched = physically_stopped
  else:
    launch_latched = cruise_standstill
  starting_condition = (not should_stop and
                        (not launch_latched or sng_resume or unacked_follow) and
                        not brake_pressed)
  started_condition = v_ego > CP.vEgoStarting and (unacked_follow or not (use_gm_auto_hold_sng(CP) and cruise_standstill))

  if not active:
    long_control_state = LongCtrlState.off

  else:
    if long_control_state == LongCtrlState.off:
      if not starting_condition:
        long_control_state = LongCtrlState.stopping
      else:
        if starting_condition and CP.startingState:
          long_control_state = LongCtrlState.starting
        else:
          long_control_state = LongCtrlState.pid

    elif long_control_state == LongCtrlState.stopping:
      if starting_condition and CP.startingState:
        long_control_state = LongCtrlState.starting
      elif starting_condition:
        long_control_state = LongCtrlState.pid

    elif long_control_state in [LongCtrlState.starting, LongCtrlState.pid]:
      if stopping_condition:
        long_control_state = LongCtrlState.stopping
      elif started_condition:
        long_control_state = LongCtrlState.pid
  return long_control_state

class LongControl:
  def __init__(self, CP, CP_SP):
    self.CP = CP
    self.CP_SP = CP_SP
    self.long_control_state = LongCtrlState.off
    self.pid = PIDController((CP.longitudinalTuning.kpBP, CP.longitudinalTuning.kpV),
                             (CP.longitudinalTuning.kiBP, CP.longitudinalTuning.kiV),
                             rate=1 / DT_CTRL)
    self.wayon_carrot_profile = is_enabled(CP)
    self.speed_pid_enabled = self.wayon_carrot_profile
    self.speed_pid_kf = PID_KF
    self.speed_pid = PIDController(([0.0], [PID_KP]),
                                   ([0.0], [PID_KI]),
                                   rate=1 / DT_CTRL)
    self.accel_smoother = AdaptiveLongitudinalSmoother()
    self.coast_controller = WayonCoastController()
    self.lead_approach_controller = LeadApproachController()
    self.lead_trend_anticipator = LeadTrendAnticipator()
    self.stop_controller = LowSpeedStopController()
    self.queue_creep_controller = QueueCreepController()
    self.response_learner = LongitudinalResponseLearner(
      float(CP.longitudinalActuatorDelay), enabled=self.wayon_carrot_profile)
    self.last_output_accel = 0.0
    self.sng_stop_frames = 0
    self.sng_lead_frames = 0
    self.sng_lead_baseline_m = None
    self.sng_resume_ready = False
    self.sng_resume_frames = 0
    self.sng_resume_attempted = False
    self.sng_resume_failed = False
    self.sng_resume_succeeded = False
    self.sng_resume_moved = False
    self.sng_unacked_follow = False
    self.sng_resume_started_at = None
    self.sng_started_frames = 0
    self.sng_manual_resume = False
    self.sng_ui_resume = False
    self.sng_ui_hold_release = False
    self.sng_ui_creep = False
    self.sng_ui_creep_distance = 0.0
    self.sng_ui_creep_last_time = None
    self.sng_ui_phase = None
    self.sng_ui_motion_frames = 0
    self.sng_auto_attempt_id = 0
    self.sng_auto_logged_stages = set()
    self.gas_override_active = False

  def reset(self):
    self.pid.reset()
    self.speed_pid.reset()

  def reset_sng_resume(self, clear_attempt=True):
    self.sng_stop_frames = 0
    self.sng_lead_frames = 0
    self.sng_lead_baseline_m = None
    self.sng_resume_ready = False
    self.sng_resume_frames = 0
    self.sng_resume_started_at = None
    self.sng_started_frames = 0
    self.sng_ui_resume = False
    self.sng_ui_hold_release = False
    self.sng_ui_creep = False
    self.sng_ui_creep_distance = 0.0
    self.sng_ui_creep_last_time = None
    self.sng_ui_phase = None
    self.sng_ui_motion_frames = 0
    self.sng_unacked_follow = False
    if clear_attempt:
      self.sng_resume_attempted = False
      self.sng_resume_failed = False
      self.sng_resume_succeeded = False
      self.sng_resume_moved = False
      self.sng_manual_resume = False
      self.sng_auto_logged_stages.clear()

  def log_gm_auto_resume(self, stage, **kwargs):
    if not use_gm_auto_hold_sng(self.CP) or self.sng_ui_resume or self.sng_manual_resume:
      return
    if stage in self.sng_auto_logged_stages:
      return
    self.sng_auto_logged_stages.add(stage)
    cloudlog.event("gm_auto_resume", stage=stage, attempt=self.sng_auto_attempt_id, **kwargs)

  def fail_sng_resume(self, reason="conditions_changed"):
    if self.sng_ui_resume:
      cloudlog.event("gm_manual_resume", stage="stopped", reason=reason)
    elif self.sng_resume_attempted and not self.sng_manual_resume:
      self.log_gm_auto_resume("failed", reason=reason)
    self.reset_sng_resume(clear_attempt=False)
    self.sng_resume_failed = True
    self.sng_resume_succeeded = False
    self.sng_resume_moved = False

  def get_resume_request(self, enabled, long_active, CS, long_plan):
    if self.sng_ui_phase == "release":
      return False
    requested = enabled and CS.cruiseState.standstill and (not long_plan.shouldStop or self.sng_ui_creep)
    if use_gm_auto_hold_sng(self.CP):
      return bool(requested and long_active and self.sng_resume_ready and not self.sng_manual_resume and
                  CS.canValid and CS.cruiseState.enabled and not CS.accFaulted)
    return requested and (not self.CP.autoResumeSng or self.sng_resume_ready)

  def get_stopping_decel_rate(self, standstill: bool) -> float:
    if self.wayon_carrot_profile and not standstill:
      return MOVING_STOPPING_DECEL_RATE
    return self.CP.stoppingDecelRate

  def update_sng_resume(self, active, CS, long_plan, radar_state, now=None, manual_resume=False, manual_resume_sensors_valid=False):
    lead = radar_state.leadOne if radar_state is not None else None
    valid_lead = (lead is not None and lead.status and
                  SNG_LEAD_MIN_DISTANCE < lead.dRel < SNG_LEAD_MAX_DISTANCE)

    if not self.CP.autoResumeSng or not active or CS.brakePressed or CS.gasPressed:
      if self.sng_resume_attempted and not self.sng_manual_resume:
        reason = "brake_pressed" if CS.brakePressed else "gas_pressed" if CS.gasPressed else "control_inactive"
        self.log_gm_auto_resume("failed", reason=reason)
      self.reset_sng_resume()
      return False

    if use_gm_auto_hold_sng(self.CP):
      return self.update_gm_sng_resume(CS, long_plan, valid_lead, lead, monotonic() if now is None else now,
                                       manual_resume, radar_state, manual_resume_sensors_valid)

    if CS.vEgo > max(self.CP.vEgoStarting, SNG_PRESTOP_TRACK_SPEED):
      self.reset_sng_resume()
      return False

    if self.sng_resume_ready:
      if long_plan.shouldStop or not valid_lead:
        self.reset_sng_resume(clear_attempt=False)
        return False
      self.sng_resume_frames += 1
      if self.sng_resume_frames >= SNG_RESUME_TIMEOUT_FRAMES:
        self.reset_sng_resume(clear_attempt=False)
      return self.sng_resume_ready

    safe_stop = (CS.standstill and CS.cruiseState.standstill and
                 self.long_control_state == LongCtrlState.stopping)
    if not safe_stop or self.sng_resume_attempted or not valid_lead:
      self.reset_sng_resume(clear_attempt=False)
      return False

    self.sng_stop_frames = min(self.sng_stop_frames + 1, SNG_STOP_CONFIRM_FRAMES)
    if self.sng_lead_baseline_m is None:
      self.sng_lead_baseline_m = lead.dRel
    else:
      self.sng_lead_baseline_m = min(self.sng_lead_baseline_m, lead.dRel)

    lead_departing = (self.sng_stop_frames >= SNG_STOP_CONFIRM_FRAMES and
                      not long_plan.shouldStop and
                      (lead.vRel > SNG_LEAD_MIN_REL_SPEED or
                       lead.dRel - self.sng_lead_baseline_m > SNG_LEAD_MIN_DISTANCE_DELTA))
    self.sng_lead_frames = min(self.sng_lead_frames + 1, SNG_LEAD_CONFIRM_FRAMES) if lead_departing else 0
    self.sng_resume_ready = self.sng_lead_frames >= SNG_LEAD_CONFIRM_FRAMES
    self.sng_resume_attempted |= self.sng_resume_ready
    return self.sng_resume_ready

  def update_gm_sng_resume(self, CS, long_plan, valid_lead, lead, now, ui_resume=False, radar_state=None, sensors_valid=False):
    if CS.regenBraking or CS.parkingBrake or CS.gearShifter not in (car.CarState.GearShifter.drive, car.CarState.GearShifter.low):
      if self.sng_resume_attempted and not self.sng_manual_resume:
        reason = "regen_braking" if CS.regenBraking else "parking_brake" if CS.parkingBrake else "gear_invalid"
        self.log_gm_auto_resume("failed", reason=reason)
      self.reset_sng_resume()
      return False

    if self.sng_resume_attempted and not self.sng_manual_resume:
      if gm_cruise_active(CS):
        self.log_gm_auto_resume("pcm_active", speed=float(CS.vEgo), raw_speed=float(CS.vEgoRaw))
      if CS.aEgo > 0.2 and CS.vEgoRaw > 0.05:
        self.log_gm_auto_resume("positive_accel_proxy", accel=float(CS.aEgo), speed=float(CS.vEgo),
                                raw_speed=float(CS.vEgoRaw))
      if gm_resume_motion_confirmed(CS):
        self.sng_resume_moved = True
        self.log_gm_auto_resume("vehicle_moving", speed=float(CS.vEgo), raw_speed=float(CS.vEgoRaw),
                                accel=float(CS.aEgo))
    if (self.sng_resume_succeeded and self.sng_resume_moved and CS.standstill and abs(CS.vEgo) < 0.05 and
        self.long_control_state == LongCtrlState.stopping):
      # A successful low-speed launch can be followed by another stop without
      # ever reaching 1.5 m/s in traffic. Confirm that new stop from scratch.
      self.reset_sng_resume()

    # A physical RES is an explicit driver retry, not permission for another
    # synthetic burst. Keep the normal planner/lead and driver-override gates.
    manual_resume = any(b.type == car.CarState.ButtonEvent.Type.accelCruise and b.pressed for b in CS.buttonEvents)
    cruise_valid = CS.canValid and CS.cruiseState.enabled and not CS.accFaulted
    if self.sng_unacked_follow:
      if not cruise_valid or not valid_lead or not manual_resume_obstacle_clear(long_plan, radar_state):
        self.fail_sng_resume("unacked_follow_invalid")
        return False
      if long_plan.shouldStop:
        if CS.standstill and abs(CS.vEgoRaw) < 0.05:
          self.log_gm_auto_resume("unacked_follow_stopped")
          self.reset_sng_resume()
        return False
      self.sng_started_frames = self.sng_started_frames + 1 if gm_resume_motion_confirmed(CS) else 0
      if self.sng_started_frames >= SNG_STARTED_CONFIRM_FRAMES:
        self.log_gm_auto_resume("pcm_active_confirmed", speed=float(CS.vEgo), raw_speed=float(CS.vEgoRaw))
        self.reset_sng_resume(clear_attempt=False)
        self.sng_resume_succeeded = True
        self.sng_resume_moved = True
        return False
      return True
    if (ui_resume and sensors_valid and manual_resume_obstacle_clear(long_plan, radar_state) and
        self.long_control_state == LongCtrlState.stopping and
        manual_resume_eligible(self.CP, CS, True, True)):
      # An explicit screen tap may retry and does not require a lead. Its
      # request already passed the local socket expiry and freshness checks.
      self.reset_sng_resume()
      self.sng_ui_resume = True
      self.sng_ui_hold_release = not CS.cruiseState.standstill
      self.sng_ui_creep = bool(long_plan.shouldStop)
      self.sng_ui_creep_last_time = now
      self.sng_ui_phase = "release"
      self.sng_resume_attempted = True
      self.sng_resume_ready = True
      self.sng_resume_started_at = now
      cloudlog.event("gm_manual_resume", stage="brake_release",
                     pcm_standstill=bool(CS.cruiseState.standstill))
    if manual_resume and cruise_valid and valid_lead and not long_plan.shouldStop and \
        (CS.standstill or self.sng_resume_ready or self.sng_resume_failed):
      self.sng_manual_resume = True
      self.sng_ui_resume = False
      self.sng_ui_hold_release = False
      self.sng_ui_creep = False
      self.sng_ui_phase = None
      self.sng_resume_failed = False
      self.sng_resume_succeeded = False
      self.sng_resume_moved = False
      self.sng_resume_attempted = True
      self.sng_resume_ready = True
      self.sng_resume_started_at = now
      self.sng_resume_frames = 0
      self.sng_started_frames = 0

    if (self.sng_resume_succeeded and not gm_cruise_active(CS) and not long_plan.shouldStop and
        self.long_control_state in (LongCtrlState.starting, LongCtrlState.pid)):
      # A temporary ACK must not leave starting/PID applying acceleration
      # indefinitely if the PCM relatches. Require driver action after failure.
      self.fail_sng_resume("pcm_relatched")
      return False

    # Process an outstanding attempt before any speed-based reset. Wheel creep
    # must not erase its deadline or masquerade as PCM acceptance.
    if self.sng_resume_ready:
      if self.sng_ui_resume and (not sensors_valid or not manual_resume_obstacle_clear(long_plan, radar_state)):
        self.fail_sng_resume("perception_or_obstacle")
        return False
      if self.sng_ui_phase is not None:
        elapsed = now - self.sng_ui_creep_last_time
        self.sng_ui_creep_last_time = now
        self.sng_ui_creep_distance += abs(CS.vEgoRaw) * max(elapsed, 0.0)
        if (not all(math.isfinite(v) for v in (CS.vEgoRaw, CS.vEgo)) or
            not 0.0 <= elapsed <= 0.1 or CS.vEgoRaw < -0.05 or
            max(abs(CS.vEgoRaw), abs(CS.vEgo)) >= SNG_MANUAL_CREEP_MAX_SPEED or
            self.sng_ui_creep_distance >= SNG_MANUAL_CREEP_MAX_DISTANCE):
          self.fail_sng_resume("creep_limit")
          return False
        # Once the planner permits departure, hand control back permanently.
        # A later stop request cannot reopen this manual exception.
        if self.sng_ui_creep and not long_plan.shouldStop:
          self.sng_ui_creep = False
          cloudlog.event("gm_manual_resume", stage="planner_allows_start")
        if self.sng_ui_phase == "release":
          moving = not CS.standstill and CS.vEgoRaw >= SNG_MANUAL_CREEP_MIN_SPEED
          self.sng_ui_motion_frames = self.sng_ui_motion_frames + 1 if moving else 0
          if self.sng_ui_motion_frames >= 3:
            self.sng_ui_phase = "resuming"
            # Brake release/creep must not consume the PCM response window.
            self.sng_resume_started_at = now
            cloudlog.event("gm_manual_resume", stage="creep_confirmed_res_requested", speed=float(CS.vEgoRaw))
      if not cruise_valid or (long_plan.shouldStop and not self.sng_ui_creep) or (not valid_lead and not self.sng_ui_resume):
        reason = "cruise_invalid" if not cruise_valid else "planner_restopped" if long_plan.shouldStop else "lead_lost"
        self.fail_sng_resume(reason)
        return False
      self.sng_resume_frames += 1
      # A transient PCM ACTIVE at zero speed can relatch without departure.
      # Require observed wheel motion before accepting any resume request.
      started = (self.sng_ui_phase != "release" and not self.sng_ui_creep and
                 gm_resume_motion_confirmed(CS))
      self.sng_started_frames = self.sng_started_frames + 1 if started else 0
      if self.sng_started_frames >= SNG_STARTED_CONFIRM_FRAMES:
        if self.sng_ui_resume:
          cloudlog.event("gm_manual_resume", stage="accepted", speed=float(CS.vEgo))
        elif not self.sng_manual_resume:
          self.log_gm_auto_resume("pcm_active_confirmed", speed=float(CS.vEgo), raw_speed=float(CS.vEgoRaw))
        self.reset_sng_resume(clear_attempt=False)
        self.sng_resume_succeeded = True
        return False
      timeout = SNG_MANUAL_RELEASE_TIMEOUT if self.sng_ui_phase == "release" else SNG_RESUME_TIMEOUT_FRAMES * DT_CTRL
      if self.sng_resume_started_at is None or now - self.sng_resume_started_at >= timeout:
        if (not self.sng_ui_resume and not self.sng_manual_resume and use_traverse_unacked_follow(self.CP) and
            not CS.standstill and CS.vEgoRaw >= SNG_MANUAL_CREEP_MIN_SPEED and
            manual_resume_obstacle_clear(long_plan, radar_state)):
          self.sng_resume_ready = False
          self.sng_unacked_follow = True
          self.sng_started_frames = 0
          self.accel_smoother.reset(0.0)
          self.log_gm_auto_resume("unacked_follow", speed=float(CS.vEgo), raw_speed=float(CS.vEgoRaw))
          return True
        self.fail_sng_resume("brake_release_timeout" if self.sng_ui_phase == "release" else "resume_ack_timeout")
        return False
      return True

    if gm_cruise_active(CS) and CS.vEgo > SNG_PRESTOP_TRACK_SPEED:
      self.reset_sng_resume()
      return False
    if self.sng_resume_attempted:
      return False

    # This feature resumes an engaged, confirmed stop. Tracking a lead while
    # still moving is not sufficient authorization to inject a RES button.
    safe_stop = (CS.standstill and abs(CS.vEgo) < 0.05 and cruise_valid and
                 self.long_control_state == LongCtrlState.stopping)
    if not safe_stop or not valid_lead:
      self.reset_sng_resume(clear_attempt=False)
      return False
    self.sng_stop_frames = min(self.sng_stop_frames + 1, SNG_STOP_CONFIRM_FRAMES)
    self.sng_lead_baseline_m = lead.dRel if self.sng_lead_baseline_m is None else min(self.sng_lead_baseline_m, lead.dRel)
    if self.sng_stop_frames >= SNG_STOP_CONFIRM_FRAMES:
      if "hold_confirmed" not in self.sng_auto_logged_stages:
        self.sng_auto_attempt_id += 1
      self.log_gm_auto_resume("hold_confirmed", lead_distance=float(lead.dRel), pcm_standstill=bool(CS.cruiseState.standstill))
    lead_departing = (self.sng_stop_frames >= SNG_STOP_CONFIRM_FRAMES and not long_plan.shouldStop and
                     (lead.vRel > SNG_LEAD_MIN_REL_SPEED or lead.dRel - self.sng_lead_baseline_m > SNG_LEAD_MIN_DISTANCE_DELTA))
    self.sng_lead_frames = min(self.sng_lead_frames + 1, SNG_LEAD_CONFIRM_FRAMES) if lead_departing else 0
    if self.sng_lead_frames >= SNG_LEAD_CONFIRM_FRAMES:
      self.log_gm_auto_resume("lead_departed", lead_distance=float(lead.dRel), lead_relative_speed=float(lead.vRel),
                              distance_delta=float(lead.dRel - self.sng_lead_baseline_m))
      self.sng_resume_ready = True
      self.sng_resume_attempted = True
      self.sng_resume_moved = False
      self.sng_resume_started_at = now
    return self.sng_resume_ready

  def update(self, active, CS, long_plan, accel_limits, radar_state=None, icbm=None, pitch=0.0, manual_resume=False,
             manual_resume_sensors_valid=False):
    """Update longitudinal control. This updates the state machine and runs a PID loop"""
    previous_state_active = self.long_control_state != LongCtrlState.off
    if CS.gasPressed and (previous_state_active or self.gas_override_active):
      self.gas_override_active = True
    override_released = active and self.gas_override_active and not CS.gasPressed
    if override_released or (not active and not CS.gasPressed):
      self.gas_override_active = False

    a_target = long_plan.aTarget
    planner_should_stop = long_plan.shouldStop
    if self.wayon_carrot_profile:
      accel_limits = (accel_limits[0], min(accel_limits[1], get_grade_adjusted_max_accel(CS.vEgo, pitch)))
    self.pid.neg_limit = accel_limits[0]
    self.pid.pos_limit = accel_limits[1]
    self.speed_pid.neg_limit = accel_limits[0]
    self.speed_pid.pos_limit = accel_limits[1]
    sng_resume = self.update_sng_resume(active, CS, long_plan, radar_state, manual_resume=manual_resume,
                                       manual_resume_sensors_valid=manual_resume_sensors_valid)
    lead = radar_state.leadOne if radar_state is not None else None
    queue_creep_enabled = bool(
      self.wayon_carrot_profile and active and CS.canValid and not CS.brakePressed and not CS.gasPressed and
      not CS.regenBraking and not CS.parkingBrake and
      CS.gearShifter in (car.CarState.GearShifter.drive, car.CarState.GearShifter.low) and
      self.sng_ui_phase is None and not self.sng_resume_ready and not self.sng_unacked_follow
    )
    queue_creep = self.queue_creep_controller.update(
      queue_creep_enabled, planner_should_stop, CS.vEgo, CS.vEgoRaw, CS.standstill, lead)
    should_stop = planner_should_stop and not self.sng_ui_creep and not queue_creep.active
    sng_launch_failed = (self.CP.autoResumeSng and self.sng_resume_attempted and not sng_resume and
                         self.long_control_state == LongCtrlState.starting and CS.vEgo <= self.CP.vEgoStarting)
    if use_gm_auto_hold_sng(self.CP):
      sng_launch_failed = self.sng_resume_failed

    self.long_control_state = long_control_state_trans(self.CP, self.CP_SP, active, self.long_control_state, CS.vEgo,
                                                       should_stop or sng_launch_failed, CS.brakePressed,
                                                       CS.cruiseState.standstill, sng_resume, self.sng_unacked_follow,
                                                       CS.standstill)
    if self.sng_ui_phase is not None:
      self.long_control_state = LongCtrlState.starting
    elif queue_creep.active:
      # Remaining in stopping would force inactive regen and a brake floor in
      # the GM output layer. PID is required to track the bounded creep speed.
      self.long_control_state = LongCtrlState.pid
    if self.long_control_state == LongCtrlState.off:
      self.reset()
      self.coast_controller.reset()
      self.lead_approach_controller.reset()
      self.lead_trend_anticipator.reset()
      self.stop_controller.reset()
      self.queue_creep_controller.reset()
      output_accel = 0.
      self.accel_smoother.reset(CS.aEgo)

    elif self.long_control_state == LongCtrlState.stopping:
      self.coast_controller.reset()
      self.lead_approach_controller.reset()
      self.lead_trend_anticipator.reset()
      output_accel = self.last_output_accel
      if output_accel > self.CP.stopAccel:
        output_accel = min(output_accel, 0.0)
        output_accel -= self.get_stopping_decel_rate(CS.standstill) * DT_CTRL
      lead = radar_state.leadOne if radar_state is not None else None
      if self.wayon_carrot_profile and not self.sng_resume_failed:
        output_accel = self.stop_controller.update(output_accel, CS.vEgo, CS.aEgo, CS.standstill,
                                                   should_stop or sng_launch_failed, lead)
      self.reset()
      self.accel_smoother.reset(output_accel)

    elif self.long_control_state == LongCtrlState.starting:
      self.coast_controller.reset()
      self.lead_approach_controller.reset()
      self.lead_trend_anticipator.reset()
      self.stop_controller.reset()
      self.reset()
      if self.sng_ui_phase is not None:
        # Explicit, bounded brake release: zero gas and zero friction brake.
        # Do not apply startAccel before creep and PCM acceptance.
        output_accel = 0.0
        self.accel_smoother.reset(output_accel)
      elif self.wayon_carrot_profile:
        v_target_now = float(long_plan.speeds[0]) if len(long_plan.speeds) else CS.vEgo
        lead = radar_state.leadOne if radar_state is not None else None
        cutin_risk = cutin_risk_for_control(radar_state) if radar_state is not None else None
        output_accel = self.accel_smoother.update(
          self.CP.startAccel, CS.aEgo, CS.vEgo, v_target_now,
          planned_jerk=float(getattr(long_plan, "jTargetNow", 0.0)),
          lead=lead, cutin_risk=cutin_risk, accel_limits=(accel_limits[0], accel_limits[1]),
          launch_transition=True)
      else:
        output_accel = self.CP.startAccel
        self.accel_smoother.reset(output_accel)

    else:  # LongCtrlState.pid
      if self.speed_pid_enabled:
        v_target_now = (queue_creep.target_speed if queue_creep.active else
                        float(long_plan.speeds[0]) if len(long_plan.speeds) else CS.vEgo)
        error = v_target_now - CS.vEgo
        if queue_creep.active:
          creep_speed = max(abs(CS.vEgo), abs(CS.vEgoRaw))
          output_accel = get_queue_creep_accel(v_target_now, creep_speed, CS.aEgo)
          self.speed_pid.reset()
        else:
          output_accel = self.speed_pid.update(error, speed=CS.vEgo, feedforward=a_target * self.speed_pid_kf)
        self.pid.reset()
        cutin_risk = cutin_risk_for_control(radar_state) if radar_state is not None else None
        automatic_control = icbm_blocks_coast(icbm, CS.vEgo)
        lead_safety_cap = self.lead_approach_controller.update(
          active, CS.vEgo, lead, self.response_learner.response_delay(CS.vEgo))
        if queue_creep.active:
          self.coast_controller.reset()
          self.lead_trend_anticipator.reset()
        regular_coast = not queue_creep.active and self.coast_controller.update(
          active, CS.vEgo, v_target_now, output_accel, pitch, automatic_control, lead, cutin_risk,
          measured_accel=CS.aEgo, previous_accel=self.last_output_accel, lead_accel_cap=lead_safety_cap)
        anticipatory_coast = not queue_creep.active and self.lead_trend_anticipator.update(
          active and self.wayon_carrot_profile, CS.vEgo, output_accel, CS.aEgo, lead)
        if regular_coast or anticipatory_coast:
          output_accel = 0.0
        else:
          output_accel = apply_uphill_accel_compensation(output_accel, CS.vEgo, v_target_now, pitch)
        if not queue_creep.active:
          output_accel = self.response_learner.correction(output_accel, CS.vEgo)
        if lead_safety_cap is not None:
          output_accel = min(output_accel, lead_safety_cap)
        if queue_creep.active:
          output_accel = rate_limit_queue_creep_accel(output_accel, self.last_output_accel)
          self.accel_smoother.reset(output_accel)
        else:
          output_accel = self.accel_smoother.update(
            output_accel, CS.aEgo, CS.vEgo, v_target_now,
            planned_jerk=float(getattr(long_plan, "jTargetNow", 0.0)),
            lead=lead, cutin_risk=cutin_risk, accel_limits=(accel_limits[0], accel_limits[1]),
            throttle_release=anticipatory_coast, override_release=override_released)
      else:
        error = a_target - CS.aEgo
        output_accel = self.pid.update(error, speed=CS.vEgo, feedforward=a_target)
        self.speed_pid.reset()

    if self.sng_unacked_follow:
      output_accel = min(output_accel, 0.0)
      if self.accel_smoother.output_accel > 0.0:
        self.accel_smoother.reset(output_accel)
    self.last_output_accel = np.clip(output_accel, accel_limits[0], accel_limits[1])
    lead = radar_state.leadOne if radar_state is not None else None
    cutin_risk = cutin_risk_for_control(radar_state) if radar_state is not None else None
    urgent = bool((lead is not None and getattr(lead, "status", False) and
                   (getattr(lead, "dRel", 1000.0) < 8.0 or getattr(lead, "vRel", 0.0) < -2.0)) or
                  (cutin_risk is not None and getattr(cutin_risk, "status", False) and
                   getattr(cutin_risk, "score", 0.0) > 0.35))
    self.response_learner.update(self.last_output_accel, CS.aEgo, CS.vEgo,
                                 self.wayon_carrot_profile and active and self.long_control_state == LongCtrlState.pid,
                                 pitch, CS.gasPressed, CS.brakePressed, urgent)
    return self.last_output_accel
