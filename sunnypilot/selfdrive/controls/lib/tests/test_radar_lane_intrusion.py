from types import SimpleNamespace

from openpilot.sunnypilot.selfdrive.controls.lib.radar_lane_intrusion import RadarLaneIntrusionDetector


def line(y_values):
  return SimpleNamespace(x=[0.0, 20.0, 40.0, 60.0], y=y_values)


def model(left=None, right=None, probabilities=None):
  left = left or [-1.8] * 4
  right = right or [1.8] * 4
  probabilities = probabilities or [0.8, 0.9, 0.9, 0.8]
  return SimpleNamespace(
    laneLines=[line([-5.4] * 4), line(left), line(right), line([5.4] * 4)],
    laneLineProbs=probabilities,
  )


def point(track_id=7, distance=30.0, model_y=-3.1):
  return SimpleNamespace(trackId=track_id, dRel=distance, yRel=-model_y, vRel=0.0)


def update(detector, now, model_y, track_id=7, distance=30.0, model_v2=None,
           speed=20.0, lane_change=False):
  return detector.update(
    speed, [point(track_id, distance, model_y)], model_v2 or model(), now,
    lane_change_active=lane_change,
  )


def drive_left_cut_in(detector, model_v2=None, track_id=7):
  samples = [-3.2, -3.1, -3.0, -2.8, -2.6, -2.45, -2.30, -2.15]
  return [update(detector, index * 0.05, lateral, track_id=track_id, model_v2=model_v2)
          for index, lateral in enumerate(samples)]


def test_left_adjacent_vehicle_crossing_lane_boundary_alerts_once():
  detector = RadarLaneIntrusionDetector()
  results = drive_left_cut_in(detector)

  alerts = [result for result in results if result is not None]
  assert len(alerts) == 1
  assert alerts[0].track_id == 7
  assert alerts[0].side == "left"


def test_right_adjacent_vehicle_crossing_lane_boundary_alerts():
  detector = RadarLaneIntrusionDetector()
  samples = [3.2, 3.1, 3.0, 2.8, 2.6, 2.45, 2.30, 2.15]
  results = [update(detector, index * 0.05, lateral) for index, lateral in enumerate(samples)]

  alert = next(result for result in results if result is not None)
  assert alert.side == "right"


def test_stable_adjacent_vehicle_does_not_alert():
  detector = RadarLaneIntrusionDetector()
  assert all(update(detector, index * 0.05, -3.1) is None for index in range(20))
  assert detector.lane_risks == {"left": 0.0, "right": 0.0}


def test_left_lane_risk_grows_as_vehicle_approaches_boundary():
  detector = RadarLaneIntrusionDetector()
  samples = [-3.5, -3.5, -3.5, -3.3, -3.0, -2.7, -2.6]
  risks = []
  for index, lateral in enumerate(samples):
    update(detector, index * 0.05, lateral)
    risks.append(detector.lane_risks["left"])

  assert risks[:3] == [0.0, 0.0, 0.0]
  assert 0.0 < risks[3] < risks[4] < risks[5] < risks[6]
  assert risks[6] > 0.99
  assert detector.lane_risks["right"] == 0.0


def test_lane_risk_accepts_navdy_radar_dicts_and_fades():
  detector = RadarLaneIntrusionDetector()
  for index, lateral in enumerate([-3.5, -3.5, -3.5, -3.0]):
    detector.update(20.0, [{"trackId": 8, "dRel": 30.0, "yRel": -lateral}],
                    model(), index * 0.05)
  initial_risk = detector.lane_risks["left"]

  detector.update(20.0, [], model(), 0.25)

  assert initial_risk > 0.0
  assert 0.0 < detector.lane_risks["left"] < initial_risk


def test_five_hz_navdy_samples_keep_track_history():
  detector = RadarLaneIntrusionDetector()
  samples = [-3.5, -3.4, -3.3, -3.0, -2.7, -2.4, -2.2, -2.0]
  results = [update(detector, index * 0.21, lateral) for index, lateral in enumerate(samples)]

  assert detector.lane_risks["left"] > 0.0
  assert any(result is not None for result in results)


def test_new_track_already_inside_lane_does_not_alert():
  detector = RadarLaneIntrusionDetector()
  assert all(update(detector, index * 0.05, -0.5) is None for index in range(10))


def test_single_lateral_jump_does_not_alert():
  detector = RadarLaneIntrusionDetector()
  samples = [-3.2, -3.1, -3.0, -2.2, -3.0, -3.0, -3.0]
  assert all(update(detector, index * 0.05, lateral) is None
             for index, lateral in enumerate(samples))


def test_track_id_change_does_not_inherit_outside_history():
  detector = RadarLaneIntrusionDetector()
  for index, lateral in enumerate([-3.2, -3.1, -3.0]):
    assert update(detector, index * 0.05, lateral, track_id=7) is None
  for index, lateral in enumerate([-2.45, -2.30, -2.15], start=3):
    assert update(detector, index * 0.05, lateral, track_id=8) is None


def test_low_confidence_lane_lines_do_not_alert():
  detector = RadarLaneIntrusionDetector()
  low_confidence = model(probabilities=[0.8, 0.3, 0.9, 0.8])
  assert all(result is None for result in drive_left_cut_in(detector, low_confidence))


def test_own_lane_change_clears_track_history():
  detector = RadarLaneIntrusionDetector()
  for index, lateral in enumerate([-3.2, -3.1, -3.0]):
    assert update(detector, index * 0.05, lateral) is None
  assert update(detector, 0.15, -2.8, lane_change=True) is None
  for index, lateral in enumerate([-2.45, -2.30, -2.15], start=4):
    assert update(detector, index * 0.05, lateral) is None


def test_curved_lane_following_vehicle_does_not_false_alert():
  detector = RadarLaneIntrusionDetector()
  curved = model(
    left=[-1.8, -1.4, -1.0, -0.6],
    right=[1.8, 2.2, 2.6, 3.0],
  )
  distances = [20.0 + index * 2.0 for index in range(12)]
  results = []
  for index, distance in enumerate(distances):
    left_boundary = -1.8 + 0.02 * distance
    results.append(update(
      detector, index * 0.05, left_boundary - 1.3,
      distance=distance, model_v2=curved,
    ))
  assert all(result is None for result in results)


def test_detector_is_disabled_at_low_speed():
  detector = RadarLaneIntrusionDetector()
  assert all(update(detector, index * 0.05, lateral, speed=4.9) is None
             for index, lateral in enumerate([-3.2, -3.1, -3.0, -2.45, -2.30, -2.15]))
