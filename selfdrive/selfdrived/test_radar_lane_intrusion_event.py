from types import SimpleNamespace

from cereal import custom

from openpilot.selfdrive.selfdrived import selfdrived


class FakeEvents:
  def __init__(self):
    self.names = []

  def add(self, event_name):
    self.names.append(event_name)


class FakeSubMaster:
  def __init__(self, intrusion):
    self.updated = {"radarLaneIntrusionSP": True}
    self.intrusion = intrusion

  def __getitem__(self, service):
    assert service == "radarLaneIntrusionSP"
    return self.intrusion


def test_radar_lane_intrusion_message_adds_warning_event(monkeypatch):
  intrusion = SimpleNamespace(
    detected=True,
    trackId=49,
    side="left",
    distance=43.7,
    lateral=-2.2,
    inwardSpeed=0.5,
  )
  instance = object.__new__(selfdrived.SelfdriveD)
  instance.radar_lane_intrusion_cooldown = 0.0
  instance.sm = FakeSubMaster(intrusion)
  instance.events_sp = FakeEvents()
  logged = {}
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda name, **values: logged.update(name=name, **values))

  instance._update_radar_lane_intrusion()

  assert instance.events_sp.names == [custom.OnroadEventSP.EventName.radarLaneIntrusion]
  assert instance.radar_lane_intrusion_cooldown == selfdrived.LANE_INTRUSION_COOLDOWN
  assert logged["name"] == "radarLaneIntrusion"
  assert (logged["trackId"], logged["side"]) == (49, "left")
