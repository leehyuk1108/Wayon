from typing import Any


LEAD_DUPLICATE_DISTANCE = 3.0
LEAD_DUPLICATE_SPEED = 2.0
LEAD_DUPLICATE_LATERAL = 1.2


def _lead_value(lead: Any, name: str, default: Any) -> Any:
  if isinstance(lead, dict):
    return lead.get(name, default)
  return getattr(lead, name, default)


def radar_track_matches_any_lead(track_id: int, *leads: Any) -> bool:
  return track_id >= 0 and any(
    bool(_lead_value(lead, "status", False)) and bool(_lead_value(lead, "radar", False)) and
    int(_lead_value(lead, "radarTrackId", -1)) == track_id
    for lead in leads
  )


def cutin_risk_for_control(radar_state: Any) -> Any | None:
  """Avoid applying pre-cut-in control twice after the same track becomes a lead."""
  risk = _lead_value(radar_state, "leadCutInRisk", None)
  if risk is None or not bool(_lead_value(risk, "status", False)):
    return risk
  track_id = int(_lead_value(risk, "radarTrackId", -1))
  if radar_track_matches_any_lead(
    track_id,
    _lead_value(radar_state, "leadOne", None),
    _lead_value(radar_state, "leadTwo", None),
  ):
    return None
  return risk


def leads_are_duplicates(lead_one: dict[str, Any], lead_two: dict[str, Any]) -> bool:
  if not lead_one.get("status", False) or not lead_two.get("status", False):
    return False

  id_one = int(lead_one.get("radarTrackId", -1))
  id_two = int(lead_two.get("radarTrackId", -1))
  if id_one >= 0 and id_one == id_two:
    return True
  if id_one >= 0 and id_two >= 0:
    return False

  return abs(float(lead_one.get("dRel", 0.0)) - float(lead_two.get("dRel", 0.0))) < LEAD_DUPLICATE_DISTANCE and \
         abs(float(lead_one.get("vLead", 0.0)) - float(lead_two.get("vLead", 0.0))) < LEAD_DUPLICATE_SPEED and \
         abs(float(lead_one.get("yRel", 0.0)) - float(lead_two.get("yRel", 0.0))) < LEAD_DUPLICATE_LATERAL
