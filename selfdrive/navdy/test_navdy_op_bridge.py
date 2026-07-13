#!/usr/bin/env python3
import sys
import types
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import navdy_op_bridge

openpilot_module = types.ModuleType("openpilot")
openpilot_common_module = types.ModuleType("openpilot.common")
openpilot_realtime_module = types.ModuleType("openpilot.common.realtime")
openpilot_realtime_module.set_core_affinity = lambda cores: None
sys.modules.setdefault("openpilot", openpilot_module)
sys.modules.setdefault("openpilot.common", openpilot_common_module)
sys.modules.setdefault("openpilot.common.realtime", openpilot_realtime_module)

import navdy_power_bridge


def test_navdy_disengaged_speed_uses_engaged_system_typeface():
  layout = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
           "res/layout/screen_home_smartdash.xml"
  root = ET.parse(layout).getroot()
  android = "{http://schemas.android.com/apk/res/android}"
  navdy = "{http://schemas.android.com/apk/res-auto}"
  speed_view = next(view for view in root.iter()
                    if view.attrib.get(f"{android}id") == "@id/speedView")

  assert speed_view.tag == "com.navdy.hud.app.view.FontTextView"
  assert speed_view.attrib[f"{android}textSize"] == "66.0sp"
  assert f"{navdy}fontFile" not in speed_view.attrib


def test_navdy_outside_temperature_view_binds_and_throttles_obd_pid():
  patch = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning"
  root = ET.parse(patch / "res/layout/screen_home_smartdash.xml").getroot()
  android = "{http://schemas.android.com/apk/res/android}"
  temp_view = next(view for view in root.iter()
                   if view.attrib.get(f"{android}id") == "@id/si_temperature")
  receiver = (patch / "smali/com/navdy/hud/app/openpilot/OpenpilotStateReceiver.smali").read_text()
  temp_class = (patch / "smali/com/navdy/hud/app/openpilot/OpenpilotOutsideTempView.smali").read_text()
  overlay_builder = receiver.split(".method private static buildOverlayView", 1)[1].split(".end method", 1)[0]
  temp_updater = receiver.split(".method private static updateOutsideTemp()V", 1)[1].split(".end method", 1)[0]

  assert temp_view.tag == "com.navdy.hud.app.openpilot.OpenpilotOutsideTempView"
  assert "->bindOutsideTempView(Landroid/widget/TextView;)V" in temp_class
  assert "sOutsideTempTextView" not in overlay_builder
  assert "const/16 v5, 0x46" in temp_updater
  assert "const-wide/16 v4, 0x1388" in temp_updater


def test_navdy_music_uses_artist_title_and_refreshes_recreated_dash():
  patch = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
          "SmartDashView.music-metadata.patch"
  smali_patch = patch.read_text()
  refresh_hunks = smali_patch.split("@@ -3336", 1)[0]

  assert "MusicTrackInfo;->author:Ljava/lang/String;" in smali_patch
  assert "StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;" in smali_patch
  assert "invoke-virtual {v3, v2}" in smali_patch
  assert 'const-string v4, " - "' in smali_patch
  assert "+    :cond_navdy_music_refresh" in refresh_hunks
  assert "-    if-nez v0, :cond_1" in refresh_hunks


def test_payload_exports_standstill_and_op_available():
  cruise_state = SimpleNamespace(standstill=True, speed=27.7)
  car_state = SimpleNamespace(
    cruiseState=cruise_state,
    gearShifter="drive",
    leftBlinker=False,
    rightBlinker=False,
    leftBlindspot=False,
    rightBlindspot=False,
    standstill=True,
    vCruise=100.0,
    vCruiseCluster=0.0,
    vEgo=0.0,
    vEgoCluster=0.0,
  )
  selfdrive_state = SimpleNamespace(
    active=False,
    alertText1="",
    alertText2="",
    enabled=False,
    engageable=True,
    state="preEnabled",
  )

  payload = navdy_op_bridge.payload_from_messages(selfdrive_state, car_state, 7)

  assert payload["standstill"] is True
  assert payload["cruiseStandstill"] is True
  assert payload["opAvailable"] is True
  assert payload["engaged"] is False


def test_payload_keeps_pre_enabled_stop_icon_for_cruise_standstill():
  car_state = SimpleNamespace(
    cruiseState=SimpleNamespace(standstill=True, speed=0.0),
    gearShifter="drive",
    standstill=False,
    vCruise=80.0,
    vCruiseCluster=80.0,
    vEgo=0.0,
    vEgoCluster=0.0,
  )
  selfdrive_state = SimpleNamespace(active=False, enabled=False, engageable=True, state="preEnabled")

  payload = navdy_op_bridge.payload_from_messages(selfdrive_state, car_state, 8)

  assert payload["state"] == "preEnabled"
  assert payload["standstill"] is True
  assert payload["cruiseStandstill"] is True
  assert payload["setSpeedKph"] == 80.0


def test_payload_hides_stop_icon_while_disengaged_at_standstill():
  car_state = SimpleNamespace(
    cruiseState=SimpleNamespace(standstill=True, speed=0.0),
    gearShifter="drive",
    standstill=True,
    vCruise=80.0,
    vCruiseCluster=80.0,
    vEgo=0.0,
    vEgoCluster=0.0,
  )
  selfdrive_state = SimpleNamespace(active=False, enabled=False, engageable=True, state="disabled")

  payload = navdy_op_bridge.payload_from_messages(selfdrive_state, car_state, 9)

  assert payload["standstill"] is False
  assert payload["cruiseStandstill"] is False


def test_payload_shows_stop_icon_while_engaged_at_standstill():
  car_state = SimpleNamespace(
    cruiseState=SimpleNamespace(standstill=False, speed=0.0),
    gearShifter="drive",
    standstill=True,
    vCruise=80.0,
    vCruiseCluster=80.0,
    vEgo=0.0,
    vEgoCluster=0.0,
  )
  selfdrive_state = SimpleNamespace(active=True, enabled=True, engageable=True, state="enabled")

  payload = navdy_op_bridge.payload_from_messages(selfdrive_state, car_state, 10)

  assert payload["standstill"] is True
  assert payload["cruiseStandstill"] is True


def test_payload_exports_alert_metadata_for_navdy_banner():
  selfdrive_state = SimpleNamespace(
    active=True,
    enabled=True,
    engageable=True,
    state="enabled",
    alertText1="즉시 운전대를 잡으세요",
    alertText2="조향 제어가 종료됩니다",
    alertType="steerUnavailable/immediateDisable",
    alertStatus="critical",
    alertSize="full",
  )

  payload = navdy_op_bridge.payload_from_messages(
      selfdrive_state, navdy_op_bridge.default_car_state(), 11)

  assert payload["alertText1"] == "즉시 운전대를 잡으세요"
  assert payload["alertText2"] == "조향 제어가 종료됩니다"
  assert payload["alertType"] == "steerUnavailable/immediateDisable"
  assert payload["alertStatus"] == "critical"
  assert payload["alertSize"] == "full"


def test_navdy_hud_patch_colors_current_speed_for_camera_overspeed():
  receiver = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
             "smali/com/navdy/hud/app/openpilot/OpenpilotStateReceiver.smali"
  smali = receiver.read_text()

  assert "TrafficIncidentWidgetPresenter;->getLastCameraSpeedLimit()I" in smali
  assert "cmpl-double v4, v16, v8" in smali
  assert ":cond_navdy_camera_speed_white" in smali
  assert "const/high16 v1, -0x10000" in smali
  assert "const/4 v1, -0x1" in smali


def test_navdy_hud_patch_keeps_status_icons_while_disengaged():
  receiver = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
             "smali/com/navdy/hud/app/openpilot/OpenpilotStateReceiver.smali"
  smali = receiver.read_text()
  layout_method = smali.split(".method private static applyStatusLayout(Z)V", 1)[1].split(".end method", 1)[0]
  update_method = smali.split(".method private static updateOpenpilotOverlay", 1)[1].split(".end method", 1)[0]

  for field in ("sLeftTurnView", "sRightTurnView", "sLeftBsmView", "sRightBsmView",
                "sStandstillView", "sOpReadyView", "sSetSpeedRow"):
    assert f"->{field}:" in layout_method
  assert "cond_standstill_disengaged" in layout_method
  assert "const/16 v3, 0xeb" in layout_method
  assert "const/16 v3, 0x112" in layout_method
  assert "cond_set_speed_disengaged" in layout_method
  assert "const/16 v3, 0x12f" in layout_method
  assert "const/16 v3, 0x128" in layout_method
  assert "->applyStatusLayout(Z)V" in update_method
  assert "->setTurnBlinkers(ZZ)V" in update_method
  assert "->sLeftBsmView:" in update_method
  assert "->sRightBsmView:" in update_method
  assert "->setOpenpilotIconState(ZZ)V" in update_method
  assert "->sSetSpeedRow:" in update_method
  assert "->hideEngagedOverlay()V" not in smali


def test_navdy_path_view_retains_geometry_during_fast_state_updates():
  path_view = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
              "smali/com/navdy/hud/app/openpilot/OpenpilotPathView.smali"
  smali = path_view.read_text()
  update_method = smali.split(".method public updatePayload", 1)[1].split(".end method", 1)[0]

  assert "JSONObject;->has(Ljava/lang/String;)Z" in update_method
  assert "if-nez p1, :cond_navdy_path_payload_present" in update_method
  assert update_method.index("return-void") < update_method.index("\n    :cond_navdy_path_payload_present")


def test_payload_uses_structured_reverse_alert_when_gear_sample_is_unavailable():
  selfdrive_state = SimpleNamespace(
    active=False,
    enabled=False,
    engageable=False,
    state="disabled",
    alertType="reverseGear/permanent",
  )

  payload = navdy_op_bridge.payload_from_messages(
      selfdrive_state, navdy_op_bridge.default_car_state(), 9)

  assert payload["gear"] == "reverse"


def test_available_services_skips_missing_starpilot_plan():
  messaging = SimpleNamespace(SERVICE_LIST={"selfdriveState": object(), "carStateSP": object()})

  assert navdy_op_bridge.available_services(
      messaging, ["selfdriveState", "carStateSP", "starpilotPlan"]) == ["selfdriveState", "carStateSP"]


def test_car_state_sp_mirror_exports_navdy_vehicle_signals():
  car_state_sp = SimpleNamespace(
    navdyCruiseStandstill=True,
    navdyCruiseSpeed=27.7,
    navdyCruiseSpeedCluster=28.0,
    navdyGearShifter="drive",
    navdyLeftBlinker=True,
    navdyRightBlinker=False,
    navdyLeftBlindspot=True,
    navdyRightBlindspot=False,
    navdyStandstill=True,
    navdyVCruise=99.0,
    navdyVCruiseCluster=100.0,
    navdyVEgo=10.0,
    navdyVEgoCluster=10.5,
  )

  car_state = navdy_op_bridge.car_state_from_sp(car_state_sp)

  assert car_state.gearShifter == "drive"
  assert car_state.vCruiseCluster == 100.0
  assert car_state.standstill is True
  assert car_state.cruiseState.standstill is True
  assert car_state.leftBlinker is True
  assert car_state.leftBlindspot is True


def test_navdy_bridge_avoids_saturated_car_state_service():
  assert navdy_op_bridge.NAVDY_CAR_STATE_SERVICE == "carStateSP"
  assert navdy_op_bridge.NAVDY_MODEL_SERVICE not in navdy_op_bridge.NAVDY_FAST_SERVICES


def test_navdy_model_geometry_projects_path_and_middle_lane_lines():
  path = SimpleNamespace(x=[0.0, 40.0, 80.0], y=[0.0, 0.5, 1.0])
  lane_lines = [
    SimpleNamespace(x=[], y=[]),
    SimpleNamespace(x=[0.0, 40.0, 80.0], y=[1.8, 2.1, 2.5]),
    SimpleNamespace(x=[0.0, 40.0, 80.0], y=[-1.8, -1.4, -1.0]),
  ]
  model = SimpleNamespace(position=path, laneLines=lane_lines, laneLineProbs=[0.0, 0.8, 0.7])

  geometry = navdy_op_bridge.navdy_model_geometry(model)

  assert len(geometry["navPathLeft"]) == 6
  assert len(geometry["navLaneLeft"]) == 6
  assert geometry["navPathLeft"][1] > geometry["navPathLeft"][-1]
  assert geometry["navLaneLeft"][0] < geometry["navLaneRight"][0]
  assert geometry["navLaneLeftProb"] == 0.8


def test_navdy_model_line_caps_geometry_at_ten_points():
  points = navdy_op_bridge.navdy_model_line(
      [index * 2.5 for index in range(33)],
      [0.0] * 33,
  )

  assert len(points) == 20
  assert points[:2] == [160.0, 96.0]
  assert points[-2:] == [160.0, 8.0]


def test_payload_only_exports_model_geometry_while_active():
  model = SimpleNamespace(
    position=SimpleNamespace(x=[0.0, 80.0], y=[0.0, 0.0]),
    laneLines=[
      SimpleNamespace(x=[], y=[]),
      SimpleNamespace(x=[0.0, 80.0], y=[1.8, 1.8]),
      SimpleNamespace(x=[0.0, 80.0], y=[-1.8, -1.8]),
    ],
    laneLineProbs=[0.0, 1.0, 1.0],
  )
  car_state = navdy_op_bridge.default_car_state()
  engaged = SimpleNamespace(active=True, enabled=True, engageable=True, state="enabled")
  disengaged = SimpleNamespace(active=False, enabled=False, engageable=True, state="disabled")

  assert "navPathLeft" in navdy_op_bridge.payload_from_messages(engaged, car_state, 1, model_v2=model)
  assert "navPathLeft" not in navdy_op_bridge.payload_from_messages(disengaged, car_state, 2, model_v2=model)


def test_live_payload_ready_uses_recent_messages_not_alive_flags():
  sm = SimpleNamespace(
    alive={"selfdriveState": False, "carStateSP": False},
    recv_time={"selfdriveState": 10.0, "carStateSP": 10.1},
    seen={"selfdriveState": True, "carStateSP": True},
  )

  assert navdy_op_bridge.live_payload_ready(sm, True, now=10.2)
  assert not navdy_op_bridge.live_payload_ready(sm, True, now=11.2)


def test_live_payload_ready_allows_missing_car_state_when_selfdrive_is_recent():
  sm = SimpleNamespace(
    alive={"selfdriveState": False, "carStateSP": False},
    recv_time={"selfdriveState": 10.0, "carStateSP": 0.0},
    seen={"selfdriveState": True, "carStateSP": False},
  )

  assert navdy_op_bridge.live_payload_ready(sm, True, now=10.2)


def test_default_car_state_keeps_payload_safe_without_vehicle_sample():
  selfdrive_state = SimpleNamespace(
    active=False,
    alertText1="",
    alertText2="",
    enabled=False,
    engageable=True,
    state="disabled",
  )
  controls_state = SimpleNamespace(vCruiseClusterDEPRECATED=42.0, vCruiseDEPRECATED=0.0)

  payload = navdy_op_bridge.payload_from_messages(
      selfdrive_state, navdy_op_bridge.default_car_state(), 8, controls_state)

  assert payload["vEgoKph"] == 0.0
  assert payload["gear"] == "unknown"
  assert payload["setSpeedKph"] == 42.0


def test_manager_defaults_use_starpilot_socket_transport():
  assert "--socket-transport" in navdy_power_bridge.DEFAULT_ARGS


def test_manager_defaults_keep_fast_state_and_throttle_path():
  hz = float(navdy_power_bridge.DEFAULT_ARGS[navdy_power_bridge.DEFAULT_ARGS.index("--hz") + 1])
  path_update_sec = float(navdy_power_bridge.DEFAULT_ARGS[navdy_power_bridge.DEFAULT_ARGS.index("--path-update-sec") + 1])
  assert hz == 5.0
  assert path_update_sec == 0.1
  assert path_update_sec < 1.0 / hz
  assert "--min-emit-sec" not in navdy_power_bridge.DEFAULT_ARGS
  assert navdy_power_bridge.DEFAULT_ARGS[navdy_power_bridge.DEFAULT_ARGS.index("--heartbeat-sec") + 1] == "5"
  assert navdy_power_bridge.DEFAULT_ARGS[navdy_power_bridge.DEFAULT_ARGS.index("--power-on-ensure-sec") + 1] == "60"


def test_navdy_path_update_is_independent_from_fast_state_rate():
  assert navdy_op_bridge.navdy_path_update_due(True, 10.0, 0.0, 1.0)
  assert not navdy_op_bridge.navdy_path_update_due(True, 10.5, 10.0, 1.0)
  assert navdy_op_bridge.navdy_path_update_due(True, 11.0, 10.0, 1.0)
  assert not navdy_op_bridge.navdy_path_update_due(False, 11.0, 0.0, 1.0)


def test_should_emit_payload_respects_min_emit_interval():
  args = SimpleNamespace(once=False, min_emit_sec=1.0, heartbeat_sec=5.0)
  payload = {"state": "enabled", "vEgoKph": 10.0}
  changed_payload = {"state": "enabled", "vEgoKph": 11.0}
  last_signature = navdy_op_bridge.payload_signature(payload)

  should_emit, _ = navdy_op_bridge.should_emit_payload(changed_payload, args, 10.5, last_signature, 10.0)
  assert not should_emit

  should_emit, _ = navdy_op_bridge.should_emit_payload(changed_payload, args, 11.1, last_signature, 10.0)
  assert should_emit


def test_fast_state_change_emits_before_next_path_update():
  args = SimpleNamespace(once=False, min_emit_sec=0.0, heartbeat_sec=5.0)
  payload = {"state": "enabled", "leftBlinker": False}
  changed_payload = {"state": "enabled", "leftBlinker": True}

  should_emit, _ = navdy_op_bridge.should_emit_payload(
      changed_payload, args, 10.2, navdy_op_bridge.payload_signature(payload), 10.0)

  assert should_emit


def test_manager_child_ignores_inherited_manager_argv():
  assert navdy_power_bridge.should_use_default_args(
      "navdy_bridge", ["manager.py", "--socket-transport"])


if __name__ == "__main__":
  test_payload_exports_standstill_and_op_available()
  test_available_services_skips_missing_starpilot_plan()
  test_live_payload_ready_uses_recent_messages_not_alive_flags()
  test_live_payload_ready_allows_missing_car_state_when_selfdrive_is_recent()
  test_default_car_state_keeps_payload_safe_without_vehicle_sample()
  test_navdy_path_view_retains_geometry_during_fast_state_updates()
  test_manager_defaults_use_starpilot_socket_transport()
  test_manager_defaults_keep_fast_state_and_throttle_path()
  test_navdy_path_update_is_independent_from_fast_state_rate()
  test_should_emit_payload_respects_min_emit_interval()
  test_fast_state_change_emits_before_next_path_update()
  test_manager_child_ignores_inherited_manager_argv()
