import numpy as np
from cereal import car
from openpilot.common.realtime import DT_CTRL
from openpilot.selfdrive.controls.lib.drive_helpers import CONTROL_N
from openpilot.common.pid import PIDController
from openpilot.selfdrive.modeld.constants import ModelConstants
from openpilot.sunnypilot.selfdrive.controls.lib.wayon_carrot_long_profile import PID_KF, PID_KI, PID_KP, is_enabled

CONTROL_N_T_IDX = ModelConstants.T_IDXS[:CONTROL_N]

LongCtrlState = car.CarControl.Actuators.LongControlState

SOFT_HOLD_LEAD_CONFIRM_FRAMES = round(0.12 / DT_CTRL)
SOFT_HOLD_LEAD_MIN_DISTANCE = 4.0
SOFT_HOLD_LEAD_MAX_DISTANCE = 10.0
SOFT_HOLD_LEAD_MIN_REL_SPEED = 0.4


def long_control_state_trans(CP, CP_SP, active, long_control_state, v_ego,
                             should_stop, brake_pressed, cruise_standstill,
                             soft_hold_resume=False):
  # Gas Interceptor
  cruise_standstill = cruise_standstill and not CP_SP.enableGasInterceptor

  stopping_condition = should_stop
  starting_condition = (not should_stop and
                        (not cruise_standstill or soft_hold_resume) and
                        not brake_pressed)
  started_condition = v_ego > CP.vEgoStarting

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
    self.last_output_accel = 0.0
    self.soft_hold_lead_frames = 0
    self.soft_hold_resume_ready = False

  def reset(self):
    self.pid.reset()
    self.speed_pid.reset()

  def update_soft_hold_resume(self, CS, long_plan, radar_state):
    lead = radar_state.leadOne if radar_state is not None else None
    lead_departing = (self.wayon_carrot_profile and CS.brakeHoldActive and not CS.brakePressed and
                      lead is not None and lead.status and
                      SOFT_HOLD_LEAD_MIN_DISTANCE < lead.dRel < SOFT_HOLD_LEAD_MAX_DISTANCE and
                      lead.vRel > SOFT_HOLD_LEAD_MIN_REL_SPEED)
    self.soft_hold_lead_frames = min(self.soft_hold_lead_frames + 1, SOFT_HOLD_LEAD_CONFIRM_FRAMES) if lead_departing else 0
    self.soft_hold_resume_ready = (lead_departing and
                                   self.soft_hold_lead_frames >= SOFT_HOLD_LEAD_CONFIRM_FRAMES and
                                   not long_plan.shouldStop)
    return self.soft_hold_resume_ready

  def update(self, active, CS, long_plan, accel_limits, radar_state=None):
    """Update longitudinal control. This updates the state machine and runs a PID loop"""
    a_target = long_plan.aTarget
    should_stop = long_plan.shouldStop
    self.pid.neg_limit = accel_limits[0]
    self.pid.pos_limit = accel_limits[1]
    self.speed_pid.neg_limit = accel_limits[0]
    self.speed_pid.pos_limit = accel_limits[1]
    if active:
      soft_hold_resume = self.update_soft_hold_resume(CS, long_plan, radar_state)
    else:
      self.soft_hold_lead_frames = 0
      self.soft_hold_resume_ready = False
      soft_hold_resume = False

    self.long_control_state = long_control_state_trans(self.CP, self.CP_SP, active, self.long_control_state, CS.vEgo,
                                                       should_stop, CS.brakePressed,
                                                       CS.cruiseState.standstill, soft_hold_resume)
    if self.long_control_state == LongCtrlState.off:
      self.reset()
      output_accel = 0.

    elif self.long_control_state == LongCtrlState.stopping:
      output_accel = self.last_output_accel
      if output_accel > self.CP.stopAccel:
        output_accel = min(output_accel, 0.0)
        output_accel -= self.CP.stoppingDecelRate * DT_CTRL
      self.reset()

    elif self.long_control_state == LongCtrlState.starting:
      output_accel = self.CP.startAccel
      self.reset()

    else:  # LongCtrlState.pid
      if self.speed_pid_enabled:
        v_target_now = float(long_plan.speeds[0]) if len(long_plan.speeds) else CS.vEgo
        error = v_target_now - CS.vEgo
        output_accel = self.speed_pid.update(error, speed=CS.vEgo, feedforward=a_target * self.speed_pid_kf)
        self.pid.reset()
      else:
        error = a_target - CS.aEgo
        output_accel = self.pid.update(error, speed=CS.vEgo, feedforward=a_target)
        self.speed_pid.reset()

    self.last_output_accel = np.clip(output_accel, accel_limits[0], accel_limits[1])
    return self.last_output_accel
