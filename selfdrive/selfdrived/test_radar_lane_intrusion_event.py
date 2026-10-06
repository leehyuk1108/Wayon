from types import SimpleNamespace

from cereal import custom, log

from openpilot.selfdrive.selfdrived import selfdrived


class FakeEvents:
  def __init__(self):
    self.names = []

  def add(self, event_name):
    self.names.append(event_name)


class FakeSubMaster:
  def __init__(self, cutin_risk, selected=True):
    self.updated = {"radarState": True}
    self.valid = {"radarState": True, "modelV2": True}
    self.logMonoTime = {"radarState": 1_000_000_000, "modelV2": 1_000_000_000}
    selected_track = cutin_risk.radarTrackId if selected else cutin_risk.radarTrackId + 1
    self.radar_state = SimpleNamespace(
      leadOne=SimpleNamespace(status=selected, radar=True, radarTrackId=selected_track,
                              dRel=cutin_risk.dRel, yRel=cutin_risk.yRel, vRel=cutin_risk.vRel, modelProb=0.9),
      leadTwo=SimpleNamespace(status=False, radar=False, radarTrackId=-1),
      leadCutInRisk=cutin_risk,
    )
    self.model = SimpleNamespace(
      laneLines=[SimpleNamespace(x=[0.0, 60.0], y=[y, y]) for y in (-5.4, -1.8, 1.8, 5.4)],
      laneLineProbs=[0.9] * 4,
      meta=SimpleNamespace(laneChangeState=log.LaneChangeState.off),
    )

  def __getitem__(self, service):
    return {"radarState": self.radar_state, "modelV2": self.model}[service]


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
  instance.CP = SimpleNamespace(brand='gm')
  instance.cutin_warning_tracker = selfdrived.CutInWarningTracker()
  instance.sm = FakeSubMaster(risk, selected=selected)
  instance.events_sp = FakeEvents()
  return instance


def update(instance, now, y_rel, left_blinker=False, right_blinker=False):
  instance.sm.logMonoTime = {"radarState": int(now * 1e9), "modelV2": int(now * 1e9)}
  instance.sm.radar_state.leadCutInRisk.yRel = y_rel
  instance.sm.radar_state.leadOne.yRel = y_rel
  instance._update_radar_lane_intrusion(SimpleNamespace(vEgo=20.0, leftBlinker=left_blinker, rightBlinker=right_blinker))


def crossing(instance):
  for now in (1.0, 1.05, 1.10, 1.20):
    update(instance, now, 3.2)
  for now in (1.30, 1.35, 1.45):
    update(instance, now, 2.2)


def test_selected_longitudinal_cutin_adds_warning_event(monkeypatch):
  instance = make_instance(cutin_risk())
  logged = {}
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda name, **values: logged.update(name=name, **values))

  crossing(instance)

  assert instance.events_sp.names == [custom.OnroadEventSP.EventName.radarLaneIntrusion]
  assert logged["name"] == "radarCutInWarning"
  assert logged["trackId"] == 49
  assert logged["predecelAccel"] <= 0.0


def test_unselected_cutin_candidate_does_not_warn(monkeypatch):
  instance = make_instance(cutin_risk(), selected=False)
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda *args, **kwargs: None)

  crossing(instance)

  assert instance.events_sp.names == []


def test_low_confidence_selected_candidate_does_not_warn(monkeypatch):
  instance = make_instance(cutin_risk())
  instance.sm.radar_state.leadOne.modelProb = 0.20
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda *args, **kwargs: None)

  crossing(instance)

  assert instance.events_sp.names == []


def test_selected_nonclosing_cutin_still_warns(monkeypatch):
  instance = make_instance(cutin_risk(vRel=1.0))
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda *args, **kwargs: None)

  crossing(instance)

  assert instance.events_sp.names == [custom.OnroadEventSP.EventName.radarLaneIntrusion]


def test_continuous_cutin_warns_only_on_rising_edge(monkeypatch):
  instance = make_instance(cutin_risk())
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda *args, **kwargs: None)

  crossing(instance)
  update(instance, 1.50, 1.0)
  update(instance, 1.65, 1.0)

  assert instance.events_sp.names == [custom.OnroadEventSP.EventName.radarLaneIntrusion]


def test_existing_lead_does_not_warn_on_risk_reappearance(monkeypatch):
  instance = make_instance(cutin_risk())
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda *args, **kwargs: None)
  for i in range(100):
    update(instance, 1.0 + i * 0.05, 0.1 if i % 2 else -0.1)
  assert instance.events_sp.names == []


def test_invalid_telemetry_clears_crossing_history(monkeypatch):
  instance = make_instance(cutin_risk())
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda *args, **kwargs: None)
  for now in (1.0, 1.05, 1.10, 1.20):
    update(instance, now, 3.2)
  instance.sm.valid['radarState'] = False
  update(instance, 1.30, 2.2)
  instance.sm.valid['radarState'] = True
  update(instance, 1.35, 2.2)
  update(instance, 1.50, 2.2)
  assert instance.events_sp.names == []


def test_different_car_crossing_is_not_lost_to_global_cooldown(monkeypatch):
  instance = make_instance(cutin_risk())
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda *args, **kwargs: None)
  crossing(instance)
  instance.sm.radar_state.leadCutInRisk.radarTrackId = 50
  instance.sm.radar_state.leadOne.radarTrackId = 50
  for now in (1.60, 1.65, 1.70, 1.80):
    update(instance, now, 3.2)
  for now in (1.90, 1.95, 2.05):
    update(instance, now, 2.2)
  assert instance.events_sp.names == [custom.OnroadEventSP.EventName.radarLaneIntrusion] * 2


def test_does_not_change_other_brands_warning_behavior(monkeypatch):
  instance = make_instance(cutin_risk())
  instance.CP.brand = 'toyota'
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda *args, **kwargs: None)
  crossing(instance)
  assert instance.events_sp.names == []


def test_manual_lane_change_and_settling_do_not_warn(monkeypatch):
  instance = make_instance(cutin_risk())
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda *args, **kwargs: None)
  for now in (1.0, 1.05, 1.10, 1.20):
    update(instance, now, 3.2, right_blinker=True)
  for now in (1.30, 1.35, 1.45):
    update(instance, now, 2.2)
  assert instance.events_sp.names == []


def test_stale_model_clears_crossing_history(monkeypatch):
  instance = make_instance(cutin_risk())
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda *args, **kwargs: None)
  for now in (1.0, 1.05, 1.10, 1.20):
    update(instance, now, 3.2)
  instance.sm.logMonoTime['radarState'] = 1_500_000_000
  instance._update_radar_lane_intrusion(SimpleNamespace(vEgo=20.0, leftBlinker=False, rightBlinker=False))
  for now in (1.55, 1.60, 1.75):
    update(instance, now, 2.2)
  assert instance.events_sp.names == []


def test_hazard_lights_do_not_disable_cutin_warning(monkeypatch):
  instance = make_instance(cutin_risk())
  monkeypatch.setattr(selfdrived.cloudlog, "event", lambda *args, **kwargs: None)
  for now in (1.0, 1.05, 1.10, 1.20):
    update(instance, now, 3.2, left_blinker=True, right_blinker=True)
  for now in (1.30, 1.35, 1.45):
    update(instance, now, 2.2, left_blinker=True, right_blinker=True)
  assert instance.events_sp.names == [custom.OnroadEventSP.EventName.radarLaneIntrusion]
