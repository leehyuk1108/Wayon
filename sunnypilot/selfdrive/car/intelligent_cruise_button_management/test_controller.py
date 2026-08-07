import json
import os
from types import SimpleNamespace

from cereal import car
from cereal import custom
from openpilot.common.constants import CV
from openpilot.selfdrive.car.helpers import convert_carControlSP
from openpilot.sunnypilot.selfdrive.car.intelligent_cruise_button_management.controller import (
  IntelligentCruiseButtonManagement,
  NAVDY_CAMERA_SOURCE,
)
from openpilot.sunnypilot.selfdrive.car.intelligent_cruise_button_management.helpers import get_minimum_set_speed


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


def make_plan(target_kph=100.0, *, vision_target_kph=0.0, vision_active=False):
  return SimpleNamespace(
    vTarget=target_kph * CV.KPH_TO_MS,
    smartCruiseControl=SimpleNamespace(
      vision=SimpleNamespace(vTarget=vision_target_kph * CV.KPH_TO_MS, active=vision_active),
    ),
  )


def write_camera_state(path, speed, camera_type="fixed"):
  path.write_text(json.dumps({"cameraSpeedKph": speed, "cameraSource": NAVDY_CAMERA_SOURCE,
                              "cameraType": camera_type}))


def test_metric_minimum_set_speed_matches_vehicle_limit():
  assert get_minimum_set_speed(True) == 25
  assert get_minimum_set_speed(False) == 20


def test_camera_speed_becomes_temporary_target(tmp_path):
  camera_path = tmp_path / "camera.json"
  write_camera_state(camera_path, 60)
  controller = make_controller(tmp_path)

  controller.run(make_state(), make_control(), make_plan(), True)

  assert controller.v_target == 60
  assert controller.automatic_control_active


def test_mobile_camera_does_not_activate_icbm(tmp_path):
  camera_path = tmp_path / "camera.json"
  write_camera_state(camera_path, 60, "mobile")
  controller = make_controller(tmp_path)

  controller.run(make_state(), make_control(), make_plan(), True)

  assert controller.v_target == 100
  assert not controller.automatic_speed_control_active
  assert not controller.automatic_control_active


def test_planner_target_is_ignored_without_camera(tmp_path):
  controller = make_controller(tmp_path)
  controller.run(make_state(stock_set_kph=100), make_control(), make_plan(40), True)

  assert controller.v_target == 100
  assert not controller.automatic_speed_control_active
  assert not controller.automatic_control_active
  assert controller.cruise_button == custom.IntelligentCruiseButtonManagement.SendButtonState.none


def test_lead_slowdown_does_not_activate_without_camera(tmp_path):
  controller = make_controller(tmp_path)
  state = make_state(ego_kph=40, stock_set_kph=100, restore_kph=100, accel=-1.0)
  for _ in range(100):
    controller.run(state, make_control(), make_plan(100), True)

  assert controller.v_target == 100
  assert not controller.automatic_control_active
  assert controller.cruise_button == custom.IntelligentCruiseButtonManagement.SendButtonState.none


def test_active_vision_curve_becomes_temporary_target(tmp_path):
  controller = make_controller(tmp_path)
  controller.run(make_state(stock_set_kph=100), make_control(),
                 make_plan(100, vision_target_kph=70, vision_active=True), True)

  assert controller.v_target == 70
  assert controller.automatic_speed_control_active
  assert controller.automatic_control_active


def test_inactive_vision_target_is_ignored(tmp_path):
  controller = make_controller(tmp_path)
  controller.run(make_state(stock_set_kph=100), make_control(),
                 make_plan(100, vision_target_kph=70, vision_active=False), True)

  assert controller.v_target == 100
  assert not controller.automatic_speed_control_active
  assert controller.cruise_button == custom.IntelligentCruiseButtonManagement.SendButtonState.none


def test_standstill_does_not_activate_without_camera(tmp_path):
  controller = make_controller(tmp_path)
  controller.run(make_state(ego_kph=0, stock_set_kph=70, restore_kph=100),
                 make_control(), make_plan(), True)

  assert controller.v_target == 100
  assert not controller.automatic_control_active
  assert controller.cruise_button == custom.IntelligentCruiseButtonManagement.SendButtonState.none


def test_camera_session_restores_driver_target_after_camera_clears(tmp_path):
  camera_path = tmp_path / "camera.json"
  write_camera_state(camera_path, 50)
  controller = make_controller(tmp_path)
  state = make_state(stock_set_kph=100, restore_kph=100)

  controller.run(state, make_control(), make_plan(), True)
  assert controller.v_target == 50
  assert controller.automatic_speed_control_active

  write_camera_state(camera_path, 0)
  controller.camera_state_checked_at = 0.0
  state.cruiseState.speedCluster = 50 * CV.KPH_TO_MS
  controller.run(state, make_control(), make_plan(), True)
  assert controller.v_target == 100
  assert controller.automatic_speed_control_active
  assert controller.automatic_control_active

  state.cruiseState.speedCluster = 100 * CV.KPH_TO_MS
  controller.run(state, make_control(), make_plan(), True)
  assert controller.v_target == 100
  assert not controller.automatic_speed_control_active
  assert not controller.automatic_control_active


def test_camera_session_sends_decrease_then_restore_increase(tmp_path):
  camera_path = tmp_path / "camera.json"
  write_camera_state(camera_path, 50)
  controller = make_controller(tmp_path)
  state = make_state(stock_set_kph=100, restore_kph=100)

  for _ in range(50):
    controller.run(state, make_control(), make_plan(), True)
  assert controller.cruise_button == custom.IntelligentCruiseButtonManagement.SendButtonState.decrease

  state.cruiseState.speedCluster = 50 * CV.KPH_TO_MS
  for _ in range(2):
    controller.run(state, make_control(), make_plan(), True)
  assert controller.state == custom.IntelligentCruiseButtonManagement.IntelligentCruiseButtonManagementState.holding

  write_camera_state(camera_path, 0)
  controller.camera_state_checked_at = 0.0
  for _ in range(50):
    controller.run(state, make_control(), make_plan(), True)
  assert controller.v_target == 100
  assert controller.cruise_button == custom.IntelligentCruiseButtonManagement.SendButtonState.increase


def test_manual_button_cancels_temporary_profile(tmp_path):
  controller = make_controller(tmp_path)
  controller.automatic_speed_control_active = True
  controller.automatic_control_active = True
  state = make_state(stock_set_kph=60)
  button_type = car.CarState.ButtonEvent.Type.decelCruise
  state.buttonEvents = [SimpleNamespace(type=SimpleNamespace(raw=button_type), pressed=True)]

  controller.run(state, make_control(), make_plan(), True)

  assert not controller.automatic_speed_control_active
  assert not controller.automatic_control_active


def test_disengage_cancels_temporary_profile(tmp_path):
  controller = make_controller(tmp_path)
  controller.automatic_speed_control_active = True
  controller.automatic_control_active = True
  control = make_control()
  control.enabled = False

  controller.run(make_state(stock_set_kph=60), control, make_plan(), True)

  assert not controller.automatic_speed_control_active
  assert not controller.automatic_control_active


def test_unset_restore_speed_never_requests_255(tmp_path):
  controller = make_controller(tmp_path)
  state = make_state(stock_set_kph=60, restore_kph=255)

  controller.run(state, make_control(), make_plan(60), True)

  assert controller.v_target == 60


def test_stale_camera_state_is_ignored(tmp_path):
  camera_path = tmp_path / "camera.json"
  write_camera_state(camera_path, 60)
  os.utime(camera_path, (1, 1))
  controller = make_controller(tmp_path)

  controller.run(make_state(ego_kph=100), make_control(), make_plan(), True)

  assert controller.v_target == 100
  assert not controller.automatic_control_active


def test_untagged_notification_number_is_not_a_camera_target(tmp_path):
  camera_path = tmp_path / "camera.json"
  camera_path.write_text(json.dumps({"cameraSpeedKph": 30}))
  controller = make_controller(tmp_path)

  controller.run(make_state(ego_kph=20, stock_set_kph=70, restore_kph=70),
                 make_control(), make_plan(), True)

  assert controller.v_target == 70
  assert not controller.automatic_control_active


def test_automatic_control_status_survives_car_control_conversion():
  message = custom.CarControlSP.new_message()
  message.intelligentCruiseButtonManagement.automaticControlActive = True
  message.intelligentCruiseButtonManagement.automaticTargetSpeedKph = 80

  converted = convert_carControlSP(message)

  assert converted.intelligentCruiseButtonManagement.automaticControlActive
  assert converted.intelligentCruiseButtonManagement.automaticTargetSpeedKph == 80
