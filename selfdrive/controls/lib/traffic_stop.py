from __future__ import annotations

from collections import deque
from enum import IntEnum

import numpy as np

from openpilot.common.constants import CV
from openpilot.common.realtime import DT_MDL


TRAFFIC_STOP_DISTANCE_RATIO_SPEED_BP_KPH = (0.0, 100.0)
TRAFFIC_STOP_DISTANCE_RATIO = (1.0, 0.7)
TRAFFIC_STOP_DISTANCE_FADE_BP_M = (0.0, 50.0)
TRAFFIC_STOP_ENTRY_STEERING_LIMIT_DEG = 50.0
TRAFFIC_STOP_MAX_ENTRY_SPEED_KPH = 82.0
TRAFFIC_STOP_SOFT_DECEL_MPS2 = 2.2
TRAFFIC_STOP_MAX_DECEL_MPS2 = 4.0
TRAFFIC_STOP_RESPONSE_TIME_S = 0.5
TRAFFIC_STOP_DISTANCE_UNCERTAINTY_M = 5.0
TRAFFIC_STOP_DECEL_SAFETY_BUFFER_MPS2 = 0.2
TRAFFIC_STOP_DISTANCE_STABILITY_SAMPLES = 8
TRAFFIC_STOP_DISTANCE_ADJUST_M = 2.5
TRAFFIC_STOP_CANCEL_COOLDOWN_S = 10.0


class TrafficStopState(IntEnum):
  inactive = 0
  stopping = 1
  stopped = 2


class TrafficSignalState(IntEnum):
  off = 0
  red = 1
  green = 2


class MovingAverage:
  def __init__(self, sample_count: int):
    self._values: deque[float] = deque(maxlen=max(1, int(sample_count)))

  def reset(self) -> None:
    self._values.clear()

  def update(self, value: float, median: bool = False) -> float:
    value = float(value)
    if np.isfinite(value):
      self._values.append(value)
    if not self._values:
      return 0.0
    return float(np.median(self._values) if median else np.mean(self._values))


class TrafficStopDistanceTracker:
  """Reject transient closer stop-line estimates while accounting for ego motion."""

  def __init__(self, sample_count: int = TRAFFIC_STOP_DISTANCE_STABILITY_SAMPLES):
    self._world_candidates: deque[float] = deque(maxlen=max(1, int(sample_count)))
    self._distance_traveled = 0.0

  def reset(self) -> None:
    self._world_candidates.clear()
    self._distance_traveled = 0.0

  def update(self, model_distance: float, ego_distance: float) -> float:
    if np.isfinite(ego_distance):
      self._distance_traveled += max(0.0, float(ego_distance))
    if np.isfinite(model_distance):
      self._world_candidates.append(
        self._distance_traveled + max(0.0, float(model_distance)))
    if not self._world_candidates:
      return 0.0
    return max(0.0, max(self._world_candidates) - self._distance_traveled)


def get_virtual_traffic_stop_distance(model_distance: float, v_ego_kph: float) -> float:
  model_distance = max(0.0, float(model_distance))
  distance_ratio = float(np.interp(
    max(0.0, float(v_ego_kph)),
    TRAFFIC_STOP_DISTANCE_RATIO_SPEED_BP_KPH,
    TRAFFIC_STOP_DISTANCE_RATIO,
  ))
  applied_ratio = float(np.interp(
    model_distance,
    TRAFFIC_STOP_DISTANCE_FADE_BP_M,
    (1.0, distance_ratio),
  ))
  return max(0.0, model_distance * applied_ratio)


def get_traffic_stop_obstacle_distance(stop_distance: float) -> float:
  return max(0.0, float(stop_distance) + TRAFFIC_STOP_DISTANCE_ADJUST_M)


def get_traffic_stop_accel_floor(v_ego: float, raw_stop_distance: float,
                                 target_stop_distance: float) -> float:
  values = (v_ego, raw_stop_distance, target_stop_distance)
  if not all(np.isfinite(value) for value in values):
    return -TRAFFIC_STOP_MAX_DECEL_MPS2

  v_ego = max(0.0, float(v_ego))
  available_distance = (
    float(raw_stop_distance)
    - max(0.0, float(target_stop_distance))
    - v_ego * TRAFFIC_STOP_RESPONSE_TIME_S
    - TRAFFIC_STOP_DISTANCE_UNCERTAINTY_M
  )
  if available_distance <= 0.0:
    return -TRAFFIC_STOP_MAX_DECEL_MPS2

  required_decel = v_ego ** 2 / (2.0 * available_distance)
  allowed_decel = np.clip(
    max(TRAFFIC_STOP_SOFT_DECEL_MPS2,
        required_decel + TRAFFIC_STOP_DECEL_SAFETY_BUFFER_MPS2),
    TRAFFIC_STOP_SOFT_DECEL_MPS2,
    TRAFFIC_STOP_MAX_DECEL_MPS2,
  )
  return -float(allowed_decel)


class TrafficStopController:
  """Carrot-style model stop prediction and stable stop-line tracking."""

  def __init__(self):
    self._stop_x_median = MovingAverage(3)
    self._stop_x_average = MovingAverage(15)
    self._model_v_average = MovingAverage(10)
    self._distance_tracker = TrafficStopDistanceTracker()
    self.reset()

  def reset(self) -> None:
    self.state = TrafficStopState.inactive
    self.signal_state = TrafficSignalState.off
    self.stop_distance = 1000.0
    self.model_distance = 1000.0
    self.raw_model_distance = 1000.0
    self.reference_speed_kph: float | None = None
    self._actual_stop_distance = 0.0
    self._stop_count = 0
    self._start_count = 0
    self._cooldown_frames = 0
    self._stop_x_median.reset()
    self._stop_x_average.reset()
    self._model_v_average.reset()
    self._distance_tracker.reset()

  @property
  def active(self) -> bool:
    return self.state != TrafficStopState.inactive

  @property
  def should_stop(self) -> bool:
    return self.state == TrafficStopState.stopped

  def _detect_signal_state(self, v_cruise: float, v_values: list[float], v_ego: float,
                           a_ego: float, model_x: float, model_y: float,
                           lead_distance: float) -> None:
    model_v = self._model_v_average.update(v_values[-1])
    start_sign = model_v > 5.0 or model_v > v_values[0] + 2.0
    v_ego_kph = v_ego * CV.MS_TO_KPH

    if v_ego_kph < 1.0:
      stop_sign = model_x < 20.0 and model_v < 10.0
    elif v_ego_kph < TRAFFIC_STOP_MAX_ENTRY_SPEED_KPH:
      max_model_distance = float(np.interp(v_values[0] * CV.MS_TO_KPH,
                                           [60.0, 80.0], [120.0, 150.0]))
      stop_sign = (
        model_x < lead_distance - 3.0 and
        model_x < max_model_distance and
        (model_v < 3.0 or model_v < v_values[0] * 0.7) and
        abs(model_y) < 5.0
      )
      if v_cruise != 0.0 and self.state == TrafficStopState.inactive and a_ego < -1.0:
        stop_sign = False
    else:
      stop_sign = False

    self._stop_count = self._stop_count + 1 if stop_sign else 0
    self._start_count = self._start_count + 1 if start_sign and not stop_sign else 0
    if self._stop_count * DT_MDL > 0.0:
      self.signal_state = TrafficSignalState.red
    elif self._start_count * DT_MDL > 0.2:
      self.signal_state = TrafficSignalState.green
    else:
      self.signal_state = TrafficSignalState.off

  def update(self, enabled: bool, car_state, radar_state, model, v_cruise: float) -> None:
    x_values = list(getattr(getattr(model, "position", None), "x", []))
    y_values = list(getattr(getattr(model, "position", None), "y", []))
    v_values = list(getattr(getattr(model, "velocity", None), "x", []))
    if not enabled or len(x_values) < 2 or not y_values or len(v_values) < 2:
      self.reset()
      return

    v_ego = float(car_state.vEgo)
    v_ego_kph = v_ego * CV.MS_TO_KPH
    stop_index = min(31, len(x_values) - 1)
    filtered_stop_x = self._stop_x_median.update(x_values[stop_index], median=True)
    filtered_stop_x = self._stop_x_average.update(filtered_stop_x)
    self.raw_model_distance = max(0.0, filtered_stop_x)
    stable_model_distance = self._distance_tracker.update(
      self.raw_model_distance, v_ego * DT_MDL)
    self.model_distance = stable_model_distance

    lead = radar_state.leadOne
    lead_detected = bool(lead.status)
    lead_distance = float(lead.dRel) if lead_detected else 1000.0
    self._detect_signal_state(
      v_cruise, v_values, v_ego, float(car_state.aEgo),
      float(x_values[-1]), float(y_values[-1]), lead_distance,
    )

    if car_state.gasPressed:
      self.state = TrafficStopState.inactive
      self._cooldown_frames = round(TRAFFIC_STOP_CANCEL_COOLDOWN_S / DT_MDL)
    elif self.state == TrafficStopState.stopped:
      if self.signal_state == TrafficSignalState.green or \
         (lead_detected and lead_distance - self.raw_model_distance < 2.0):
        self.state = TrafficStopState.inactive
    elif self.state == TrafficStopState.stopping:
      if self.signal_state == TrafficSignalState.green or \
         (lead_detected and lead_distance - self.raw_model_distance < 2.0):
        self.state = TrafficStopState.inactive
      else:
        self.reference_speed_kph = max(
          v_ego_kph, float(self.reference_speed_kph or 0.0))
        if stable_model_distance > 10.0:
          self._actual_stop_distance = get_virtual_traffic_stop_distance(
            stable_model_distance, self.reference_speed_kph)
        if v_ego < 0.3:
          self.state = TrafficStopState.stopped
    else:
      self._cooldown_frames = max(0, self._cooldown_frames - 1)
      if not lead_detected and self.signal_state == TrafficSignalState.red and \
         abs(float(car_state.steeringAngleDeg)) < TRAFFIC_STOP_ENTRY_STEERING_LIMIT_DEG and \
         self._cooldown_frames == 0:
        self.state = TrafficStopState.stopping
        self.reference_speed_kph = v_ego_kph
        self._actual_stop_distance = get_virtual_traffic_stop_distance(
          stable_model_distance, self.reference_speed_kph)

    if self.active:
      self._actual_stop_distance = max(
        0.0, self._actual_stop_distance - v_ego * DT_MDL)
      self.stop_distance = self._actual_stop_distance
    else:
      self.stop_distance = 1000.0
      self.model_distance = 1000.0
      self.reference_speed_kph = None
      self._actual_stop_distance = 0.0

  def limit_cruise_speed(self, v_cruise: float) -> float:
    if not self.active or self.stop_distance >= 300.0:
      return v_cruise
    soft_distance = max(self.stop_distance - 1.0, 0.0)
    soft_speed = float(np.sqrt(2.0 * 2.4 * soft_distance))
    return min(v_cruise, soft_speed)
