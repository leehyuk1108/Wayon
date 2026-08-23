from typing import Any


LEAD_DUPLICATE_DISTANCE = 3.0
LEAD_DUPLICATE_SPEED = 2.0
LEAD_DUPLICATE_LATERAL = 1.2


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
