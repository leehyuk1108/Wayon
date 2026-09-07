from openpilot.sunnypilot.selfdrive.controls.lib.radar_lead_helpers import cutin_risk_for_control, leads_are_duplicates
from openpilot.selfdrive.controls.radard import RadarD, cutin_matches_selected_lead, select_radar_v_ego
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


def test_closing_radar_lead_is_held_across_farther_track_switch():
  radar = RadarD.__new__(RadarD)
  radar.current_time = 10.0
  radar.lead_holds = [None, None]
  closing = {
    "status": True, "radar": True, "radarTrackId": 7,
    "dRel": 30.0, "vRel": -3.0, "modelProb": 0.9, "score": 0.0,
  }
  assert radar.hold_radar_lead(0, closing)["radarTrackId"] == 7

  radar.current_time = 10.2
  farther = {
    "status": True, "radar": True, "radarTrackId": 8,
    "dRel": 50.0, "vRel": -1.0, "modelProb": 0.9, "score": 0.0,
  }
  held = radar.hold_radar_lead(0, farther)
  assert held["radarTrackId"] == 7
  assert held["dRel"] < closing["dRel"]


def test_closer_radar_track_switches_immediately():
  radar = RadarD.__new__(RadarD)
  radar.current_time = 10.0
  radar.lead_holds = [None, None]
  radar.hold_radar_lead(0, {
    "status": True, "radar": True, "radarTrackId": 7,
    "dRel": 30.0, "vRel": -1.0, "modelProb": 0.9, "score": 0.0,
  })
  radar.current_time = 10.1
  closer = {
    "status": True, "radar": True, "radarTrackId": 8,
    "dRel": 18.0, "vRel": -2.0, "modelProb": 0.9, "score": 0.0,
  }
  assert radar.hold_radar_lead(0, closer)["radarTrackId"] == 8


def test_stale_car_state_uses_current_model_velocity():
  assert select_radar_v_ego(0.0, 15.0, 10.4, 0.0) == 10.4
  assert select_radar_v_ego(10.9, 0.02, 10.4, 0.0) == 10.9


def test_brief_same_object_vision_fallback_keeps_radar_lead():
  radar = RadarD.__new__(RadarD)
  radar.current_time = 10.0
  radar.lead_holds = [None, None]
  radar.hold_radar_lead(0, {
    "status": True, "radar": True, "radarTrackId": 22,
    "dRel": 29.0, "yRel": -0.6, "vRel": -0.5, "modelProb": 1.0, "score": 0.0,
  })
  radar.current_time = 10.05
  fallback = radar.hold_radar_lead(0, {
    "status": True, "radar": False, "radarTrackId": -1,
    "dRel": 23.1, "yRel": -0.2, "vRel": -0.4, "modelProb": 1.0, "score": 0.0,
  })
  assert fallback["radar"]
  assert fallback["radarTrackId"] == 22
  assert fallback["dRel"] > 28.0
