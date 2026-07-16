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
  assert "if-ltz v6, :cond_temp_throttled" in temp_updater
  assert "if-gez v6, :cond_temp_throttled" not in temp_updater


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


def test_navdy_disengaged_music_sits_above_current_speed():
  layout = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
           "res/layout/screen_home_smartdash.xml"
  root = ET.parse(layout).getroot()
  android = "{http://schemas.android.com/apk/res/android}"
  music_view = next(view for view in root.iter()
                    if view.attrib.get(f"{android}id") == "@id/music_track_info")
  music_row = next(parent for parent in root.iter() if music_view in list(parent))

  assert music_row.attrib[f"{android}layout_marginTop"] == "77.0dip"
  assert music_row.attrib[f"{android}layout_height"] == "26.0dip"
  assert music_view.attrib[f"{android}textSize"] == "16.0sp"


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


def test_payload_hides_resume_required_banner_during_autohold_standstill():
  car_state = SimpleNamespace(
    cruiseState=SimpleNamespace(standstill=True, speed=0.0),
    gearShifter="drive",
    standstill=True,
    vCruise=80.0,
    vCruiseCluster=80.0,
    vEgo=0.0,
    vEgoCluster=0.0,
  )
  selfdrive_state = SimpleNamespace(
    active=True,
    enabled=True,
    engageable=True,
    state="enabled",
    alertText1="Resume 버튼을 누르세요",
    alertText2="",
    alertType="resumeRequired/warning",
    alertStatus="userPrompt",
    alertSize="small",
  )

  payload = navdy_op_bridge.payload_from_messages(selfdrive_state, car_state, 12)

  assert payload["standstill"] is True
  assert payload["alertText1"] == ""
  assert payload["alertText2"] == ""
  assert payload["alertType"] == ""
  assert payload["alertStatus"] == "normal"
  assert payload["alertSize"] == "none"


def test_payload_hides_resume_required_banner_even_when_vehicle_state_is_stale():
  car_state = SimpleNamespace(
    cruiseState=SimpleNamespace(standstill=False, speed=20.0),
    gearShifter="drive",
    standstill=False,
    vCruise=80.0,
    vCruiseCluster=80.0,
    vEgo=5.0,
    vEgoCluster=5.0,
  )
  selfdrive_state = SimpleNamespace(
    active=True,
    enabled=True,
    engageable=True,
    state="enabled",
    alertText1="Resume 버튼을 누르세요",
    alertText2="",
    alertType="resumeRequired/warning",
    alertStatus="userPrompt",
    alertSize="small",
  )

  payload = navdy_op_bridge.payload_from_messages(selfdrive_state, car_state, 13)

  assert payload["alertText1"] == ""
  assert payload["alertText2"] == ""
  assert payload["alertType"] == ""
  assert payload["alertStatus"] == "normal"
  assert payload["alertSize"] == "none"


def test_payload_exports_sunnypilot_e2e_alert_flags():
  selfdrive_state = SimpleNamespace(
    active=True,
    enabled=True,
    engageable=True,
    state="enabled",
  )
  longitudinal_plan_sp = SimpleNamespace(e2eAlerts=SimpleNamespace(
    greenLightAlert=True,
    leadDepartAlert=False,
  ))

  payload = navdy_op_bridge.payload_from_messages(
      selfdrive_state, navdy_op_bridge.default_car_state(), 14,
      longitudinal_plan_sp=longitudinal_plan_sp)

  assert payload["greenLightAlert"] is True
  assert payload["leadDepartAlert"] is False


def test_navdy_e2e_alerts_become_held_korean_banners():
  args = SimpleNamespace()
  green = {
    "alertSize": "none",
    "greenLightAlert": True,
    "leadDepartAlert": False,
  }
  navdy_op_bridge.apply_navdy_e2e_alert(green, args, 10.0)

  assert green["alertText1"] == "신호 변경됨"
  assert green["alertText2"] == "전방 신호 변경 감지됨"
  assert green["alertType"] == "greenLight/permanent"
  assert green["alertSize"] == "mid"

  held = {
    "alertSize": "none",
    "greenLightAlert": False,
    "leadDepartAlert": False,
  }
  navdy_op_bridge.apply_navdy_e2e_alert(held, args, 12.9)
  assert held["alertText1"] == "신호 변경됨"

  expired = {
    "alertSize": "none",
    "greenLightAlert": False,
    "leadDepartAlert": False,
  }
  navdy_op_bridge.apply_navdy_e2e_alert(expired, args, 13.1)
  assert "alertText1" not in expired


def test_navdy_lead_depart_alert_does_not_replace_critical_alert():
  args = SimpleNamespace()
  critical = {
    "alertText1": "즉시 운전대를 잡으세요",
    "alertType": "steerUnavailable/immediateDisable",
    "alertSize": "full",
    "greenLightAlert": False,
    "leadDepartAlert": True,
  }

  navdy_op_bridge.apply_navdy_e2e_alert(critical, args, 20.0)

  assert critical["alertText1"] == "즉시 운전대를 잡으세요"
  assert critical["alertType"] == "steerUnavailable/immediateDisable"


def test_mici_hud_renders_green_light_and_lead_depart_alerts():
  ui_root = Path(__file__).parents[1] / "ui" / "sunnypilot"
  hud = (ui_root / "mici/onroad/hud_renderer.py").read_text()
  circular = (ui_root / "onroad/circular_alerts.py").read_text()

  assert "self.circular_alerts_renderer = CircularAlertsRenderer()" in hud
  assert "self.circular_alerts_renderer.update()" in hud
  assert "self.circular_alerts_renderer.render(rect)" in hud
  assert 'alert_type == "resumeRequired"' in circular
  assert 'self._alert_text = "신호\\n변경됨"' in circular
  assert 'self._alert_text = "전방 차량\\n출발"' in circular


def test_navdy_hud_patch_colors_current_speed_for_camera_overspeed():
  receiver = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
             "smali/com/navdy/hud/app/openpilot/OpenpilotStateReceiver.smali"
  smali = receiver.read_text()

  assert "TrafficIncidentWidgetPresenter;->getLastCameraSpeedLimit()I" in smali
  assert "cmpl-double v4, v16, v8" in smali
  assert ":cond_navdy_camera_speed_white" in smali
  assert "const/high16 v1, -0x10000" in smali
  assert "const/4 v1, -0x1" in smali


def test_navdy_hud_patch_colors_disengaged_speed_for_camera_overspeed():
  patch = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
          "SmartDashView.disengaged-speed-color.patch"
  smali_patch = patch.read_text()

  assert "TrafficIncidentWidgetPresenter;->getLastCameraSpeedLimit()I" in smali_patch
  assert "if-le p1, v1, :cond_navdy_stock_speed_white" in smali_patch
  assert "const/high16 v1, -0x10000" in smali_patch
  assert "const/4 v1, -0x1" in smali_patch
  assert "TextView;->setTextColor(I)V" in smali_patch


def test_navdy_alert_backgrounds_keep_hud_visible():
  source = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
           "src/com/navdy/hud/app/openpilot/OpenpilotAlertBannerView.java"
  java = source.read_text()

  assert "Color.argb(160, 0, 0, 0)" in java
  assert "Color.argb(170, 255, 115, 0)" in java
  assert "Color.argb(180, 255, 0, 21)" in java


def test_navdy_alert_banner_suppresses_resume_required():
  patch_root = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning"
  java = (patch_root / "src/com/navdy/hud/app/openpilot/OpenpilotAlertBannerView.java").read_text()
  smali = (patch_root / "smali/com/navdy/hud/app/openpilot/OpenpilotAlertBannerView.smali").read_text()

  assert 'type.startsWith("resumeRequired")' in java
  assert 'title.startsWith("Resume 버튼")' in java
  assert 'const-string v6, "resumeRequired"' in smali
  assert ":cond_navdy_hide_resume_required" in smali


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
              "src/com/navdy/hud/app/openpilot/OpenpilotPathView.java"
  java = path_view.read_text()
  state_only = java.split('if (!json.has("navPathLeft")) {', 1)[1].split("\n      }", 1)[0]

  assert "invalidate();" in state_only
  assert "return;" in state_only
  assert "clearGeometry();" not in state_only


def test_navdy_path_view_reads_and_draws_road_edges():
  path_view = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
              "src/com/navdy/hud/app/openpilot/OpenpilotPathView.java"
  java = path_view.read_text()

  for side in ("Left", "Right"):
    assert f'json.optJSONArray("navRoadEdge{side}")' in java
    assert f"drawRoadEdge(canvas, roadEdge{side}, roadEdge{side}Prob)" in java
  assert "roadEdgePaint.setStyle(Paint.Style.STROKE)" in java
  assert "confidence < ROAD_EDGE_MIN_CONFIDENCE" in java


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


def test_navdy_model_geometry_projects_path_and_all_lane_lines():
  path = SimpleNamespace(x=[0.0, 40.0, 80.0], y=[0.0, 0.5, 1.0])
  lane_lines = [
    SimpleNamespace(x=[0.0, 40.0, 80.0], y=[-5.0, -5.2, -5.5]),
    SimpleNamespace(x=[0.0, 40.0, 80.0], y=[-1.8, -2.1, -2.5]),
    SimpleNamespace(x=[0.0, 40.0, 80.0], y=[1.8, 1.4, 1.0]),
    SimpleNamespace(x=[0.0, 40.0, 80.0], y=[5.0, 4.8, 4.5]),
  ]
  road_edges = [
    SimpleNamespace(x=[0.0, 40.0, 80.0], y=[-5.5, -5.8, -6.0]),
    SimpleNamespace(x=[0.0, 40.0, 80.0], y=[5.5, 5.2, 5.0]),
  ]
  model = SimpleNamespace(
    position=path,
    laneLines=lane_lines,
    laneLineProbs=[0.6, 0.8, 0.7, 0.5],
    roadEdges=road_edges,
    roadEdgeStds=[0.2, 0.3],
  )

  geometry = navdy_op_bridge.navdy_model_geometry(model)

  assert len(geometry["navPathLeft"]) == 6
  assert len(geometry["navLaneLeft"]) == 6
  assert geometry["navPathLeft"][1] > geometry["navPathLeft"][-1]
  assert geometry["navPathLeft"][0] < geometry["navPathRight"][0]
  assert geometry["navLaneLeft"][0] < geometry["navLaneRight"][0]
  assert geometry["navLaneFarLeft"][0] < geometry["navLaneLeft"][0]
  assert geometry["navLaneFarRight"][0] > geometry["navLaneRight"][0]
  assert len(geometry["navRoadEdgeLeft"]) == 6
  assert geometry["navRoadEdgeLeft"][0] < geometry["navLaneFarLeft"][0]
  assert geometry["navRoadEdgeRight"][0] > geometry["navLaneFarRight"][0]
  assert geometry["navRoadEdgeLeftProb"] == 0.8
  assert geometry["navLaneLeftProb"] == 0.8


def test_navdy_model_geometry_hides_uncertain_road_edges():
  path = SimpleNamespace(x=[0.0, 80.0], y=[0.0, 0.0])
  lane_lines = [
    SimpleNamespace(x=[0.0, 80.0], y=[-5.0, -5.0]),
    SimpleNamespace(x=[0.0, 80.0], y=[-1.8, -1.8]),
    SimpleNamespace(x=[0.0, 80.0], y=[1.8, 1.8]),
    SimpleNamespace(x=[0.0, 80.0], y=[5.0, 5.0]),
  ]
  road_edges = [
    SimpleNamespace(x=[0.0, 80.0], y=[-6.0, -6.0]),
    SimpleNamespace(x=[0.0, 80.0], y=[6.0, 6.0]),
  ]
  model = SimpleNamespace(
    position=path,
    laneLines=lane_lines,
    laneLineProbs=[0.5, 0.9, 0.9, 0.5],
    roadEdges=road_edges,
    roadEdgeStds=[1.108, 0.679],
  )

  geometry = navdy_op_bridge.navdy_model_geometry(model)

  assert "navRoadEdgeLeft" not in geometry
  assert "navRoadEdgeRight" not in geometry


def test_navdy_model_line_keeps_modelv2_left_right_orientation():
  left = navdy_op_bridge.navdy_model_line([0.0, 80.0], [-1.0, -1.0])
  right = navdy_op_bridge.navdy_model_line([0.0, 80.0], [1.0, 1.0])

  assert left[0] < 160.0 < right[0]


def navdy_vehicle_test_model():
  lane_lines = [
    SimpleNamespace(x=[0.0, 80.0], y=[-5.2, -5.2]),
    SimpleNamespace(x=[0.0, 80.0], y=[-1.8, -1.8]),
    SimpleNamespace(x=[0.0, 80.0], y=[1.8, 1.8]),
    SimpleNamespace(x=[0.0, 80.0], y=[5.2, 5.2]),
  ]
  leads = [
    SimpleNamespace(prob=0.92, x=[31.52], y=[0.2], yStd=[0.3], v=[15.0]),
    SimpleNamespace(prob=0.1, x=[50.0], y=[0.0], yStd=[1.0], v=[20.0]),
  ]
  return SimpleNamespace(
    position=SimpleNamespace(x=[0.0, 80.0], y=[0.0, 0.0]),
    laneLines=lane_lines,
    laneLineProbs=[0.8, 0.95, 0.95, 0.8],
    leadsV3=leads,
    velocity=SimpleNamespace(x=[20.0]),
  )


def test_navdy_vehicle_geometry_fuses_camera_lead_and_classifies_adjacent_lanes():
  radar_points = [
    {"trackId": 10, "dRel": 30.0, "yRel": -0.2, "vRel": -5.0},
    {"trackId": 11, "dRel": 26.0, "yRel": 3.0, "vRel": 0.5},
    {"trackId": 12, "dRel": 24.0, "yRel": -3.0, "vRel": -1.0},
    {"trackId": 13, "dRel": 20.0, "yRel": 8.0, "vRel": 0.0},
  ]

  vehicles = navdy_op_bridge.navdy_vehicle_geometry(navdy_vehicle_test_model(), radar_points)["navVehicles"]
  by_id = {vehicle["trackId"]: vehicle for vehicle in vehicles}

  assert set(by_id) == {10, 11, 12}
  assert by_id[10]["source"] == "fused"
  assert by_id[10]["lane"] == "center"
  assert by_id[10]["lateralM"] == 0.2
  assert by_id[11]["lane"] == "left"
  assert by_id[11]["screenX"] < 160.0
  assert by_id[11]["yawDeg"] < 0.0
  assert by_id[12]["lane"] == "right"
  assert by_id[12]["screenX"] > 160.0
  assert by_id[12]["yawDeg"] > 0.0
  assert by_id[10]["yawDeg"] == 0.0


def test_navdy_radar_width_recovers_continuous_vehicle_center():
  left = {"yRel": 3.0, "widthM": 1.75}
  right = {"yRel": -3.0, "widthM": 1.75}
  center = {"yRel": 0.2, "widthM": 1.75}

  assert navdy_op_bridge.navdy_radar_center_model_y(left) == -3.875
  assert navdy_op_bridge.navdy_radar_center_model_y(right) == 2.125
  assert navdy_op_bridge.navdy_radar_center_model_y(center) == -1.075


def test_navdy_vehicle_geometry_exports_raw_edge_width_and_corrected_center():
  model = navdy_vehicle_test_model()
  model.leadsV3 = []
  radar_points = [
    {"trackId": 40, "dRel": 30.0, "yRel": 3.0, "vRel": -2.0, "widthM": 1.75},
    {"trackId": 41, "dRel": 30.0, "yRel": -3.0, "vRel": -1.0, "widthM": 1.75},
  ]

  vehicles = navdy_op_bridge.navdy_vehicle_geometry(model, radar_points)["navVehicles"]
  by_id = {vehicle["trackId"]: vehicle for vehicle in vehicles}

  assert by_id[40]["lane"] == "left"
  assert by_id[40]["lateralM"] == -3.88
  assert by_id[40]["rawRadarLateralM"] == -3.0
  assert by_id[40]["widthM"] == 1.75
  assert by_id[40]["widthCenterApplied"] is True
  assert by_id[41]["lane"] == "right"
  assert by_id[41]["lateralM"] == 3.0
  assert by_id[41]["widthCenterApplied"] is False
  assert by_id[40]["screenX"] < navdy_op_bridge.navdy_project_point(30.0, -3.0)[0]
  assert by_id[41]["screenX"] == navdy_op_bridge.navdy_project_point(30.0, 3.0)[0]
  assert all(not vehicle["widthCenterApplied"] or vehicle["lane"] == "left" for vehicle in vehicles)


def test_navdy_vehicle_yaw_follows_local_lane_curve():
  model = navdy_vehicle_test_model()
  model.position = SimpleNamespace(x=[0.0, 40.0, 80.0], y=[0.0, 6.0, 20.0])
  model.laneLines = [
    SimpleNamespace(x=[0.0, 40.0, 80.0], y=[-5.2, 0.8, 14.8]),
    SimpleNamespace(x=[0.0, 40.0, 80.0], y=[-1.8, 4.2, 18.2]),
    SimpleNamespace(x=[0.0, 40.0, 80.0], y=[1.8, 7.8, 21.8]),
    SimpleNamespace(x=[0.0, 40.0, 80.0], y=[5.2, 11.2, 25.2]),
  ]

  straight = navdy_op_bridge.navdy_vehicle_yaw_deg(navdy_vehicle_test_model(), "center", 30.0, 160.0)
  center = navdy_op_bridge.navdy_vehicle_yaw_deg(model, "center", 30.0, 160.0)
  left = navdy_op_bridge.navdy_vehicle_yaw_deg(model, "left", 30.0, 70.0)
  right = navdy_op_bridge.navdy_vehicle_yaw_deg(model, "right", 30.0, 250.0)

  assert straight == 0.0
  assert center < -5.0
  assert left < -12.0
  assert right < 12.0


def test_navdy_vehicle_perspective_yaw_turns_adjacent_lanes_more_aggressively():
  assert navdy_op_bridge.navdy_vehicle_perspective_yaw_deg("left", 132.0) == -8.0
  assert navdy_op_bridge.navdy_vehicle_perspective_yaw_deg("right", 218.0) == 12.0
  assert navdy_op_bridge.navdy_vehicle_perspective_yaw_deg("right", 280.0) == 24.0
  assert navdy_op_bridge.navdy_vehicle_perspective_yaw_deg("center", 280.0) == 0.0


def test_navdy_payload_signature_tracks_vehicle_yaw_changes():
  straight = {"navVehicles": [{"trackId": 1, "yawDeg": 0.0}]}
  curved = {"navVehicles": [{"trackId": 1, "yawDeg": 8.0}]}

  assert navdy_op_bridge.payload_signature(straight) != navdy_op_bridge.payload_signature(curved)


def test_navdy_payload_signature_tracks_lane_risk_changes():
  clear = {"navLaneRiskLeft": 0.0, "navLaneRiskRight": 0.0}
  danger = {"navLaneRiskLeft": 0.65, "navLaneRiskRight": 0.0}

  assert navdy_op_bridge.payload_signature(clear) != navdy_op_bridge.payload_signature(danger)


def test_navdy_lane_risk_payload_forwards_detector_sides():
  class FakeDetector:
    def __init__(self):
      self.lane_risks = {"left": 0.37, "right": 0.82}
      self.args = None

    def update(self, *args, **kwargs):
      self.args = (args, kwargs)

  detector = FakeDetector()
  model_v2 = SimpleNamespace(meta=SimpleNamespace(laneChangeState="off"))
  radar_points = [{"trackId": 9, "dRel": 20.0, "yRel": 3.0}]

  payload = navdy_op_bridge.update_navdy_lane_risk(
    detector, model_v2, radar_points, 18.0, 10.0)

  assert payload == {"navLaneRiskLeft": 0.37, "navLaneRiskRight": 0.82}
  assert detector.args[0] == (18.0, radar_points, model_v2, 10.0)
  assert detector.args[1] == {"lane_change_active": False}


def test_navdy_lane_intrusion_message_forwards_detection_details():
  class FakeMessaging:
    @staticmethod
    def new_message(service):
      assert service == "radarLaneIntrusionSP"
      return SimpleNamespace(valid=False, radarLaneIntrusionSP=SimpleNamespace())

  class FakePubMaster:
    def send(self, service, msg):
      self.sent = (service, msg)

  intrusion = SimpleNamespace(
    track_id=18, side="right", distance_m=24.5, lateral_m=2.1, inward_speed_mps=0.8)
  pm = FakePubMaster()

  navdy_op_bridge.publish_radar_lane_intrusion(
    FakeMessaging, pm, intrusion,
    {"navLaneRiskLeft": 0.2, "navLaneRiskRight": 0.9})

  service, msg = pm.sent
  state = msg.radarLaneIntrusionSP
  assert service == "radarLaneIntrusionSP"
  assert msg.valid
  assert state.detected
  assert (state.trackId, state.side) == (18, "right")
  assert (state.distance, state.lateral, state.inwardSpeed) == (24.5, 2.1, 0.8)
  assert (state.leftRisk, state.rightRisk) == (0.2, 0.9)


def test_navdy_vehicle_geometry_keeps_unmatched_camera_lead():
  vehicles = navdy_op_bridge.navdy_vehicle_geometry(navdy_vehicle_test_model(), [])["navVehicles"]

  assert len(vehicles) == 1
  assert vehicles[0]["source"] == "vision"
  assert vehicles[0]["lane"] == "center"


def test_navdy_vehicle_geometry_merges_overlapping_secondary_camera_hypothesis():
  model = navdy_vehicle_test_model()
  model.leadsV3[1] = SimpleNamespace(
    prob=0.88, x=[26.32], y=[0.0], yStd=[0.4], v=[15.5])
  radar_points = [
    {"trackId": 30, "dRel": 30.0, "yRel": -0.2, "vRel": -5.0},
  ]

  vehicles = navdy_op_bridge.navdy_vehicle_geometry(model, radar_points)["navVehicles"]

  assert len(vehicles) == 1
  assert vehicles[0]["trackId"] == 30
  assert vehicles[0]["source"] == "fused"


def test_navdy_vehicle_geometry_uses_screen_overlap_for_large_distance_delta():
  model = navdy_vehicle_test_model()
  model.leadsV3 = [
    SimpleNamespace(prob=0.9, x=[22.52], y=[0.0], yStd=[0.3], v=[16.0]),
  ]
  radar_points = [
    {"trackId": 31, "dRel": 30.0, "yRel": 0.0, "vRel": -4.0},
  ]

  vehicles = navdy_op_bridge.navdy_vehicle_geometry(model, radar_points)["navVehicles"]

  assert len(vehicles) == 1
  assert vehicles[0]["trackId"] == 31
  assert vehicles[0]["source"] == "fused"


def test_navdy_vehicle_geometry_preserves_separated_camera_and_radar_targets():
  model = navdy_vehicle_test_model()
  model.leadsV3 = [
    SimpleNamespace(prob=0.9, x=[21.52], y=[0.0], yStd=[0.3], v=[16.0]),
  ]
  radar_points = [
    {"trackId": 32, "dRel": 60.0, "yRel": 0.0, "vRel": -4.0},
  ]

  vehicles = navdy_op_bridge.navdy_vehicle_geometry(model, radar_points)["navVehicles"]

  assert len(vehicles) == 2
  assert {vehicle["source"] for vehicle in vehicles} == {"radar", "vision"}


def test_navdy_vehicle_geometry_uses_path_when_lane_markings_are_missing():
  model = navdy_vehicle_test_model()
  model.position = SimpleNamespace(x=[0.0, 80.0], y=[0.0, 0.0])
  model.laneLineProbs = [0.01, 0.04, 0.05, 0.01]
  radar_points = [
    {"trackId": 20, "dRel": 30.0, "yRel": -0.2, "vRel": -2.0},
    {"trackId": 21, "dRel": 24.0, "yRel": 3.0, "vRel": 0.0},
  ]

  vehicles = navdy_op_bridge.navdy_vehicle_geometry(model, radar_points)["navVehicles"]
  by_id = {vehicle["trackId"]: vehicle for vehicle in vehicles}

  assert by_id[20]["source"] == "fused"
  assert by_id[20]["lane"] == "center"
  assert by_id[21]["lane"] == "left"


def test_navdy_camera_lead_uses_path_without_lane_line_geometry():
  model = navdy_vehicle_test_model()
  model.position = SimpleNamespace(x=[0.0, 80.0], y=[0.0, 0.0])
  model.laneLines = []
  model.laneLineProbs = []

  leads = navdy_op_bridge.navdy_camera_leads(model)

  assert len(leads) == 1
  assert leads[0]["lane"] == "center"


def test_navdy_radar_reader_converts_raw_can_before_parser_update():
  converted = [(123, [(0x500, b"\x01", 1)])]

  class FakeRadarInterface:
    def __init__(self):
      self.received = None

    def update(self, can_list):
      self.received = can_list
      return "radar-data"

  reader = object.__new__(navdy_op_bridge.NavdyRadarReader)
  reader._radar_interface = FakeRadarInterface()
  reader._can_capnp_to_list = lambda raw: converted if raw == [b"raw-can"] else []

  assert reader._radar_update([b"raw-can"]) == "radar-data"
  assert reader._radar_interface.received == converted


def test_navdy_radar_reader_extracts_track_widths_from_raw_parser():
  reader = object.__new__(navdy_op_bridge.NavdyRadarReader)
  reader._radar_interface = SimpleNamespace(rcp=SimpleNamespace(vl={
    1120: {"FLRRNumValidTargets": 1},
    1121: {"TrkObjectID": 23, "TrkWidth": 1.75},
    1122: {"TrkObjectID": 24, "TrkWidth": 0.0},
  }))

  assert reader._radar_track_widths() == {23: 1.75}


def test_navdy_radar_reader_falls_back_to_persistent_car_params():
  class FakeParams:
    def __init__(self):
      self.keys = []

    def get(self, key):
      self.keys.append(key)
      return b"persistent" if key == "CarParamsPersistent" else None

  params = FakeParams()

  assert navdy_op_bridge.navdy_car_params_bytes(params) == b"persistent"
  assert params.keys == ["CarParams", "CarParamsPersistent"]


def test_navdy_path_renderer_animates_dashed_lanes_and_keeps_road_edges_solid():
  source = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
           "src/com/navdy/hud/app/openpilot/OpenpilotPathView.java"
  java = source.read_text()

  assert "LANE_DASH_PATTERN = {56.0f, 24.0f}" in java
  assert "LANE_DASH_CYCLE = 80.0f" in java
  assert "new DashPathEffect(LANE_DASH_PATTERN, dashPhase)" in java
  assert "Math.min(80.0f, Math.max(18.0f, vehicleSpeedKph * 0.8f))" in java
  assert "drawLane(canvas, laneFarLeft, laneFarLeftProb, 0.0f)" in java
  assert "drawLane(canvas, laneLeft, laneLeftProb, laneRiskLeft)" in java
  assert "drawLane(canvas, laneRight, laneRightProb, laneRiskRight)" in java
  assert "drawLane(canvas, laneFarRight, laneFarRightProb, 0.0f)" in java
  assert "canvas.drawPath(linePath(points), roadEdgePaint)" in java
  assert "canvas.drawPath(linePath(points), lanePaint)" in java
  assert "vehicleSpeedKph > 1.0f" in java
  assert "postInvalidateDelayed(DASH_FRAME_MS)" in java
  assert java.index("drawRoadEdge(canvas, roadEdgeLeft") < java.index("lanePaint.setPathEffect")


def test_navdy_path_renderer_blends_inner_lanes_toward_red_by_risk():
  patch_root = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning"
  source = patch_root / "src/com/navdy/hud/app/openpilot/OpenpilotPathView.java"
  java = source.read_text()
  smali = (patch_root / "smali/com/navdy/hud/app/openpilot/OpenpilotPathView.smali").read_text()

  assert "COLOR_LANE_DANGER = 0xffff2028" in java
  assert 'json.optDouble("navLaneRiskLeft", 0.0)' in java
  assert 'json.optDouble("navLaneRiskRight", 0.0)' in java
  assert "lanePaint.setColorFilter(laneRiskFilters[filterIndex])" in java
  assert "new LightingColorFilter[LANE_RISK_FILTER_STEPS + 1]" in java
  assert 'const-string v2, "navLaneRiskLeft"' in smali
  assert 'const-string v1, "navLaneRiskRight"' in smali
  assert ".method private drawLane(Landroid/graphics/Canvas;[FFF)V" in smali


def test_navdy_vehicle_markers_remain_visible_at_long_range():
  source = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
           "src/com/navdy/hud/app/openpilot/OpenpilotPathView.java"
  java = source.read_text()

  assert "float width = 12.0f + nearScale * 46.5f" in java
  assert "float height = width * 1.55f" in java


def test_navdy_path_renderer_draws_fused_camera_and_radar_vehicles():
  patch_root = Path(__file__).parent / "hud_patch" / \
               "engaged-path-v7-alert-banner-speed-warning"
  source = patch_root / "src/com/navdy/hud/app/openpilot/OpenpilotPathView.java"
  marker = patch_root / "res/drawable-nodpi/navdy_vehicle_marker.png"
  java = source.read_text()
  png = marker.read_bytes()

  assert 'json.has("navVehicles")' in java
  assert 'vehicle.optDouble("screenX", 160.0)' in java
  assert "drawVehicles(canvas);" in java
  assert "COLOR_VEHICLE_RADAR" in java
  assert "COLOR_VEHICLE_VISION" in java
  assert "COLOR_VEHICLE_FUSED" in java
  assert "BitmapFactory.decodeResource" in java
  assert "new LightingColorFilter" in java
  assert "canvas.drawBitmap(marker, null, destination, vehicleBitmapPaint)" in java
  assert png[:8] == b"\x89PNG\r\n\x1a\n"
  assert int.from_bytes(png[16:20], "big") == 256
  assert int.from_bytes(png[20:24], "big") == 256


def test_navdy_vehicle_markers_follow_bridge_yaw_with_legacy_fallback():
  patch_root = Path(__file__).parent / "hud_patch" / \
               "engaged-path-v7-alert-banner-speed-warning"
  source = patch_root / "src/com/navdy/hud/app/openpilot/OpenpilotPathView.java"
  java = source.read_text()

  assert 'vehicle.optDouble("yawDeg", 0.0)' in java
  assert "Float.isNaN(yawDeg)" in java
  assert "Math.round(absoluteYaw / 4.0f) - 1" in java
  for side in ("left", "right"):
    for angle in (4, 8, 12, 16, 20, 24):
      name = f"navdy_vehicle_marker_{side}_{angle}"
      marker = patch_root / f"res/drawable-nodpi/{name}.png"
      assert f'loadVehicleMarker(context, "{name}")' in java
      assert marker.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


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
      SimpleNamespace(x=[0.0, 80.0], y=[-1.8, -1.8]),
      SimpleNamespace(x=[0.0, 80.0], y=[1.8, 1.8]),
    ],
    laneLineProbs=[0.0, 1.0, 1.0],
  )
  car_state = navdy_op_bridge.default_car_state()
  engaged = SimpleNamespace(active=True, enabled=True, engageable=True, state="enabled")
  disengaged = SimpleNamespace(active=False, enabled=False, engageable=True, state="disabled")

  assert "navPathLeft" in navdy_op_bridge.payload_from_messages(engaged, car_state, 1, model_v2=model)
  assert "navRoadEdgeLeft" not in navdy_op_bridge.payload_from_messages(engaged, car_state, 1, model_v2=model)
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
  assert "--radar-overlay" in navdy_power_bridge.DEFAULT_ARGS


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
