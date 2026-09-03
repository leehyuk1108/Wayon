from types import SimpleNamespace

from cereal import custom

from openpilot.selfdrive.selfdrived import selfdrived


class FakeEvents:
  def __init__(self):
    self.names = []

  def add(self, event_name):
    self.names.append(event_name)


class FakeSubMaster:
  def __init__(self, cutin_risk):
    self.updated = {"radarState": True}
    self.radar_state = SimpleNamespace(leadCutInRisk=cutin_risk)

  def __getitem__(self, service):
    assert service == "radarState"
    return self.radar_state


def cutin_risk(**overrides):
  values = {
    "status": True,
    "radar": True,
    "radarTrackId": 49,
    "dRel": 18.0,
    "yRel": 2.2,
    "vRel": -4.0,
    "vLat": 0.5,
    "score": 0.6,
  }
  values.update(overrides)
  return SimpleNamespace(**values)


def make_instance(risk):
  instance = object.__new__(selfdrived.SelfdriveD)
  instance.radar_lane_intrusion_cooldown = 0.0
  instance.previous_cutin_warning_active = False
  instance.previous_cutin_warning_track_id = -1
  instance.sm = FakeSubMaster(risk)
  instance.events_sp = FakeEvents()
  return instance


def test_longitudinal_cutin_predecel_adds_warning_event(monkeypatch):
  instance = make_instance(cutin_risk())
  logged = {}
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda name, **values: logged.update(name=name, **values))

  instance._update_radar_lane_intrusion(SimpleNamespace(vEgo=20.0))

  assert instance.events_sp.names == [custom.OnroadEventSP.EventName.radarLaneIntrusion]
  assert instance.radar_lane_intrusion_cooldown == selfdrived.LANE_INTRUSION_COOLDOWN
  assert logged["name"] == "radarCutInWarning"
  assert logged["trackId"] == 49
  assert logged["predecelAccel"] <= 0.0


def test_cutin_not_used_by_longitudinal_control_does_not_warn(monkeypatch):
  instance = make_instance(cutin_risk(vRel=1.0))
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda *args, **kwargs: None)

  instance._update_radar_lane_intrusion(SimpleNamespace(vEgo=20.0))

  assert instance.events_sp.names == []
  assert not instance.previous_cutin_warning_active


def test_continuous_cutin_warns_only_on_rising_edge(monkeypatch):
  instance = make_instance(cutin_risk())
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda *args, **kwargs: None)

  instance._update_radar_lane_intrusion(SimpleNamespace(vEgo=20.0))
  instance.radar_lane_intrusion_cooldown = 0.0
  instance._update_radar_lane_intrusion(SimpleNamespace(vEgo=20.0))

  assert instance.events_sp.names == [custom.OnroadEventSP.EventName.radarLaneIntrusion]
