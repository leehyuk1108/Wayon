from types import SimpleNamespace

import numpy as np
from openpilot.selfdrive.controls.lib.traffic_stop import (
  TrafficSignalState,
  TrafficStopController,
  TrafficStopDistanceTracker,
  TrafficStopState,
  get_traffic_stop_accel_floor,
  get_virtual_traffic_stop_distance,
)


def model(stop_distance=70.0, terminal_speed=0.0, lateral_endpoint=0.0):
  return SimpleNamespace(
    position=SimpleNamespace(
      x=np.linspace(0.0, stop_distance, 33).tolist(),
      y=np.linspace(0.0, lateral_endpoint, 33).tolist(),
    ),
    velocity=SimpleNamespace(
      x=np.linspace(15.0, terminal_speed, 33).tolist(),
    ),
  )


def car_state(speed=15.0, accel=0.0, steering=0.0, gas=False):
  return SimpleNamespace(
    vEgo=speed,
    aEgo=accel,
    steeringAngleDeg=steering,
    gasPressed=gas,
  )


def radar_state(lead=False, distance=40.0):
  return SimpleNamespace(leadOne=SimpleNamespace(status=lead, dRel=distance))


def test_distance_tracker_rejects_single_closer_jump():
  tracker = TrafficStopDistanceTracker(sample_count=3)
  assert tracker.update(80.0, 0.0) == 80.0
  assert tracker.update(30.0, 1.0) == 79.0
  assert tracker.update(78.0, 1.0) == 78.0


def test_virtual_stop_advance_fades_near_line():
  assert get_virtual_traffic_stop_distance(100.0, 100.0) == 70.0
  assert get_virtual_traffic_stop_distance(0.0, 100.0) == 0.0
  assert 17.0 < get_virtual_traffic_stop_distance(20.0, 100.0) < 20.0


def test_red_stop_prediction_activates_without_lead():
  controller = TrafficStopController()
  controller.update(True, car_state(), radar_state(), model(), 25.0)

  assert controller.signal_state == TrafficSignalState.red
  assert controller.state == TrafficStopState.stopping
  assert controller.active
  assert 0.0 < controller.stop_distance < controller.model_distance


def test_real_lead_prevents_signal_stop_entry():
  controller = TrafficStopController()
  controller.update(True, car_state(), radar_state(lead=True, distance=35.0), model(), 25.0)

  assert controller.state == TrafficStopState.inactive


def test_green_prediction_releases_active_stop():
  controller = TrafficStopController()
  controller.update(True, car_state(), radar_state(), model(), 25.0)
  assert controller.active

  green_model = model(stop_distance=120.0, terminal_speed=20.0)
  for _ in range(15):
    controller.update(True, car_state(), radar_state(), green_model, 25.0)

  assert controller.signal_state == TrafficSignalState.green
  assert controller.state == TrafficStopState.inactive


def test_signal_stop_accel_floor_is_soft_while_distance_is_available():
  assert get_traffic_stop_accel_floor(20.0, 140.0, 6.0) == -2.2
  assert get_traffic_stop_accel_floor(20.0, 30.0, 6.0) <= -3.0
