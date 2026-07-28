#!/usr/bin/env python3
"""FrogPilot C3 NNFF lateral controller adapted to the current controlsd API."""

import math
import os
from collections import deque

import numpy as np

from cereal import log
from openpilot.common.constants import ACCELERATION_DUE_TO_GRAVITY
from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.common.pid import PIDController
from openpilot.selfdrive.controls.lib.drive_helpers import CONTROL_N
from openpilot.selfdrive.controls.lib.latcontrol import LatControl
from openpilot.selfdrive.modeld.constants import ModelConstants
from openpilot.sunnypilot.selfdrive.controls.lib.latcontrol_torque_ext_base import (
  LAT_PLAN_MIN_IDX,
  get_lookahead_value,
  get_predicted_lateral_jerk,
  sign,
)
from openpilot.sunnypilot.selfdrive.controls.lib.nnlc.helpers import MOCK_MODEL_PATH
from openpilot.sunnypilot.selfdrive.controls.lib.nnlc.model import NNTorqueModel


LOW_SPEED_X = [0, 10, 20, 30]
LOW_SPEED_Y = [12, 3, 1, 0]
KP = 1.0
KI = 0.3
VERSION = 3


def roll_pitch_adjust(roll, pitch):
  return roll * math.cos(pitch)


class _C3NNFFExtension:
  """Compatibility surface expected by the current controlsd torque path."""

  def __init__(self, controller):
    self.controller = controller

  def update_limits(self):
    self.controller.update_limits()

  def update_lateral_lag(self, lag):
    self.controller.update_live_delay(lag)

  def update_model_v2(self, model_v2):
    self.controller.model_v2 = model_v2


class LatControlNNFFC3(LatControl):
  """The Full NNFF controller used by the testing-v1-apn C3 branch."""

  def __init__(self, CP, CP_SP, CI, dt):
    super().__init__(CP, CP_SP, CI, dt)

    model_path = CP_SP.neuralNetworkLateralControl.model.path
    self.nnff_loaded = model_path != MOCK_MODEL_PATH and os.path.isfile(model_path)
    self.lat_torque_nn_model = NNTorqueModel(model_path) if self.nnff_loaded else None
    self.model_path = model_path
    self.model_v2 = None

    self.torque_params = CP.lateralTuning.torque.as_builder()
    self.pid = PIDController(KP, KI, 0.0, pos_limit=self.steer_max,
                             neg_limit=-self.steer_max, rate=1 / self.dt)
    self.torque_from_lateral_accel = CI.torque_from_lateral_accel()
    self.steering_angle_deadzone_deg = self.torque_params.steeringAngleDeadzoneDeg

    self.friction_look_ahead_bp = [9.0, 30.0]
    self.friction_look_ahead_v = [1.4, 2.0]
    self.lat_accel_friction_factor = 0.7
    self.lat_jerk_friction_factor = 0.4
    self.t_diffs = np.diff(ModelConstants.T_IDXS)

    self.pitch = FirstOrderFilter(0.0, 0.5, self.dt)
    self.nn_friction_override = (
      self.lat_torque_nn_model.friction_override if self.lat_torque_nn_model else False
    )

    self.future_times = [0.3, 0.6, 1.0, 1.5]
    self.nn_future_times = [time + CP.steerActuatorDelay for time in self.future_times]
    self.past_times = [-0.3, -0.2, -0.1]
    history_check_frames = [int(abs(time) / self.dt) for time in self.past_times]
    self.history_frame_offsets = [history_check_frames[0] - frame for frame in history_check_frames]
    self.lateral_accel_desired_deque = deque(maxlen=history_check_frames[0])
    self.roll_deque = deque(maxlen=history_check_frames[0])
    self.past_future_len = len(self.past_times) + len(self.nn_future_times)

    self.extension = _C3NNFFExtension(self)

  def update_limits(self):
    self.pid.set_limits(self.steer_max, -self.steer_max)

  def update_live_delay(self, lat_delay):
    delay = max(0.01, float(lat_delay))
    self.nn_future_times = [time + delay for time in self.future_times]
    self.past_future_len = len(self.past_times) + len(self.nn_future_times)

  def update_live_torque_params(self, latAccelFactor, latAccelOffset, friction):
    self.torque_params.latAccelFactor = latAccelFactor
    self.torque_params.latAccelOffset = latAccelOffset
    self.torque_params.friction = friction

  def update(self, active, CS, VM, params, steer_limited_by_safety,
             desired_curvature, calibrated_pose, curvature_limited, lat_delay):
    pid_log = log.ControlsState.LateralTorqueState.new_message()
    pid_log.version = VERSION

    if not active:
      output_torque = 0.0
      pid_log.active = False
    else:
      delay = max(0.01, float(lat_delay))

      actual_curvature = -VM.calc_curvature(
        math.radians(CS.steeringAngleDeg - params.angleOffsetDeg),
        CS.vEgo,
        params.roll,
      )
      roll_compensation = params.roll * ACCELERATION_DUE_TO_GRAVITY
      desired_lateral_accel = desired_curvature * CS.vEgo ** 2
      actual_lateral_accel = actual_curvature * CS.vEgo ** 2

      low_speed_factor = float(np.interp(CS.vEgo, LOW_SPEED_X, LOW_SPEED_Y)) ** 2
      setpoint = desired_lateral_accel + low_speed_factor * desired_curvature
      measurement = actual_lateral_accel + low_speed_factor * actual_curvature
      gravity_adjusted_lateral_accel = desired_lateral_accel - roll_compensation

      model_good = (
        self.model_v2 is not None and
        len(self.model_v2.orientation.x) >= CONTROL_N
      )
      lookahead_lateral_jerk = 0.0

      if self.nnff_loaded and model_good:
        actual_curvature_rate = -VM.calc_curvature(
          math.radians(CS.steeringRateDeg), CS.vEgo, 0.0)
        actual_lateral_jerk = actual_curvature_rate * CS.vEgo ** 2

        lookahead = float(np.interp(
          CS.vEgo, self.friction_look_ahead_bp, self.friction_look_ahead_v))
        friction_upper_idx = next(
          (index for index, value in enumerate(ModelConstants.T_IDXS) if value > lookahead),
          16,
        )
        predicted_lateral_jerk = get_predicted_lateral_jerk(
          self.model_v2.acceleration.y, self.t_diffs)
        desired_lateral_jerk = (
          np.interp(delay, ModelConstants.T_IDXS, self.model_v2.acceleration.y) -
          desired_lateral_accel
        ) / delay
        lookahead_lateral_jerk = get_lookahead_value(
          predicted_lateral_jerk[LAT_PLAN_MIN_IDX:friction_upper_idx],
          desired_lateral_jerk,
        )

        if lookahead_lateral_jerk == 0.0:
          actual_lateral_jerk = 0.0
          self.lat_accel_friction_factor = 1.0

        lateral_jerk_setpoint = self.lat_jerk_friction_factor * lookahead_lateral_jerk
        lateral_jerk_measurement = self.lat_jerk_friction_factor * actual_lateral_jerk

        pitch = 0.0
        roll = params.roll
        if calibrated_pose is not None:
          pitch = self.pitch.update(calibrated_pose.orientation.pitch)
          roll = roll_pitch_adjust(roll, pitch)

        self.roll_deque.append(roll)
        self.lateral_accel_desired_deque.append(desired_lateral_accel)

        adjusted_future_times = [
          time + 0.5 * CS.aEgo * (time / max(CS.vEgo, 1.0))
          for time in self.nn_future_times
        ]
        past_rolls = [
          self.roll_deque[min(len(self.roll_deque) - 1, offset)]
          for offset in self.history_frame_offsets
        ]
        future_rolls = [
          roll_pitch_adjust(
            np.interp(time, ModelConstants.T_IDXS, self.model_v2.orientation.x) + roll,
            np.interp(time, ModelConstants.T_IDXS, self.model_v2.orientation.y) + pitch,
          )
          for time in adjusted_future_times
        ]
        past_lateral_accels_desired = [
          self.lateral_accel_desired_deque[min(
            len(self.lateral_accel_desired_deque) - 1, offset)]
          for offset in self.history_frame_offsets
        ]
        future_lateral_accels = [
          np.interp(time, ModelConstants.T_IDXS, self.model_v2.acceleration.y)
          for time in adjusted_future_times
        ]

        nnff_common = past_rolls + future_rolls
        nnff_setpoint_input = (
          [CS.vEgo, setpoint, lateral_jerk_setpoint, roll] +
          [setpoint] * self.past_future_len +
          nnff_common
        )
        nnff_measurement_input = (
          [CS.vEgo, measurement, lateral_jerk_measurement, roll] +
          [measurement] * self.past_future_len +
          nnff_common
        )

        torque_from_setpoint = self.lat_torque_nn_model.evaluate(nnff_setpoint_input)
        torque_from_measurement = self.lat_torque_nn_model.evaluate(nnff_measurement_input)
        pid_log.error = torque_from_setpoint - torque_from_measurement

        error_blend = float(np.interp(
          abs(desired_lateral_accel), [1.0, 2.0], [0.0, 1.0]))
        if error_blend > 0.0:
          torque_from_error = self.lat_torque_nn_model.evaluate([
            CS.vEgo,
            setpoint - measurement,
            lateral_jerk_setpoint - lateral_jerk_measurement,
            0.0,
          ])
          if (sign(pid_log.error) == sign(torque_from_error) and
              abs(pid_log.error) < abs(torque_from_error)):
            pid_log.error = float(
              pid_log.error * (1.0 - error_blend) +
              torque_from_error * error_blend
            )

        friction_input = (
          self.lat_accel_friction_factor * (setpoint - measurement) +
          self.lat_jerk_friction_factor * lookahead_lateral_jerk
        )
        nn_input = (
          [CS.vEgo, desired_lateral_accel, friction_input, roll] +
          past_lateral_accels_desired +
          future_lateral_accels +
          nnff_common
        )
        ff = self.lat_torque_nn_model.evaluate(nn_input)

        if self.nn_friction_override:
          pid_log.error += self.torque_from_lateral_accel(
            0.0, self.torque_params)
      else:
        torque_from_measurement = self.torque_from_lateral_accel(
          measurement, self.torque_params)
        torque_from_setpoint = self.torque_from_lateral_accel(
          setpoint, self.torque_params)
        pid_log.error = float(torque_from_setpoint - torque_from_measurement)
        ff = self.torque_from_lateral_accel(
          gravity_adjusted_lateral_accel, self.torque_params)

      freeze_integrator = (
        steer_limited_by_safety or CS.steeringPressed or CS.vEgo < 5
      )
      output_torque = self.pid.update(
        pid_log.error,
        feedforward=ff,
        speed=CS.vEgo,
        freeze_integrator=freeze_integrator,
      )

      pid_log.active = True
      pid_log.p = float(self.pid.p)
      pid_log.i = float(self.pid.i)
      pid_log.d = float(self.pid.d)
      pid_log.f = float(self.pid.f)
      pid_log.output = float(-output_torque)
      pid_log.actualLateralAccel = float(actual_lateral_accel)
      pid_log.desiredLateralAccel = float(desired_lateral_accel)
      pid_log.desiredLateralJerk = float(lookahead_lateral_jerk)
      pid_log.saturated = bool(self._check_saturation(
        self.steer_max - abs(output_torque) < 1e-3,
        CS,
        steer_limited_by_safety,
        curvature_limited,
      ))

    return -output_torque, 0.0, pid_log
