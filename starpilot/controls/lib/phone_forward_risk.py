PHONE_DISTRACTED_TYPE = 1 << 2

MIN_FORWARD_RISK_SPEED = 5.0
CUT_IN_CLOSE_DISTANCE = 35.0
INTRUSION_DISTANCE = 45.0
FAST_CLOSING_DISTANCE = 55.0
FAST_CLOSING_SPEED = 3.0
FAST_CLOSING_TTC = 6.0
FAST_CLOSING_DT = 0.05
OBSERVED_CLOSING_DISTANCE = 25.0
OBSERVED_CLOSING_MIN_DREL_DROP = 0.5
OBSERVED_CLOSING_MIN_REPORTED_SPEED = 2.0
DEFAULT_LANE_WIDTH = 3.6


def phone_detected_from_distracted_type(distracted_type):
  return bool(int(distracted_type) & PHONE_DISTRACTED_TYPE)


def _lead_value(lead, name, default=0.0):
  try:
    return float(getattr(lead, name))
  except (TypeError, ValueError):
    return default


def _lead_int(lead, name, default=-1):
  try:
    return int(getattr(lead, name))
  except (TypeError, ValueError):
    return default


def _lead_active(v_ego, lead):
  if lead is None or not bool(getattr(lead, "status", False)) or v_ego < MIN_FORWARD_RISK_SPEED:
    return False

  d_rel = _lead_value(lead, "dRel")
  return d_rel > 0.0


def lead_closing_risk(v_ego, lead, previous_lead_status=False, previous_lead_d_rel=0.0,
                      lead_history_initialized=True, dt=FAST_CLOSING_DT):
  if not _lead_active(v_ego, lead):
    return False

  if bool(getattr(lead, "fcw", False)):
    return True

  d_rel = _lead_value(lead, "dRel")
  v_rel = _lead_value(lead, "vRel")
  reported_closing_speed = max(0.0, -v_rel)
  observed_closing_speed = 0.0
  if lead_history_initialized and previous_lead_status and previous_lead_d_rel > d_rel:
    d_rel_drop = previous_lead_d_rel - d_rel
    if (d_rel < OBSERVED_CLOSING_DISTANCE and
        d_rel_drop >= OBSERVED_CLOSING_MIN_DREL_DROP and
        reported_closing_speed >= OBSERVED_CLOSING_MIN_REPORTED_SPEED):
      observed_closing_speed = d_rel_drop / max(dt, 0.01)

  closing_speed = max(reported_closing_speed, observed_closing_speed)
  fast_closing = d_rel < FAST_CLOSING_DISTANCE and closing_speed >= FAST_CLOSING_SPEED
  return fast_closing and d_rel / max(closing_speed, 0.1) <= FAST_CLOSING_TTC


def lead_lane_intrusion_risk(v_ego, lead, previous_lead_status=False, previous_lead_y_rel=0.0,
                             previous_radar_track_id=-1, lane_width=0.0,
                             lead_history_initialized=True):
  if not _lead_active(v_ego, lead):
    return False

  d_rel = _lead_value(lead, "dRel")
  y_rel = _lead_value(lead, "yRel")
  radar_track_id = _lead_int(lead, "radarTrackId")

  effective_lane_width = lane_width if lane_width > 0.0 else DEFAULT_LANE_WIDTH
  lane_half_width = max(1.25, min(2.0, effective_lane_width / 2.0))

  new_radar_target = previous_lead_status and previous_radar_track_id >= 0 and radar_track_id >= 0
  new_radar_target &= previous_radar_track_id != radar_track_id

  close_cut_in = lead_history_initialized and (not previous_lead_status or new_radar_target)
  close_cut_in &= d_rel < min(CUT_IN_CLOSE_DISTANCE, max(20.0, v_ego * 2.5))

  entering_lane = previous_lead_status and abs(previous_lead_y_rel) > lane_half_width + 0.35
  entering_lane &= abs(y_rel) <= lane_half_width
  entering_lane &= d_rel < INTRUSION_DISTANCE

  return close_cut_in or entering_lane
