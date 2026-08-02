#!/usr/bin/env python3
"""Read openpilot state and forward compact JSON for Navdy tests.

Run on comma/openpilot root. Default prints JSON lines.
If Navdy enumerates as ADB from comma, add --adb-serial or --adb-path.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import select
import shlex
import socket
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
from typing import Any


KPH_PER_MS = 3.6
DEFAULT_ACTION = "com.navdy.OPENPILOT_STATE"
DEFAULT_COMPONENT = "com.navdy.hud.app/.openpilot.OpenpilotStateReceiver"
DEFAULT_SERVICE_COMPONENT = "com.navdy.hud.app/.openpilot.OpenpilotStateService"
DEFAULT_SOCKET_PORT = 18765
DEFAULT_DEVICE_SOCKET_PORT = 8765
NAVDY_CAMERA_STATE_PATH = "/dev/shm/navdy_camera_state.json"
NAVDY_LANE_MARKING_STATE_PATH = "/dev/shm/navdy_lane_marking_state.json"
DISPLAY_ON_TEXT = "Display Power: state=ON"
DISPLAY_OFF_TEXT = "Display Power: state=OFF"
WAKEFULNESS_AWAKE_TEXT = "mWakefulness=Awake"
WAKEFULNESS_ASLEEP_TEXT = "mWakefulness=Asleep"
INTERACTIVE_ON_TEXT = "mHalInteractiveModeEnabled=true"
INTERACTIVE_OFF_TEXT = "mHalInteractiveModeEnabled=false"
KEYEVENT_POWER = "26"
KEYEVENT_WAKEUP = "224"
ONROAD_PROCESS_NAMES = (
  "selfdrive.controls.controlsd",
  "selfdrive.selfdrived.selfdrived",
  "selfdrive.car.card",
  "selfdrive.modeld.modeld",
  "./camerad",
)
NAVDY_CAR_STATE_SERVICE = "carStateSP"
NAVDY_FAST_SERVICES = (
  "selfdriveState",
  "selfdriveStateSP",
  NAVDY_CAR_STATE_SERVICE,
  "controlsState",
  "starpilotPlan",
  "longitudinalPlan",
  "longitudinalPlanSP",
)
NAVDY_MODEL_SERVICE = "modelV2"
NAVDY_CALIBRATION_SERVICE = "liveCalibration"
NAVDY_RADAR_TO_CAMERA_M = 1.52
NAVDY_VEHICLE_MAX_DISTANCE_M = 80.0
NAVDY_VEHICLE_MAX_COUNT = 8
NAVDY_RADAR_STALE_SEC = 0.35
NAVDY_RADAR_RETRY_SEC = 5.0
NAVDY_RADAR_MAX_TRACK_WIDTH_M = 4.0
NAVDY_E2E_ALERT_HOLD_SEC = 3.0
NAVDY_E2E_CAPTURE_HOLD_SEC = 2.0
NAVDY_FALLBACK_LANE_WIDTH_M = 3.6
NAVDY_MIN_LANE_WIDTH_M = 2.4
NAVDY_MAX_LANE_WIDTH_M = 4.8
NAVDY_VEHICLE_YAW_SAMPLE_M = 4.0
NAVDY_VEHICLE_MAX_YAW_DEG = 24.0
NAVDY_VEHICLE_NEAR_WIDTH_PX = 58.5
NAVDY_VEHICLE_FAR_WIDTH_PX = 12.0
NAVDY_VEHICLE_DUPLICATE_IOU = 0.25


def quiet_completed(cmd: list[str], returncode: int = 1) -> subprocess.CompletedProcess:
  return subprocess.CompletedProcess(cmd, returncode, stdout="", stderr="")


def finite_float(value: Any, default: float = 0.0) -> float:
  try:
    value = float(value)
  except (TypeError, ValueError):
    return default
  return value if math.isfinite(value) else default


def rounded(value: float, digits: int = 1) -> float:
  return round(finite_float(value), digits)


def create_navdy_lane_risk_detector() -> Any:
  try:
    from openpilot.sunnypilot.selfdrive.controls.lib.radar_lane_intrusion import RadarLaneIntrusionDetector
    return RadarLaneIntrusionDetector()
  except ImportError:
    return None


def create_navdy_lane_marking_classifier(args: argparse.Namespace) -> Any:
  if not args.lane_marking_classifier:
    return None
  try:
    from openpilot.selfdrive.navdy.lane_marking_classifier import NavdyLaneMarkingClassifier
    return NavdyLaneMarkingClassifier(
      interval_sec=args.lane_marking_interval_sec,
      stale_sec=args.lane_marking_stale_sec,
      stdout=args.stdout,
    )
  except Exception as error:
    if args.stdout:
      print(f"navdy lane classifier unavailable: {error}", flush=True)
    return None


def publish_navdy_lane_marking_state(markings: dict[str, str],
                                     path: str = NAVDY_LANE_MARKING_STATE_PATH) -> None:
  state = {
    "leftType": str(markings.get("navLaneLeftType", "unknown")),
    "rightType": str(markings.get("navLaneRightType", "unknown")),
    "updatedAtMonotonic": time.monotonic(),
  }
  temp_path = path + ".tmp"
  try:
    with open(temp_path, "w", encoding="utf-8") as state_file:
      json.dump(state, state_file, separators=(",", ":"))
    os.replace(temp_path, path)
  except OSError:
    try:
      os.unlink(temp_path)
    except OSError:
      pass


def navdy_lane_risk_values(detector: Any) -> dict[str, float]:
  risks = getattr(detector, "lane_risks", {}) if detector is not None else {}
  return {
    "navLaneRiskLeft": rounded(risks.get("left", 0.0), 2),
    "navLaneRiskRight": rounded(risks.get("right", 0.0), 2),
  }


def evaluate_navdy_lane_risk(detector: Any, model_v2: Any, radar_points: list[dict[str, Any]],
                             v_ego: float, now: float) -> tuple[dict[str, float], Any]:
  if detector is None or model_v2 is None:
    return navdy_lane_risk_values(detector), None
  meta = getattr(model_v2, "meta", None)
  lane_change_active = enum_text(getattr(meta, "laneChangeState", "off")) != "off"
  intrusion = detector.update(
    v_ego, radar_points, model_v2, now, lane_change_active=lane_change_active)
  return navdy_lane_risk_values(detector), intrusion


def update_navdy_lane_risk(detector: Any, model_v2: Any, radar_points: list[dict[str, Any]],
                           v_ego: float, now: float) -> dict[str, float]:
  return evaluate_navdy_lane_risk(detector, model_v2, radar_points, v_ego, now)[0]


def publish_radar_lane_intrusion(messaging: Any, pm: Any, intrusion: Any,
                                 risks: dict[str, float]) -> None:
  msg = messaging.new_message("radarLaneIntrusionSP")
  msg.valid = True
  state = msg.radarLaneIntrusionSP
  state.detected = intrusion is not None
  state.trackId = int(getattr(intrusion, "track_id", -1))
  side = str(getattr(intrusion, "side", "none"))
  state.side = side if side in ("left", "right") else "none"
  state.distance = finite_float(getattr(intrusion, "distance_m", 0.0))
  state.lateral = finite_float(getattr(intrusion, "lateral_m", 0.0))
  state.inwardSpeed = finite_float(getattr(intrusion, "inward_speed_mps", 0.0))
  state.leftRisk = finite_float(risks.get("navLaneRiskLeft", 0.0))
  state.rightRisk = finite_float(risks.get("navLaneRiskRight", 0.0))
  pm.send("radarLaneIntrusionSP", msg)


def enum_text(value: Any) -> str:
  text = str(value)
  return text.split(".")[-1]


def blinker_text(left: bool, right: bool) -> str:
  if left and right:
    return "hazard"
  if left:
    return "left"
  if right:
    return "right"
  return "off"


def blindspot_text(left: bool, right: bool) -> str:
  if left and right:
    return "both"
  if left:
    return "left"
  if right:
    return "right"
  return "off"


def hold_bool(args: argparse.Namespace, name: str, value: bool, now: float, hold_sec: float) -> bool:
  attr = f"_hold_{name}_until"
  if value:
    setattr(args, attr, now + max(hold_sec, 0.0))
    return True
  return now < float(getattr(args, attr, 0.0))


def navdy_e2e_alert_allowed(payload: dict[str, Any]) -> bool:
  return str(payload.get("gear", "unknown")).lower() not in ("neutral", "park", "reverse", "unknown")


class NavdyE2EAlertReader:
  """Latch one-frame planner alerts without increasing the main bridge rate."""

  def __init__(self, messaging: Any):
    self._messaging = messaging
    self._sock = messaging.sub_sock("longitudinalPlanSP", conflate=False, timeout=1000)
    self._lock = threading.Lock()
    self._green_until = 0.0
    self._lead_until = 0.0
    self._thread = threading.Thread(target=self._run, name="navdy_e2e_alert_reader", daemon=True)
    self._thread.start()

  def is_alive(self) -> bool:
    return self._thread.is_alive()

  def capture(self, green_light: bool, lead_depart: bool, now: float | None = None) -> None:
    now = time.monotonic() if now is None else now
    with self._lock:
      if green_light:
        self._green_until = max(self._green_until, now + NAVDY_E2E_CAPTURE_HOLD_SEC)
      if lead_depart:
        self._lead_until = max(self._lead_until, now + NAVDY_E2E_CAPTURE_HOLD_SEC)

  def pending(self, now: float | None = None, consume: bool = False) -> tuple[bool, bool]:
    now = time.monotonic() if now is None else now
    with self._lock:
      green_light = now < self._green_until
      lead_depart = now < self._lead_until
      if consume:
        if green_light:
          self._green_until = 0.0
        if lead_depart:
          self._lead_until = 0.0
      return green_light, lead_depart

  def _run(self) -> None:
    while True:
      try:
        msg = self._messaging.recv_one(self._sock)
        if msg is None:
          continue
        e2e_alerts = msg.longitudinalPlanSP.e2eAlerts
        self.capture(bool(e2e_alerts.greenLightAlert), bool(e2e_alerts.leadDepartAlert))
      except Exception:
        time.sleep(0.1)


def apply_navdy_e2e_alert(payload: dict[str, Any], args: argparse.Namespace, now: float) -> None:
  if not navdy_e2e_alert_allowed(payload):
    setattr(args, "_navdy_e2e_alert_name", "")
    setattr(args, "_navdy_e2e_alert_until", 0.0)
    return

  alert_name = ""
  if payload.get("greenLightAlert"):
    alert_name = "greenLight"
  elif payload.get("leadDepartAlert"):
    alert_name = "leadDeparting"
  if alert_name:
    held_name = str(getattr(args, "_navdy_e2e_alert_name", ""))
    held_until = float(getattr(args, "_navdy_e2e_alert_until", 0.0))
    if alert_name != held_name or now >= held_until:
      setattr(args, "_navdy_e2e_alert_name", alert_name)
      setattr(args, "_navdy_e2e_alert_until", now + NAVDY_E2E_ALERT_HOLD_SEC)

  if now >= float(getattr(args, "_navdy_e2e_alert_until", 0.0)):
    return
  if str(payload.get("alertSize", "none")) != "none":
    return

  held_name = str(getattr(args, "_navdy_e2e_alert_name", ""))
  if held_name == "greenLight":
    payload["alertText1"] = "신호 변경됨"
    payload["alertText2"] = "전방 신호 변경 감지됨"
  elif held_name == "leadDeparting":
    payload["alertText1"] = "전방 차량 출발"
    payload["alertText2"] = "전방 차량이 출발했습니다"
  else:
    return
  payload["alertType"] = f"{held_name}/permanent"
  payload["alertStatus"] = "normal"
  payload["alertSize"] = "mid"


def stabilize_display_payload(payload: dict[str, Any], args: argparse.Namespace, now: float) -> dict[str, Any]:
  set_speed = finite_float(payload.get("setSpeedKph", 0.0))
  if set_speed > 0.0:
    setattr(args, "_last_set_speed_kph", set_speed)
  elif payload.get("enabled") or payload.get("active") or payload.get("engaged"):
    last_set_speed = finite_float(getattr(args, "_last_set_speed_kph", 0.0))
    if last_set_speed > 0.0:
      payload["setSpeedKph"] = rounded(last_set_speed)

  left_blinker = hold_bool(args, "left_blinker", bool(payload.get("leftBlinker", False)),
                           now, args.blinker_hold_sec)
  right_blinker = hold_bool(args, "right_blinker", bool(payload.get("rightBlinker", False)),
                            now, args.blinker_hold_sec)
  left_blindspot = hold_bool(args, "left_blindspot", bool(payload.get("leftBlindspot", False)),
                             now, args.blindspot_hold_sec)
  right_blindspot = hold_bool(args, "right_blindspot", bool(payload.get("rightBlindspot", False)),
                              now, args.blindspot_hold_sec)

  payload["leftBlinker"] = left_blinker
  payload["rightBlinker"] = right_blinker
  payload["blinkers"] = blinker_text(left_blinker, right_blinker)
  payload["leftBlindspot"] = left_blindspot
  payload["rightBlindspot"] = right_blindspot
  payload["blindspot"] = blindspot_text(left_blindspot, right_blindspot)
  payload["opAvailable"] = bool(payload.get("opAvailable",
                                            payload.get("engageable") or payload.get("enabled") or payload.get("active")))
  payload["standstill"] = bool(payload.get("standstill", payload.get("cruiseStandstill", False)))
  payload["cruiseStandstill"] = bool(payload.get("cruiseStandstill", payload.get("standstill", False)))
  apply_navdy_e2e_alert(payload, args, now)
  return payload


def reverse_gear_alert_active(selfdrive_state: Any) -> bool:
  alert_type = str(getattr(selfdrive_state, "alertType", "")).split("/", 1)[0]
  return alert_type in ("reverseGear", "silentReverseGear")


def gear_text(car_state: Any, selfdrive_state: Any = None) -> str:
  # The car process may stop publishing a gear sample as soon as reverse takes
  # the system offroad. selfdriveState keeps the structured reverse event alive.
  if reverse_gear_alert_active(selfdrive_state):
    return "reverse"
  return enum_text(getattr(car_state, "gearShifter", "unknown")).lower()


def default_car_state() -> Any:
  return SimpleNamespace(
    cruiseState=SimpleNamespace(standstill=False, speed=0.0, speedCluster=0.0),
    gearShifter="unknown",
    leftBlinker=False,
    rightBlinker=False,
    leftBlindspot=False,
    rightBlindspot=False,
    standstill=False,
    vCruise=0.0,
    vCruiseCluster=0.0,
    vEgo=0.0,
    vEgoCluster=0.0,
  )


def car_state_from_sp(car_state_sp: Any) -> Any:
  return SimpleNamespace(
    cruiseState=SimpleNamespace(
      standstill=bool(getattr(car_state_sp, "navdyCruiseStandstill", False)),
      speed=finite_float(getattr(car_state_sp, "navdyCruiseSpeed", 0.0)),
      speedCluster=finite_float(getattr(car_state_sp, "navdyCruiseSpeedCluster", 0.0)),
    ),
    gearShifter=str(getattr(car_state_sp, "navdyGearShifter", "unknown")),
    leftBlinker=bool(getattr(car_state_sp, "navdyLeftBlinker", False)),
    rightBlinker=bool(getattr(car_state_sp, "navdyRightBlinker", False)),
    leftBlindspot=bool(getattr(car_state_sp, "navdyLeftBlindspot", False)),
    rightBlindspot=bool(getattr(car_state_sp, "navdyRightBlindspot", False)),
    standstill=bool(getattr(car_state_sp, "navdyStandstill", False)),
    vCruise=finite_float(getattr(car_state_sp, "navdyVCruise", 0.0)),
    vCruiseCluster=finite_float(getattr(car_state_sp, "navdyVCruiseCluster", 0.0)),
    vEgo=finite_float(getattr(car_state_sp, "navdyVEgo", 0.0)),
    vEgoCluster=finite_float(getattr(car_state_sp, "navdyVEgoCluster", 0.0)),
  )


def is_cruise_standstill(car_state: Any) -> bool:
  return bool(getattr(getattr(car_state, "cruiseState", None), "standstill", False))


def planner_speed_to_kph(value: Any) -> float:
  speed = finite_float(value, 0.0)
  return speed * KPH_PER_MS if 0.0 < speed < 80.0 else 0.0


def set_speed_kph(car_state: Any, controls_state: Any = None,
                  starpilot_plan: Any = None, longitudinal_plan: Any = None) -> float:
  for holder, names in (
      (car_state, ("vCruiseCluster", "vCruise")),
      (controls_state, ("vCruiseClusterDEPRECATED", "vCruiseDEPRECATED")),
  ):
    for name in names:
      speed = finite_float(getattr(holder, name, 0.0))
      if 0.0 < speed < 255.0:
        return speed

  cruise_state = getattr(car_state, "cruiseState", None)
  for name in ("speedCluster", "speed"):
    speed_ms = finite_float(getattr(cruise_state, name, 0.0))
    if speed_ms > 0.0:
      return speed_ms * KPH_PER_MS

  for holder, name in ((starpilot_plan, "vCruise"), (longitudinal_plan, "vCruiseDEPRECATED")):
    speed = planner_speed_to_kph(getattr(holder, name, 0.0))
    if speed > 0.0:
      return speed

  return 0.0


def navdy_model_line(x_values: Any, y_values: Any, lateral_offset: float = 0.0) -> list[float]:
  points = []
  x_values = x_values if x_values is not None else []
  y_values = y_values if y_values is not None else []
  for x_raw, y_raw in zip(x_values, y_values):
    x = finite_float(x_raw, -1.0)
    y = finite_float(y_raw, 0.0) + lateral_offset
    if 0.0 <= x <= 80.0:
      points.append((x, y))

  if len(points) > 10:
    last = len(points) - 1
    points = [points[round(i * last / 9)] for i in range(10)]

  projected = []
  for x, y in points:
    projected.extend(navdy_project_point(x, y))
  return projected


def navdy_project_point(x_value: Any, y_value: Any) -> list[float]:
  x = finite_float(x_value, -1.0)
  y = finite_float(y_value, 0.0)
  if not 0.0 <= x <= NAVDY_VEHICLE_MAX_DISTANCE_M:
    return []
  distance = min(x / NAVDY_VEHICLE_MAX_DISTANCE_M, 1.0) ** 0.65
  lateral_scale = 44.0 * (1.0 - distance) + 8.0 * distance
  return [
    rounded(160.0 + y * lateral_scale),
    rounded(96.0 - 88.0 * distance),
  ]


def model_line_y_at(line: Any, distance_m: float) -> float | None:
  x_values = list(getattr(line, "x", []))
  y_values = list(getattr(line, "y", []))
  points = [(finite_float(x, -1.0), finite_float(y, 0.0)) for x, y in zip(x_values, y_values)]
  points = [(x, y) for x, y in points if x >= 0.0]
  if len(points) < 2 or distance_m < points[0][0] or distance_m > points[-1][0]:
    return None
  for (x0, y0), (x1, y1) in zip(points, points[1:]):
    if x0 <= distance_m <= x1:
      if x1 <= x0:
        return y1
      ratio = (distance_m - x0) / (x1 - x0)
      return y0 + (y1 - y0) * ratio
  return None


def navdy_path_lane_for_model_point(model_v2: Any, distance_m: float, model_y: float,
                                    left: float | None = None, right: float | None = None) -> str:
  path_y = model_line_y_at(getattr(model_v2, "position", None), distance_m)
  if path_y is None:
    return ""

  lane_width = NAVDY_FALLBACK_LANE_WIDTH_M
  if left is not None and right is not None:
    measured_width = right - left
    if NAVDY_MIN_LANE_WIDTH_M <= measured_width <= NAVDY_MAX_LANE_WIDTH_M:
      lane_width = measured_width

  offset = model_y - path_y
  if -0.5 * lane_width <= offset <= 0.5 * lane_width:
    return "center"
  if -1.5 * lane_width <= offset < -0.5 * lane_width:
    return "left"
  if 0.5 * lane_width < offset <= 1.5 * lane_width:
    return "right"
  return ""


def navdy_lane_for_model_point(model_v2: Any, distance_m: float, model_y: float) -> str:
  lane_lines = list(getattr(model_v2, "laneLines", []))
  lane_probs = list(getattr(model_v2, "laneLineProbs", []))
  if len(lane_lines) < 3:
    return navdy_path_lane_for_model_point(model_v2, distance_m, model_y)

  def probability(index: int) -> float:
    return finite_float(lane_probs[index], 0.0) if index < len(lane_probs) else 0.0

  left = model_line_y_at(lane_lines[1], distance_m)
  right = model_line_y_at(lane_lines[2], distance_m)
  if left is None or right is None or left >= right:
    return navdy_path_lane_for_model_point(model_v2, distance_m, model_y)
  inner_confidence = min(probability(1), probability(2))
  if left <= model_y <= right and inner_confidence >= 0.3:
    return "center"

  if len(lane_lines) < 4:
    return navdy_path_lane_for_model_point(model_v2, distance_m, model_y, left, right)
  far_left = model_line_y_at(lane_lines[0], distance_m)
  far_right = model_line_y_at(lane_lines[3], distance_m)
  left_confidence = min(probability(0), probability(1))
  right_confidence = min(probability(2), probability(3))
  if far_left is not None and far_left <= model_y < left and left_confidence >= 0.2:
    return "left"
  if far_right is not None and right < model_y <= far_right and right_confidence >= 0.2:
    return "right"
  if inner_confidence >= 0.3:
    if model_y < left and far_left is not None and left_confidence >= 0.2:
      return ""
    if model_y > right and far_right is not None and right_confidence >= 0.2:
      return ""
  return navdy_path_lane_for_model_point(model_v2, distance_m, model_y, left, right)


def navdy_lane_center_y_at(model_v2: Any, lane: str, distance_m: float) -> float | None:
  lane_lines = list(getattr(model_v2, "laneLines", []))
  lane_probs = list(getattr(model_v2, "laneLineProbs", []))
  path_y = model_line_y_at(getattr(model_v2, "position", None), distance_m)

  def probability(index: int) -> float:
    return finite_float(lane_probs[index], 0.0) if index < len(lane_probs) else 0.0

  def lane_midpoint(first: int, second: int, min_probability: float) -> float | None:
    if len(lane_lines) <= max(first, second):
      return None
    if min(probability(first), probability(second)) < min_probability:
      return None
    first_y = model_line_y_at(lane_lines[first], distance_m)
    second_y = model_line_y_at(lane_lines[second], distance_m)
    if first_y is None or second_y is None:
      return None
    return 0.5 * (first_y + second_y)

  if lane == "center":
    if path_y is not None:
      return path_y
    return lane_midpoint(1, 2, 0.3)

  if lane == "left":
    lane_y = lane_midpoint(0, 1, 0.2)
    lateral_sign = -1.0
  elif lane == "right":
    lane_y = lane_midpoint(2, 3, 0.2)
    lateral_sign = 1.0
  else:
    return None
  if lane_y is not None:
    return lane_y
  if path_y is None:
    return None

  lane_width = NAVDY_FALLBACK_LANE_WIDTH_M
  if len(lane_lines) >= 3:
    left = model_line_y_at(lane_lines[1], distance_m)
    right = model_line_y_at(lane_lines[2], distance_m)
    if left is not None and right is not None:
      measured_width = right - left
      if NAVDY_MIN_LANE_WIDTH_M <= measured_width <= NAVDY_MAX_LANE_WIDTH_M:
        lane_width = measured_width
  return path_y + lateral_sign * lane_width


def navdy_vehicle_perspective_yaw_deg(lane: str, screen_x: float) -> float:
  offset = abs(finite_float(screen_x, 160.0) - 160.0)
  if offset < 24.0:
    angle = 0.0
  elif offset < 48.0:
    angle = 8.0
  elif offset < 72.0:
    angle = 12.0
  elif offset < 104.0:
    angle = 16.0
  else:
    angle = 24.0
  if lane == "left":
    return -angle
  if lane == "right":
    return angle
  return 0.0


def navdy_vehicle_yaw_deg(model_v2: Any, lane: str, distance_m: float, screen_x: float) -> float:
  yaw_deg = navdy_vehicle_perspective_yaw_deg(lane, screen_x)
  near_distance = max(0.0, distance_m - NAVDY_VEHICLE_YAW_SAMPLE_M)
  far_distance = min(NAVDY_VEHICLE_MAX_DISTANCE_M, distance_m + NAVDY_VEHICLE_YAW_SAMPLE_M)
  if far_distance - near_distance < 1.0:
    return rounded(yaw_deg)

  near_y = navdy_lane_center_y_at(model_v2, lane, near_distance)
  far_y = navdy_lane_center_y_at(model_v2, lane, far_distance)
  if near_y is None or far_y is None:
    return rounded(yaw_deg)

  # modelV2 y grows to vehicle-right. The HUD sprite yaw sign is the inverse.
  lane_heading_deg = math.degrees(math.atan2(far_y - near_y, far_distance - near_distance))
  yaw_deg -= lane_heading_deg
  return rounded(max(-NAVDY_VEHICLE_MAX_YAW_DEG, min(NAVDY_VEHICLE_MAX_YAW_DEG, yaw_deg)))


def navdy_vehicle_marker_rect(vehicle: dict[str, Any]) -> tuple[float, float, float, float] | None:
  distance_m = max(0.0, min(NAVDY_VEHICLE_MAX_DISTANCE_M,
                            finite_float(vehicle.get("distanceM", 0.0))))
  screen = navdy_project_point(distance_m, vehicle.get("modelY", 0.0))
  if len(screen) != 2:
    return None
  near_scale = 1.0 - distance_m / NAVDY_VEHICLE_MAX_DISTANCE_M
  width = NAVDY_VEHICLE_FAR_WIDTH_PX + near_scale * (
    NAVDY_VEHICLE_NEAR_WIDTH_PX - NAVDY_VEHICLE_FAR_WIDTH_PX)
  height = width * 1.55
  return (
    screen[0] - width * 0.82,
    screen[1] - height * 0.55,
    screen[0] + width * 0.82,
    screen[1] + height * 0.45,
  )


def navdy_vehicle_overlap_iou(first: dict[str, Any], second: dict[str, Any]) -> float:
  if first.get("lane") != second.get("lane"):
    return 0.0
  first_rect = navdy_vehicle_marker_rect(first)
  second_rect = navdy_vehicle_marker_rect(second)
  if first_rect is None or second_rect is None:
    return 0.0

  left = max(first_rect[0], second_rect[0])
  top = max(first_rect[1], second_rect[1])
  right = min(first_rect[2], second_rect[2])
  bottom = min(first_rect[3], second_rect[3])
  if right <= left or bottom <= top:
    return 0.0
  intersection = (right - left) * (bottom - top)
  first_area = (first_rect[2] - first_rect[0]) * (first_rect[3] - first_rect[1])
  second_area = (second_rect[2] - second_rect[0]) * (second_rect[3] - second_rect[1])
  return intersection / max(first_area + second_area - intersection, 1.0)


def navdy_radar_track_width_m(point: dict[str, Any]) -> float:
  return max(0.0, min(
    NAVDY_RADAR_MAX_TRACK_WIDTH_M, finite_float(point.get("widthM", 0.0), 0.0)))


def navdy_radar_center_model_y(point: dict[str, Any]) -> float:
  radar_y = finite_float(point.get("yRel", 0.0), 0.0)
  width_m = navdy_radar_track_width_m(point)
  return -radar_y - 0.5 * width_m


def navdy_camera_leads(model_v2: Any) -> list[dict[str, Any]]:
  leads = list(getattr(model_v2, "leadsV3", []))
  velocity = getattr(model_v2, "velocity", None)
  model_v_ego = finite_float(next(iter(getattr(velocity, "x", [])), 0.0), 0.0)
  candidates = []
  for index, lead in enumerate(leads[:2]):
    probability = finite_float(getattr(lead, "prob", 0.0), 0.0)
    x_values = list(getattr(lead, "x", []))
    y_values = list(getattr(lead, "y", []))
    if probability < 0.5 or not x_values or not y_values:
      continue
    distance_m = finite_float(x_values[0], 0.0) - NAVDY_RADAR_TO_CAMERA_M
    model_y = finite_float(y_values[0], 0.0)
    if not 2.0 <= distance_m <= NAVDY_VEHICLE_MAX_DISTANCE_M:
      continue
    lane = navdy_lane_for_model_point(model_v2, distance_m, model_y)
    if not lane:
      continue
    v_values = list(getattr(lead, "v", []))
    y_stds = list(getattr(lead, "yStd", []))
    candidates.append({
      "trackId": -100 - index,
      "distanceM": distance_m,
      "modelY": model_y,
      "relativeSpeedMps": finite_float(v_values[0], model_v_ego) - model_v_ego if v_values else 0.0,
      "lane": lane,
      "source": "vision",
      "confidence": probability,
      "yStd": finite_float(y_stds[0], 1.0) if y_stds else 1.0,
    })
  return candidates


def navdy_vehicle_geometry(model_v2: Any, radar_points: list[dict[str, Any]]) -> dict[str, Any]:
  if model_v2 is None:
    return {"navVehicles": []}

  vehicles = []
  for point in radar_points:
    distance_m = finite_float(point.get("dRel", 0.0), 0.0)
    radar_y = finite_float(point.get("yRel", 0.0), 0.0)
    if not 2.0 <= distance_m <= NAVDY_VEHICLE_MAX_DISTANCE_M:
      continue
    # GM radar yRel is positive left; modelV2 y is positive right.
    raw_model_y = -radar_y
    width_m = navdy_radar_track_width_m(point)
    center_model_y = navdy_radar_center_model_y(point)
    raw_lane = navdy_lane_for_model_point(model_v2, distance_m, raw_model_y)
    center_lane = navdy_lane_for_model_point(model_v2, distance_m, center_model_y)
    width_center_applied = center_lane == "left"
    model_y = center_model_y if width_center_applied else raw_model_y
    lane = center_lane if width_center_applied else raw_lane
    if not lane:
      continue
    vehicles.append({
      "trackId": int(point.get("trackId", -1)),
      "distanceM": distance_m,
      "modelY": model_y,
      "rawModelY": raw_model_y,
      "widthM": width_m,
      "widthCenterApplied": width_center_applied,
      "relativeSpeedMps": finite_float(point.get("vRel", 0.0), 0.0),
      "lane": lane,
      "source": "radar",
      "confidence": 0.65,
    })

  used_radar = set()
  unmatched_vision = []
  for vision in sorted(navdy_camera_leads(model_v2), key=lambda item: item["confidence"], reverse=True):
    best_index = -1
    best_key = (2, float("inf"))
    distance_tolerance = max(5.0, vision["distanceM"] * 0.25)
    lateral_tolerance = max(1.5, vision["yStd"] * 2.0)
    for index, radar in enumerate(vehicles):
      if index in used_radar:
        continue
      distance_delta = abs(radar["distanceM"] - vision["distanceM"])
      lateral_delta = abs(radar["modelY"] - vision["modelY"])
      coordinate_match = distance_delta <= distance_tolerance and lateral_delta <= lateral_tolerance
      overlap_iou = navdy_vehicle_overlap_iou(radar, vision)
      if not coordinate_match and overlap_iou < NAVDY_VEHICLE_DUPLICATE_IOU:
        continue
      match_key = (
        (0, distance_delta / distance_tolerance + lateral_delta / lateral_tolerance)
        if coordinate_match else (1, -overlap_iou)
      )
      if match_key < best_key:
        best_index = index
        best_key = match_key
    if best_index >= 0:
      used_radar.add(best_index)
      vehicles[best_index]["source"] = "fused"
      vehicles[best_index]["confidence"] = rounded(max(0.75, vision["confidence"]), 2)
      vehicles[best_index]["modelY"] = vision["modelY"]
      continue

    overlapping_radar = max(
      ((navdy_vehicle_overlap_iou(radar, vision), index) for index, radar in enumerate(vehicles)),
      default=(0.0, -1),
    )
    if overlapping_radar[0] >= NAVDY_VEHICLE_DUPLICATE_IOU:
      index = overlapping_radar[1]
      used_radar.add(index)
      vehicles[index]["source"] = "fused"
      vehicles[index]["confidence"] = rounded(max(0.75, vision["confidence"]), 2)
      vehicles[index]["modelY"] = vision["modelY"]
    elif not any(navdy_vehicle_overlap_iou(other, vision) >= NAVDY_VEHICLE_DUPLICATE_IOU
                 for other in unmatched_vision):
      unmatched_vision.append(vision)

  vehicles.extend(unmatched_vision)
  priority = {"fused": 0, "vision": 1, "radar": 2}
  selected = sorted(vehicles, key=lambda item: (priority[item["source"]], item["distanceM"]))[:NAVDY_VEHICLE_MAX_COUNT]
  output = []
  for vehicle in sorted(selected, key=lambda item: item["distanceM"], reverse=True):
    screen = navdy_project_point(vehicle["distanceM"], vehicle["modelY"])
    if len(screen) != 2:
      continue
    output.append({
      "trackId": vehicle["trackId"],
      "screenX": rounded(max(4.0, min(316.0, screen[0]))),
      "screenY": screen[1],
      "yawDeg": navdy_vehicle_yaw_deg(model_v2, vehicle["lane"], vehicle["distanceM"], screen[0]),
      "distanceM": rounded(vehicle["distanceM"]),
      "relativeSpeedMps": rounded(vehicle["relativeSpeedMps"]),
      "lateralM": rounded(vehicle["modelY"], 2),
      "rawRadarLateralM": rounded(vehicle.get("rawModelY", vehicle["modelY"]), 2),
      "widthM": rounded(vehicle.get("widthM", 0.0), 2),
      "widthCenterApplied": bool(vehicle.get("widthCenterApplied", False)),
      "lane": vehicle["lane"],
      "source": vehicle["source"],
      "confidence": rounded(vehicle["confidence"], 2),
    })
  return {"navVehicles": output}


def navdy_model_geometry(model_v2: Any) -> dict[str, Any]:
  if model_v2 is None:
    return {}

  position = getattr(model_v2, "position", None)
  lane_lines = list(getattr(model_v2, "laneLines", []))
  road_edges = list(getattr(model_v2, "roadEdges", []))
  if position is None or len(lane_lines) < 3:
    return {}

  path_x = getattr(position, "x", [])
  path_y = getattr(position, "y", [])
  lane_left = lane_lines[1]
  lane_right = lane_lines[2]
  geometry = {
    "navPathLeft": navdy_model_line(path_x, path_y, -1.0),
    "navPathRight": navdy_model_line(path_x, path_y, 1.0),
    "navLaneLeft": navdy_model_line(getattr(lane_left, "x", []), getattr(lane_left, "y", [])),
    "navLaneRight": navdy_model_line(getattr(lane_right, "x", []), getattr(lane_right, "y", [])),
  }
  if not all(len(points) >= 4 for points in geometry.values()):
    return {}

  lane_probs = list(getattr(model_v2, "laneLineProbs", []))
  if len(lane_lines) >= 4:
    geometry["navLaneFarLeft"] = navdy_model_line(
      getattr(lane_lines[0], "x", []), getattr(lane_lines[0], "y", []))
    geometry["navLaneFarRight"] = navdy_model_line(
      getattr(lane_lines[3], "x", []), getattr(lane_lines[3], "y", []))

  geometry["navLaneFarLeftProb"] = rounded(lane_probs[0] if len(lane_probs) > 0 else 0.0, 2)
  geometry["navLaneLeftProb"] = rounded(lane_probs[1] if len(lane_probs) > 1 else 0.0, 2)
  geometry["navLaneRightProb"] = rounded(lane_probs[2] if len(lane_probs) > 2 else 0.0, 2)
  geometry["navLaneFarRightProb"] = rounded(lane_probs[3] if len(lane_probs) > 3 else 0.0, 2)

  road_edge_stds = list(getattr(model_v2, "roadEdgeStds", []))
  for index, side in enumerate(("Left", "Right")):
    if index >= len(road_edges) or index >= len(road_edge_stds):
      continue
    confidence = max(0.0, min(1.0, 1.0 - finite_float(road_edge_stds[index], 1.0)))
    if confidence < 0.5:
      continue
    points = navdy_model_line(getattr(road_edges[index], "x", []), getattr(road_edges[index], "y", []))
    if len(points) >= 4:
      geometry[f"navRoadEdge{side}"] = points
      geometry[f"navRoadEdge{side}Prob"] = rounded(confidence, 2)
  return geometry


class NavdyRadarReader:
  def __init__(self, messaging: Any, car_fingerprint: str):
    from opendbc.car import structs
    from opendbc.car.gm.radar_interface import RadarInterface
    from openpilot.common.swaglog import cloudlog
    from openpilot.selfdrive.pandad import can_capnp_to_list

    cp = structs.CarParams(carFingerprint=car_fingerprint, radarUnavailable=False)
    self._radar_interface = RadarInterface(cp, structs.CarParamsSP())
    self._can_capnp_to_list = can_capnp_to_list
    self._cloudlog = cloudlog
    self._messaging = messaging
    self._can_sock = messaging.sub_sock("can", conflate=False, timeout=100)
    self._lock = threading.Lock()
    self._active = False
    self._tracks: dict[int, dict[str, Any]] = {}
    self._last_error = ""
    self._thread = threading.Thread(target=self._run, name="navdy_radar_reader", daemon=True)
    self._thread.start()

  def set_active(self, active: bool) -> None:
    with self._lock:
      if self._active == active:
        return
      self._active = active
      self._tracks.clear()

  def is_alive(self) -> bool:
    return self._thread.is_alive()

  def snapshot(self, now: float | None = None) -> list[dict[str, Any]]:
    now = time.monotonic() if now is None else now
    with self._lock:
      if not self._active:
        return []
      return [
        {
          "trackId": track_id,
          "dRel": track["dRel"],
          "yRel": track["yRel"],
          "vRel": track["vRel"],
          "widthM": track["widthM"],
        }
        for track_id, track in self._tracks.items()
        if track["samples"] >= 2 and now - track["updatedAt"] <= NAVDY_RADAR_STALE_SEC
      ]

  def _radar_update(self, can_strings: list[bytes]) -> Any:
    return self._radar_interface.update(self._can_capnp_to_list(can_strings))

  def _radar_track_widths(self) -> dict[int, float]:
    parser = getattr(self._radar_interface, "rcp", None)
    widths = {}
    for values in getattr(parser, "vl", {}).values():
      if "TrkObjectID" not in values or "TrkWidth" not in values:
        continue
      track_id = int(values["TrkObjectID"])
      width_m = navdy_radar_track_width_m({"widthM": values["TrkWidth"]})
      if width_m > 0.0:
        widths[track_id] = width_m
    return widths

  def _run(self) -> None:
    while True:
      try:
        can_strings = self._messaging.drain_sock_raw(self._can_sock, wait_for_one=True)
        with self._lock:
          active = self._active
        if not active or not can_strings:
          continue
        radar_data = self._radar_update(can_strings)
        if radar_data is None:
          continue
        errors = getattr(radar_data, "errors", None)
        if errors is not None and (bool(getattr(errors, "canError", False)) or
                                   bool(getattr(errors, "radarFault", False))):
          with self._lock:
            self._tracks.clear()
          continue
        self._update_tracks(
          list(getattr(radar_data, "points", [])), self._radar_track_widths())
        with self._lock:
          self._last_error = ""
      except Exception as error:
        error_text = str(error)
        with self._lock:
          self._tracks.clear()
          should_log = error_text != self._last_error
          self._last_error = error_text
        if should_log:
          self._cloudlog.exception(f"navdy radar reader failed: {error_text}")
        time.sleep(0.1)

  def _update_tracks(self, points: list[Any], widths: dict[int, float] | None = None) -> None:
    now = time.monotonic()
    widths = widths or {}
    with self._lock:
      for point in points:
        track_id = int(getattr(point, "trackId", -1))
        distance_m = finite_float(getattr(point, "dRel", 0.0), 0.0)
        lateral_m = finite_float(getattr(point, "yRel", 0.0), 0.0)
        relative_speed = finite_float(getattr(point, "vRel", 0.0), 0.0)
        width_m = navdy_radar_track_width_m({"widthM": widths.get(track_id, 0.0)})
        if track_id < 0 or not 0.0 < distance_m < 255.875:
          continue

        previous = self._tracks.get(track_id)
        jump_limit = max(8.0, distance_m * 0.35)
        if previous is None or abs(previous["dRel"] - distance_m) > jump_limit:
          self._tracks[track_id] = {
            "dRel": distance_m,
            "yRel": lateral_m,
            "vRel": relative_speed,
            "widthM": width_m,
            "samples": 1,
            "updatedAt": now,
          }
          continue

        alpha = 0.55
        previous["dRel"] += alpha * (distance_m - previous["dRel"])
        previous["yRel"] += alpha * (lateral_m - previous["yRel"])
        previous["vRel"] += alpha * (relative_speed - previous["vRel"])
        if width_m > 0.0:
          previous["widthM"] += alpha * (width_m - previous["widthM"])
        previous["samples"] += 1
        previous["updatedAt"] = now

      for track_id in list(self._tracks):
        if now - self._tracks[track_id]["updatedAt"] > NAVDY_RADAR_STALE_SEC:
          del self._tracks[track_id]


def navdy_car_params_bytes(params: Any) -> bytes | None:
  return params.get("CarParams") or params.get("CarParamsPersistent")


def create_navdy_radar_reader(messaging: Any, stdout: bool = False) -> NavdyRadarReader | None:
  try:
    from cereal import car
    from openpilot.common.params import Params
    from opendbc.car.gm.values import DBC

    car_params_raw = navdy_car_params_bytes(Params())
    if not car_params_raw:
      return None
    car_params = messaging.log_from_bytes(car_params_raw, car.CarParams)
    car_fingerprint = str(getattr(car_params, "carFingerprint", ""))
    if car_fingerprint not in DBC:
      return None
    return NavdyRadarReader(messaging, car_fingerprint)
  except Exception as error:
    if stdout:
      print(f"navdy radar reader unavailable: {error}", flush=True)
    return None


def payload_from_messages(selfdrive_state: Any, car_state: Any, seq: int,
                          controls_state: Any = None, starpilot_plan: Any = None,
                          longitudinal_plan: Any = None, model_v2: Any = None,
                          longitudinal_plan_sp: Any = None,
                          selfdrive_state_sp: Any = None) -> dict[str, Any]:
  left_blinker = bool(getattr(car_state, "leftBlinker", False))
  right_blinker = bool(getattr(car_state, "rightBlinker", False))
  left_blindspot = bool(getattr(car_state, "leftBlindspot", False))
  right_blindspot = bool(getattr(car_state, "rightBlindspot", False))
  enabled = bool(getattr(selfdrive_state, "enabled", False))
  active = bool(getattr(selfdrive_state, "active", False))
  engageable = bool(getattr(selfdrive_state, "engageable", False))
  state = enum_text(getattr(selfdrive_state, "state", "unknown"))
  cruise_standstill = is_cruise_standstill(car_state)
  vehicle_standstill = bool(getattr(car_state, "standstill", False) or cruise_standstill)
  # preEnabled is the stopped engagement-wait state. Otherwise show the stop
  # icon only while openpilot is engaged and the vehicle is stationary.
  show_stop_icon = state == "preEnabled" or ((enabled or active) and vehicle_standstill)

  v_ego_cluster = finite_float(getattr(car_state, "vEgoCluster", 0.0))
  v_ego_ms = finite_float(getattr(car_state, "vEgo", 0.0))
  v_ego_kph = (v_ego_cluster if v_ego_cluster > 0.0 else v_ego_ms) * KPH_PER_MS
  alert_text_1 = str(getattr(selfdrive_state, "alertText1", ""))
  alert_text_2 = str(getattr(selfdrive_state, "alertText2", ""))
  alert_type = str(getattr(selfdrive_state, "alertType", ""))
  alert_status = enum_text(getattr(selfdrive_state, "alertStatus", "normal"))
  alert_size = enum_text(getattr(selfdrive_state, "alertSize", "none"))
  if alert_type.split("/", 1)[0] == "resumeRequired":
    alert_text_1 = ""
    alert_text_2 = ""
    alert_type = ""
    alert_status = "normal"
    alert_size = "none"
  e2e_alerts = getattr(longitudinal_plan_sp, "e2eAlerts", None)
  green_light_alert = bool(getattr(e2e_alerts, "greenLightAlert", False))
  lead_depart_alert = bool(getattr(e2e_alerts, "leadDepartAlert", False))
  icbm = getattr(selfdrive_state_sp, "intelligentCruiseButtonManagement", None)
  automatic_acc_active = bool(getattr(icbm, "automaticControlActive", False))
  automatic_acc_target_kph = finite_float(getattr(icbm, "automaticTargetSpeedKph", 0.0))
  physical_acc_speed = finite_float(getattr(getattr(car_state, "cruiseState", None), "speedCluster", 0.0))
  physical_acc_speed_kph = physical_acc_speed * KPH_PER_MS if physical_acc_speed > 0.0 else 0.0
  automatic_acc_at_target = (
    automatic_acc_active and physical_acc_speed_kph > 0.0 and automatic_acc_target_kph > 0.0 and
    round(physical_acc_speed_kph) == round(automatic_acc_target_kph)
  )

  payload = {
    "schema": "navdy.openpilot.v1",
    "seq": seq,
    "ts": round(time.time(), 3),
    "state": state,
    "enabled": enabled,
    "active": active,
    "engaged": active,
    "disengaged": not enabled,
    "engageable": engageable,
    "opAvailable": engageable,
    "standstill": show_stop_icon,
    "cruiseStandstill": show_stop_icon,
    "setSpeedKph": rounded(set_speed_kph(car_state, controls_state, starpilot_plan, longitudinal_plan)),
    "actualAccSetKph": rounded(physical_acc_speed_kph) if automatic_acc_active else 0.0,
    "automaticAccTargetKph": rounded(automatic_acc_target_kph) if automatic_acc_active else 0.0,
    "automaticAccActive": automatic_acc_active,
    "automaticAccAtTarget": automatic_acc_at_target,
    "vEgoKph": rounded(v_ego_kph),
    "gear": gear_text(car_state, selfdrive_state),
    "leftBlinker": left_blinker,
    "rightBlinker": right_blinker,
    "blinkers": blinker_text(left_blinker, right_blinker),
    "leftBlindspot": left_blindspot,
    "rightBlindspot": right_blindspot,
    "blindspot": blindspot_text(left_blindspot, right_blindspot),
    "alertText1": alert_text_1,
    "alertText2": alert_text_2,
    "alertType": alert_type,
    "alertStatus": alert_status,
    "alertSize": alert_size,
    "greenLightAlert": green_light_alert,
    "leadDepartAlert": lead_depart_alert,
  }
  if active:
    payload.update(navdy_model_geometry(model_v2))
  return payload


def synthetic_payload(args: argparse.Namespace, seq: int) -> dict[str, Any]:
  left = (seq % 20) < 5
  right = 10 <= (seq % 20) < 15
  if args.synthetic_left_blindspot or args.synthetic_right_blindspot:
    left_blindspot = args.synthetic_left_blindspot
    right_blindspot = args.synthetic_right_blindspot
  else:
    left_blindspot = 5 <= (seq % 24) < 10
    right_blindspot = 15 <= (seq % 24) < 20
  return {
    "schema": "navdy.openpilot.v1",
    "seq": seq,
    "ts": round(time.time(), 3),
    "state": "enabled",
    "enabled": True,
    "active": True,
    "engaged": True,
    "disengaged": False,
    "engageable": True,
    "opAvailable": True,
    "standstill": args.synthetic_standstill,
    "cruiseStandstill": args.synthetic_standstill,
    "setSpeedKph": 100.0,
    "actualAccSetKph": 60.0,
    "automaticAccTargetKph": 70.0,
    "automaticAccActive": True,
    "vEgoKph": 82.0,
    "gear": args.synthetic_gear,
    "leftBlinker": left,
    "rightBlinker": right,
    "blinkers": blinker_text(left, right),
    "leftBlindspot": left_blindspot,
    "rightBlindspot": right_blindspot,
    "blindspot": blindspot_text(left_blindspot, right_blindspot),
    "alertText1": "",
    "alertText2": "",
    "alertType": "",
    "alertStatus": "normal",
    "alertSize": "none",
    "greenLightAlert": False,
    "leadDepartAlert": False,
  }


def send_adb(payload: dict[str, Any], args: argparse.Namespace) -> bool:
  json_payload = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
  shell_cmd = "am broadcast"
  if args.component:
    shell_cmd += " -n " + shlex.quote(args.component)
  shell_cmd += " -a " + shlex.quote(args.action)
  shell_cmd += " --es payload " + shlex.quote(json_payload)
  return run_adb(args, ["shell", shell_cmd]).returncode == 0


def adb_sender_loop(args: argparse.Namespace) -> None:
  cond = getattr(args, "_adb_sender_cond")
  while True:
    with cond:
      while getattr(args, "_adb_sender_pending", None) is None:
        cond.wait()
      payload = getattr(args, "_adb_sender_pending")
      setattr(args, "_adb_sender_pending", None)
    send_adb(payload, args)


def start_adb_sender(args: argparse.Namespace) -> None:
  if not args.adb_path or args.once or args.sync_adb:
    return
  setattr(args, "_adb_sender_pending", None)
  setattr(args, "_adb_sender_cond", threading.Condition())
  thread = threading.Thread(target=adb_sender_loop, args=(args,), daemon=True)
  setattr(args, "_adb_sender_thread", thread)
  thread.start()


def queue_adb(payload: dict[str, Any], args: argparse.Namespace) -> None:
  cond = getattr(args, "_adb_sender_cond", None)
  if cond is None:
    send_adb(payload, args)
    return
  with cond:
    setattr(args, "_adb_sender_pending", dict(payload))
    cond.notify()


def ensure_socket_forward(args: argparse.Namespace) -> None:
  if not args.adb_path:
    return
  run_adb(args, ["forward", f"tcp:{args.socket_port}", f"tcp:{args.device_socket_port}"])
  run_adb(args, ["shell", "am", "startservice", "-n", args.service_component])


def close_socket(args: argparse.Namespace) -> None:
  conn = getattr(args, "_socket_conn", None)
  setattr(args, "_socket_conn", None)
  if conn is not None:
    try:
      conn.close()
    except OSError:
      pass


def connect_socket(args: argparse.Namespace, force: bool = False) -> bool:
  if getattr(args, "_socket_conn", None) is not None:
    return True

  now = time.monotonic()
  last = float(getattr(args, "_last_socket_connect_at", 0.0))
  if not force and now - last < max(args.socket_reconnect_sec, 0.1):
    return False
  setattr(args, "_last_socket_connect_at", now)

  if args.adb_path:
    ensure_socket_forward(args)
  try:
    conn = socket.create_connection((args.socket_host, args.socket_port),
                                    timeout=max(args.socket_timeout_sec, 0.05))
    conn.settimeout(max(args.socket_timeout_sec, 0.05))
  except OSError:
    close_socket(args)
    return False
  setattr(args, "_socket_conn", conn)
  return True


def start_socket_transport(args: argparse.Namespace) -> None:
  if not args.socket_transport:
    return
  if args.once:
    connect_socket(args, force=True)
    return
  setattr(args, "_socket_sender_pending", None)
  setattr(args, "_socket_sender_cond", threading.Condition())
  thread = threading.Thread(target=socket_sender_loop, args=(args,), daemon=True)
  setattr(args, "_socket_sender_thread", thread)
  thread.start()


def socket_send(payload: dict[str, Any], args: argparse.Namespace) -> bool:
  if not args.socket_transport or not connect_socket(args):
    return False
  json_payload = json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n"
  try:
    conn = getattr(args, "_socket_conn")
    conn.sendall(json_payload.encode("utf-8"))
    read_navdy_feedback(conn, args)
    return True
  except OSError:
    close_socket(args)
  return False


def publish_navdy_camera_state(camera_speed_kph: Any, args: argparse.Namespace) -> None:
  try:
    speed = int(camera_speed_kph)
  except (TypeError, ValueError):
    return
  speed = speed if 20 <= speed <= 140 else 0

  previous = getattr(args, "_navdy_camera_speed_kph", None)
  try:
    if previous == speed and os.path.exists(NAVDY_CAMERA_STATE_PATH):
      os.utime(NAVDY_CAMERA_STATE_PATH, None)
      return
    temp_path = NAVDY_CAMERA_STATE_PATH + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as state_file:
      json.dump({"cameraSpeedKph": speed}, state_file, separators=(",", ":"))
    os.replace(temp_path, NAVDY_CAMERA_STATE_PATH)
    setattr(args, "_navdy_camera_speed_kph", speed)
  except OSError:
    pass


def read_navdy_feedback(conn: socket.socket, args: argparse.Namespace) -> None:
  try:
    readable, _, _ = select.select([conn], [], [], 0.01)
    if not readable:
      return
    buffer = getattr(args, "_socket_feedback_buffer", b"") + conn.recv(512)
    lines = buffer.split(b"\n")
    setattr(args, "_socket_feedback_buffer", lines.pop())
    for line in lines:
      if not line:
        continue
      feedback = json.loads(line)
      publish_navdy_camera_state(feedback.get("cameraSpeedKph", 0), args)
  except (OSError, TypeError, ValueError, json.JSONDecodeError):
    return


def socket_sender_loop(args: argparse.Namespace) -> None:
  cond = getattr(args, "_socket_sender_cond")
  while True:
    with cond:
      while getattr(args, "_socket_sender_pending", None) is None:
        cond.wait()
      payload = getattr(args, "_socket_sender_pending")
      setattr(args, "_socket_sender_pending", None)
    connected = connect_socket(args)
    if connected:
      with cond:
        latest = getattr(args, "_socket_sender_pending", None)
        if latest is not None:
          payload = latest
          setattr(args, "_socket_sender_pending", None)
    if (not connected or not socket_send(payload, args)) and args.adb_path and args.adb_fallback:
      queue_adb(payload, args)


def queue_socket(payload: dict[str, Any], args: argparse.Namespace) -> None:
  cond = getattr(args, "_socket_sender_cond", None)
  if cond is None:
    if not socket_send(payload, args) and args.adb_path and args.adb_fallback:
      queue_adb(payload, args)
    return
  with cond:
    setattr(args, "_socket_sender_pending", dict(payload))
    cond.notify()


def adb_base_cmd(args: argparse.Namespace) -> list[str]:
  cmd = [args.adb_path]
  if args.adb_server_port > 0:
    cmd += ["-P", str(args.adb_server_port)]
  if args.adb_serial:
    cmd += ["-s", args.adb_serial]
  return cmd


def recover_adb(args: argparse.Namespace, reason: str, force: bool = False) -> None:
  if not args.adb_path:
    return

  lock = getattr(args, "_adb_recover_lock", None)
  if lock is None:
    lock = threading.Lock()
    args._adb_recover_lock = lock

  with lock:
    now = time.monotonic()
    last = float(getattr(args, "_last_adb_recover_at", 0.0))
    if not force and now - last < max(args.adb_recover_sec, 0.1):
      return
    args._last_adb_recover_at = now

    server_cmd = [args.adb_path]
    if args.adb_server_port > 0:
      server_cmd += ["-P", str(args.adb_server_port)]

    restart_server = False
    try:
      status = subprocess.run(
        server_cmd + ["devices"],
        check=False,
        capture_output=True,
        text=True,
        timeout=max(args.adb_timeout_sec, 0.1),
      )
      device_status = f"{status.stdout}\n{status.stderr}".lower()
      restart_server = status.returncode != 0 or "\toffline" in device_status or "device offline" in device_status
    except subprocess.TimeoutExpired:
      restart_server = True

    try:
      if restart_server:
        subprocess.run(server_cmd + ["kill-server"], check=False, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=max(args.adb_timeout_sec, 0.1))
      subprocess.run(server_cmd + ["start-server"], check=False, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, timeout=max(args.adb_timeout_sec, 0.1))
      if args.adb_wait_device_sec > 0.0:
        subprocess.run(server_cmd + ["wait-for-device"], check=False, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=max(args.adb_wait_device_sec, 0.1))
    except subprocess.TimeoutExpired:
      if args.stdout:
        print(f"adb recover timeout reason={reason}", flush=True)


def run_adb(args: argparse.Namespace, adb_args: list[str], capture: bool = False) -> subprocess.CompletedProcess:
  cmd = adb_base_cmd(args) + adb_args
  stdout = subprocess.PIPE if capture else subprocess.DEVNULL
  stderr = subprocess.PIPE if capture else subprocess.DEVNULL
  try:
    proc = subprocess.run(cmd, check=False, stdout=stdout, stderr=stderr, text=True,
                          timeout=max(args.adb_timeout_sec, 0.1))
  except subprocess.TimeoutExpired:
    recover_adb(args, "timeout")
    return quiet_completed(cmd, 124)
  if proc.returncode != 0:
    recover_adb(args, "returncode")
  return proc


def adb_shell(args: argparse.Namespace, shell_args: list[str], capture: bool = False) -> subprocess.CompletedProcess:
  return run_adb(args, ["shell"] + shell_args, capture=capture)


def set_stay_on_while_plugged_in(args: argparse.Namespace, stay_on: bool) -> None:
  if args.adb_path:
    value = "1" if stay_on else "0"
    adb_shell(args, ["settings", "put", "global", "stay_on_while_plugged_in", value])


def navdy_display_on(args: argparse.Namespace) -> bool | None:
  if not args.adb_path:
    return None
  proc = adb_shell(args, ["dumpsys", "power"], capture=True)
  if proc.returncode != 0:
    return None
  text = proc.stdout or ""
  if DISPLAY_OFF_TEXT in text:
    return False
  if WAKEFULNESS_ASLEEP_TEXT in text or INTERACTIVE_OFF_TEXT in text:
    return False
  if DISPLAY_ON_TEXT in text:
    return True
  if WAKEFULNESS_AWAKE_TEXT in text or INTERACTIVE_ON_TEXT in text:
    return True
  return None


def set_navdy_display(args: argparse.Namespace, should_be_on: bool, reason: str) -> bool:
  if not args.adb_path:
    return False
  current = navdy_display_on(args)
  if current is should_be_on:
    return True
  if current is None:
    recover_adb(args, f"power-{reason}")
    if not should_be_on:
      return False
  keyevent = KEYEVENT_WAKEUP if should_be_on else KEYEVENT_POWER
  set_stay_on_while_plugged_in(args, should_be_on)
  proc = adb_shell(args, ["input", "keyevent", keyevent])
  if args.stdout:
    print(f"navdy display {'on' if should_be_on else 'off'} reason={reason}", flush=True)
  if proc.returncode != 0:
    return False
  time.sleep(0.5 if should_be_on else 2.0)
  verified = navdy_display_on(args)
  return proc.returncode == 0 if verified is None else verified is should_be_on


def emit(payload: dict[str, Any], args: argparse.Namespace) -> None:
  line = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
  if args.stdout:
    print(line, flush=True)
  if args.socket_transport:
    queue_socket(payload, args)
    return
  if args.adb_path and args.adb_fallback:
    queue_adb(payload, args)


def import_messaging():
  for root in (os.getcwd(), "/data/openpilot"):
    if os.path.isdir(os.path.join(root, "cereal")) and root not in sys.path:
      sys.path.insert(0, root)
  try:
    from cereal import messaging  # pylint: disable=import-outside-toplevel
  except Exception as exc:
    raise SystemExit(f"Cannot import cereal.messaging. Run from openpilot root on comma: {exc}") from exc
  return messaging


def maybe_reexec_openpilot_python(args: argparse.Namespace) -> None:
  if args.synthetic:
    return
  venv_python = "/usr/local/venv/bin/python3"
  if os.path.exists(venv_python) and sys.executable != venv_python:
    os.execv(venv_python, [venv_python] + sys.argv)


def payload_signature(payload: dict[str, Any]) -> tuple[Any, ...]:
  return (
    payload.get("state"),
    payload.get("enabled"),
    payload.get("active"),
    payload.get("engaged"),
    payload.get("opAvailable"),
    payload.get("standstill"),
    payload.get("cruiseStandstill"),
    payload.get("setSpeedKph"),
    payload.get("actualAccSetKph"),
    payload.get("automaticAccTargetKph"),
    payload.get("automaticAccActive"),
    payload.get("automaticAccAtTarget"),
    payload.get("vEgoKph"),
    payload.get("gear"),
    payload.get("leftBlinker"),
    payload.get("rightBlinker"),
    payload.get("leftBlindspot"),
    payload.get("rightBlindspot"),
    payload.get("alertText1"),
    payload.get("alertText2"),
    payload.get("alertType"),
    payload.get("alertStatus"),
    payload.get("alertSize"),
    payload.get("greenLightAlert"),
    payload.get("leadDepartAlert"),
    tuple(payload.get("navPathLeft", [])),
    tuple(payload.get("navPathRight", [])),
    tuple(payload.get("navLaneFarLeft", [])),
    tuple(payload.get("navLaneLeft", [])),
    tuple(payload.get("navLaneRight", [])),
    tuple(payload.get("navLaneFarRight", [])),
    payload.get("navLaneFarLeftProb"),
    payload.get("navLaneLeftProb"),
    payload.get("navLaneRightProb"),
    payload.get("navLaneFarRightProb"),
    payload.get("navLaneFarLeftType"),
    payload.get("navLaneLeftType"),
    payload.get("navLaneRightType"),
    payload.get("navLaneFarRightType"),
    payload.get("navLaneRiskLeft"),
    payload.get("navLaneRiskRight"),
    tuple(payload.get("navRoadEdgeLeft", [])),
    tuple(payload.get("navRoadEdgeRight", [])),
    payload.get("navRoadEdgeLeftProb"),
    payload.get("navRoadEdgeRightProb"),
    tuple(
      (
        vehicle.get("trackId"),
        vehicle.get("screenX"),
        vehicle.get("screenY"),
        vehicle.get("yawDeg"),
        vehicle.get("distanceM"),
        vehicle.get("relativeSpeedMps"),
        vehicle.get("lane"),
        vehicle.get("source"),
      )
      for vehicle in payload.get("navVehicles", [])
    ),
  )


def should_emit_payload(payload: dict[str, Any], args: argparse.Namespace, now: float,
                        last_signature: tuple[Any, ...] | None, last_emit_at: float) -> tuple[bool, tuple[Any, ...]]:
  signature = payload_signature(payload)
  if not args.once and last_emit_at > 0.0 and now - last_emit_at < max(args.min_emit_sec, 0.0):
    return False, signature
  return (
    signature != last_signature or
    now - last_emit_at >= max(args.heartbeat_sec, 0.1) or
    args.once
  ), signature


def panda_ignition_started(panda_states: Any) -> bool:
  try:
    return any(bool(getattr(panda_state, "ignitionLine", False) or
                    getattr(panda_state, "ignitionCan", False))
               for panda_state in panda_states)
  except TypeError:
    return False


def service_active(sm: Any, service: str) -> bool:
  try:
    return bool(sm.alive[service] or sm.updated[service])
  except (KeyError, TypeError):
    return False


def openpilot_messages_started(sm: Any) -> bool:
  return any(service_active(sm, service)
             for service in (NAVDY_CAR_STATE_SERVICE, "selfdriveState", "controlsState"))


def onroad_process_started(args: argparse.Namespace, now: float) -> bool:
  last = bool(getattr(args, "_last_onroad_process_started", False))
  last_check = float(getattr(args, "_last_onroad_process_check_at", 0.0))
  if now - last_check < max(args.onroad_process_check_sec, 0.1):
    return last

  setattr(args, "_last_onroad_process_check_at", now)
  try:
    proc = subprocess.run(["ps", "-eo", "cmd"], check=False, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, text=True, timeout=1.0)
  except subprocess.TimeoutExpired:
    return last

  started = False
  if proc.returncode == 0:
    started = any(process_name in line
                  for line in proc.stdout.splitlines()
                  for process_name in ONROAD_PROCESS_NAMES)

  if args.stdout and started != last:
    print(f"onroad process fallback started={started}", flush=True)
  setattr(args, "_last_onroad_process_started", started)
  return started


def power_started(sm: Any, args: argparse.Namespace | None = None, now: float = 0.0) -> bool:
  if bool(getattr(sm["deviceState"], "started", False)) or panda_ignition_started(sm["pandaStates"]):
    return True
  if openpilot_messages_started(sm):
    return True
  return bool(args and onroad_process_started(args, now))


def service_recent(sm: Any, service: str, now: float, max_age: float = 1.0) -> bool:
  return bool(sm.seen[service] and now - sm.recv_time[service] <= max_age)


def live_payload_ready(sm: Any, started: bool, now: float | None = None) -> bool:
  if not started:
    return True
  now = time.monotonic() if now is None else now
  return bool(service_recent(sm, "selfdriveState", now))


def navdy_path_update_due(active: bool, now: float, last_update_at: float,
                          update_sec: float) -> bool:
  return bool(active and (last_update_at <= 0.0 or
                          now - last_update_at >= max(update_sec, 0.1)))


def available_services(messaging: Any, requested: list[str]) -> list[str]:
  service_list = getattr(messaging, "SERVICE_LIST", None)
  if service_list is None:
    return requested
  return [service for service in requested if service in service_list]


def sm_optional(sm: Any, services: list[str], service: str) -> Any:
  return sm[service] if service in services else None


def due_for_power_on_ensure(args: argparse.Namespace, now: float) -> bool:
  last = float(getattr(args, "_last_power_on_ensure_at", 0.0))
  if now - last < max(args.power_on_ensure_sec, 0.1):
    return False
  setattr(args, "_last_power_on_ensure_at", now)
  return True


def due_for_power_off_ensure(args: argparse.Namespace, now: float) -> bool:
  last = float(getattr(args, "_last_power_off_ensure_at", 0.0))
  if now - last < max(args.power_off_ensure_sec, 0.1):
    return False
  setattr(args, "_last_power_off_ensure_at", now)
  return True


def manage_navdy_power(args: argparse.Namespace, started: bool, now: float, offroad_since: float | None,
                       last_target_on: bool | None) -> tuple[float | None, bool | None]:
  if not args.manage_navdy_power:
    return offroad_since, last_target_on

  if started:
    if last_target_on is not True or due_for_power_on_ensure(args, now):
      if set_navdy_display(args, True, "onroad"):
        last_target_on = True
    return None, last_target_on

  if offroad_since is None:
    offroad_since = now
  if now - offroad_since >= max(args.power_off_delay_sec, 0.0):
    ensure_due = due_for_power_off_ensure(args, now)
    if last_target_on is not False or ensure_due:
      if set_navdy_display(args, False, "offroad"):
        last_target_on = False
  return offroad_since, last_target_on


def power_manager_loop(args: argparse.Namespace) -> None:
  cond = getattr(args, "_power_manager_cond")
  offroad_since = None
  last_target_on = None
  while True:
    with cond:
      while getattr(args, "_power_started", None) is None:
        cond.wait()
      started = bool(getattr(args, "_power_started"))
    offroad_since, last_target_on = manage_navdy_power(
        args, started, time.monotonic(), offroad_since, last_target_on)
    with cond:
      cond.wait(timeout=0.5)


def start_power_manager(args: argparse.Namespace) -> None:
  if not args.manage_navdy_power or args.once:
    return
  setattr(args, "_power_started", None)
  setattr(args, "_power_manager_cond", threading.Condition())
  thread = threading.Thread(target=power_manager_loop, args=(args,), daemon=True)
  setattr(args, "_power_manager_thread", thread)
  thread.start()


def update_navdy_power(args: argparse.Namespace, started: bool, now: float) -> None:
  cond = getattr(args, "_power_manager_cond", None)
  if cond is None:
    offroad_since = getattr(args, "_power_offroad_since", None)
    last_target_on = getattr(args, "_power_last_target_on", None)
    offroad_since, last_target_on = manage_navdy_power(
        args, started, now, offroad_since, last_target_on)
    setattr(args, "_power_offroad_since", offroad_since)
    setattr(args, "_power_last_target_on", last_target_on)
    return
  with cond:
    setattr(args, "_power_started", bool(started))
    cond.notify()


def run_live(args: argparse.Namespace) -> None:
  maybe_reexec_openpilot_python(args)
  messaging = import_messaging()
  services = available_services(messaging, list(NAVDY_FAST_SERVICES))
  model_services = available_services(
    messaging, [NAVDY_MODEL_SERVICE, NAVDY_CALIBRATION_SERVICE])
  if args.manage_navdy_power:
    services += available_services(messaging, ["deviceState", "pandaStates"])
  sm = messaging.SubMaster(services)
  model_sm = messaging.SubMaster(model_services) if model_services else None
  lane_intrusion_pm = messaging.PubMaster(["radarLaneIntrusionSP"])
  seq = 0
  period = 1.0 / max(args.hz, 0.1)
  last_signature = None
  last_emit_at = 0.0
  last_path_update_at = 0.0
  radar_reader = create_navdy_radar_reader(messaging, args.stdout) if args.radar_overlay else None
  lane_risk_detector = create_navdy_lane_risk_detector()
  lane_marking_classifier = create_navdy_lane_marking_classifier(args)
  e2e_alert_reader = NavdyE2EAlertReader(messaging) if "longitudinalPlanSP" in services else None
  last_radar_reader_attempt_at = time.monotonic() if radar_reader is not None else 0.0
  once_deadline = time.monotonic() + max(args.once_timeout_sec, 0.1)
  while True:
    time.sleep(period)
    sm.update(0)
    now = time.monotonic()
    has_update = any(sm.updated[service] for service in services)
    started = power_started(sm, args, now) if args.manage_navdy_power else True
    if args.manage_navdy_power:
      update_navdy_power(args, started, now)
    if not has_update and not (args.once and now >= once_deadline):
      continue
    if not live_payload_ready(sm, started, now):
      continue
    if service_recent(sm, NAVDY_CAR_STATE_SERVICE, now):
      car_state = car_state_from_sp(sm[NAVDY_CAR_STATE_SERVICE])
    else:
      car_state = default_car_state()
    active = bool(getattr(sm["selfdriveState"], "active", False))
    if lane_marking_classifier is not None:
      if not lane_marking_classifier.is_alive():
        lane_marking_classifier = None
      else:
        lane_marking_classifier.set_active(active)
        if not active:
          publish_navdy_lane_marking_state({})
    if radar_reader is not None and not radar_reader.is_alive():
      radar_reader = None
    if args.radar_overlay and radar_reader is None and \
       (last_radar_reader_attempt_at <= 0.0 or now - last_radar_reader_attempt_at >= NAVDY_RADAR_RETRY_SEC):
      last_radar_reader_attempt_at = now
      radar_reader = create_navdy_radar_reader(messaging, args.stdout)
    if radar_reader is not None:
      radar_reader.set_active(active)
    path_geometry = {}
    if navdy_path_update_due(active, now, last_path_update_at, args.path_update_sec):
      last_path_update_at = now
      if model_sm is not None:
        model_sm.update(0)
        if service_recent(model_sm, NAVDY_MODEL_SERVICE, now):
          model_v2 = model_sm[NAVDY_MODEL_SERVICE]
          path_geometry = navdy_model_geometry(model_v2)
          if lane_marking_classifier is not None:
            if service_recent(model_sm, NAVDY_CALIBRATION_SERVICE, now):
              lane_marking_classifier.submit(
                model_v2, model_sm[NAVDY_CALIBRATION_SERVICE], now)
            lane_markings = lane_marking_classifier.snapshot(now)
            path_geometry.update(lane_markings)
            publish_navdy_lane_marking_state(lane_markings)
          radar_points = radar_reader.snapshot(now) if radar_reader is not None else []
          path_geometry.update(navdy_vehicle_geometry(model_v2, radar_points))
          lane_risks, intrusion = evaluate_navdy_lane_risk(
            lane_risk_detector, model_v2, radar_points,
            finite_float(getattr(car_state, "vEgo", 0.0)), now)
          path_geometry.update(lane_risks)
          publish_radar_lane_intrusion(messaging, lane_intrusion_pm, intrusion, lane_risks)
    elif not active:
      last_path_update_at = 0.0
      if lane_risk_detector is not None:
        lane_risk_detector.reset()
    path_geometry.update(navdy_lane_risk_values(lane_risk_detector))
    payload = payload_from_messages(sm["selfdriveState"],
                                    car_state,
                                    seq,
                                    sm_optional(sm, services, "controlsState"),
                                    sm_optional(sm, services, "starpilotPlan"),
                                    sm_optional(sm, services, "longitudinalPlan"),
                                    longitudinal_plan_sp=sm_optional(sm, services, "longitudinalPlanSP"),
                                    selfdrive_state_sp=sm_optional(sm, services, "selfdriveStateSP"))
    if e2e_alert_reader is not None:
      captured_green, captured_lead = e2e_alert_reader.pending(
        now, consume=navdy_e2e_alert_allowed(payload))
      payload["greenLightAlert"] = bool(payload["greenLightAlert"] or captured_green)
      payload["leadDepartAlert"] = bool(payload["leadDepartAlert"] or captured_lead)
    payload.update(path_geometry)
    payload = stabilize_display_payload(payload, args, now)
    should_emit, signature = should_emit_payload(payload, args, now, last_signature, last_emit_at)
    if should_emit:
      emit(payload, args)
      last_signature = signature
      last_emit_at = now
      seq += 1
      if args.once:
        return
      continue
    seq += 1


def run_synthetic(args: argparse.Namespace) -> None:
  seq = 0
  period = 1.0 / max(args.hz, 0.1)
  while True:
    now = time.monotonic()
    update_navdy_power(args, args.synthetic_started, now)
    emit(synthetic_payload(args, seq), args)
    seq += 1
    if args.once:
      return
    time.sleep(period)


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--hz", type=float, default=5.0, help="Update rate for bridge output.")
  parser.add_argument("--path-update-sec", type=float, default=1.0,
                      help="Minimum interval between model path samples.")
  parser.add_argument("--radar-overlay", dest="radar_overlay", action="store_true", default=True,
                      help="Fuse passive raw GM radar targets into the Navdy path overlay (default).")
  parser.add_argument("--no-radar-overlay", dest="radar_overlay", action="store_false",
                      help="Disable passive raw radar targets in the Navdy path overlay.")
  parser.add_argument("--lane-marking-classifier", dest="lane_marking_classifier",
                      action="store_true", default=False,
                      help="Classify solid, dashed, and yellow center lane markings for Navdy.")
  parser.add_argument("--no-lane-marking-classifier", dest="lane_marking_classifier",
                      action="store_false", help="Disable Navdy lane-marking classification.")
  parser.add_argument("--lane-marking-interval-sec", type=float, default=0.5,
                      help="Minimum interval between camera lane-marking samples.")
  parser.add_argument("--lane-marking-stale-sec", type=float, default=2.0,
                      help="Age after which a lane-marking result becomes unknown.")
  parser.add_argument("--once", action="store_true", help="Send one payload and exit.")
  parser.add_argument("--synthetic", action="store_true", help="Send fake OP data without cereal imports.")
  parser.add_argument("--synthetic-gear", default="drive", help="Gear text for --synthetic payloads.")
  parser.add_argument("--synthetic-started", action="store_true", help="Synthetic onroad flag for power tests.")
  parser.add_argument("--synthetic-standstill", action="store_true", help="Force standstill true in --synthetic payloads.")
  parser.add_argument("--synthetic-left-blindspot", action="store_true", help="Force left BSM true in --synthetic payloads.")
  parser.add_argument("--synthetic-right-blindspot", action="store_true", help="Force right BSM true in --synthetic payloads.")
  parser.add_argument("--stdout", action="store_true", default=True, help="Print JSON lines.")
  parser.add_argument("--no-stdout", dest="stdout", action="store_false", help="Do not print JSON lines.")
  parser.add_argument("--adb-path", default="", help="Path to adb on comma. Empty disables adb broadcast.")
  parser.add_argument("--adb-server-port", type=int, default=0, help="ADB server port, e.g. 5038 on comma.")
  parser.add_argument("--adb-serial", default="", help="Navdy adb serial if multiple devices appear.")
  parser.add_argument("--adb-timeout-sec", type=float, default=4.0, help="ADB command timeout.")
  parser.add_argument("--adb-recover-sec", type=float, default=5.0, help="Minimum interval between adb recovery attempts.")
  parser.add_argument("--adb-wait-device-sec", type=float, default=1.0, help="Short wait-for-device timeout after adb start-server.")
  parser.add_argument("--sync-adb", action="store_true", help="Send ADB broadcasts on the polling thread.")
  parser.add_argument("--socket-transport", action="store_true", help="Use adb forward + Navdy socket service for low-latency payloads.")
  parser.add_argument("--socket-host", default="127.0.0.1", help="Host address for forwarded Navdy socket.")
  parser.add_argument("--socket-port", type=int, default=DEFAULT_SOCKET_PORT, help="Host TCP port forwarded to Navdy.")
  parser.add_argument("--device-socket-port", type=int, default=DEFAULT_DEVICE_SOCKET_PORT, help="Navdy TCP port for the socket service.")
  parser.add_argument("--service-component", default=DEFAULT_SERVICE_COMPONENT, help="Android service component for socket transport.")
  parser.add_argument("--socket-timeout-sec", type=float, default=0.25, help="Socket connect/write timeout.")
  parser.add_argument("--socket-reconnect-sec", type=float, default=1.0, help="Minimum interval between socket reconnect attempts.")
  parser.add_argument("--no-adb-fallback", dest="adb_fallback", action="store_false", help="Disable broadcast fallback when socket send fails.")
  parser.set_defaults(adb_fallback=True)
  parser.add_argument("--action", default=DEFAULT_ACTION, help="Android broadcast action on Navdy.")
  parser.add_argument("--component", default=DEFAULT_COMPONENT, help="Explicit Android receiver component.")
  parser.add_argument("--heartbeat-sec", type=float, default=3.0, help="Re-send unchanged live state at this interval.")
  parser.add_argument("--min-emit-sec", type=float, default=0.0, help="Minimum interval between live payload sends.")
  parser.add_argument("--once-timeout-sec", type=float, default=3.0, help="For --once, emit cached state after this wait.")
  parser.add_argument("--manage-navdy-power", action="store_true", help="Wake Navdy on onroad and sleep it on offroad.")
  parser.add_argument("--power-off-delay-sec", type=float, default=30.0, help="Offroad duration before Navdy display sleep.")
  parser.add_argument("--power-on-ensure-sec", type=float, default=1.0,
                      help="Re-check Navdy display state at this interval while onroad.")
  parser.add_argument("--power-off-ensure-sec", type=float, default=5.0,
                      help="Re-check Navdy display state at this interval after the offroad delay.")
  parser.add_argument("--onroad-process-check-sec", type=float, default=1.0,
                      help="Minimum interval for onroad process fallback checks.")
  parser.add_argument("--blinker-hold-sec", type=float, default=1.6,
                      help="Keep blinker icon visible after a true sample.")
  parser.add_argument("--blindspot-hold-sec", type=float, default=1.6,
                      help="Keep blindspot icon visible after a true sample.")
  return parser.parse_args()


def main() -> int:
  args = parse_args()
  setattr(args, "_last_adb_recover_at", 0.0)
  args._adb_recover_lock = threading.Lock()
  setattr(args, "_last_power_on_ensure_at", 0.0)
  setattr(args, "_last_power_off_ensure_at", 0.0)
  setattr(args, "_last_onroad_process_check_at", 0.0)
  setattr(args, "_last_onroad_process_started", False)
  setattr(args, "_last_set_speed_kph", 0.0)
  setattr(args, "_last_socket_connect_at", 0.0)
  setattr(args, "_socket_conn", None)
  if args.adb_path:
    recover_adb(args, "startup", force=True)
  if args.adb_path:
    start_adb_sender(args)
  start_socket_transport(args)
  start_power_manager(args)
  if args.synthetic:
    run_synthetic(args)
  else:
    run_live(args)
  return 0


if __name__ == "__main__":
  sys.exit(main())
