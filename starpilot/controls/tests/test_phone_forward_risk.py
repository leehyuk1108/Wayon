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


def test_close_new_lead_without_lateral_history_is_not_lane_intrusion():
  assert not lead_lane_intrusion_risk(
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


def test_close_new_radar_track_without_lateral_history_is_not_lane_intrusion():
  assert not lead_lane_intrusion_risk(
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
    lead=lead(dRel=22.0, vRel=-7.0, vLead=17.0),
  )


def test_bad_zero_lead_speed_does_not_create_closing_risk():
  assert not lead_closing_risk(v_ego=24.0, lead=lead(dRel=35.0, vRel=0.0, vLead=0.0))


def test_observed_distance_drop_without_fast_reported_closing_is_not_closing_risk():
  assert not lead_closing_risk(
    v_ego=24.0,
    lead=lead(dRel=22.5, vRel=-2.0, vLead=22.0),
    previous_lead_status=True,
    previous_lead_d_rel=23.1,
    lead_history_initialized=True,
  )


def test_moderate_closing_at_comfortable_distance_is_not_closing_risk():
  assert not lead_closing_risk(
    v_ego=24.0,
    lead=lead(dRel=35.0, vRel=-6.0, vLead=18.0),
    previous_lead_status=True,
    previous_lead_d_rel=35.2,
    lead_history_initialized=True,
  )


def test_observed_distance_drop_needs_reported_closing_confirmation():
  assert not lead_closing_risk(
    v_ego=24.0,
    lead=lead(dRel=22.5, vRel=-0.4, vLead=23.6),
    previous_lead_status=True,
    previous_lead_d_rel=23.1,
    lead_history_initialized=True,
  )


def test_far_lead_with_small_relative_speed_and_distance_jitter_is_not_closing_risk():
  assert not lead_closing_risk(
    v_ego=24.0,
    lead=lead(dRel=42.8, vRel=-0.4, vLead=23.6),
    previous_lead_status=True,
    previous_lead_d_rel=43.2,
    lead_history_initialized=True,
  )


def test_fcw_flag_without_real_closing_is_not_closing_risk():
  assert not lead_closing_risk(
    v_ego=18.0,
    lead=lead(dRel=24.0, vRel=0.0, vLead=18.0, fcw=True),
    previous_lead_status=True,
    previous_lead_d_rel=24.0,
    lead_history_initialized=True,
  )


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
