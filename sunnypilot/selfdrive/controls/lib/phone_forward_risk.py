PHONE_DISTRACTED_TYPE = 1 << 2

MIN_FORWARD_RISK_SPEED = 5.0
FAST_CLOSING_DISTANCE = 40.0
FAST_CLOSING_SPEED = 5.0
FAST_CLOSING_TTC = 4.0
FAST_CLOSING_DT = 0.05
OBSERVED_CLOSING_DISTANCE = 30.0
OBSERVED_CLOSING_MIN_DREL_DROP = 0.5
OBSERVED_CLOSING_MIN_REPORTED_SPEED = 4.0


def phone_detected_from_distracted_type(phone_detected: bool) -> bool:
  return bool(phone_detected)


def _lead_value(lead, name, default=0.0):
  try:
    return float(getattr(lead, name))
  except (TypeError, ValueError):
    return default


def _lead_active(v_ego, lead):
  if lead is None or not bool(getattr(lead, "status", False)) or v_ego < MIN_FORWARD_RISK_SPEED:
    return False
  return _lead_value(lead, "dRel") > 0.0


def lead_closing_risk(v_ego, lead, previous_lead_status=False, previous_lead_d_rel=0.0,
                      lead_history_initialized=True, dt=FAST_CLOSING_DT):
  if not _lead_active(v_ego, lead):
    return False
  d_rel = _lead_value(lead, "dRel")
  reported_closing_speed = max(0.0, -_lead_value(lead, "vRel"))
  observed_closing = False
  if lead_history_initialized and previous_lead_status and previous_lead_d_rel > d_rel:
    d_rel_drop = previous_lead_d_rel - d_rel
    observed_closing = (d_rel < OBSERVED_CLOSING_DISTANCE and
                        d_rel_drop >= OBSERVED_CLOSING_MIN_DREL_DROP and
                        reported_closing_speed >= OBSERVED_CLOSING_MIN_REPORTED_SPEED)
  fast_closing = d_rel < FAST_CLOSING_DISTANCE and reported_closing_speed >= FAST_CLOSING_SPEED
  return (fast_closing or observed_closing) and d_rel / max(reported_closing_speed, 0.1) <= FAST_CLOSING_TTC
