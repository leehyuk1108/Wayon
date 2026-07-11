from types import SimpleNamespace

from openpilot.sunnypilot.selfdrive.controls.lib.phone_forward_risk import lead_closing_risk, lead_lane_intrusion_risk


def lead(**kwargs):
  defaults = {"status": True, "dRel": 30.0, "yRel": 0.0, "vRel": 0.0, "radarTrackId": 4}
  defaults.update(kwargs)
  return SimpleNamespace(**defaults)


def test_adjacent_vehicle_entering_lane_is_lane_intrusion():
  assert lead_lane_intrusion_risk(20.0, lead(dRel=32.0, yRel=0.7), previous_lead_status=True,
                                  previous_lead_y_rel=2.4, lane_width=3.6, lead_history_initialized=True)


def test_fast_closing_lead_is_closing_risk():
  assert lead_closing_risk(24.0, lead(dRel=22.0, vRel=-7.0))


def test_far_steady_lead_is_not_a_phone_forward_risk():
  assert not lead_closing_risk(22.0, lead(dRel=60.0, vRel=0.2))
  assert not lead_lane_intrusion_risk(22.0, lead(dRel=60.0, vRel=0.2), previous_lead_status=True,
                                      previous_lead_y_rel=0.2, lane_width=3.6, lead_history_initialized=True)
