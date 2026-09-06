from openpilot.sunnypilot.selfdrive.controls.lib.radar_lead_helpers import leads_are_duplicates
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


def test_selected_longitudinal_lead_is_not_republished_as_cutin_risk():
  lead_one = SimpleNamespace(status=True, radar=True, radarTrackId=7)
  lead_two = SimpleNamespace(status=False, radar=False, radarTrackId=-1)
  assert cutin_matches_selected_lead(7, lead_one, lead_two)
  assert not cutin_matches_selected_lead(8, lead_one, lead_two)
