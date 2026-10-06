from types import SimpleNamespace as NS

import pytest

from openpilot.sunnypilot.selfdrive.controls.lib.cutin_warning import CutInWarningTracker


def model(probability=0.9):
  return NS(laneLines=[NS(x=[0.0, 60.0], y=[y, y]) for y in (-5.4, -1.8, 1.8, 5.4)],
            laneLineProbs=[probability] * 4)


def lead(y=3.2, **overrides):
  fields = dict(status=True, radar=True, radarTrackId=13, dRel=20.0, yRel=y, vRel=-1.0,
                modelProb=0.9, score=1.0, vLat=0.5)
  fields.update(overrides)
  return NS(**fields)


def radar(y=3.2, selected=True, vision=False, risk=True, **overrides):
  candidate = lead(y, **overrides)
  selected_lead = lead(candidate.yRel, radar=not vision, radarTrackId=-1 if vision else candidate.radarTrackId,
                       dRel=candidate.dRel, vRel=candidate.vRel, modelProb=candidate.modelProb)
  selected_lead.status = selected
  return NS(leadOne=selected_lead, leadTwo=lead(status=False), leadCutInRisk=lead(y, status=risk, **overrides))


def arm(tracker, sign=1.0, risk=True):
  for now in (0.0, 0.05, 0.10, 0.20):
    assert tracker.update(radar(3.2 * sign, selected=not risk, risk=risk), model(), 15.0, now) is None


def enter(tracker, sign=1.0, **overrides):
  warnings = []
  for now in (0.30, 0.35, 0.45, 0.50, 0.55):
    warning = tracker.update(radar(2.2 * sign, **overrides), model(), 15.0, now)
    if warning is not None:
      warnings.append(warning)
  return warnings


@pytest.mark.parametrize("sign,side", [(1.0, "left"), (-1.0, "right")])
def test_recent_crossing_warns_once(sign, side):
  tracker = CutInWarningTracker()
  arm(tracker, sign)
  warnings = enter(tracker, sign)
  assert len(warnings) == 1
  assert warnings[0].track_id == 13
  assert warnings[0].side == side
  assert not warnings[0].selected_by_vision


def test_existing_centered_lead_is_not_a_new_cutin():
  tracker = CutInWarningTracker()
  for i in range(200):
    y = (0.08, 0.23, -0.16, 0.0)[i % 4]
    assert tracker.update(radar(y, risk=i % 7 == 0), model(), 15.0, i * 0.05) is None


def test_steady_adjacent_car_does_not_warn():
  tracker = CutInWarningTracker()
  arm(tracker)
  for i in range(20):
    assert tracker.update(radar(3.2), model(), 15.0, 0.30 + i * 0.05) is None


def test_unselected_crossing_does_not_warn():
  tracker = CutInWarningTracker()
  arm(tracker)
  assert enter(tracker, selected=False) == []


def test_matching_vision_fallback_does_not_lose_warning():
  tracker = CutInWarningTracker()
  arm(tracker)
  warnings = enter(tracker, vision=True)
  assert len(warnings) == 1
  assert warnings[0].selected_by_vision


@pytest.mark.parametrize("field,number", [("dRel", 30.0), ("yRel", -2.2), ("vRel", 5.0)])
def test_other_vision_vehicle_cannot_confirm_candidate(field, number):
  tracker = CutInWarningTracker()
  arm(tracker)
  for now in (0.30, 0.35, 0.45):
    observation = radar(2.2, vision=True)
    setattr(observation.leadOne, field, number)
    assert tracker.update(observation, model(), 15.0, now) is None


def test_brief_candidate_dropout_does_not_retrigger_same_crossing():
  tracker = CutInWarningTracker()
  arm(tracker)
  assert len(enter(tracker)) == 1
  for now in (0.60, 0.65, 0.80, 0.90):
    assert tracker.update(radar(1.0, risk=now == 0.90), model(), 15.0, now) is None


def test_selected_slow_crossing_works_without_risk_threshold():
  tracker = CutInWarningTracker()
  arm(tracker, risk=False)
  warnings = []
  for i in range(1, 31):
    warning = tracker.update(radar(3.2 - i * 0.04, risk=False), model(), 15.0, 0.20 + i * 0.05)
    if warning is not None:
      warnings.append(warning)
  assert len(warnings) == 1


def test_one_frame_entry_is_not_enough():
  tracker = CutInWarningTracker()
  arm(tracker)
  assert tracker.update(radar(2.2), model(), 15.0, 0.30) is None
  assert tracker.update(radar(3.2), model(), 15.0, 0.35) is None


def test_old_outside_history_expires():
  tracker = CutInWarningTracker()
  arm(tracker)
  for i in range(1, 81):
    assert tracker.update(radar(1.0, selected=False), model(), 15.0, 0.20 + i * 0.05) is None
  for i in range(81, 90):
    assert tracker.update(radar(1.0), model(), 15.0, 0.20 + i * 0.05) is None


def test_track_id_change_inside_does_not_inherit_outside_history():
  tracker = CutInWarningTracker()
  arm(tracker)
  assert enter(tracker, radarTrackId=14) == []


@pytest.mark.parametrize("probability", [0.2, float("nan")])
def test_uncertain_selected_vehicle_does_not_confirm(probability):
  tracker = CutInWarningTracker()
  arm(tracker)
  assert enter(tracker, modelProb=probability) == []


def test_unreliable_lane_geometry_does_not_confirm():
  tracker = CutInWarningTracker()
  arm(tracker)
  for now in (0.30, 0.35, 0.45):
    assert tracker.update(radar(2.2), model(0.2), 15.0, now) is None


@pytest.mark.parametrize("field,number", [("dRel", float("nan")), ("yRel", float("nan")),
                                         ("vRel", float("nan")), ("dRel", 100.0)])
def test_invalid_candidate_does_not_warn(field, number):
  tracker = CutInWarningTracker()
  arm(tracker)
  assert enter(tracker, **{field: number}) == []


@pytest.mark.parametrize("speed,lane_change", [(0.0, False), (15.0, True)])
def test_own_lane_change_and_low_speed_clear_history(speed, lane_change):
  tracker = CutInWarningTracker()
  arm(tracker)
  assert tracker.update(radar(2.2), model(), speed, 0.30, lane_change) is None
  assert enter(tracker) == []


def test_telemetry_gap_does_not_reuse_old_identity():
  tracker = CutInWarningTracker()
  arm(tracker)
  for now in (2.0, 2.05, 2.20):
    assert tracker.update(radar(2.2), model(), 15.0, now) is None


@pytest.mark.parametrize("y,distance", [(0.0, 20.0), (2.2, 5.0)])
def test_position_jump_does_not_create_a_crossing(y, distance):
  tracker = CutInWarningTracker()
  arm(tracker)
  for now in (0.30, 0.35, 0.45):
    assert tracker.update(radar(y, dRel=distance), model(), 15.0, now) is None


def test_established_lead_boundary_drift_is_not_a_new_cutin():
  tracker = CutInWarningTracker()
  for now, y in ((0.0, 1.0), (0.05, 1.4), (0.10, 1.8), (0.20, 2.2),
                 (0.25, 2.2), (0.40, 2.2), (0.50, 1.8), (0.55, 1.8), (0.70, 1.8)):
    assert tracker.update(radar(y), model(), 15.0, now) is None


def test_warned_vehicle_must_fully_leave_before_another_crossing():
  tracker = CutInWarningTracker()
  arm(tracker)
  assert len(enter(tracker)) == 1
  for now, y in ((0.60, 1.0), (0.65, 1.8), (0.70, 2.2), (0.90, 2.2), (1.0, 1.8), (1.2, 1.8)):
    assert tracker.update(radar(y), model(), 15.0, now) is None
  for now, y in ((1.3, 2.6), (1.4, 3.2), (1.6, 3.2)):
    assert tracker.update(radar(y), model(), 15.0, now) is None
  warnings = [tracker.update(radar(2.2), model(), 15.0, now) for now in (1.7, 1.75, 1.85)]
  assert sum(w is not None for w in warnings) == 1


def test_established_lead_can_leave_and_reenter_on_the_other_side():
  tracker = CutInWarningTracker()
  for now, y in ((0.0, 0.0), (0.05, 1.0), (0.10, 2.0), (0.20, 3.2), (0.40, 3.2)):
    assert tracker.update(radar(y), model(), 15.0, now) is None
  warnings = [tracker.update(radar(2.2), model(), 15.0, now) for now in (0.5, 0.55, 0.65)]
  assert sum(w is not None for w in warnings) == 1


def test_manual_lane_change_settling_does_not_reuse_relative_motion():
  tracker = CutInWarningTracker()
  assert tracker.update(radar(3.2), model(), 15.0, 0.0, lane_change_active=True) is None
  for now, y in ((0.1, 3.2), (0.3, 3.2), (0.4, 2.2), (0.6, 2.2), (0.8, 1.8)):
    assert tracker.update(radar(y), model(), 15.0, now) is None
  for now, y in ((1.0, 1.0), (1.1, 1.0)):
    assert tracker.update(radar(y), model(), 15.0, now) is None


def test_lane_confidence_dropout_after_manual_change_preserves_established_lead():
  tracker = CutInWarningTracker()
  assert tracker.update(radar(1.0), model(), 15.0, 0.0) is None
  for i in range(1, 31):
    assert tracker.update(radar(2.2), model(0.1), 15.0, i * 0.05, lane_change_active=i <= 5) is None
  for now, y in ((1.6, 2.2), (1.65, 2.2), (1.8, 2.2), (1.9, 1.8), (2.0, 1.8), (2.1, 1.8)):
    assert tracker.update(radar(y), model(), 15.0, now) is None


def test_brief_lane_dropout_does_not_erase_recent_confirmed_outside_history():
  tracker = CutInWarningTracker()
  arm(tracker)
  for now in (0.3, 0.4, 0.5):
    assert tracker.update(radar(2.2), model(0.1), 15.0, now) is None
  warnings = [tracker.update(radar(2.2), model(), 15.0, now) for now in (0.6, 0.65, 0.75)]
  assert sum(w is not None for w in warnings) == 1
