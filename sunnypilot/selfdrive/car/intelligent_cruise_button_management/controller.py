"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import json
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

State = custom.IntelligentCruiseButtonManagement.IntelligentCruiseButtonManagementState
SendButtonState = custom.IntelligentCruiseButtonManagement.SendButtonState

INACTIVE_TIMER = 0.4
NAVDY_CAMERA_STATE_PATH = "/dev/shm/navdy_camera_state.json"
NAVDY_CAMERA_STATE_MAX_AGE = 1.5


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
    self.camera_state_checked_at = 0.0
    self.camera_control_active = False

    self.cruise_button_timers = CRUISE_BUTTON_TIMER

  @property
  def v_cruise_equal(self) -> bool:
    return self.v_target == self.v_cruise_cluster

  @property
  def automatic_target_speed_kph(self) -> float:
    return float(self.v_target if self.is_metric else self.v_target * CV.MPH_TO_KPH)

  def reset_temporary_control(self) -> None:
    self.camera_control_active = False
    self.automatic_control_active = False

  def read_camera_speed(self) -> int:
    now = time.monotonic()
    if now - self.camera_state_checked_at < 0.1:
      return self.camera_speed
    self.camera_state_checked_at = now

    try:
      stat = os.stat(self.camera_state_path)
      if time.time() - stat.st_mtime > NAVDY_CAMERA_STATE_MAX_AGE:
        self.camera_speed = 0
      else:
        with open(self.camera_state_path, encoding="utf-8") as state_file:
          state = json.load(state_file)
        speed = int(state.get("cameraSpeedKph", 0))
        self.camera_speed = speed if 20 <= speed <= 140 else 0
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
      self.camera_speed = 0
    return self.camera_speed

  def camera_target(self, CS: car.CarState) -> int:
    restore_speed = CS.vCruiseCluster if 0.0 < CS.vCruiseCluster < V_CRUISE_UNSET else CS.vCruise
    if not 0.0 < restore_speed < V_CRUISE_UNSET:
      restore_speed = max(self.v_cruise_min, self.v_cruise_cluster)
    restore_target = max(self.v_cruise_min, min(V_CRUISE_MAX, round(restore_speed)))

    camera_target = self.read_camera_speed()
    if camera_target > 0 and not self.is_metric:
      camera_target = round(camera_target * CV.KPH_TO_MPH)

    if self.v_cruise_min <= camera_target < restore_target:
      self.camera_control_active = True
      self.automatic_control_active = True
      return camera_target

    # Once a camera has lowered the physical ACC set speed, restore the
    # driver's virtual set speed before ending the camera-control session.
    if self.camera_control_active and self.v_cruise_cluster != restore_target:
      self.automatic_control_active = True
      return restore_target

    self.camera_control_active = False
    self.automatic_control_active = False
    return restore_target

  def update_calculations(self, CS: car.CarState) -> None:
    speed_conv = CV.MS_TO_KPH if self.is_metric else CV.MS_TO_MPH
    self.v_cruise_min = get_minimum_set_speed(self.is_metric)
    self.v_cruise_cluster = round(CS.cruiseState.speedCluster * speed_conv)
    self.v_target = self.camera_target(CS)

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

  def run(self, CS: car.CarState, CC: car.CarControl, _LP_SP: custom.LongitudinalPlanSP, is_metric: bool) -> None:
    if self.CP_SP.pcmCruiseSpeed:
      self.reset_temporary_control()
      return

    self.is_metric = is_metric

    self.update_calculations(CS)
    self.update_readiness(CS, CC)

    self.cruise_button = self.update_state_machine()

    self.is_ready_prev = self.is_ready
