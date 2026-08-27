"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import json
import math
import os
import time

from cereal import car, custom
from opendbc.car import structs
from openpilot.common.constants import CV
from openpilot.common.realtime import DT_CTRL
from openpilot.sunnypilot.selfdrive.car.intelligent_cruise_button_management.helpers import get_minimum_set_speed
from openpilot.sunnypilot.selfdrive.car.cruise_ext import (
  CRUISE_BUTTON_TIMER,
  V_CRUISE_MAX,
  V_CRUISE_UNSET,
  update_manual_button_timers,
)
from openpilot.sunnypilot.selfdrive.controls.lib.wayon_longitudinal_coordinator import (
  empty_response_profile,
  learned_delay_for_speed,
  load_response_profile,
  RESPONSE_PROFILE_PATH,
)
from openpilot.sunnypilot.selfdrive.controls.lib.wayon_carrot_long_profile import is_enabled

State = custom.IntelligentCruiseButtonManagement.IntelligentCruiseButtonManagementState
SendButtonState = custom.IntelligentCruiseButtonManagement.SendButtonState

INACTIVE_TIMER = 0.4
NAVDY_CAMERA_STATE_PATH = "/dev/shm/navdy_camera_state.json"
NAVDY_CAMERA_STATE_MAX_AGE = 2.5
NAVDY_CAMERA_SOURCE = "trafficNotification"
# Finish lowering the planner ceiling early enough for the real vehicle to
# settle at the posted speed by 100 m before the camera.  The previous profile
# reached the posted-speed ceiling at 100 m, leaving no room for MPC, actuator,
# and vehicle response lag.
CAMERA_COMPLIANCE_DISTANCE_M = 100.0
CAMERA_SETTLING_TIME_S = 4.0
CAMERA_COAST_PROFILE_DECEL_MPS2 = 0.35
SECTION_TARGET_MARGIN_KPH = 1
SECTION_MIN_OFFSET_KPH = -20
SECTION_MAX_OFFSET_KPH = 20
SECTION_EXIT_DISTANCE_M = 300.0
SECTION_ENTRY_ARM_DISTANCE_M = 350.0
SECTION_ENTRY_MIN_REMAINING_M = 500.0
SECTION_ENTRY_MIN_JUMP_M = 250.0
SECTION_FEEDBACK_HOLD_FRAMES = round(3.0 / DT_CTRL)


SEND_BUTTONS = {
  State.increasing: SendButtonState.increase,
  State.decreasing: SendButtonState.decrease,
}


class IntelligentCruiseButtonManagement:
  def __init__(self, CP: structs.CarParams, CP_SP: structs.CarParamsSP,
               camera_state_path: str = NAVDY_CAMERA_STATE_PATH):
    self.CP = CP
    self.CP_SP = CP_SP

    self.v_target = 0
    self.v_cruise_cluster = 0
    self.v_cruise_min = 0
    self.cruise_button = SendButtonState.none
    self.state = State.inactive
    self.pre_active_timer = 0
    self.automatic_control_active = False

    self.is_ready = False
    self.is_ready_prev = False
    self.is_metric = False
    self.camera_state_path = camera_state_path
    self.camera_speed = 0
    self.camera_type = ""
    self.camera_distance_m = 0.0
    self.camera_state_checked_at = 0.0
    self.automatic_speed_control_active = False
    self.automatic_control_source = "inactive"
    self.wayon_longitudinal_profile = is_enabled(CP)
    self.default_response_delay = float(getattr(self.CP, "longitudinalActuatorDelay", 0.5))
    self.response_profile = (load_response_profile(RESPONSE_PROFILE_PATH, self.default_response_delay)
                             if self.wayon_longitudinal_profile else empty_response_profile(self.default_response_delay))
    self.response_profile_checked_at = 0.0
    self.predicted_arrival_speed_kph = 0.0
    self.required_accel = 0.0

    self.section_phase = "inactive"
    self.section_limit_kph = 0
    self.section_total_distance_m = 0.0
    self.section_remaining_m = 0.0
    self.section_last_remaining_m = 0.0
    self.section_elapsed_s = 0.0
    self.section_distance_travelled_m = 0.0
    self.section_average_kph = 0.0
    self.section_last_target_kph = 0
    self.section_feedback_hold_frames = 0

    self.cruise_button_timers = CRUISE_BUTTON_TIMER

  @property
  def v_cruise_equal(self) -> bool:
    return self.v_target == self.v_cruise_cluster

  @property
  def automatic_target_speed_kph(self) -> float:
    return float(self.v_target if self.is_metric else self.v_target * CV.MPH_TO_KPH)

  @property
  def section_progress(self) -> float:
    if self.section_total_distance_m <= 0.0:
      return 0.0
    travelled_m = self.section_total_distance_m - self.section_remaining_m
    return max(0.0, min(1.0, travelled_m / self.section_total_distance_m))

  def reset_temporary_control(self) -> None:
    self.automatic_speed_control_active = False
    self.automatic_control_active = False
    self.automatic_control_source = "inactive"

  def reset_section_control(self) -> None:
    self.section_phase = "inactive"
    self.section_limit_kph = 0
    self.section_total_distance_m = 0.0
    self.section_remaining_m = 0.0
    self.section_last_remaining_m = 0.0
    self.section_elapsed_s = 0.0
    self.section_distance_travelled_m = 0.0
    self.section_average_kph = 0.0
    self.section_last_target_kph = 0
    self.section_feedback_hold_frames = 0

  def read_camera_speed(self) -> int:
    now = time.monotonic()
    if now - self.camera_state_checked_at < 0.1:
      return self.camera_speed
    self.camera_state_checked_at = now

    try:
      stat = os.stat(self.camera_state_path)
      if time.time() - stat.st_mtime > NAVDY_CAMERA_STATE_MAX_AGE:  # noqa: TID251
        self.camera_speed = 0
        self.camera_type = ""
        self.camera_distance_m = 0.0
      else:
        with open(self.camera_state_path, encoding="utf-8") as state_file:
          state = json.load(state_file)
        speed = int(state.get("cameraSpeedKph", 0))
        source_valid = state.get("cameraSource") == NAVDY_CAMERA_SOURCE
        camera_type = str(state.get("cameraType", "fixed")).lower()
        camera_is_mobile = camera_type == "mobile"
        self.camera_speed = speed if source_valid and not camera_is_mobile and 20 <= speed <= 140 else 0
        self.camera_type = camera_type if self.camera_speed > 0 else ""
        distance_m = float(state.get("cameraDistanceM", 0.0))
        self.camera_distance_m = distance_m if math.isfinite(distance_m) and distance_m >= 0.0 else 0.0
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
      self.camera_speed = 0
      self.camera_type = ""
      self.camera_distance_m = 0.0
    return self.camera_speed

  def start_section_cruise(self, remaining_m: float) -> None:
    self.section_phase = "cruise"
    self.section_total_distance_m = remaining_m
    self.section_remaining_m = remaining_m
    self.section_elapsed_s = 0.0
    self.section_distance_travelled_m = 0.0
    self.section_average_kph = 0.0

  def learned_response_delay(self, v_ego: float) -> float:
    if not self.wayon_longitudinal_profile:
      return 0.0
    now = time.monotonic()
    if now - self.response_profile_checked_at >= 10.0:
      self.response_profile = load_response_profile(RESPONSE_PROFILE_PATH, self.default_response_delay)
      self.response_profile_checked_at = now
    return learned_delay_for_speed(self.response_profile, v_ego, self.default_response_delay)

  @staticmethod
  def fixed_camera_target(restore_target_kph: int, limit_kph: int, remaining_m: float,
                          v_ego: float | None = None, response_delay: float = 0.0) -> int:
    approach_speed = max(0.0, v_ego) if v_ego is not None else restore_target_kph * CV.KPH_TO_MS
    settling_time = CAMERA_SETTLING_TIME_S + max(0.0, response_delay)
    settling_distance_m = approach_speed * settling_time
    target_distance_m = CAMERA_COMPLIANCE_DISTANCE_M + settling_distance_m
    decel_distance_m = max(0.0, remaining_m - target_distance_m)
    limit_ms = limit_kph * CV.KPH_TO_MS
    allowed_ms = math.sqrt(limit_ms ** 2 + 2.0 * CAMERA_COAST_PROFILE_DECEL_MPS2 * decel_distance_m)
    allowed_kph = math.floor(allowed_ms * CV.MS_TO_KPH)
    return max(limit_kph, min(restore_target_kph, allowed_kph))

  def update_arrival_prediction(self, CS: car.CarState, target_kph: float,
                                endpoint_distance_m: float) -> None:
    self.predicted_arrival_speed_kph = 0.0
    self.required_accel = 0.0
    if target_kph <= 0.0 or endpoint_distance_m <= 0.0:
      return

    response_delay = self.learned_response_delay(float(CS.vEgo))
    usable_distance_m = max(1.0, endpoint_distance_m - max(0.0, float(CS.vEgo)) * response_delay)
    target_ms = target_kph * CV.KPH_TO_MS
    speed_sq = max(0.0, float(CS.vEgo) ** 2 + 2.0 * float(CS.aEgo) * usable_distance_m)
    self.predicted_arrival_speed_kph = math.sqrt(speed_sq) * CV.MS_TO_KPH
    if CS.vEgo > target_ms:
      self.required_accel = max(-2.0, (target_ms ** 2 - float(CS.vEgo) ** 2) / (2.0 * usable_distance_m))

  def update_section_target(self, CS: car.CarState, restore_target: int, limit_kph: int,
                            remaining_m: float) -> int:
    if self.section_phase == "inactive" or self.section_limit_kph != limit_kph:
      self.reset_section_control()
      self.section_phase = "approach"
      self.section_limit_kph = limit_kph

    previous_remaining = self.section_last_remaining_m
    self.section_last_remaining_m = remaining_m
    self.section_remaining_m = remaining_m
    self.section_feedback_hold_frames = SECTION_FEEDBACK_HOLD_FRAMES

    if self.section_phase == "approach":
      entered_section = (
        0.0 < previous_remaining <= SECTION_ENTRY_ARM_DISTANCE_M and
        remaining_m >= SECTION_ENTRY_MIN_REMAINING_M and
        remaining_m - previous_remaining >= SECTION_ENTRY_MIN_JUMP_M
      )
      if entered_section:
        self.start_section_cruise(remaining_m)
      else:
        self.section_last_target_kph = min(limit_kph, restore_target)
        return self.section_last_target_kph

    if self.section_phase == "cruise":
      self.section_elapsed_s += DT_CTRL
      self.section_distance_travelled_m += max(0.0, float(CS.vEgo)) * DT_CTRL
      if self.section_elapsed_s > 0.0:
        self.section_average_kph = self.section_distance_travelled_m / self.section_elapsed_s * CV.MS_TO_KPH

      if remaining_m <= SECTION_EXIT_DISTANCE_M:
        self.section_phase = "exit"

    if self.section_phase == "exit":
      self.section_last_target_kph = min(limit_kph, restore_target)
      return self.section_last_target_kph

    target_average_kph = max(self.v_cruise_min, limit_kph - SECTION_TARGET_MARGIN_KPH)
    target_total_time_s = self.section_total_distance_m / (target_average_kph * CV.KPH_TO_MS)
    remaining_time_s = target_total_time_s - self.section_elapsed_s
    if remaining_time_s <= DT_CTRL:
      required_speed_kph = limit_kph + SECTION_MAX_OFFSET_KPH
    else:
      required_speed_kph = remaining_m / remaining_time_s * CV.MS_TO_KPH

    required_speed_kph = max(limit_kph + SECTION_MIN_OFFSET_KPH,
                             min(limit_kph + SECTION_MAX_OFFSET_KPH, required_speed_kph))
    self.section_last_target_kph = min(restore_target, round(required_speed_kph))
    return self.section_last_target_kph

  def held_section_target(self, restore_target: int) -> int:
    if self.section_phase == "inactive" or self.section_feedback_hold_frames <= 0:
      self.reset_section_control()
      return restore_target
    self.section_feedback_hold_frames -= 1
    held_target = self.section_last_target_kph or self.section_limit_kph
    return min(restore_target, held_target)

  def automatic_target(self, CS: car.CarState, LP_SP: custom.LongitudinalPlanSP) -> int:
    speed_conv = CV.MS_TO_KPH if self.is_metric else CV.MS_TO_MPH
    restore_speed = CS.vCruiseCluster if 0.0 < CS.vCruiseCluster < V_CRUISE_UNSET else CS.vCruise
    if not 0.0 < restore_speed < V_CRUISE_UNSET:
      restore_speed = max(self.v_cruise_min, self.v_cruise_cluster)
    restore_target = max(self.v_cruise_min, min(V_CRUISE_MAX, round(restore_speed)))

    camera_target = self.read_camera_speed()
    camera_target_kph = camera_target
    restore_target_kph = round(restore_target if self.is_metric else restore_target * CV.MPH_TO_KPH)
    if self.camera_type == "section" and camera_target_kph > 0:
      camera_target_kph = self.update_section_target(CS, restore_target_kph, camera_target_kph, self.camera_distance_m)
    elif self.camera_type == "fixed" and camera_target_kph > 0:
      self.reset_section_control()
      camera_target_kph = self.fixed_camera_target(
        restore_target_kph, camera_target_kph, self.camera_distance_m,
        float(CS.vEgo), self.learned_response_delay(float(CS.vEgo)))
    elif self.section_phase != "inactive" and camera_target_kph == 0:
      camera_target_kph = self.held_section_target(restore_target_kph)
    elif self.camera_type != "section":
      self.reset_section_control()

    if camera_target_kph > 0:
      if self.camera_type == "fixed":
        endpoint_distance_m = max(1.0, self.camera_distance_m - CAMERA_COMPLIANCE_DISTANCE_M)
        prediction_target_kph = self.camera_speed
      elif self.camera_type == "section" and self.section_phase in ("approach", "exit"):
        endpoint_distance_m = max(1.0, self.camera_distance_m)
        prediction_target_kph = self.camera_speed
      else:
        endpoint_distance_m = max(60.0, CS.vEgo * (4.0 + self.learned_response_delay(float(CS.vEgo))))
        prediction_target_kph = camera_target_kph
      self.update_arrival_prediction(CS, prediction_target_kph, endpoint_distance_m)
    else:
      self.predicted_arrival_speed_kph = 0.0
      self.required_accel = 0.0

    camera_target = camera_target_kph
    if camera_target > 0 and not self.is_metric:
      camera_target = round(camera_target * CV.KPH_TO_MPH)

    vision = getattr(getattr(LP_SP, "smartCruiseControl", None), "vision", None)
    vision_target_ms = float(getattr(vision, "vTarget", 0.0))
    vision_target = round(vision_target_ms * speed_conv) if math.isfinite(vision_target_ms) else 0
    if not bool(getattr(vision, "active", False)):
      vision_target = 0

    limiter_targets = [(target, source) for target, source in ((camera_target, "camera"), (vision_target, "curve"))
                       if self.v_cruise_min <= target < restore_target]
    if limiter_targets:
      selected_target, selected_source = min(limiter_targets, key=lambda item: item[0])
      self.automatic_speed_control_active = True
      self.automatic_control_active = True
      self.automatic_control_source = selected_source
      return selected_target

    # Restore the driver's virtual set speed after the camera or curve clears.
    if self.automatic_speed_control_active and self.v_cruise_cluster != restore_target:
      self.automatic_control_active = True
      self.automatic_control_source = "restore"
      return restore_target

    self.automatic_speed_control_active = False
    self.automatic_control_active = False
    self.automatic_control_source = "inactive"
    return restore_target

  def update_calculations(self, CS: car.CarState, LP_SP: custom.LongitudinalPlanSP) -> None:
    speed_conv = CV.MS_TO_KPH if self.is_metric else CV.MS_TO_MPH
    self.v_cruise_min = get_minimum_set_speed(self.is_metric)
    self.v_cruise_cluster = round(CS.cruiseState.speedCluster * speed_conv)
    self.v_target = self.automatic_target(CS, LP_SP)

  def update_state_machine(self) -> custom.IntelligentCruiseButtonManagement.SendButtonState:
    self.pre_active_timer = max(0, self.pre_active_timer - 1)

    # HOLDING, ACCELERATING, DECELERATING, PRE_ACTIVE
    if self.state != State.inactive:
      if not self.is_ready:
        self.state = State.inactive

      else:
        # PRE_ACTIVE
        if self.state == State.preActive:
          if self.pre_active_timer <= 0:
            if self.v_cruise_equal:
              self.state = State.holding

            elif self.v_target > self.v_cruise_cluster:
              self.state = State.increasing

            elif self.v_target < self.v_cruise_cluster and self.v_cruise_cluster > self.v_cruise_min:
              self.state = State.decreasing

        # HOLDING
        elif self.state == State.holding:
          if not self.v_cruise_equal:
            self.state = State.preActive

        # ACCELERATING
        elif self.state == State.increasing:
          if self.v_target <= self.v_cruise_cluster:
            self.state = State.holding

        # DECELERATING
        elif self.state == State.decreasing:
          if self.v_target >= self.v_cruise_cluster or self.v_cruise_cluster <= self.v_cruise_min:
            self.state = State.holding

    # INACTIVE
    elif self.state == State.inactive:
      if self.is_ready and not self.is_ready_prev:
        self.pre_active_timer = int(INACTIVE_TIMER / DT_CTRL)
        self.state = State.preActive

    send_button = SEND_BUTTONS.get(self.state, SendButtonState.none)

    return send_button

  def update_readiness(self, CS: car.CarState, CC: car.CarControl) -> None:
    update_manual_button_timers(CS, self.cruise_button_timers)

    ready = (self.automatic_control_active and CC.enabled and not CC.cruiseControl.override and
             not CC.cruiseControl.cancel and not CC.cruiseControl.resume)
    button_pressed = any(self.cruise_button_timers[k] > 0 for k in self.cruise_button_timers)

    self.is_ready = ready and not button_pressed
    if not CC.enabled or button_pressed or CC.cruiseControl.override or CC.cruiseControl.cancel or CC.cruiseControl.resume:
      self.reset_temporary_control()

  def run(self, CS: car.CarState, CC: car.CarControl, LP_SP: custom.LongitudinalPlanSP, is_metric: bool) -> None:
    openpilot_long = bool(getattr(self.CP, "openpilotLongitudinalControl", False))
    if self.CP_SP.pcmCruiseSpeed and not openpilot_long:
      self.reset_temporary_control()
      return

    self.is_metric = is_metric

    self.update_calculations(CS, LP_SP)

    if openpilot_long:
      # GM long control continuously requests stock ACC cancel while openpilot
      # owns longitudinal actuation. That output is not a driver cancellation
      # and must not clear the camera target calculated above.
      self.is_ready = self.automatic_control_active and CC.enabled
      if not CC.enabled:
        self.reset_temporary_control()
      # OP long consumes the calculated target directly in plannerd. Never
      # request synthetic stock ACC button presses in this mode.
      self.cruise_button = SendButtonState.none
      self.state = State.holding if self.automatic_control_active else State.inactive
      self.is_ready_prev = self.is_ready
      return

    self.update_readiness(CS, CC)
    self.cruise_button = self.update_state_machine()

    self.is_ready_prev = self.is_ready
