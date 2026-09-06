from types import SimpleNamespace

from cereal import custom

from openpilot.selfdrive.selfdrived import selfdrived


class FakeEvents:
  def __init__(self):
    self.names = []

  def add(self, event_name):
    self.names.append(event_name)


class FakeSubMaster:
  def __init__(self, cutin_risk, selected=True):
    self.updated = {"radarState": True}
    selected_track = cutin_risk.radarTrackId if selected else cutin_risk.radarTrackId + 1
    self.radar_state = SimpleNamespace(
      leadOne=SimpleNamespace(status=True, radar=True, radarTrackId=selected_track),
      leadTwo=SimpleNamespace(status=False, radar=False, radarTrackId=-1),
      leadCutInRisk=cutin_risk,
    )

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


def make_instance(risk, selected=True):
  instance = object.__new__(selfdrived.SelfdriveD)
  instance.radar_lane_intrusion_cooldown = 0.0
  instance.previous_cutin_warning_active = False
  instance.previous_cutin_warning_track_id = -1
  instance.sm = FakeSubMaster(risk, selected=selected)
  instance.events_sp = FakeEvents()
  return instance


def test_selected_longitudinal_cutin_adds_warning_event(monkeypatch):
  instance = make_instance(cutin_risk())
  logged = {}
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda name, **values: logged.update(name=name, **values))

  instance._update_radar_lane_intrusion(SimpleNamespace(vEgo=20.0))

  assert instance.events_sp.names == [custom.OnroadEventSP.EventName.radarLaneIntrusion]
  assert instance.radar_lane_intrusion_cooldown == selfdrived.LANE_INTRUSION_COOLDOWN
  assert logged["name"] == "radarCutInWarning"
  assert logged["trackId"] == 49
  assert logged["predecelAccel"] <= 0.0


def test_unselected_cutin_candidate_does_not_warn(monkeypatch):
  instance = make_instance(cutin_risk(), selected=False)
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda *args, **kwargs: None)

  instance._update_radar_lane_intrusion(SimpleNamespace(vEgo=20.0))

  assert instance.events_sp.names == []
  assert not instance.previous_cutin_warning_active


def test_low_score_selected_candidate_does_not_warn(monkeypatch):
  instance = make_instance(cutin_risk(score=0.20))
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda *args, **kwargs: None)

  instance._update_radar_lane_intrusion(SimpleNamespace(vEgo=20.0))

  assert instance.events_sp.names == []
  assert not instance.previous_cutin_warning_active


def test_selected_nonclosing_cutin_still_warns(monkeypatch):
  instance = make_instance(cutin_risk(vRel=1.0))
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda *args, **kwargs: None)

  instance._update_radar_lane_intrusion(SimpleNamespace(vEgo=20.0))

  assert instance.events_sp.names == [custom.OnroadEventSP.EventName.radarLaneIntrusion]


def test_continuous_cutin_warns_only_on_rising_edge(monkeypatch):
  instance = make_instance(cutin_risk())
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda *args, **kwargs: None)

  instance._update_radar_lane_intrusion(SimpleNamespace(vEgo=20.0))
  instance.radar_lane_intrusion_cooldown = 0.0
  instance._update_radar_lane_intrusion(SimpleNamespace(vEgo=20.0))

  assert instance.events_sp.names == [custom.OnroadEventSP.EventName.radarLaneIntrusion]
