from types import SimpleNamespace

from openpilot.starpilot.controls.lib.phone_forward_risk import (
  PHONE_DISTRACTED_TYPE,
  lead_closing_risk,
  lead_lane_intrusion_risk,
  phone_detected_from_distracted_type,
)


def lead(**kwargs):
  defaults = {
    "status": True,
    "dRel": 30.0,
    "yRel": 0.0,
    "vRel": 0.0,
    "vLead": 20.0,
    "fcw": False,
    "radarTrackId": 4,
  }
  defaults.update(kwargs)
  return SimpleNamespace(**defaults)


def test_phone_detected_uses_phone_bit_only():
  assert phone_detected_from_distracted_type(PHONE_DISTRACTED_TYPE)
  assert not phone_detected_from_distracted_type(0)
  assert not phone_detected_from_distracted_type(1 << 1)


def test_close_new_lead_is_lane_intrusion_after_history_exists():
  assert lead_lane_intrusion_risk(
    v_ego=18.0,
    lead=lead(dRel=24.0),
    previous_lead_status=False,
    lead_history_initialized=True,
  )


def test_initial_lead_sample_does_not_alert_as_cut_in():
  assert not lead_lane_intrusion_risk(
    v_ego=18.0,
    lead=lead(dRel=24.0),
    previous_lead_status=False,
    lead_history_initialized=False,
  )


def test_close_new_radar_track_is_lane_intrusion():
  assert lead_lane_intrusion_risk(
    v_ego=18.0,
    lead=lead(dRel=24.0, radarTrackId=7),
    previous_lead_status=True,
    previous_radar_track_id=4,
    lead_history_initialized=True,
  )


def test_adjacent_vehicle_entering_lane_is_lane_intrusion():
  assert lead_lane_intrusion_risk(
    v_ego=20.0,
    lead=lead(dRel=32.0, yRel=0.7),
    previous_lead_status=True,
    previous_lead_y_rel=2.4,
    lane_width=3.6,
    lead_history_initialized=True,
  )


def test_fast_closing_lead_is_closing_risk():
  assert lead_closing_risk(
    v_ego=24.0,
    lead=lead(dRel=35.0, vRel=-7.0, vLead=17.0),
  )


def test_fcw_flag_is_closing_risk():
  assert lead_closing_risk(v_ego=18.0, lead=lead(fcw=True))


def test_far_steady_lead_is_not_any_phone_forward_risk():
  assert not lead_closing_risk(v_ego=22.0, lead=lead(dRel=60.0, vRel=0.2, vLead=22.2))
  assert not lead_lane_intrusion_risk(
    v_ego=22.0,
    lead=lead(dRel=60.0, vRel=0.2, vLead=22.2),
    previous_lead_status=True,
    previous_lead_y_rel=0.2,
    lane_width=3.6,
    lead_history_initialized=True,
  )
