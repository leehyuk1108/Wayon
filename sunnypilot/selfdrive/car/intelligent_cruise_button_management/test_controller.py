import json
import os
from types import SimpleNamespace

from cereal import car
from cereal import custom
from openpilot.common.constants import CV
from openpilot.selfdrive.car.helpers import convert_carControlSP
from openpilot.sunnypilot.selfdrive.car.intelligent_cruise_button_management.controller import (
  DECEL_RELEASE_TIME,
  DECEL_TRIGGER_TIME,
  RESTORE_SPEED_WINDOW,
  FOLLOW_SPEED_BUFFER,
  IntelligentCruiseButtonManagement,
)
from openpilot.sunnypilot.selfdrive.car.intelligent_cruise_button_management.helpers import get_minimum_set_speed
from openpilot.common.realtime import DT_CTRL


def make_controller(tmp_path):
  return IntelligentCruiseButtonManagement(
    SimpleNamespace(), SimpleNamespace(pcmCruiseSpeed=False), str(tmp_path / "camera.json"))


def make_state(*, ego_kph=80.0, stock_set_kph=100.0, restore_kph=100.0, accel=0.0):
  return SimpleNamespace(
    aEgo=accel,
    vEgo=ego_kph * CV.KPH_TO_MS,
    vEgoCluster=ego_kph * CV.KPH_TO_MS,
    vCruise=restore_kph,
    vCruiseCluster=restore_kph,
    cruiseState=SimpleNamespace(speedCluster=stock_set_kph * CV.KPH_TO_MS),
    buttonEvents=[],
  )


def make_control():
  return SimpleNamespace(
    enabled=True,
    cruiseControl=SimpleNamespace(override=False, cancel=False, resume=False),
  )


def make_plan(target_kph=100.0):
  return SimpleNamespace(vTarget=target_kph * CV.KPH_TO_MS)


def test_metric_minimum_set_speed_matches_vehicle_limit():
  assert get_minimum_set_speed(True) == 25
  assert get_minimum_set_speed(False) == 20


def test_camera_speed_becomes_temporary_target(tmp_path):
  camera_path = tmp_path / "camera.json"
  camera_path.write_text(json.dumps({"cameraSpeedKph": 60}))
  controller = make_controller(tmp_path)

  controller.run(make_state(), make_control(), make_plan(), True)

  assert controller.v_target == 60
  assert controller.automatic_control_active


def test_deceleration_lowers_stock_target_near_ego_then_restores_gradually(tmp_path):
  controller = make_controller(tmp_path)
  state = make_state(ego_kph=62, accel=-0.5)

  for _ in range(int(DECEL_TRIGGER_TIME / DT_CTRL) + 1):
    controller.run(state, make_control(), make_plan(), True)

  assert controller.v_target == 72
  assert controller.automatic_control_active

  state.aEgo = 0.0
  state.vEgo = state.vEgoCluster = 60 * CV.KPH_TO_MS
  state.cruiseState.speedCluster = 72 * CV.KPH_TO_MS
  for _ in range(int(DECEL_RELEASE_TIME / DT_CTRL) + 1):
    controller.run(state, make_control(), make_plan(), True)

  assert controller.v_target == 60 + RESTORE_SPEED_WINDOW
  assert controller.automatic_control_active


def test_lead_slowdown_uses_ten_kph_moving_ceiling(tmp_path):
  controller = make_controller(tmp_path)
  state = make_state(ego_kph=70, stock_set_kph=100, restore_kph=100, accel=-0.5)

  for _ in range(int(DECEL_TRIGGER_TIME / DT_CTRL) + 1):
    controller.run(state, make_control(), make_plan(), True)

  assert FOLLOW_SPEED_BUFFER == 10
  assert controller.v_target == 80
  assert controller.automatic_target_speed_kph == 80


def test_moving_ceiling_tracks_ego_until_restore_target(tmp_path):
  controller = make_controller(tmp_path)
  controller.is_metric = True
  controller.v_cruise_min = 30
  controller.restore_control_active = True
  controller.v_cruise_cluster = 80

  state = make_state(ego_kph=74, stock_set_kph=80, restore_kph=100)
  assert controller.temporary_target(state, 100) == 84

  state.vEgo = state.vEgoCluster = 95 * CV.KPH_TO_MS
  controller.v_cruise_cluster = 96
  assert controller.temporary_target(state, 100) == 100


def test_standstill_arms_continuous_speed_window_at_vehicle_minimum(tmp_path):
  controller = make_controller(tmp_path)
  state = make_state(ego_kph=0, stock_set_kph=70, restore_kph=100)

  controller.run(state, make_control(), make_plan(), True)

  assert controller.v_target == 25
  assert controller.restore_control_active
  assert controller.automatic_control_active


def test_speed_window_reactivates_without_a_new_deceleration_trigger(tmp_path):
  controller = make_controller(tmp_path)
  restored = make_state(ego_kph=100, stock_set_kph=100, restore_kph=100)

  controller.run(restored, make_control(), make_plan(), True)
  assert controller.v_target == 100
  assert not controller.automatic_control_active

  slowed = make_state(ego_kph=70, stock_set_kph=100, restore_kph=100, accel=0.0)
  controller.run(slowed, make_control(), make_plan(), True)

  assert controller.v_target == 80
  assert controller.restore_control_active
  assert controller.automatic_control_active


def test_continuous_speed_window_tracks_reacceleration(tmp_path):
  controller = make_controller(tmp_path)

  state = make_state(ego_kph=0, stock_set_kph=25, restore_kph=100)
  controller.run(state, make_control(), make_plan(), True)
  assert controller.v_target == 25

  state.vEgo = state.vEgoCluster = 22 * CV.KPH_TO_MS
  state.cruiseState.speedCluster = 25 * CV.KPH_TO_MS
  controller.run(state, make_control(), make_plan(), True)
  assert controller.v_target == 32

  state.vEgo = state.vEgoCluster = 55 * CV.KPH_TO_MS
  state.cruiseState.speedCluster = 32 * CV.KPH_TO_MS
  controller.run(state, make_control(), make_plan(), True)
  assert controller.v_target == 65

  state.vEgo = state.vEgoCluster = 90 * CV.KPH_TO_MS
  state.cruiseState.speedCluster = 65 * CV.KPH_TO_MS
  controller.run(state, make_control(), make_plan(), True)
  assert controller.v_target == 100


def test_state_machine_restarts_control_after_speed_drops_from_holding(tmp_path):
  controller = make_controller(tmp_path)
  state = make_state(ego_kph=70, stock_set_kph=80, restore_kph=100)

  for _ in range(50):
    controller.run(state, make_control(), make_plan(), True)
  assert controller.v_target == 80
  assert controller.state == custom.IntelligentCruiseButtonManagement.IntelligentCruiseButtonManagementState.holding

  state.vEgo = state.vEgoCluster = 50 * CV.KPH_TO_MS
  controller.run(state, make_control(), make_plan(), True)
  controller.run(state, make_control(), make_plan(), True)

  assert controller.v_target == 60
  assert controller.state == custom.IntelligentCruiseButtonManagement.IntelligentCruiseButtonManagementState.decreasing
  assert controller.cruise_button == custom.IntelligentCruiseButtonManagement.SendButtonState.decrease


def test_manual_button_cancels_temporary_profile(tmp_path):
  controller = make_controller(tmp_path)
  controller.restore_control_active = True
  controller.automatic_control_active = True
  state = make_state(stock_set_kph=60)
  button_type = car.CarState.ButtonEvent.Type.decelCruise
  state.buttonEvents = [SimpleNamespace(type=SimpleNamespace(raw=button_type), pressed=True)]

  controller.run(state, make_control(), make_plan(), True)

  assert not controller.restore_control_active
  assert not controller.automatic_control_active


def test_disengage_cancels_temporary_profile(tmp_path):
  controller = make_controller(tmp_path)
  controller.restore_control_active = True
  controller.automatic_control_active = True
  control = make_control()
  control.enabled = False

  controller.run(make_state(stock_set_kph=60), control, make_plan(), True)

  assert not controller.restore_control_active
  assert not controller.automatic_control_active


def test_unset_restore_speed_never_requests_255(tmp_path):
  controller = make_controller(tmp_path)
  state = make_state(stock_set_kph=60, restore_kph=255)

  controller.run(state, make_control(), make_plan(60), True)

  assert controller.v_target == 60


def test_stale_camera_state_is_ignored(tmp_path):
  camera_path = tmp_path / "camera.json"
  camera_path.write_text(json.dumps({"cameraSpeedKph": 60}))
  os.utime(camera_path, (1, 1))
  controller = make_controller(tmp_path)

  controller.run(make_state(ego_kph=100), make_control(), make_plan(), True)

  assert controller.v_target == 100
  assert not controller.automatic_control_active


def test_automatic_control_status_survives_car_control_conversion():
  message = custom.CarControlSP.new_message()
  message.intelligentCruiseButtonManagement.automaticControlActive = True
  message.intelligentCruiseButtonManagement.automaticTargetSpeedKph = 80

  converted = convert_carControlSP(message)

  assert converted.intelligentCruiseButtonManagement.automaticControlActive
  assert converted.intelligentCruiseButtonManagement.automaticTargetSpeedKph == 80
