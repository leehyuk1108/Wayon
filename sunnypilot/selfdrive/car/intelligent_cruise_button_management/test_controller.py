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


def make_controller(tmp_path, *, openpilot_long=False, pcm_cruise_speed=False):
  return IntelligentCruiseButtonManagement(
    SimpleNamespace(openpilotLongitudinalControl=openpilot_long),
    SimpleNamespace(pcmCruiseSpeed=pcm_cruise_speed),
    str(tmp_path / "camera.json"))


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


def write_camera_state(path, speed, camera_type="fixed", distance_m=0.0):
  path.write_text(json.dumps({"cameraSpeedKph": speed, "cameraSource": NAVDY_CAMERA_SOURCE,
                              "cameraType": camera_type, "cameraDistanceM": distance_m}))


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
  assert controller.automatic_control_source == "camera"


def test_fixed_camera_profile_reserves_settling_distance_before_compliance_point(tmp_path):
  camera_path = tmp_path / "camera.json"
  controller = make_controller(tmp_path, openpilot_long=True, pcm_cruise_speed=True)
  state = make_state(ego_kph=100, stock_set_kph=100, restore_kph=100)

  write_camera_state(camera_path, 50, "fixed", 1000)
  controller.run(state, make_control(), make_plan(), True)
  assert 95 <= controller.v_target < 100
  assert controller.automatic_control_active
  assert controller.required_accel < 0.0

  write_camera_state(camera_path, 50, "fixed", 300)
  controller.camera_state_checked_at = 0.0
  controller.run(state, make_control(), make_plan(), True)
  assert 50 < controller.v_target < 100
  assert controller.automatic_control_active

  write_camera_state(camera_path, 50, "fixed", 200)
  controller.camera_state_checked_at = 0.0
  controller.run(state, make_control(), make_plan(), True)
  assert controller.v_target == 50

  # Hold the posted speed through the required 100 m compliance point.
  write_camera_state(camera_path, 50, "fixed", 100)
  controller.camera_state_checked_at = 0.0
  controller.run(state, make_control(), make_plan(), True)
  assert controller.v_target == 50


def test_fixed_camera_profile_holds_limit_inside_one_hundred_meters(tmp_path):
  assert IntelligentCruiseButtonManagement.fixed_camera_target(100, 50, 99) == 50


def test_fixed_camera_profile_starts_with_early_coast_window():
  assert IntelligentCruiseButtonManagement.fixed_camera_target(80, 60, 600) == 80
  assert IntelligentCruiseButtonManagement.fixed_camera_target(80, 60, 490) == 79


def test_openpilot_long_uses_camera_target_without_requesting_buttons(tmp_path):
  camera_path = tmp_path / "camera.json"
  write_camera_state(camera_path, 60)
  controller = make_controller(tmp_path, openpilot_long=True, pcm_cruise_speed=True)

  controller.run(make_state(), make_control(), make_plan(), True)

  assert controller.v_target == 60
  assert controller.automatic_control_active
  assert controller.state == custom.IntelligentCruiseButtonManagement.IntelligentCruiseButtonManagementState.holding
  assert controller.cruise_button == custom.IntelligentCruiseButtonManagement.SendButtonState.none


def test_openpilot_long_keeps_camera_target_during_internal_stock_acc_cancel(tmp_path):
  camera_path = tmp_path / "camera.json"
  write_camera_state(camera_path, 60)
  controller = make_controller(tmp_path, openpilot_long=True, pcm_cruise_speed=True)
  control = make_control()
  control.cruiseControl.cancel = True

  controller.run(make_state(), control, make_plan(), True)

  assert controller.v_target == 60
  assert controller.automatic_control_active
  assert controller.state == custom.IntelligentCruiseButtonManagement.IntelligentCruiseButtonManagementState.holding
  assert controller.cruise_button == custom.IntelligentCruiseButtonManagement.SendButtonState.none


def test_mobile_camera_does_not_activate_icbm(tmp_path):
  camera_path = tmp_path / "camera.json"
  write_camera_state(camera_path, 60, "mobile")
  controller = make_controller(tmp_path)

  controller.run(make_state(), make_control(), make_plan(), True)

  assert controller.v_target == 100
  assert not controller.automatic_speed_control_active
  assert not controller.automatic_control_active


def test_section_approach_uses_posted_limit_before_entry(tmp_path):
  camera_path = tmp_path / "camera.json"
  write_camera_state(camera_path, 100, "section", 1200)
  controller = make_controller(tmp_path)

  controller.run(make_state(ego_kph=110, stock_set_kph=130, restore_kph=130),
                 make_control(), make_plan(), True)

  assert controller.section_phase == "approach"
  assert controller.v_target == 100


def test_section_distance_jump_starts_average_control(tmp_path):
  camera_path = tmp_path / "camera.json"
  write_camera_state(camera_path, 100, "section", 100)
  controller = make_controller(tmp_path)
  state = make_state(ego_kph=100, stock_set_kph=100, restore_kph=130)
  controller.run(state, make_control(), make_plan(), True)

  write_camera_state(camera_path, 100, "section", 5000)
  controller.camera_state_checked_at = 0.0
  controller.run(state, make_control(), make_plan(), True)

  assert controller.section_phase == "cruise"
  assert controller.section_total_distance_m == 5000
  assert controller.v_target == 99


def test_section_low_average_can_use_limit_plus_twenty(tmp_path):
  controller = make_controller(tmp_path)
  controller.is_metric = True
  controller.v_cruise_min = 25
  controller.section_phase = "cruise"
  controller.section_limit_kph = 100
  controller.section_total_distance_m = 5000
  controller.section_elapsed_s = 150
  controller.section_distance_travelled_m = 50 * CV.KPH_TO_MS * 150

  target = controller.update_section_target(
    make_state(ego_kph=50, restore_kph=130), 130, 100, 2917)

  assert round(controller.section_average_kph) == 50
  assert target == 120


def test_section_target_settles_below_posted_average(tmp_path):
  controller = make_controller(tmp_path)
  controller.is_metric = True
  controller.v_cruise_min = 25
  controller.section_phase = "cruise"
  controller.section_limit_kph = 100
  controller.section_total_distance_m = 5000
  controller.section_elapsed_s = 100
  controller.section_distance_travelled_m = 99 * CV.KPH_TO_MS * 100

  target = controller.update_section_target(
    make_state(ego_kph=99, restore_kph=130), 130, 100, 2250)

  assert round(controller.section_average_kph) == 99
  assert target == 99


def test_section_average_overshoot_requests_recovery_below_limit(tmp_path):
  controller = make_controller(tmp_path)
  controller.is_metric = True
  controller.v_cruise_min = 25
  controller.section_phase = "cruise"
  controller.section_limit_kph = 80
  controller.section_total_distance_m = 4000
  controller.section_elapsed_s = 90
  controller.section_distance_travelled_m = 82 * CV.KPH_TO_MS * 90

  remaining_m = controller.section_total_distance_m - controller.section_distance_travelled_m
  target = controller.update_section_target(
    make_state(ego_kph=82, restore_kph=100), 100, 80, remaining_m)

  assert controller.section_average_kph > 80
  assert target < 80


def test_section_exit_starts_at_exactly_three_hundred_meters(tmp_path):
  controller = make_controller(tmp_path)
  controller.is_metric = True
  controller.v_cruise_min = 25
  controller.section_phase = "cruise"
  controller.section_limit_kph = 100
  controller.section_total_distance_m = 5000

  target = controller.update_section_target(
    make_state(ego_kph=120, restore_kph=130), 130, 100, 300)

  assert controller.section_phase == "exit"
  assert target == 100


def test_section_target_never_exceeds_driver_restore_speed(tmp_path):
  controller = make_controller(tmp_path)
  controller.is_metric = True
  controller.v_cruise_min = 25
  controller.section_phase = "cruise"
  controller.section_limit_kph = 100
  controller.section_total_distance_m = 5000
  controller.section_elapsed_s = 100
  controller.section_distance_travelled_m = 80 * CV.KPH_TO_MS * 100

  target = controller.update_section_target(
    make_state(ego_kph=80, restore_kph=110), 110, 100, 2778)

  assert target == 110


def test_section_feedback_gap_holds_last_dynamic_target(tmp_path):
  controller = make_controller(tmp_path)
  controller.is_metric = True
  controller.v_cruise_min = 25
  controller.section_phase = "cruise"
  controller.section_limit_kph = 100
  controller.section_total_distance_m = 5000
  controller.section_elapsed_s = 100
  controller.section_distance_travelled_m = 80 * CV.KPH_TO_MS * 100

  target = controller.update_section_target(
    make_state(ego_kph=80, restore_kph=130), 130, 100, 2778)

  assert target == 120
  assert controller.held_section_target(130) == 120


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
  assert controller.automatic_control_source == "curve"


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
  assert controller.automatic_control_source == "restore"

  state.cruiseState.speedCluster = 100 * CV.KPH_TO_MS
  controller.run(state, make_control(), make_plan(), True)
  assert controller.v_target == 100
  assert not controller.automatic_speed_control_active
  assert not controller.automatic_control_active
  assert controller.automatic_control_source == "inactive"


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
  message.intelligentCruiseButtonManagement.sectionPhase = "cruise"
  message.intelligentCruiseButtonManagement.sectionProgress = 0.64
  message.intelligentCruiseButtonManagement.controlSource = "camera"

  converted = convert_carControlSP(message)

  assert converted.intelligentCruiseButtonManagement.automaticControlActive
  assert converted.intelligentCruiseButtonManagement.automaticTargetSpeedKph == 80
  assert converted.intelligentCruiseButtonManagement.sectionPhase == "cruise"
  assert abs(converted.intelligentCruiseButtonManagement.sectionProgress - 0.64) < 1e-5
  assert converted.intelligentCruiseButtonManagement.controlSource == "camera"
