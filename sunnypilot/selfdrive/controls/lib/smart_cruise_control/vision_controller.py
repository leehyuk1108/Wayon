"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import numpy as np

import cereal.messaging as messaging
from cereal import custom
from openpilot.common.params import Params
from openpilot.common.realtime import DT_MDL
from openpilot.selfdrive.car.cruise import V_CRUISE_UNSET
from openpilot.sunnypilot import PARAMS_UPDATE_PERIOD
from openpilot.sunnypilot.selfdrive.controls.lib.smart_cruise_control import MIN_V

VisionState = custom.LongitudinalPlanSP.SmartCruiseControl.VisionState

ACTIVE_STATES = (VisionState.entering, VisionState.turning, VisionState.leaving)
ENABLED_STATES = (VisionState.enabled, VisionState.overriding, *ACTIVE_STATES)

_ENTERING_PRED_LAT_ACC_TH = 1.3  # Predicted Lat Acc threshold to trigger entering turn state.
_ABORT_ENTERING_PRED_LAT_ACC_TH = 1.1  # Predicted Lat Acc threshold to abort entering state if speed drops.

_TURNING_LAT_ACC_TH = 1.6  # Lat Acc threshold to trigger turning state.

_LEAVING_LAT_ACC_TH = 1.3  # Lat Acc threshold to trigger leaving turn state.
_FINISH_LAT_ACC_TH = 1.1  # Lat Acc threshold to trigger the end of the turn cycle.

_A_LAT_REG_MAX = 2.  # Comfortable maximum lateral acceleration.
_COMFORTABLE_DECEL = 1.2  # m/s^2. Maximum planned longitudinal deceleration.
_REACTION_TIME = 0.7  # s. Account for controller and vehicle response delay.
_CURVATURE_FLOOR = 1e-4
_CURVATURE_FILTER_WINDOW = 5
_TARGET_ENTER_TAU = 0.35  # s. React promptly to a curve ahead.
_TARGET_EXIT_TAU = 1.5  # s. Restore speed slowly after the curve clears.
_CURVE_CONFIRM_TIME = 0.25  # s. Reject short-lived model predictions.
_CURVE_RELEASE_TIME = 0.5  # s. Avoid toggling off between adjacent curve samples.

# Lookup table for the minimum smooth deceleration during the ENTERING state
# depending on the actual maximum absolute lateral acceleration predicted on the turn ahead.
_ENTERING_SMOOTH_DECEL_V = [-0.2, -1.]  # min decel value allowed on ENTERING state
_ENTERING_SMOOTH_DECEL_BP = [1.3, 3.]  # absolute value of lat acc ahead

# Lookup table for the acceleration for the TURNING state
# depending on the current lateral acceleration of the vehicle.
_TURNING_ACC_V = [0.5, 0., -0.4]  # acc value
_TURNING_ACC_BP = [1.5, 2.3, 3.]  # absolute value of current lat acc

_LEAVING_ACC = 0.5  # Conformable acceleration to regain speed while leaving a turn.


class SmartCruiseControlVision:
  v_target: float = 0
  a_target: float = 0.
  v_ego: float = 0.
  a_ego: float = 0.
  output_v_target: float = V_CRUISE_UNSET
  output_a_target: float = 0.

  def __init__(self):
    self.params = Params()
    self.frame = -1
    self.long_enabled = False
    self.long_override = False
    self.is_enabled = False
    self.is_active = False
    self.enabled = self.params.get_bool("SmartCruiseControlVision")
    self.v_cruise_setpoint = 0.

    self.state = VisionState.disabled
    self.current_lat_acc = 0.
    self.max_pred_lat_acc = 0.
    self.raw_v_target = V_CRUISE_UNSET
    self.curve_confirm_frames = 0
    self.curve_release_frames = 0

  def get_a_target_from_control(self) -> float:
    return self.a_target

  def get_v_target_from_control(self) -> float:
    if self.is_active:
      return max(self.v_target, MIN_V)

    return V_CRUISE_UNSET

  def _update_params(self) -> None:
    if self.frame % int(PARAMS_UPDATE_PERIOD / DT_MDL) == 0:
      self.enabled = self.params.get_bool("SmartCruiseControlVision")

  @staticmethod
  def _smooth_curvature(curvature: np.ndarray) -> np.ndarray:
    if len(curvature) < 3:
      return curvature

    radius = _CURVATURE_FILTER_WINDOW // 2
    padded = np.pad(curvature, (radius, radius), mode="edge")
    return np.array([
      np.median(padded[i:i + _CURVATURE_FILTER_WINDOW])
      for i in range(len(curvature))
    ])

  def _distance_speed_profile(self, sm: messaging.SubMaster) -> tuple[float, float]:
    model = sm['modelV2']
    count = min(len(model.position.x), len(model.orientationRate.z), len(model.velocity.x))
    if count < 3:
      return V_CRUISE_UNSET, 0.

    distance = np.asarray(model.position.x, dtype=float)[:count]
    yaw_rate = np.abs(np.asarray(model.orientationRate.z, dtype=float)[:count])
    velocity = np.abs(np.asarray(model.velocity.x, dtype=float)[:count])
    valid = np.isfinite(distance) & np.isfinite(yaw_rate) & np.isfinite(velocity) & (distance >= 0.) & (velocity > 1.)
    if np.count_nonzero(valid) < 3:
      return V_CRUISE_UNSET, 0.

    distance = distance[valid]
    curvature = self._smooth_curvature(yaw_rate[valid] / velocity[valid])
    predicted_lat_acc = curvature * self.v_ego ** 2
    max_pred_lat_acc = float(np.max(predicted_lat_acc))

    safe_curve_speed = np.sqrt(_A_LAT_REG_MAX / np.maximum(curvature, _CURVATURE_FLOOR))
    effective_distance = np.maximum(distance - self.v_ego * _REACTION_TIME, 0.)
    allowed_speed_now = np.sqrt(safe_curve_speed ** 2 + 2. * _COMFORTABLE_DECEL * effective_distance)
    return float(np.min(allowed_speed_now)), max_pred_lat_acc

  def _filter_target(self, raw_target: float) -> None:
    if not np.isfinite(raw_target) or raw_target >= V_CRUISE_UNSET:
      raw_target = self.v_cruise_setpoint if self.v_cruise_setpoint > 0. else V_CRUISE_UNSET

    if self.v_target <= 0. or self.v_target >= V_CRUISE_UNSET:
      self.v_target = raw_target
      return

    tau = _TARGET_ENTER_TAU if raw_target < self.v_target else _TARGET_EXIT_TAU
    alpha = DT_MDL / (tau + DT_MDL)
    self.v_target += alpha * (raw_target - self.v_target)

  def _update_calculations(self, sm: messaging.SubMaster) -> None:
    if not self.long_enabled:
      return

    self.current_lat_acc = self.v_ego ** 2 * abs(sm['controlsState'].curvature)
    profile_target, self.max_pred_lat_acc = self._distance_speed_profile(sm)
    cruise_target = self.v_cruise_setpoint if self.v_cruise_setpoint > 0. else V_CRUISE_UNSET
    self.raw_v_target = min(profile_target, cruise_target)
    self._filter_target(self.raw_v_target)

    curve_predicted = self.v_ego > MIN_V and self.max_pred_lat_acc >= _ENTERING_PRED_LAT_ACC_TH
    if curve_predicted:
      self.curve_confirm_frames = min(self.curve_confirm_frames + 1, int(_CURVE_CONFIRM_TIME / DT_MDL) + 1)
      self.curve_release_frames = 0
    else:
      self.curve_confirm_frames = 0
      self.curve_release_frames += 1

  def _update_state_machine(self) -> tuple[bool, bool]:
    # ENABLED, ENTERING, TURNING, LEAVING, OVERRIDING
    if self.state != VisionState.disabled:
      # longitudinal and feature disable always have priority in a non-disabled state
      if not self.long_enabled or not self.enabled:
        self.state = VisionState.disabled
      elif self.long_override:
        self.state = VisionState.overriding

      else:
        # ENABLED
        if self.state == VisionState.enabled:
          # Do not enter a turn control cycle if the speed is low.
          if self.v_ego <= MIN_V:
            pass
          # If significant lateral acceleration is predicted ahead, then move to Entering turn state.
          elif self.curve_confirm_frames >= int(_CURVE_CONFIRM_TIME / DT_MDL):
            self.state = VisionState.entering

        # OVERRIDING
        elif self.state == VisionState.overriding:
          if not self.long_override:
            self.state = VisionState.enabled

        # ENTERING
        elif self.state == VisionState.entering:
          # Transition to Turning if current lateral acceleration is over the threshold.
          if self.current_lat_acc >= _TURNING_LAT_ACC_TH:
            self.state = VisionState.turning
          # Abort if the predicted lateral acceleration drops
          elif (self.max_pred_lat_acc < _ABORT_ENTERING_PRED_LAT_ACC_TH and
                self.curve_release_frames >= int(_CURVE_RELEASE_TIME / DT_MDL)):
            self.state = VisionState.enabled

        # TURNING
        elif self.state == VisionState.turning:
          # Transition to Leaving if current lateral acceleration drops below a threshold.
          if self.current_lat_acc <= _LEAVING_LAT_ACC_TH:
            self.state = VisionState.leaving

        # LEAVING
        elif self.state == VisionState.leaving:
          # Transition back to Turning if current lateral acceleration goes back over the threshold.
          if self.current_lat_acc >= _TURNING_LAT_ACC_TH:
            self.state = VisionState.turning
          # Finish if current lateral acceleration goes below a threshold.
          elif self.current_lat_acc < _FINISH_LAT_ACC_TH:
            self.state = VisionState.enabled

    # DISABLED
    elif self.state == VisionState.disabled:
      if self.long_enabled and self.enabled:
        if self.long_override:
          self.state = VisionState.overriding
        else:
          self.state = VisionState.enabled

    enabled = self.state in ENABLED_STATES
    active = self.state in ACTIVE_STATES

    return enabled, active

  def _update_solution(self) -> float:
    # DISABLED, ENABLED, OVERRIDING
    if self.state not in ACTIVE_STATES:
      # when not overshooting, calculate v_turn as the speed at the prediction horizon when following
      # the smooth deceleration.
      a_target = self.a_ego
    # ENTERING
    elif self.state == VisionState.entering:
      # The distance profile already determines when to slow. This acceleration
      # only shapes the direct longitudinal-control response toward that target.
      profile_accel = (self.v_target - self.v_ego) / max(_REACTION_TIME, 0.1)
      smooth_decel = np.interp(self.max_pred_lat_acc, _ENTERING_SMOOTH_DECEL_BP, _ENTERING_SMOOTH_DECEL_V)
      a_target = float(np.clip(min(profile_accel, smooth_decel), -_COMFORTABLE_DECEL, 0.))
    # TURNING
    elif self.state == VisionState.turning:
      # When turning, we provide a target acceleration that is comfortable for the lateral acceleration felt.
      a_target = np.interp(self.current_lat_acc, _TURNING_ACC_BP, _TURNING_ACC_V)
    # LEAVING
    elif self.state == VisionState.leaving:
      # When leaving, we provide a comfortable acceleration to regain speed.
      a_target = _LEAVING_ACC
    else:
      raise NotImplementedError(f"SCC-V state not supported: {self.state}")

    return a_target

  def update(self, sm: messaging.SubMaster, long_enabled: bool, long_override: bool, v_ego: float, a_ego: float,
             v_cruise_setpoint: float) -> None:
    self.long_enabled = long_enabled
    self.long_override = long_override
    self.v_ego = v_ego
    self.a_ego = a_ego
    self.v_cruise_setpoint = v_cruise_setpoint

    self._update_params()
    self._update_calculations(sm)

    self.is_enabled, self.is_active = self._update_state_machine()
    self.a_target = self._update_solution()

    self.output_v_target = self.get_v_target_from_control()
    self.output_a_target = self.get_a_target_from_control()

    self.frame += 1
