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
  get_max_accel as get_wayon_max_accel,
  is_enabled,
)
from openpilot.sunnypilot.selfdrive.controls.lib.adaptive_longitudinal_smoother import AdaptiveLongitudinalSmoother
from openpilot.sunnypilot.selfdrive.controls.lib.radar_lead_helpers import cutin_risk_for_control
from openpilot.sunnypilot.selfdrive.controls.lib.wayon_longitudinal_coordinator import (
  LeadTrendAnticipator,
  LongitudinalResponseLearner,
  LowSpeedStopController,
  WayonCoastController,
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


def use_gm_auto_hold_sng(CP) -> bool:
  return getattr(CP, "brand", "") == "gm" and bool(getattr(CP, "autoResumeSng", False))


def gm_cruise_active(CS) -> bool:
  # Traverse CarState only marks raw ACTIVE/STANDSTILL as enabled. In
  # particular, OFF, FAULTED and unknown PCM states are not resume ACKs.
  return CS.canValid and CS.cruiseState.enabled and not CS.cruiseState.standstill and not CS.accFaulted


def long_control_state_trans(CP, CP_SP, active, long_control_state, v_ego,
                             should_stop, brake_pressed, cruise_standstill,
                             sng_resume=False):
  # Gas Interceptor
  cruise_standstill = cruise_standstill and not CP_SP.enableGasInterceptor

  stopping_condition = should_stop
  # Traverse keeps the ACC full-stop latch clear and uses GM hydraulic hold.
  # Treat a physically stopped GM Hold as latched until the existing lead
  # departure detector explicitly opens the launch window.
  gm_hold_standstill = use_gm_auto_hold_sng(CP) and v_ego <= max(CP.vEgoStopping, 0.05)
  launch_latched = cruise_standstill or gm_hold_standstill
  starting_condition = (not should_stop and
                        (not launch_latched or sng_resume) and
                        not brake_pressed)
  started_condition = v_ego > CP.vEgoStarting and not (use_gm_auto_hold_sng(CP) and cruise_standstill)

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
    self.lead_trend_anticipator = LeadTrendAnticipator()
    self.stop_controller = LowSpeedStopController()
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
    if clear_attempt:
      self.sng_resume_attempted = False
      self.sng_resume_failed = False
      self.sng_resume_succeeded = False
      self.sng_resume_moved = False
      self.sng_manual_resume = False

  def fail_sng_resume(self, reason="conditions_changed"):
    if self.sng_ui_resume:
      cloudlog.event("gm_manual_resume", stage="stopped", reason=reason)
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
      self.reset_sng_resume()
      return False

    if self.sng_resume_attempted and gm_cruise_active(CS) and CS.vEgo > self.CP.vEgoStarting:
      self.sng_resume_moved = True
    if (self.sng_resume_succeeded and self.sng_resume_moved and CS.standstill and abs(CS.vEgo) < 0.05 and
        self.long_control_state == LongCtrlState.stopping):
      # A successful low-speed launch can be followed by another stop without
      # ever reaching 1.5 m/s in traffic. Confirm that new stop from scratch.
      self.reset_sng_resume()

    # A physical RES is an explicit driver retry, not permission for another
    # synthetic burst. Keep the normal planner/lead and driver-override gates.
    manual_resume = any(b.type == car.CarState.ButtonEvent.Type.accelCruise and b.pressed for b in CS.buttonEvents)
    cruise_valid = CS.canValid and CS.cruiseState.enabled and not CS.accFaulted
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
      self.fail_sng_resume()
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
        self.fail_sng_resume()
        return False
      self.sng_resume_frames += 1
      # An already ACTIVE PCM cannot acknowledge a new hold-only request.
      # Require observed motion for that path; wheel creep alone still cannot
      # acknowledge a request that began with PCM standstill latched.
      started = self.sng_ui_phase != "release" and not self.sng_ui_creep and gm_cruise_active(CS) and (not self.sng_ui_hold_release or
                                         (not CS.standstill and CS.vEgo > self.CP.vEgoStarting))
      self.sng_started_frames = self.sng_started_frames + 1 if started else 0
      if self.sng_started_frames >= SNG_STARTED_CONFIRM_FRAMES:
        if self.sng_ui_resume:
          cloudlog.event("gm_manual_resume", stage="accepted", speed=float(CS.vEgo))
        self.reset_sng_resume(clear_attempt=False)
        self.sng_resume_succeeded = True
        return False
      timeout = SNG_MANUAL_RELEASE_TIMEOUT if self.sng_ui_phase == "release" else SNG_RESUME_TIMEOUT_FRAMES * DT_CTRL
      if self.sng_resume_started_at is None or now - self.sng_resume_started_at >= timeout:
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
    lead_departing = (self.sng_stop_frames >= SNG_STOP_CONFIRM_FRAMES and not long_plan.shouldStop and
                     (lead.vRel > SNG_LEAD_MIN_REL_SPEED or lead.dRel - self.sng_lead_baseline_m > SNG_LEAD_MIN_DISTANCE_DELTA))
    self.sng_lead_frames = min(self.sng_lead_frames + 1, SNG_LEAD_CONFIRM_FRAMES) if lead_departing else 0
    if self.sng_lead_frames >= SNG_LEAD_CONFIRM_FRAMES:
      self.sng_resume_ready = True
      self.sng_resume_attempted = True
      self.sng_resume_moved = False
      self.sng_resume_started_at = now
    return self.sng_resume_ready

  def update(self, active, CS, long_plan, accel_limits, radar_state=None, icbm=None, pitch=0.0, manual_resume=False,
             manual_resume_sensors_valid=False):
    """Update longitudinal control. This updates the state machine and runs a PID loop"""
    a_target = long_plan.aTarget
    should_stop = long_plan.shouldStop
    if self.wayon_carrot_profile:
      accel_limits = (accel_limits[0], min(accel_limits[1], get_wayon_max_accel(CS.vEgo)))
    self.pid.neg_limit = accel_limits[0]
    self.pid.pos_limit = accel_limits[1]
    self.speed_pid.neg_limit = accel_limits[0]
    self.speed_pid.pos_limit = accel_limits[1]
    sng_resume = self.update_sng_resume(active, CS, long_plan, radar_state, manual_resume=manual_resume,
                                       manual_resume_sensors_valid=manual_resume_sensors_valid)
    should_stop = should_stop and not self.sng_ui_creep
    sng_launch_failed = (self.CP.autoResumeSng and self.sng_resume_attempted and not sng_resume and
                         self.long_control_state == LongCtrlState.starting and CS.vEgo <= self.CP.vEgoStarting)
    if use_gm_auto_hold_sng(self.CP):
      sng_launch_failed = self.sng_resume_failed

    self.long_control_state = long_control_state_trans(self.CP, self.CP_SP, active, self.long_control_state, CS.vEgo,
                                                       should_stop or sng_launch_failed, CS.brakePressed,
                                                       CS.cruiseState.standstill, sng_resume)
    if self.sng_ui_phase is not None:
      self.long_control_state = LongCtrlState.starting
    if self.long_control_state == LongCtrlState.off:
      self.reset()
      self.coast_controller.reset()
      self.lead_trend_anticipator.reset()
      self.stop_controller.reset()
      output_accel = 0.
      self.accel_smoother.reset(CS.aEgo)

    elif self.long_control_state == LongCtrlState.stopping:
      self.coast_controller.reset()
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
          lead=lead, cutin_risk=cutin_risk, accel_limits=(accel_limits[0], accel_limits[1]))
      else:
        output_accel = self.CP.startAccel
        self.accel_smoother.reset(output_accel)

    else:  # LongCtrlState.pid
      if self.speed_pid_enabled:
        v_target_now = float(long_plan.speeds[0]) if len(long_plan.speeds) else CS.vEgo
        error = v_target_now - CS.vEgo
        output_accel = self.speed_pid.update(error, speed=CS.vEgo, feedforward=a_target * self.speed_pid_kf)
        self.pid.reset()
        lead = radar_state.leadOne if radar_state is not None else None
        cutin_risk = cutin_risk_for_control(radar_state) if radar_state is not None else None
        automatic_control = bool(icbm is not None and getattr(icbm, "automaticControlActive", False))
        regular_coast = self.coast_controller.update(active, CS.vEgo, v_target_now, output_accel, pitch,
                                                     automatic_control, lead, cutin_risk,
                                                     measured_accel=CS.aEgo,
                                                     previous_accel=self.last_output_accel)
        anticipatory_coast = self.lead_trend_anticipator.update(
          active and self.wayon_carrot_profile, CS.vEgo, output_accel, CS.aEgo, lead)
        if regular_coast or anticipatory_coast:
          output_accel = 0.0
        output_accel = self.response_learner.correction(output_accel, CS.vEgo)
        output_accel = self.accel_smoother.update(
          output_accel, CS.aEgo, CS.vEgo, v_target_now,
          planned_jerk=float(getattr(long_plan, "jTargetNow", 0.0)),
          lead=lead, cutin_risk=cutin_risk, accel_limits=(accel_limits[0], accel_limits[1]),
          throttle_release=anticipatory_coast)
      else:
        error = a_target - CS.aEgo
        output_accel = self.pid.update(error, speed=CS.vEgo, feedforward=a_target)
        self.speed_pid.reset()

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
