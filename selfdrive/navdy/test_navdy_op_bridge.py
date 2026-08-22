#!/usr/bin/env python3
import json
import sys
import socket
import threading
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


def test_navdy_lane_marking_state_is_written_atomically(tmp_path):
  state_path = tmp_path / "lane_markings.json"

  navdy_op_bridge.publish_navdy_lane_marking_state({
    "navLaneLeftType": "centerSolid",
    "navLaneRightType": "dashed",
  }, str(state_path))

  state = json.loads(state_path.read_text())
  assert state["leftType"] == "centerSolid"
  assert state["rightType"] == "dashed"
  assert state["updatedAtMonotonic"] > 0.0
  assert not (tmp_path / "lane_markings.json.tmp").exists()


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
  assert "cmp-long v6, v2, v4" in temp_updater
  assert "if-ltz v6," in temp_updater
  assert "if-gez v6," not in temp_updater


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


def test_navdy_socket_receiver_coalesces_frames_and_skips_payload_logs():
  patch = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning"
  service = (patch / "smali/com/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable.smali").read_text()
  receiver = (patch / "smali/com/navdy/hud/app/openpilot/OpenpilotStateReceiver.smali").read_text()

  assert "->removeCallbacksAndMessages(Ljava/lang/Object;)V" in service
  assert "->postAtTime(Ljava/lang/Runnable;Ljava/lang/Object;J)Z" in service
  assert "socket payload=" not in service
  assert "openpilot payload=" not in receiver
  assert "state active=" not in receiver


def test_navdy_socket_returns_camera_limit_over_existing_usb_tunnel():
  patch = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning"
  service = (patch / "smali/com/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable.smali").read_text()

  assert "TrafficIncidentWidgetPresenter;->getLastCameraSpeedLimit()I" in service
  assert 'const-string v4, "{\\\"cameraSpeedKph\\\":"' in service
  assert 'cameraSource\\\":\\\"trafficNotification' in service
  assert 'cameraType\\\":\\\"' in service
  assert 'cameraDistance\\\":\\\"' in service
  assert "neg-int v4, v4" in service
  assert "if-eqz v6, :camera_type_fixed" in service
  assert "lastCameraIsSection:Z" in service
  assert 'const-string v4, "section"' in service
  assert 'const-string v4, "mobile"' in service
  assert 'const-string v4, "fixed"' in service
  assert "BufferedWriter;->flush()V" in service


def test_navdy_section_camera_view_matches_approved_hud_contract():
  patch = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning"
  receiver = (patch / "smali/com/navdy/hud/app/openpilot/OpenpilotStateReceiver.smali").read_text()
  section_view = (patch / "smali/com/navdy/hud/app/openpilot/OpenpilotSectionCameraView.smali").read_text()

  assert "sSectionCameraView:Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;" in receiver
  assert "const/16 v5, 0x1ec" in receiver  # stock camera-card x
  assert "const/16 v5, 0xd3" in receiver   # physical SmartDash y
  assert "->updatePayload(Lorg/json/JSONObject;IZ)V" in receiver
  assert '"sectionAverageKph"' in section_view
  assert '"sectionProgress"' in section_view
  assert '"sectionRemainingM"' in section_view
  assert '"\\uad6c\\uac04\\ub2e8\\uc18d"' in section_view
  assert "->drawCircle(FFFLandroid/graphics/Paint;)V" in section_view
  assert "->drawRoundRect(Landroid/graphics/RectF;FFLandroid/graphics/Paint;)V" in section_view


def test_navdy_camera_filter_does_not_treat_all_comma_alerts_as_cameras():
  patch = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
          "patch_camera_notification_filter.py"
  camera_filter = patch.read_text()

  assert 'for origin in ("carrot", "comma")' in camera_filter
  assert "if method.count(block) == 2" in camera_filter
  assert "elif method.count(disabled_block) != 2" in camera_filter
  assert "lastCameraIsMobile" in camera_filter
  assert "lastCameraIsSection" in camera_filter
  assert "MOBILE_DETECTION" in camera_filter
  assert "SECTION_DETECTION" in camera_filter
  assert "patch_camera_background" in camera_filter
  assert "patch_camera_distance_music_typeface" in camera_filter
  assert "patch_section_legacy_card_visibility" in camera_filter
  assert ":section_legacy_camera_visibility_ready" in camera_filter
  assert ":camera_speed_music_typeface" in camera_filter
  assert ":camera_distance_music_typeface" in camera_filter
  assert "Typeface;->DEFAULT:Landroid/graphics/Typeface;" in camera_filter
  assert "setTypeface(Landroid/graphics/Typeface;I)V" in camera_filter
  assert "const/high16 v2, 0x41880000    # 17.0f" in camera_filter
  assert "patch_encoded_camera_speed" in camera_filter
  assert "patch_camera_type_notification_state" in camera_filter
  assert "DISTANCE_FORMATTING" in camera_filter
  assert "patch_camera_distance_formatting" in camera_filter
  assert ":camera_distance_format_done" in camera_filter
  assert "register_mobile_camera_resource" in camera_filter
  assert "neg-int v0, v0" in camera_filter
  assert "0x7f02029f" in camera_filter
  assert 'const-string v3, "mobile"' in camera_filter
  assert 'const-string/jumbo v3, "\\uc774\\ub3d9\\uc2dd"' in camera_filter


def test_navdy_camera_clear_hides_camera_widget():
  patch = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
          "patch_camera_notification_filter.py"
  namespace = {}
  exec(compile(patch.read_text(), str(patch), "exec"), namespace)

  broken_method = """.method private static isCameraClearNotification(Lcom/navdy/service/library/events/notification/NotificationEvent;)Z
    .locals 3
    const-string v1, "Camera Clear"
    nop
    const-string v1, "No camera"
    nop
    const/4 v0, 0x0
    return v0
.end method"""
  fixed = namespace["restore_camera_clear_match"](broken_method)

  assert fixed.count("equalsIgnoreCase") == 2
  assert 'const-string v1, "Camera Clear"' in fixed
  assert 'const-string v1, "No camera"' in fixed
  assert "if-nez v2, :cond_clear_true" in fixed
  assert ":cond_clear_true" in fixed

  clear_action = """.method private clearCameraText()V
    .locals 5
    const/4 v3, 0x4
    invoke-virtual {v2, v3}, Landroid/view/View;->setVisibility(I)V
.end method"""
  namespace["validate_camera_clear_action"](clear_action)

  private_field = ".field private static lastCameraDistance:Ljava/lang/String;"
  exposed = namespace["expose_camera_distance"](private_field)
  assert exposed == ".field public static lastCameraDistance:Ljava/lang/String;"

  presenter = Path("/Users/ijonghyeog/Documents/navdy/build_work/"
                   "moving-acc-ceiling-v2-compat-20260801/smali/com/navdy/hud/app/"
                   "maps/widget/TrafficIncidentWidgetPresenter.smali")
  if presenter.is_file():
    clear_camera_text = presenter.read_text().split(".method private clearCameraText", 1)[1].split(
      ".end method", 1)[0]
    assert "const/4 v3, 0x4" in clear_camera_text
    assert "Landroid/view/View;->setVisibility(I)V" in clear_camera_text


def test_navdy_camera_card_is_mirrored_into_attached_overlay():
  patch = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning"
  receiver = (patch / "smali/com/navdy/hud/app/openpilot/OpenpilotStateReceiver.smali").read_text()
  overlay_builder = receiver.split(".method private static buildOverlayView", 1)[1].split(
    ".end method", 1)[0]

  assert "sCameraSpeedTextView:Landroid/widget/TextView;" in receiver
  assert "sCameraDistanceTextView:Landroid/widget/TextView;" in receiver
  assert "->setBackgroundResource(I)V" in receiver
  assert "TrafficIncidentWidgetPresenter;->getLastCameraSpeedLimit()I" in receiver
  assert "TrafficIncidentWidgetPresenter;->lastCameraDistance:Ljava/lang/String;" in receiver
  assert "const v2, 0x7f02029f" in receiver
  assert "const v2, 0x7f020286" in receiver
  assert "neg-int v1, v1" in receiver
  assert "const/16 v1, 0x8" in receiver
  assert "invoke-virtual {v0, v1}, Landroid/widget/TextView;->setVisibility(I)V" in receiver
  assert "const/high16 v4, 0x41d00000    # 26.0f" in receiver
  assert "const/high16 v4, 0x41f00000    # 30.0f" in receiver
  assert "LayoutInflater;->inflate(ILandroid/view/ViewGroup;)Landroid/view/View;" in receiver
  assert "const v3, 0x7f030032" in receiver  # maps_traffic_incident_widget
  assert "const v3, 0x7f0e0142" in receiver  # incidentInfo
  assert "const v3, 0x7f0e0111" in receiver  # distance textView
  assert overlay_builder.count("Typeface;->DEFAULT:Landroid/graphics/Typeface;") == 2
  assert overlay_builder.count(
    "TextView;->setTypeface(Landroid/graphics/Typeface;I)V") == 2
  assert "const/high16 v5, 0x41880000    # 17.0f" in overlay_builder
  assert "formatCameraDistance(Ljava/lang/String;)Ljava/lang/String;" in receiver
  assert 'const-string v0, "km"' in receiver
  assert "const/16 v1, 0x3e8" in receiver
  assert "div-int/lit8 v0, v0, 0x64" in receiver


def test_navdy_camera_card_uses_original_smartdash_position():
  layout = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
           "res/layout/screen_home_smartdash.xml"
  root = ET.parse(layout).getroot()
  android = "{http://schemas.android.com/apk/res/android}"
  navdy = "{http://schemas.android.com/apk/res-auto}"
  legacy_card = next(view for view in root.iter()
                     if view.attrib.get(f"{android}id") == "@id/take_snapshot_smart_dash")
  speed_limit = next(view for view in root.iter()
                     if view.attrib.get(f"{android}id") == "@id/txt_speed_limit")
  camera_distance = next(view for view in root.iter()
                         if view.attrib.get(f"{android}id") == "@id/txt_speed_limit_unavailable")

  assert legacy_card.attrib[f"{android}visibility"] == "invisible"
  assert legacy_card.attrib[f"{android}layout_width"] == "104.0dip"
  assert legacy_card.attrib[f"{android}layout_height"] == "96.0dip"
  assert legacy_card.attrib[f"{android}layout_marginLeft"] == "492.0dip"
  assert legacy_card.attrib[f"{android}layout_marginTop"] == "104.0dip"
  assert speed_limit.attrib[f"{android}textSize"] == "30.0sp"
  assert speed_limit.attrib["style"] == "@style/Roboto"
  assert f"{navdy}fontFile" not in speed_limit.attrib
  assert camera_distance.attrib[f"{android}textSize"] == "17.0sp"
  assert camera_distance.attrib["style"] == "@style/Roboto"
  assert f"{navdy}fontFile" not in camera_distance.attrib

  receiver = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
             "smali/com/navdy/hud/app/openpilot/OpenpilotStateReceiver.smali"
  mirror_setup = receiver.read_text().split("const v3, 0x7f030032", 1)[1].split(
    "new-instance v4, Landroid/widget/FrameLayout$LayoutParams;", 1)[0]
  assert "Landroid/view/View;->setVisibility(I)V" in mirror_setup


def test_navdy_visible_smartdash_camera_card_gets_music_typeface_and_dynamic_size():
  patch = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
          "patch_camera_notification_filter.py"
  script = patch.read_text()

  assert "patch_smartdash_camera_text_style" in script
  assert ":smartdash_camera_speed_three_digit" in script
  assert ":smartdash_camera_speed_size_ready" in script
  assert "if-gt v1, v5, :smartdash_camera_speed_three_digit" in script
  assert "SmartDash camera style requires five existing locals" in script
  assert "const/4 v5, 0x0" in script
  assert "const/high16 v1, 0x41f00000    # 30.0f" in script
  assert "const/high16 v1, 0x41d00000    # 26.0f" in script
  assert "const/high16 v1, 0x41880000    # 17.0f" in script


def test_navdy_ambient_write_failure_discards_stale_gatt_and_rescans():
  patch = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
          "patch_ambient_gatt_recovery.py"
  namespace = {}
  exec(compile(patch.read_text(), str(patch), "exec"), namespace)

  stale = """.method private flushNext()V
    .locals 6
    .line 423
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectIfNeeded()V
.end method"""
  fixed = namespace["patch_flush_next"](stale)

  assert "->mConnected:Z" in fixed
  assert "->mNotifyReady:Z" in fixed
  assert "->mStartQueued:Z" in fixed
  assert "->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;" in fixed
  assert "->mNotifyCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;" in fixed
  assert "->closeGatt()V" in fixed
  assert "->scheduleReconnect()V" in fixed
  assert "->connectIfNeeded()V" not in fixed


def test_navdy_hud_centers_restore_speed_and_separates_icbm_status():
  patch = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning"
  receiver = patch / "smali/com/navdy/hud/app/openpilot/OpenpilotStateReceiver.smali"
  smali = receiver.read_text()

  assert 'const-string v0, "automaticAccActive"' in smali
  assert 'const-string v0, "automaticAccAtTarget"' in smali
  assert 'const-string v0, "actualAccSetKph"' in smali
  assert 'const-string v0, "automaticAccTargetKph"' in smali
  assert "sActualAccSpeedTextView:Landroid/widget/TextView;" in smali
  assert "sAutomaticAccTargetSpeedTextView:Landroid/widget/TextView;" in smali
  assert "sAutomaticAccArrowView:Landroid/widget/ImageView;" in smali
  assert "sAutomaticAccArrowAnimation:Landroid/view/animation/AlphaAnimation;" in smali
  assert 'const-string v4, "navdy_acc_control_arrow"' in smali
  assert "Landroid/view/animation/AlphaAnimation;" in smali
  assert "->getAnimation()Landroid/view/animation/Animation;" in smali
  assert "->clearAnimation()V" in smali
  assert "->setRotation(F)V" in smali
  assert "const/high16 p1, -0x3d4c0000    # -90.0f" in smali
  assert "const/high16 p1, 0x42b40000    # 90.0f" in smali
  assert "if-nez v1, :cond_9" in smali
  reached_check = (
    "sget-boolean v1, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sAutomaticAccAtTarget:Z\n\n"
    "    if-nez v1, :cond_9"
  )
  assert reached_check in smali
  overlay_update = smali.split(".method private static updateOpenpilotOverlay", 1)[1].split(".end method", 1)[0]
  actual_acc_update = overlay_update.split("->sActualAccSpeedKph:D", 1)[1]
  speed_compare = actual_acc_update.index("cmpl-double p5, p1, p3")
  speed_format = actual_acc_update.index("->formatSetSpeed(D)Ljava/lang/String;")
  reached_state = actual_acc_update.index("->sAutomaticAccAtTarget:Z")
  assert speed_compare < speed_format < reached_state
  hidden_block = smali.rsplit(":cond_a", 1)[1].split(":goto_6", 1)[0]
  assert (
    "sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;"
    "->sAutomaticAccArrowView:Landroid/widget/ImageView;\n\n"
    "    invoke-virtual {p0}, Landroid/widget/ImageView;->clearAnimation()V\n\n"
    "    invoke-virtual {p0, p1}, Landroid/widget/ImageView;->setVisibility(I)V"
  ) in hidden_block
  assert "Landroid/view/Space;" not in smali
  assert "new-instance v2, Landroid/view/View;" in smali
  assert "const/high16 v3, 0x41980000    # 19.0f" in smali
  set_speed_builder = smali.split(".method private static buildSetSpeedRow", 1)[1].split(".end method", 1)[0]
  overlay_builder = smali.split(".method private static buildOverlayView", 1)[1].split(".end method", 1)[0]
  assert set_speed_builder.count("Landroid/widget/TextView;->setGravity(I)V") == 3
  assert "const/16 v4, 0x46" not in set_speed_builder
  assert overlay_builder.count("Landroid/widget/LinearLayout;->removeView(Landroid/view/View;)V") == 3
  assert "const/16 v4, 0x15c" in overlay_builder
  assert "const/16 v4, 0x129" in overlay_builder
  assert "const/16 v4, 0x17f" in overlay_builder
  assert "const/16 v4, 0x131" in overlay_builder
  assert "const/16 v4, 0x16c" in overlay_builder
  assert "const/16 v4, 0x142" in overlay_builder
  assert "Landroid/widget/TextView;->setBackgroundColor(I)V" in overlay_builder
  assert (patch / "res/drawable-nodpi/navdy_acc_control_arrow.png").is_file()


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


def test_navdy_secondary_text_matches_engaged_music_weight():
  layout = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
           "res/layout/screen_home_smartdash.xml"
  root = ET.parse(layout).getroot()
  android = "{http://schemas.android.com/apk/res/android}"
  navdy = "{http://schemas.android.com/apk/res-auto}"
  ids = ("@id/music_track_info", "@id/txt_time", "@id/si_temperature")

  for view_id in ids:
    view = next(view for view in root.iter() if view.attrib.get(f"{android}id") == view_id)
    assert view.attrib.get("style") == "@style/Roboto"
    assert f"{navdy}fontFile" not in view.attrib


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


def test_payload_keeps_restore_speed_and_adds_physical_and_control_targets():
  car_state = navdy_op_bridge.default_car_state()
  car_state.vCruise = 100.0
  car_state.vCruiseCluster = 100.0
  car_state.cruiseState.speedCluster = 60.0 / navdy_op_bridge.KPH_PER_MS
  selfdrive_state = SimpleNamespace(active=True, enabled=True, engageable=True, state="enabled")
  selfdrive_state_sp = SimpleNamespace(
    intelligentCruiseButtonManagement=SimpleNamespace(
      automaticControlActive=True,
      automaticTargetSpeedKph=70.0,
      state="holding",
    ))

  payload = navdy_op_bridge.payload_from_messages(
    selfdrive_state, car_state, 8, selfdrive_state_sp=selfdrive_state_sp)

  assert payload["setSpeedKph"] == 100.0
  assert payload["actualAccSetKph"] == 60.0
  assert payload["automaticAccTargetKph"] == 70.0
  assert payload["automaticAccActive"] is True
  assert payload["automaticAccAtTarget"] is False


def test_payload_exposes_section_enforcement_metrics_to_navdy():
  car_state = navdy_op_bridge.default_car_state()
  selfdrive_state = SimpleNamespace(active=True, enabled=True, engageable=True, state="enabled")
  selfdrive_state_sp = SimpleNamespace(
    intelligentCruiseButtonManagement=SimpleNamespace(
      automaticControlActive=True,
      automaticTargetSpeedKph=105.0,
      sectionPhase="cruise",
      sectionLimitKph=100.0,
      sectionAverageKph=92.4,
      sectionProgress=0.64,
      sectionRemainingM=1300.0,
    ))

  payload = navdy_op_bridge.payload_from_messages(
    selfdrive_state, car_state, 8, selfdrive_state_sp=selfdrive_state_sp)

  assert payload["sectionPhase"] == "cruise"
  assert payload["sectionLimitKph"] == 100.0
  assert payload["sectionAverageKph"] == 92.4
  assert payload["sectionProgress"] == 0.64
  assert payload["sectionRemainingM"] == 1300.0


def test_payload_marks_icbm_target_reached_from_matching_cluster_values():
  car_state = navdy_op_bridge.default_car_state()
  car_state.cruiseState.speedCluster = 49.6 / navdy_op_bridge.KPH_PER_MS
  selfdrive_state = SimpleNamespace(active=True, enabled=True, engageable=True, state="enabled")
  selfdrive_state_sp = SimpleNamespace(
    intelligentCruiseButtonManagement=SimpleNamespace(
      automaticControlActive=True,
      automaticTargetSpeedKph=50.0,
      state="decreasing",
    ))

  payload = navdy_op_bridge.payload_from_messages(
    selfdrive_state, car_state, 8, selfdrive_state_sp=selfdrive_state_sp)

  assert payload["actualAccSetKph"] == 49.6
  assert payload["automaticAccTargetKph"] == 50.0
  assert payload["automaticAccAtTarget"] is True


def test_payload_prefers_cluster_corrected_vehicle_and_acc_speeds():
  car_state = navdy_op_bridge.default_car_state()
  car_state.vEgo = 95.0 / navdy_op_bridge.KPH_PER_MS
  car_state.vEgoCluster = 100.0 / navdy_op_bridge.KPH_PER_MS
  car_state.vCruise = 95.0
  car_state.vCruiseCluster = 100.0
  car_state.cruiseState.speed = 95.0 / navdy_op_bridge.KPH_PER_MS
  car_state.cruiseState.speedCluster = 100.0 / navdy_op_bridge.KPH_PER_MS
  selfdrive_state = SimpleNamespace(active=True, enabled=True, engageable=True, state="enabled")
  selfdrive_state_sp = SimpleNamespace(
    intelligentCruiseButtonManagement=SimpleNamespace(
      automaticControlActive=True,
      automaticTargetSpeedKph=90.0,
      state="increasing",
    ))

  payload = navdy_op_bridge.payload_from_messages(
    selfdrive_state, car_state, 9, selfdrive_state_sp=selfdrive_state_sp)

  assert payload["vEgoKph"] == 100.0
  assert payload["setSpeedKph"] == 100.0
  assert payload["actualAccSetKph"] == 100.0


def test_navdy_set_speed_keeps_openpilot_speed_during_stock_acc_mismatch():
  args = SimpleNamespace()
  payload = {
    "enabled": True,
    "active": True,
    "setSpeedKph": 53.0,
    "_physicalAccSetKph": 58.1,
    "automaticAccActive": False,
  }

  navdy_op_bridge.reconcile_display_set_speed(payload, args, now=10.0)
  assert payload["setSpeedKph"] == 53.0

  payload["_physicalAccSetKph"] = 59.2
  navdy_op_bridge.reconcile_display_set_speed(payload, args, now=10.49)
  assert payload["setSpeedKph"] == 53.0

  payload["_physicalAccSetKph"] = 60.4
  navdy_op_bridge.reconcile_display_set_speed(payload, args, now=10.5)
  assert payload["setSpeedKph"] == 53.0

  payload["setSpeedKph"] = 53.0
  payload["_physicalAccSetKph"] = 60.4
  navdy_op_bridge.reconcile_display_set_speed(payload, args, now=10.6)
  assert payload["setSpeedKph"] == 53.0
  assert "_physicalAccSetKph" not in payload


def test_navdy_set_speed_ignores_short_engage_transient_and_icbm_control():
  args = SimpleNamespace()
  payload = {
    "enabled": True,
    "active": True,
    "setSpeedKph": 70.0,
    "_physicalAccSetKph": 66.0,
    "automaticAccActive": False,
  }

  navdy_op_bridge.reconcile_display_set_speed(payload, args, now=20.0)
  assert payload["setSpeedKph"] == 70.0

  payload["_physicalAccSetKph"] = 70.0
  navdy_op_bridge.reconcile_display_set_speed(payload, args, now=20.2)
  assert payload["setSpeedKph"] == 70.0
  assert not args._acc_display_physical_override

  payload["setSpeedKph"] = 100.0
  payload["_physicalAccSetKph"] = 60.0
  payload["automaticAccActive"] = True
  navdy_op_bridge.reconcile_display_set_speed(payload, args, now=21.0)
  assert payload["setSpeedKph"] == 100.0
  assert not args._acc_display_physical_override


def test_navdy_set_speed_only_holds_a_short_source_gap():
  args = SimpleNamespace(
    blinker_hold_sec=0.0,
    blindspot_hold_sec=0.0,
  )
  payload = {
    "enabled": True,
    "active": True,
    "engaged": True,
    "setSpeedKph": 70.0,
  }

  navdy_op_bridge.stabilize_display_payload(payload, args, now=10.0)
  assert payload["setSpeedKph"] == 70.0

  payload["setSpeedKph"] = 0.0
  navdy_op_bridge.stabilize_display_payload(payload, args, now=10.5)
  assert payload["setSpeedKph"] == 70.0

  payload["setSpeedKph"] = 0.0
  navdy_op_bridge.stabilize_display_payload(payload, args, now=10.61)
  assert payload["setSpeedKph"] == 0.0
  assert args._last_set_speed_kph == 0.0


def test_navdy_set_speed_cache_clears_when_disengaged():
  args = SimpleNamespace(
    blinker_hold_sec=0.0,
    blindspot_hold_sec=0.0,
  )
  payload = {
    "enabled": True,
    "active": True,
    "engaged": True,
    "setSpeedKph": 80.0,
  }
  navdy_op_bridge.stabilize_display_payload(payload, args, now=20.0)

  payload.update(enabled=False, active=False, engaged=False, setSpeedKph=0.0)
  navdy_op_bridge.stabilize_display_payload(payload, args, now=20.1)
  assert args._last_set_speed_kph == 0.0

  payload.update(enabled=True, active=True, engaged=True, setSpeedKph=0.0)
  navdy_op_bridge.stabilize_display_payload(payload, args, now=20.2)
  assert payload["setSpeedKph"] == 0.0


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
    "gear": "drive",
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
    "gear": "drive",
    "alertSize": "none",
    "greenLightAlert": False,
    "leadDepartAlert": False,
  }
  navdy_op_bridge.apply_navdy_e2e_alert(held, args, 12.9)
  assert held["alertText1"] == "신호 변경됨"

  expired = {
    "gear": "drive",
    "alertSize": "none",
    "greenLightAlert": False,
    "leadDepartAlert": False,
  }
  navdy_op_bridge.apply_navdy_e2e_alert(expired, args, 13.1)
  assert "alertText1" not in expired


def test_navdy_e2e_reader_latches_one_frame_until_consumed():
  reader = object.__new__(navdy_op_bridge.NavdyE2EAlertReader)
  reader._lock = threading.Lock()
  reader._green_until = 0.0
  reader._lead_until = 0.0

  reader.capture(True, False, now=10.0)

  assert reader.pending(now=11.9) == (True, False)
  assert reader.pending(now=11.9, consume=True) == (True, False)
  assert reader.pending(now=11.9) == (False, False)


def test_navdy_repeated_e2e_sample_does_not_extend_banner():
  args = SimpleNamespace()
  payload = {
    "gear": "drive",
    "alertSize": "none",
    "greenLightAlert": True,
    "leadDepartAlert": False,
  }

  navdy_op_bridge.apply_navdy_e2e_alert(payload, args, 10.0)
  navdy_op_bridge.apply_navdy_e2e_alert(payload, args, 10.5)

  assert args._navdy_e2e_alert_until == 13.0


def test_navdy_reverse_clears_held_e2e_banner():
  args = SimpleNamespace()
  drive = {
    "gear": "drive",
    "alertSize": "none",
    "greenLightAlert": True,
    "leadDepartAlert": False,
  }
  navdy_op_bridge.apply_navdy_e2e_alert(drive, args, 10.0)

  reverse = {
    "gear": "reverse",
    "alertSize": "none",
    "greenLightAlert": False,
    "leadDepartAlert": False,
  }
  navdy_op_bridge.apply_navdy_e2e_alert(reverse, args, 10.1)

  assert "alertText1" not in reverse
  assert args._navdy_e2e_alert_name == ""
  assert args._navdy_e2e_alert_until == 0.0


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


def test_comma_uses_standard_renderer_for_green_light_and_lead_depart_alerts():
  ui_root = Path(__file__).parents[1] / "ui" / "sunnypilot"
  mici_hud = (ui_root / "mici/onroad/hud_renderer.py").read_text()
  large_hud = (ui_root / "onroad/hud_renderer.py").read_text()
  mici_alert = (Path(__file__).parents[1] / "ui/mici/onroad/alert_renderer.py").read_text()
  large_alert = (ui_root / "onroad/alert_renderer.py").read_text()

  assert "CircularAlertsRenderer" not in mici_hud
  assert "CircularAlertsRenderer" not in large_hud
  assert "E2EAlertController" in mici_alert
  assert "E2EAlertController" in large_alert
  assert 'alert_type=f"{e2e_alert.name}/permanent"' in mici_alert


def test_navdy_hud_patch_colors_current_speed_for_camera_overspeed():
  receiver = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
             "smali/com/navdy/hud/app/openpilot/OpenpilotStateReceiver.smali"
  smali = receiver.read_text()

  assert "TrafficIncidentWidgetPresenter;->getLastCameraSpeedLimit()I" in smali
  assert "cmpl-double v4, v16, v8" in smali
  assert "if-lez v4, :cond_8" in smali
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
  assert "if-eqz p0, :cond_4" in layout_method
  assert "const/16 v3, 0xeb" in layout_method
  assert "const/16 v3, 0x112" in layout_method
  assert "if-eqz p0, :cond_6" in layout_method
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


def test_navdy_path_renderer_keeps_lane_and_road_edges_legible():
  patch_root = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning"
  java = (patch_root / "src/com/navdy/hud/app/openpilot/OpenpilotPathView.java").read_text()
  smali = (patch_root / "smali/com/navdy/hud/app/openpilot/OpenpilotPathView.smali").read_text()

  assert "lanePaint.setStrokeWidth(3.2f)" in java
  assert "roadEdgePaint.setStrokeWidth(2.8f)" in java
  assert "roadEdgePaint.setColorFilter(new LightingColorFilter(COLOR_LANE_DANGER, 0))" in java
  assert "0x55ffffff, 0xffffffff" in java
  assert "confidence * 210.0f + 25.0f" in java
  assert "0x404ccccd    # 3.2f" in smali
  assert "0x40333333    # 2.8f" in smali
  assert "-0xdfd8" in smali
  assert "Paint;->setColorFilter(Landroid/graphics/ColorFilter;)" in smali
  assert "const v5, 0x55ffffff" in smali
  assert "const/high16 v1, 0x43520000    # 210.0f" in smali
  assert "const/high16 v1, 0x41c80000    # 25.0f" in smali


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
  assert navdy_op_bridge.NAVDY_CALIBRATION_SERVICE not in navdy_op_bridge.NAVDY_FAST_SERVICES


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


def test_navdy_vehicle_geometry_marks_only_the_active_mpc_lead():
  radar_points = [
    {"trackId": 10, "dRel": 30.0, "yRel": -0.2, "vRel": -5.0},
    {"trackId": 11, "dRel": 26.0, "yRel": 3.0, "vRel": 0.5},
  ]
  radar_state = SimpleNamespace(
    leadOne=SimpleNamespace(
      status=True, radar=True, radarTrackId=10, dRel=30.0, yRel=-0.2),
    leadTwo=SimpleNamespace(
      status=True, radar=True, radarTrackId=11, dRel=26.0, yRel=3.0),
  )
  longitudinal_plan = SimpleNamespace(longitudinalPlanSource="lead0")

  vehicles = navdy_op_bridge.navdy_vehicle_geometry(
    navdy_vehicle_test_model(), radar_points, radar_state, longitudinal_plan)["navVehicles"]
  by_id = {vehicle["trackId"]: vehicle for vehicle in vehicles}

  assert by_id[10]["longitudinalLead"] is True
  assert by_id[11]["longitudinalLead"] is False


def test_navdy_vehicle_geometry_does_not_mark_a_lead_when_cruise_controls():
  radar_points = [{"trackId": 10, "dRel": 30.0, "yRel": -0.2, "vRel": -5.0}]
  radar_state = SimpleNamespace(
    leadOne=SimpleNamespace(
      status=True, radar=True, radarTrackId=10, dRel=30.0, yRel=-0.2),
  )
  longitudinal_plan = SimpleNamespace(longitudinalPlanSource="cruise")

  vehicles = navdy_op_bridge.navdy_vehicle_geometry(
    navdy_vehicle_test_model(), radar_points, radar_state, longitudinal_plan)["navVehicles"]

  assert all(vehicle["longitudinalLead"] is False for vehicle in vehicles)


def test_navdy_vehicle_geometry_marks_a_vision_only_secondary_mpc_lead():
  model = navdy_vehicle_test_model()
  model.leadsV3[1] = SimpleNamespace(
    prob=0.88, x=[41.52], y=[0.4], yStd=[0.4], v=[18.0])
  radar_state = SimpleNamespace(
    leadOne=SimpleNamespace(status=False),
    leadTwo=SimpleNamespace(
      status=True, radar=False, radarTrackId=-1, dRel=40.0, yRel=-0.4),
  )
  longitudinal_plan = SimpleNamespace(longitudinalPlanSource="lead1")

  vehicles = navdy_op_bridge.navdy_vehicle_geometry(
    model, [], radar_state, longitudinal_plan)["navVehicles"]
  by_id = {vehicle["trackId"]: vehicle for vehicle in vehicles}

  assert by_id[-101]["source"] == "vision"
  assert by_id[-101]["longitudinalLead"] is True
  assert sum(vehicle["longitudinalLead"] for vehicle in vehicles) == 1


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


def test_navdy_payload_signature_tracks_longitudinal_lead_changes():
  inactive = {"navVehicles": [{"trackId": 1, "longitudinalLead": False}]}
  active = {"navVehicles": [{"trackId": 1, "longitudinalLead": True}]}

  assert navdy_op_bridge.payload_signature(inactive) != navdy_op_bridge.payload_signature(active)


def test_navdy_payload_signature_tracks_lane_risk_changes():
  clear = {"navLaneRiskLeft": 0.0, "navLaneRiskRight": 0.0}
  danger = {"navLaneRiskLeft": 0.65, "navLaneRiskRight": 0.0}

  assert navdy_op_bridge.payload_signature(clear) != navdy_op_bridge.payload_signature(danger)


def test_navdy_payload_signature_tracks_lane_marking_type_changes():
  dashed = {"navLaneLeftType": "dashed"}
  solid = {"navLaneLeftType": "solid"}

  assert navdy_op_bridge.payload_signature(dashed) != navdy_op_bridge.payload_signature(solid)


def test_navdy_payload_signature_tracks_automatic_acc_completion():
  adjusting = {
    "automaticAccActive": True,
    "automaticAccAtTarget": False,
    "actualAccSetKph": 30.0,
    "automaticAccTargetKph": 30.0,
  }
  complete = dict(adjusting, automaticAccAtTarget=True)

  assert navdy_op_bridge.payload_signature(adjusting) != navdy_op_bridge.payload_signature(complete)


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
  assert "drawLane(canvas, laneFarLeft, laneFarLeftProb, 0.0f, laneFarLeftType)" in java
  assert "drawLane(canvas, laneLeft, laneLeftProb, laneRiskLeft, laneLeftType)" in java
  assert "drawLane(canvas, laneRight, laneRightProb, laneRiskRight, laneRightType)" in java
  assert "drawLane(canvas, laneFarRight, laneFarRightProb, 0.0f, laneFarRightType)" in java
  assert "lanePaint.setPathEffect(solid ? null : laneDashEffect)" in java
  assert "canvas.drawPath(linePath(points), roadEdgePaint)" in java
  assert "canvas.drawPath(linePath(points), lanePaint)" in java
  assert "vehicleSpeedKph > 1.0f" in java
  assert "OpenpilotPathView extends View implements Runnable" in java
  assert "if (dashFrameScheduled)" in java
  assert "postDelayed(this, DASH_FRAME_MS)" in java
  assert "removeCallbacks(this)" in java
  assert "postInvalidateDelayed(DASH_FRAME_MS)" not in java
  assert java.index("drawRoadEdge(canvas, roadEdgeLeft") < java.index("laneDashEffect = new")


def test_navdy_path_renderer_uses_classified_solid_and_center_lines():
  patch_root = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning"
  java = (patch_root / "src/com/navdy/hud/app/openpilot/OpenpilotPathView.java").read_text()

  for suffix in ("FarLeft", "Left", "Right", "FarRight"):
    assert f'readLaneType(json, "navLane{suffix}Type")' in java
  assert 'type.startsWith("center")' in java
  assert '"centerSolid".equals(type)' in java
  assert "COLOR_LANE_CENTER = 0xffffd43b" in java
  assert "centerLaneRiskFilters[filterIndex]" in java


def test_navdy_path_renderer_blends_inner_lanes_toward_red_by_risk():
  patch_root = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning"
  source = patch_root / "src/com/navdy/hud/app/openpilot/OpenpilotPathView.java"
  java = source.read_text()
  smali = (patch_root / "smali/com/navdy/hud/app/openpilot/OpenpilotPathView.smali").read_text()

  assert "COLOR_LANE_DANGER = 0xffff2028" in java
  assert 'json.optDouble("navLaneRiskLeft", 0.0)' in java
  assert 'json.optDouble("navLaneRiskRight", 0.0)' in java
  assert "centerline ? centerLaneRiskFilters[filterIndex] : laneRiskFilters[filterIndex]" in java
  assert "new LightingColorFilter[LANE_RISK_FILTER_STEPS + 1]" in java
  assert 'const-string v2, "navLaneRiskLeft"' in smali
  assert 'const-string v1, "navLaneRiskRight"' in smali
  assert ".method private drawLane(Landroid/graphics/Canvas;[FFFLjava/lang/String;)V" in smali


def test_navdy_vehicle_markers_remain_visible_at_long_range():
  source = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / \
           "src/com/navdy/hud/app/openpilot/OpenpilotPathView.java"
  java = source.read_text()

  assert "float width = 12.0f + nearScale * 46.5f" in java
  assert "float height = width * 1.55f" in java


def test_navdy_path_renderer_highlights_only_the_active_longitudinal_lead():
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
  assert "COLOR_VEHICLE_LONGITUDINAL_LEAD" in java
  assert 'vehicle.optBoolean("longitudinalLead", false)' in java
  assert 'const-string v6, "longitudinalLead"' in (
    patch_root / "smali/com/navdy/hud/app/openpilot/OpenpilotPathView.smali").read_text()
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
  assert "--lane-marking-classifier" in navdy_power_bridge.DEFAULT_ARGS


def test_manager_defaults_keep_fast_state_and_throttle_path():
  hz = float(navdy_power_bridge.DEFAULT_ARGS[navdy_power_bridge.DEFAULT_ARGS.index("--hz") + 1])
  path_update_sec = float(navdy_power_bridge.DEFAULT_ARGS[navdy_power_bridge.DEFAULT_ARGS.index("--path-update-sec") + 1])
  marking_update_sec = float(
    navdy_power_bridge.DEFAULT_ARGS[
      navdy_power_bridge.DEFAULT_ARGS.index("--lane-marking-interval-sec") + 1])
  assert hz == 5.0
  assert path_update_sec == 0.1
  assert marking_update_sec == 0.5
  assert marking_update_sec >= path_update_sec * 5.0
  assert path_update_sec < 1.0 / hz
  assert "--min-emit-sec" not in navdy_power_bridge.DEFAULT_ARGS
  assert navdy_power_bridge.DEFAULT_ARGS[navdy_power_bridge.DEFAULT_ARGS.index("--heartbeat-sec") + 1] == "5"
  assert navdy_power_bridge.DEFAULT_ARGS[navdy_power_bridge.DEFAULT_ARGS.index("--power-on-ensure-sec") + 1] == "60"
  assert navdy_power_bridge.DEFAULT_ARGS[navdy_power_bridge.DEFAULT_ARGS.index("--power-off-ensure-sec") + 1] == "5"


def test_navdy_power_rechecks_display_after_offroad_sleep(monkeypatch):
  calls = []
  args = SimpleNamespace(
      manage_navdy_power=True,
      power_off_delay_sec=30.0,
      power_off_ensure_sec=5.0,
      power_on_ensure_sec=60.0,
      _last_power_off_ensure_at=0.0,
  )
  monkeypatch.setattr(navdy_op_bridge, "set_navdy_display",
                      lambda _args, should_be_on, reason: calls.append((should_be_on, reason)) or True)

  offroad_since, target_on = navdy_op_bridge.manage_navdy_power(args, False, 131.0, 100.0, False)
  assert calls == [(False, "offroad")]
  assert offroad_since == 100.0
  assert target_on is False

  navdy_op_bridge.manage_navdy_power(args, False, 134.0, offroad_since, target_on)
  assert calls == [(False, "offroad")]

  navdy_op_bridge.manage_navdy_power(args, False, 136.0, offroad_since, target_on)
  assert calls == [(False, "offroad"), (False, "offroad")]


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


def test_socket_sender_keeps_only_latest_pending_payload():
  args = SimpleNamespace(
    _socket_sender_cond=threading.Condition(),
    _socket_sender_pending=None,
  )

  navdy_op_bridge.queue_socket({"seq": 1}, args)
  navdy_op_bridge.queue_socket({"seq": 2}, args)

  assert args._socket_sender_pending == {"seq": 2}


def test_socket_feedback_publishes_camera_speed_without_wifi(tmp_path, monkeypatch):
  camera_state = tmp_path / "navdy_camera_state.json"
  monkeypatch.setattr(navdy_op_bridge, "NAVDY_CAMERA_STATE_PATH", str(camera_state))
  sender, receiver = socket.socketpair()
  args = SimpleNamespace(_socket_feedback_buffer=b"")
  try:
    receiver.sendall(b'{"cameraSpeedKph":60,"cameraSource":"trafficNotification","cameraType":"fixed","cameraDistance":"850 m"}\n')
    assert navdy_op_bridge.read_navdy_feedback(sender, args)
  finally:
    sender.close()
    receiver.close()

  assert camera_state.read_text() == '{"cameraSpeedKph":60,"cameraSource":"trafficNotification","cameraType":"fixed","cameraDistanceM":850.0}'


def test_socket_feedback_marks_mobile_camera_for_icbm_filter(tmp_path, monkeypatch):
  camera_state = tmp_path / "navdy_camera_state.json"
  monkeypatch.setattr(navdy_op_bridge, "NAVDY_CAMERA_STATE_PATH", str(camera_state))
  sender, receiver = socket.socketpair()
  args = SimpleNamespace(_socket_feedback_buffer=b"")
  try:
    receiver.sendall(b'{"cameraSpeedKph":60,"cameraSource":"trafficNotification","cameraType":"mobile"}\n')
    assert navdy_op_bridge.read_navdy_feedback(sender, args)
  finally:
    sender.close()
    receiver.close()

  assert camera_state.read_text() == '{"cameraSpeedKph":60,"cameraSource":"trafficNotification","cameraType":"mobile","cameraDistanceM":0.0}'


def test_socket_feedback_preserves_section_camera_and_kilometer_distance(tmp_path, monkeypatch):
  camera_state = tmp_path / "navdy_camera_state.json"
  monkeypatch.setattr(navdy_op_bridge, "NAVDY_CAMERA_STATE_PATH", str(camera_state))
  sender, receiver = socket.socketpair()
  args = SimpleNamespace(_socket_feedback_buffer=b"")
  try:
    receiver.sendall(b'{"cameraSpeedKph":100,"cameraSource":"trafficNotification","cameraType":"section","cameraDistance":"1.3km"}\n')
    assert navdy_op_bridge.read_navdy_feedback(sender, args)
  finally:
    sender.close()
    receiver.close()

  assert camera_state.read_text() == \
    '{"cameraSpeedKph":100,"cameraSource":"trafficNotification","cameraType":"section","cameraDistanceM":1300.0}'


def test_camera_distance_parser_supports_navdy_formats():
  assert navdy_op_bridge.parse_camera_distance_m("320 m") == 320
  assert navdy_op_bridge.parse_camera_distance_m("1.3km") == 1300
  assert navdy_op_bridge.parse_camera_distance_m("--") == 0


def test_duplicate_camera_feedback_refreshes_heartbeat_at_bounded_rate(tmp_path, monkeypatch):
  camera_state = tmp_path / "navdy_camera_state.json"
  monkeypatch.setattr(navdy_op_bridge, "NAVDY_CAMERA_STATE_PATH", str(camera_state))
  clock = iter((10.0, 10.2, 10.6))
  monkeypatch.setattr(navdy_op_bridge.time, "monotonic", lambda: next(clock))
  touches = []
  real_utime = navdy_op_bridge.os.utime
  monkeypatch.setattr(navdy_op_bridge.os, "utime", lambda path, times: (touches.append(path), real_utime(path, times)))
  args = SimpleNamespace()

  navdy_op_bridge.publish_navdy_camera_state(100, "trafficNotification", "section", "5.0km", args)
  navdy_op_bridge.publish_navdy_camera_state(100, "trafficNotification", "section", "5.0km", args)
  navdy_op_bridge.publish_navdy_camera_state(100, "trafficNotification", "section", "5.0km", args)

  assert touches == [str(camera_state)]


def test_socket_feedback_rejects_untagged_notification_number(tmp_path, monkeypatch):
  camera_state = tmp_path / "navdy_camera_state.json"
  monkeypatch.setattr(navdy_op_bridge, "NAVDY_CAMERA_STATE_PATH", str(camera_state))
  sender, receiver = socket.socketpair()
  args = SimpleNamespace(_socket_feedback_buffer=b"")
  try:
    receiver.sendall(b'{"cameraSpeedKph":30}\n')
    assert navdy_op_bridge.read_navdy_feedback(sender, args)
  finally:
    sender.close()
    receiver.close()

  assert camera_state.read_text() == \
    '{"cameraSpeedKph":0,"cameraSource":"","cameraType":"","cameraDistanceM":0.0}'


def test_socket_feedback_detects_closed_navdy_tunnel():
  sender, receiver = socket.socketpair()
  args = SimpleNamespace(_socket_feedback_buffer=b"")
  receiver.close()
  try:
    assert not navdy_op_bridge.read_navdy_feedback(sender, args)
  finally:
    sender.close()


def test_emit_queues_socket_work_off_polling_thread():
  args = SimpleNamespace(
    stdout=False,
    socket_transport=True,
    adb_path="adb",
    adb_fallback=True,
    _socket_sender_cond=threading.Condition(),
    _socket_sender_pending=None,
  )
  original_socket_send = navdy_op_bridge.socket_send
  navdy_op_bridge.socket_send = lambda *_args, **_kwargs: (_ for _ in ()).throw(
      AssertionError("socket send must not run on polling thread"))
  try:
    navdy_op_bridge.emit({"seq": 7}, args)
  finally:
    navdy_op_bridge.socket_send = original_socket_send

  assert args._socket_sender_pending == {"seq": 7}


def test_adb_recovery_restarts_offline_dedicated_server(monkeypatch):
  args = SimpleNamespace(
    adb_path="adb",
    adb_server_port=5038,
    adb_timeout_sec=4.0,
    adb_wait_device_sec=1.0,
    adb_recover_sec=5.0,
    stdout=False,
    _last_adb_recover_at=0.0,
    _adb_recover_lock=threading.Lock(),
  )
  calls = []

  def fake_run(command, **_kwargs):
    calls.append(command)
    output = "FPI647618N4111AT\toffline\n" if command[-1] == "devices" else ""
    return SimpleNamespace(returncode=0, stdout=output, stderr="")

  monkeypatch.setattr(navdy_op_bridge.subprocess, "run", fake_run)
  monkeypatch.setattr(navdy_op_bridge.time, "monotonic", lambda: 10.0)

  navdy_op_bridge.recover_adb(args, "returncode", force=True)

  assert calls == [
    ["adb", "-P", "5038", "devices"],
    ["adb", "-P", "5038", "kill-server"],
    ["adb", "-P", "5038", "start-server"],
    ["adb", "-P", "5038", "wait-for-device"],
  ]


def test_adb_recovery_keeps_healthy_server(monkeypatch):
  args = SimpleNamespace(
    adb_path="adb",
    adb_server_port=5038,
    adb_timeout_sec=4.0,
    adb_wait_device_sec=1.0,
    adb_recover_sec=5.0,
    stdout=False,
    _last_adb_recover_at=0.0,
    _adb_recover_lock=threading.Lock(),
  )
  calls = []

  def fake_run(command, **_kwargs):
    calls.append(command)
    output = "FPI647618N4111AT\tdevice\n" if command[-1] == "devices" else ""
    return SimpleNamespace(returncode=0, stdout=output, stderr="")

  monkeypatch.setattr(navdy_op_bridge.subprocess, "run", fake_run)
  monkeypatch.setattr(navdy_op_bridge.time, "monotonic", lambda: 10.0)

  navdy_op_bridge.recover_adb(args, "startup", force=True)

  assert ["adb", "-P", "5038", "kill-server"] not in calls
  assert calls[-2:] == [
    ["adb", "-P", "5038", "start-server"],
    ["adb", "-P", "5038", "wait-for-device"],
  ]


def test_manager_child_ignores_inherited_manager_argv():
  assert navdy_power_bridge.should_use_default_args(
      "navdy_bridge", ["manager.py", "--socket-transport"])


if __name__ == "__main__":
  test_payload_exports_standstill_and_op_available()
  test_available_services_skips_missing_starpilot_plan()
  test_live_payload_ready_uses_recent_messages_not_alive_flags()
  test_live_payload_ready_allows_missing_car_state_when_selfdrive_is_recent()
  test_default_car_state_keeps_payload_safe_without_vehicle_sample()
  test_navdy_socket_receiver_coalesces_frames_and_skips_payload_logs()
  test_navdy_path_view_retains_geometry_during_fast_state_updates()
  test_manager_defaults_use_starpilot_socket_transport()
  test_manager_defaults_keep_fast_state_and_throttle_path()
  test_navdy_path_update_is_independent_from_fast_state_rate()
  test_should_emit_payload_respects_min_emit_interval()
  test_fast_state_change_emits_before_next_path_update()
  test_socket_sender_keeps_only_latest_pending_payload()
  test_emit_queues_socket_work_off_polling_thread()
  test_manager_child_ignores_inherited_manager_argv()
