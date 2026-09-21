from types import SimpleNamespace

from openpilot.selfdrive.modeld import lane_change_input_monitor as monitor_module


def test_logs_each_new_signal_once(monkeypatch):
  events = []
  monkeypatch.setattr(monitor_module.cloudlog, 'event', lambda name, **data: events.append((name, data)))
  monitor = monitor_module.LaneChangeInputMonitor()
  car_state = SimpleNamespace(leftBlinker=False, rightBlinker=False, vEgo=20.0)
  navdy_state = SimpleNamespace(navdyLeftBlinker=False, navdyRightBlinker=False)
  class SubMasterStub(dict):
    logMonoTime = {'carState': 1, 'carStateSP': 2, 'carControl': 3}

  sm = SubMasterStub(carState=car_state, carStateSP=navdy_state, carControl=SimpleNamespace(latActive=True))
  desire_helper = SimpleNamespace(alc=SimpleNamespace(lane_change_set_timer=1), lane_change_state=0)

  monitor.update(sm, desire_helper)
  navdy_state.navdyLeftBlinker = True
  monitor.update(sm, desire_helper)
  monitor.update(sm, desire_helper)
  car_state.leftBlinker = True
  monitor.update(sm, desire_helper)

  assert [data['source'] for _, data in events] == ['carStateSP', 'carState']
  assert events[0][1]['car_signal'] == 0
  assert events[0][1]['navdy_signal'] == 1
  assert events[1][1]['car_signal'] == 1


def test_stale_car_state_uses_fresh_same_card_signal_without_arming_controls():
  now = 10_000_000_000
  car_state = SimpleNamespace(leftBlinker=False, rightBlinker=False)
  navdy_state = SimpleNamespace(navdyVEgo=19.0, navdyLeftBlinker=False, navdyRightBlinker=True,
                                navdyLeftBlindspot=False, navdyRightBlindspot=False)
  class SubMasterStub(dict):
    logMonoTime = {'carState': now - 3_200_000_000, 'carStateSP': now - 30_000_000}
    valid = {'carState': True, 'carStateSP': True}

  sm = SubMasterStub(carState=car_state, carStateSP=navdy_state)
  selected, stale = monitor_module.lane_change_car_state(sm, now)
  assert stale
  assert selected.rightBlinker and selected.vEgo == 19.0
  assert selected.brakePressed and not selected.steeringPressed

  sm.logMonoTime = {'carState': now - 20_000_000, 'carStateSP': now - 30_000_000}
  selected, stale = monitor_module.lane_change_car_state(sm, now)
  assert not stale and selected is car_state


def test_stale_car_state_without_fresh_backup_has_no_change_signal():
  now = 10_000_000_000
  class SubMasterStub(dict):
    logMonoTime = {'carState': now - 3_200_000_000, 'carStateSP': now - 2_000_000_000}
    valid = {'carState': True, 'carStateSP': True}

  sm = SubMasterStub(carState=SimpleNamespace(rightBlinker=True), carStateSP=SimpleNamespace(navdyRightBlinker=True))
  selected, stale = monitor_module.lane_change_car_state(sm, now)
  assert stale and not selected.rightBlinker and selected.vEgo == 0.0
