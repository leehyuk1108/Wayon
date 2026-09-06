from openpilot.sunnypilot.selfdrive.controls.lib.radar_lead_helpers import cutin_risk_for_control, leads_are_duplicates
from openpilot.selfdrive.controls.radard import cutin_matches_selected_lead
from types import SimpleNamespace


def test_same_radar_track_is_duplicate():
  lead_one = {"status": True, "radarTrackId": 7, "dRel": 30.0, "vLead": 20.0, "yRel": 0.1}
  lead_two = {"status": True, "radarTrackId": 7, "dRel": 30.2, "vLead": 20.1, "yRel": 0.2}
  assert leads_are_duplicates(lead_one, lead_two)


def test_distinct_radar_tracks_are_preserved():
  lead_one = {"status": True, "radarTrackId": 7, "dRel": 30.0, "vLead": 20.0, "yRel": 0.1}
  lead_two = {"status": True, "radarTrackId": 8, "dRel": 30.2, "vLead": 20.1, "yRel": 0.2}
  assert not leads_are_duplicates(lead_one, lead_two)


def test_vision_duplicate_of_radar_lead_is_removed():
  lead_one = {"status": True, "radarTrackId": 7, "dRel": 30.0, "vLead": 20.0, "yRel": 0.1}
  lead_two = {"status": True, "radarTrackId": -1, "dRel": 31.0, "vLead": 20.5, "yRel": 0.3}
  assert leads_are_duplicates(lead_one, lead_two)


def test_selected_longitudinal_lead_remains_identifiable_for_warning():
  lead_one = SimpleNamespace(status=True, radar=True, radarTrackId=7)
  lead_two = SimpleNamespace(status=False, radar=False, radarTrackId=-1)
  assert cutin_matches_selected_lead(7, lead_one, lead_two)
  assert not cutin_matches_selected_lead(8, lead_one, lead_two)


def test_selected_longitudinal_lead_is_not_applied_twice_to_control():
  risk = SimpleNamespace(status=True, radar=True, radarTrackId=7)
  radar_state = SimpleNamespace(
    leadOne=SimpleNamespace(status=True, radar=True, radarTrackId=7),
    leadTwo=SimpleNamespace(status=False, radar=False, radarTrackId=-1),
    leadCutInRisk=risk,
  )
  assert cutin_risk_for_control(radar_state) is None

  radar_state.leadOne.radarTrackId = 8
  assert cutin_risk_for_control(radar_state) is risk
