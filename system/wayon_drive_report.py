#!/usr/bin/env python3
from __future__ import annotations

import math
from collections import deque
from datetime import datetime, timezone


HARD_ACCEL_MPS2 = 2.0
HARD_BRAKE_MPS2 = -2.5
LOW_SPEED_MPS = 8.33
STOPPED_MPS = 0.15
MOVING_MPS = 0.55
TIMELINE_INTERVAL_S = 5.0


def _enum_name(value):
  name = getattr(value, "name", None)
  return str(name if name is not None else value).rsplit(".", 1)[-1]


def _safe_float(value, default=0.0):
  try:
    result = float(value)
    return result if math.isfinite(result) else default
  except (TypeError, ValueError):
    return default


def _iso_at(route_start, first_mono, mono):
  if route_start is None or first_mono is None:
    return None
  timestamp = route_start.timestamp() + max(0.0, mono - first_mono)
  return datetime.fromtimestamp(timestamp, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _percent(numerator, denominator):
  return round(100.0 * numerator / denominator, 1) if denominator > 0 else None


def _clamp(value, lower, upper):
  return max(lower, min(upper, value))


class DriveReportAccumulator:
  """Builds a compact post-drive report while a route log is read once."""

  def __init__(self, route_start=None):
    self.route_start = route_start
    self.first_mono = None
    self.last_mono = None
    self.last_car_mono = None
    self.last_control_mono = None
    self.last_dm_mono = None
    self.last_speed = 0.0
    self.last_accel = None
    self.last_jerk = 0.0
    self.last_event_mono = {}
    self.recent_car = deque(maxlen=700)

    self.op_active = False
    self.op_enabled = False
    self.latest_car = None
    self.latest_lead = None
    self.lead_present = False
    self.driver_distracted = False
    self.face_detected = False
    self.steering_pressed = False

    self.car_samples = 0
    self.control_samples = 0
    self.dm_samples = 0
    self.radar_samples = 0
    self.op_active_s = 0.0
    self.manual_s = 0.0
    self.long_active_s = 0.0
    self.throttle_command_s = 0.0
    self.brake_command_s = 0.0
    self.distracted_s = 0.0
    self.face_detected_s = 0.0
    self.dm_observed_s = 0.0
    self.steering_override_s = 0.0

    self.stop_count = 0
    self.harsh_stop_count = 0
    self.hard_accel_count = 0
    self.hard_brake_count = 0
    self.low_speed_oscillation_count = 0
    self.steering_intervention_count = 0
    self.disengagement_count = 0
    self.attention_alert_count = 0
    self.system_alert_count = 0
    self.lead_acquisition_count = 0
    self.fcw_count = 0

    self.peak_accel = 0.0
    self.peak_decel = 0.0
    self.peak_jerk = 0.0
    self.peak_command_accel = 0.0
    self.peak_command_decel = 0.0
    self.low_speed_accel_sign = 0
    self.last_low_speed_switch_mono = -1e9
    self.last_timeline_mono = -1e9
    self.last_alert_type = ""
    self.last_attention_level = "none"

    self.timeline = []
    self.moments = []

  def update(self, msg):
    which = msg.which()
    if which not in ("carState", "carControl", "selfdriveState", "driverMonitoringState", "radarState", "longitudinalPlan"):
      return
    mono = _safe_float(msg.logMonoTime) / 1e9
    if self.first_mono is None:
      self.first_mono = mono
    self.last_mono = mono

    if which == "carState":
      self._update_car_state(msg.carState, mono)
    elif which == "carControl":
      self._update_car_control(msg.carControl, mono)
    elif which == "selfdriveState":
      self._update_selfdrive_state(msg.selfdriveState, mono)
    elif which == "driverMonitoringState":
      self._update_driver_monitoring(msg.driverMonitoringState, mono)
    elif which == "radarState":
      self._update_radar(msg.radarState, mono)
    elif which == "longitudinalPlan":
      self._update_longitudinal_plan(msg.longitudinalPlan, mono)

  def _event_allowed(self, event_type, mono, cooldown_s):
    previous = self.last_event_mono.get(event_type, -1e9)
    if mono - previous < cooldown_s:
      return False
    self.last_event_mono[event_type] = mono
    return True

  def _add_moment(self, mono, event_type, severity, title, detail, **extra):
    if len(self.moments) >= 120:
      return
    moment = {
      "time": _iso_at(self.route_start, self.first_mono, mono),
      "offsetS": round(max(0.0, mono - (self.first_mono or mono)), 2),
      "type": event_type,
      "severity": severity,
      "title": title,
      "detail": detail,
    }
    moment.update(extra)
    self.moments.append(moment)

  def _update_car_state(self, car_state, mono):
    speed = max(0.0, _safe_float(getattr(car_state, "vEgo", 0.0)))
    cluster_speed = _safe_float(getattr(car_state, "vEgoCluster", 0.0))
    if cluster_speed > 0.0:
      speed = cluster_speed
    accel = _safe_float(getattr(car_state, "aEgo", 0.0))
    dt = mono - self.last_car_mono if self.last_car_mono is not None else 0.0
    valid_dt = 0.0 < dt <= 0.5

    if valid_dt:
      if self.op_active:
        self.op_active_s += dt
      else:
        self.manual_s += dt
      if self.op_active and bool(getattr(car_state, "steeringPressed", False)):
        self.steering_override_s += dt

    jerk = self.last_jerk
    if valid_dt and self.last_accel is not None and dt >= 0.02:
      jerk = _clamp((accel - self.last_accel) / dt, -20.0, 20.0)
      self.last_jerk = 0.72 * self.last_jerk + 0.28 * jerk
    self.peak_accel = max(self.peak_accel, accel)
    self.peak_decel = min(self.peak_decel, accel)
    self.peak_jerk = max(self.peak_jerk, abs(self.last_jerk))

    if accel >= HARD_ACCEL_MPS2 and self._event_allowed("hard_accel", mono, 4.0):
      self.hard_accel_count += 1
      self._add_moment(mono, "hard_accel", "medium", "강한 가속", f"가속도 {accel:.1f} m/s²", speedKph=round(speed * 3.6, 1))
    if accel <= HARD_BRAKE_MPS2 and self._event_allowed("hard_brake", mono, 4.0):
      self.hard_brake_count += 1
      self._add_moment(mono, "hard_brake", "high", "강한 제동", f"감속도 {accel:.1f} m/s²", speedKph=round(speed * 3.6, 1))

    accel_sign = 1 if accel > 0.35 else -1 if accel < -0.35 else 0
    if 0.7 < speed < LOW_SPEED_MPS and accel_sign and self.low_speed_accel_sign and accel_sign != self.low_speed_accel_sign:
      if mono - self.last_low_speed_switch_mono >= 1.0:
        self.low_speed_oscillation_count += 1
        self.last_low_speed_switch_mono = mono
    if accel_sign:
      self.low_speed_accel_sign = accel_sign
    if speed >= LOW_SPEED_MPS:
      self.low_speed_accel_sign = 0

    self.recent_car.append((mono, speed, accel, self.last_jerk))
    while self.recent_car and mono - self.recent_car[0][0] > 6.0:
      self.recent_car.popleft()

    if self.last_speed >= MOVING_MPS and speed <= STOPPED_MPS:
      self._record_stop(mono)

    steering_now = bool(getattr(car_state, "steeringPressed", False))
    if self.op_active and steering_now and not self.steering_pressed and speed > 1.4:
      self.steering_intervention_count += 1
      self._add_moment(mono, "steering_intervention", "medium", "운전자 조향 개입", "오픈파일럿 주행 중 운전자가 조향에 개입했습니다.", speedKph=round(speed * 3.6, 1))
    self.steering_pressed = steering_now

    self.latest_car = car_state
    self.car_samples += 1
    self.last_speed = speed
    self.last_accel = accel
    self.last_car_mono = mono

    if mono - self.last_timeline_mono >= TIMELINE_INTERVAL_S:
      lead = self.latest_lead
      self.timeline.append({
        "time": _iso_at(self.route_start, self.first_mono, mono),
        "offsetS": round(max(0.0, mono - (self.first_mono or mono)), 1),
        "speedKph": round(speed * 3.6, 1),
        "accelMps2": round(accel, 2),
        "opActive": self.op_active,
        "leadDistanceM": round(_safe_float(getattr(lead, "dRel", None)), 1) if lead is not None else None,
        "leadRelativeSpeedMps": round(_safe_float(getattr(lead, "vRel", None)), 2) if lead is not None else None,
        "distracted": self.driver_distracted,
      })
      self.last_timeline_mono = mono

  def _record_stop(self, mono):
    self.stop_count += 1
    low_speed = [sample for sample in self.recent_car if sample[1] <= 2.0]
    peak_decel = min((sample[2] for sample in low_speed), default=0.0)
    peak_jerk = max((abs(sample[3]) for sample in low_speed), default=0.0)
    harsh = peak_decel < -1.35 or peak_jerk > 4.5
    if harsh:
      self.harsh_stop_count += 1
      self._add_moment(
        mono, "harsh_stop", "high", "정지 직전 충격",
        f"저속 최대 감속 {peak_decel:.1f} m/s² · jerk {peak_jerk:.1f} m/s³",
        speedKph=0.0,
      )

  def _update_car_control(self, car_control, mono):
    dt = mono - self.last_control_mono if self.last_control_mono is not None else 0.0
    if not 0.0 < dt <= 0.5:
      dt = 0.0
    actuators = getattr(car_control, "actuators", None)
    accel = _safe_float(getattr(actuators, "accel", 0.0)) if actuators is not None else 0.0
    if bool(getattr(car_control, "longActive", False)):
      self.long_active_s += dt
      if accel > 0.08:
        self.throttle_command_s += dt
      elif accel < -0.08:
        self.brake_command_s += dt
    self.peak_command_accel = max(self.peak_command_accel, accel)
    self.peak_command_decel = min(self.peak_command_decel, accel)
    self.control_samples += 1
    self.last_control_mono = mono

  def _update_selfdrive_state(self, state, mono):
    active = bool(getattr(state, "active", False))
    enabled = bool(getattr(state, "enabled", False))
    if self.op_active and not active:
      self.disengagement_count += 1
      car = self.latest_car
      brake = bool(getattr(car, "brakePressed", False)) if car is not None else False
      gas = bool(getattr(car, "gasPressed", False)) if car is not None else False
      steering = bool(getattr(car, "steeringPressed", False)) if car is not None else False
      reason = "브레이크" if brake else "가속 페달" if gas else "조향" if steering else "시스템 또는 버튼"
      self._add_moment(mono, "disengagement", "medium", "오픈파일럿 해제", f"해제 추정 원인: {reason}")

    alert = getattr(state, "alertType", "")
    alert_type = str(alert or "")
    alert_status = _enum_name(getattr(state, "alertStatus", "normal")).lower()
    if alert_type and alert_type != self.last_alert_type and alert_status not in ("normal", "none"):
      self.system_alert_count += 1
      text1 = str(getattr(state, "alertText1", "") or "")
      text2 = str(getattr(state, "alertText2", "") or "")
      detail = " · ".join(value for value in (text1, text2) if value) or alert_type
      severity = "high" if alert_status in ("critical", "userprompt") else "medium"
      self._add_moment(mono, "system_alert", severity, "주행 시스템 알림", detail[:180])
    self.last_alert_type = alert_type
    self.op_active = active
    self.op_enabled = enabled

  def _update_driver_monitoring(self, dm, mono):
    dt = mono - self.last_dm_mono if self.last_dm_mono is not None else 0.0
    if 0.0 < dt <= 0.5:
      self.dm_observed_s += dt
      if self.driver_distracted:
        self.distracted_s += dt
      if self.face_detected:
        self.face_detected_s += dt

    vision = getattr(dm, "visionPolicyState", None)
    distracted = bool(getattr(vision, "isDistracted", False)) if vision is not None else False
    face_detected = bool(getattr(vision, "faceDetected", False)) if vision is not None else False
    level = _enum_name(getattr(dm, "alertLevel", "none")).lower()
    if level not in ("none", "0") and level != self.last_attention_level:
      self.attention_alert_count += 1
      severity = "high" if level in ("three", "3") else "medium"
      self._add_moment(mono, "attention", severity, "운전자 주의 경고", "운전자 모니터링 경고가 발생했습니다.")
    self.last_attention_level = level
    self.driver_distracted = distracted
    self.face_detected = face_detected
    self.dm_samples += 1
    self.last_dm_mono = mono

  def _update_radar(self, radar_state, mono):
    lead = getattr(radar_state, "leadOne", None)
    present = bool(getattr(lead, "status", False)) if lead is not None else False
    if present and not self.lead_present:
      self.lead_acquisition_count += 1
      distance = _safe_float(getattr(lead, "dRel", 0.0))
      relative_speed = _safe_float(getattr(lead, "vRel", 0.0))
      if distance < 35.0 and relative_speed < -2.0 and self._event_allowed("close_lead_acquired", mono, 5.0):
        self._add_moment(
          mono, "close_lead_acquired", "high", "가까운 선행차 진입",
          f"거리 {distance:.1f} m · 상대속도 {relative_speed * 3.6:.0f} km/h",
          leadDistanceM=round(distance, 1), relativeSpeedMps=round(relative_speed, 2),
        )
    self.lead_present = present
    self.latest_lead = lead if present else None
    self.radar_samples += 1

  def _update_longitudinal_plan(self, plan, mono):
    if bool(getattr(plan, "fcw", False)) and self._event_allowed("fcw", mono, 8.0):
      self.fcw_count += 1
      self._add_moment(mono, "fcw", "critical", "전방 충돌 경고", "롱컨 전방 충돌 경고가 발생했습니다.")

  def _attach_route_context(self, route):
    timed_points = []
    for point in route:
      try:
        timestamp = datetime.fromisoformat(str(point.get("time", "")).replace("Z", "+00:00")).timestamp()
        timed_points.append((timestamp, point))
      except (TypeError, ValueError):
        continue
    if not timed_points:
      return

    for moment in self.moments:
      if not moment.get("time"):
        continue
      try:
        timestamp = datetime.fromisoformat(moment["time"].replace("Z", "+00:00")).timestamp()
      except ValueError:
        continue
      _, point = min(timed_points, key=lambda item: abs(item[0] - timestamp))
      moment["latitude"] = point.get("latitude")
      moment["longitude"] = point.get("longitude")

  def finalize(self, route):
    self._attach_route_context(route)
    duration_s = max(0.0, (self.last_mono or 0.0) - (self.first_mono or 0.0))
    observed_drive_s = self.op_active_s + self.manual_s
    op_usage = _percent(self.op_active_s, observed_drive_s)
    face_percent = _percent(self.face_detected_s, self.dm_observed_s)
    distracted_percent = _percent(self.distracted_s, self.dm_observed_s)

    comfort_penalty = (
      self.harsh_stop_count * 10.0 + self.hard_brake_count * 6.0 +
      self.hard_accel_count * 4.0 + min(20.0, self.low_speed_oscillation_count * 1.5) +
      max(0.0, self.peak_jerk - 2.5) * 1.2
    )
    comfort_score = round(_clamp(100.0 - comfort_penalty, 0.0, 100.0))
    attention_score = None
    if self.dm_observed_s >= 10.0:
      attention_score = round(_clamp(100.0 - (distracted_percent or 0.0) * 1.2 - self.attention_alert_count * 8.0, 0.0, 100.0))
    stability_score = round(_clamp(100.0 - self.system_alert_count * 8.0 - self.disengagement_count * 2.0, 0.0, 100.0))

    important = sorted(
      self.moments,
      key=lambda item: ({"critical": 3, "high": 2, "medium": 1}.get(item["severity"], 0), item["offsetS"]),
      reverse=True,
    )[:12]
    confidence = "high" if self.car_samples >= 500 and duration_s >= 60 else "medium" if self.car_samples >= 100 else "low"

    return {
      "schemaVersion": "wayon-drive-report-v1",
      "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
      "dataQuality": {
        "confidence": confidence,
        "durationS": round(duration_s, 1),
        "carStateSamples": self.car_samples,
        "controlSamples": self.control_samples,
        "driverMonitoringSamples": self.dm_samples,
        "radarSamples": self.radar_samples,
      },
      "scores": {
        "comfort": comfort_score,
        "attention": attention_score,
        "systemStability": stability_score,
      },
      "automation": {
        "opActiveS": round(self.op_active_s, 1),
        "manualS": round(self.manual_s, 1),
        "opUsagePercent": op_usage,
        "disengagementCount": self.disengagement_count,
        "steeringInterventionCount": self.steering_intervention_count,
      },
      "comfort": {
        "stopCount": self.stop_count,
        "harshStopCount": self.harsh_stop_count,
        "hardAccelerationCount": self.hard_accel_count,
        "hardBrakingCount": self.hard_brake_count,
        "lowSpeedOscillationCount": self.low_speed_oscillation_count,
        "peakAccelerationMps2": round(self.peak_accel, 2),
        "peakDecelerationMps2": round(self.peak_decel, 2),
        "peakJerkMps3": round(self.peak_jerk, 2),
      },
      "longitudinal": {
        "longActiveS": round(self.long_active_s, 1),
        "throttleCommandS": round(self.throttle_command_s, 1),
        "brakeCommandS": round(self.brake_command_s, 1),
        "peakCommandAccelerationMps2": round(self.peak_command_accel, 2),
        "peakCommandDecelerationMps2": round(self.peak_command_decel, 2),
        "leadAcquisitionCount": self.lead_acquisition_count,
        "fcwCount": self.fcw_count,
      },
      "attention": {
        "observedS": round(self.dm_observed_s, 1),
        "faceDetectedPercent": face_percent,
        "distractedS": round(self.distracted_s, 1),
        "distractedPercent": distracted_percent,
        "alertCount": self.attention_alert_count,
      },
      "system": {
        "alertCount": self.system_alert_count,
      },
      "moments": important,
      "timeline": self.timeline[:1200],
    }
