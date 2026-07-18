from types import SimpleNamespace

from cereal import car

from openpilot.sunnypilot.selfdrive.controls.lib.e2e_alerts_helper import (
  DT_MDL,
  E2EAlertsHelper,
  E2EStates,
)


class FakeParams:
  @staticmethod
  def get_bool(_key):
    return True


class FakeEvents:
  def __init__(self):
    self.names = []

  def add(self, name):
    self.names.append(name)


def make_helper():
  helper = E2EAlertsHelper()
  helper._params = FakeParams()
  helper.green_light_alert_enabled = True
  helper.lead_depart_alert_enabled = True
  return helper


def make_sm(*, gear=car.CarState.GearShifter.drive, model_distance=10.0,
            lead_status=False, lead_distance=0.0, lead_speed=0.0,
            lead_track_id=-1, controls_enabled=True):
  return {
    "carState": SimpleNamespace(
      standstill=True,
      vEgo=0.0,
      gasPressed=False,
      gearShifter=gear,
    ),
    "carControl": SimpleNamespace(enabled=controls_enabled),
    "modelV2": SimpleNamespace(position=SimpleNamespace(x=[model_distance])),
    "radarState": SimpleNamespace(leadOne=SimpleNamespace(
      status=lead_status,
      dRel=lead_distance,
      vLead=lead_speed,
      radarTrackId=lead_track_id,
    )),
  }


def run_frames(helper, sm, seconds):
  events = FakeEvents()
  alerts = []
  for _ in range(int(seconds / DT_MDL) + 1):
    helper.update(sm, events)
    alerts.append((helper.green_light_alert, helper.lead_depart_alert))
  return events, alerts


def test_green_light_requires_stopped_model_then_opens_while_in_drive():
  helper = make_helper()
  sm = make_sm(model_distance=10.0, controls_enabled=True)
  run_frames(helper, sm, 0.7)

  sm["modelV2"].position.x = [60.0]
  _, alerts = run_frames(helper, sm, 0.5)

  assert any(green for green, _lead in alerts)


def test_open_path_without_prior_stopped_model_does_not_alert():
  helper = make_helper()
  _, alerts = run_frames(helper, make_sm(model_distance=60.0), 1.5)

  assert not any(green for green, _lead in alerts)


def test_lead_can_arm_after_stopping_and_alert_while_controls_enabled():
  helper = make_helper()
  sm = make_sm(model_distance=60.0, controls_enabled=True)
  run_frames(helper, sm, 0.3)

  sm["radarState"].leadOne = SimpleNamespace(
    status=True, dRel=12.0, vLead=0.0, radarTrackId=4)
  run_frames(helper, sm, 0.9)

  sm["radarState"].leadOne.dRel = 13.5
  sm["radarState"].leadOne.vLead = 1.2
  _, alerts = run_frames(helper, sm, 0.5)

  assert any(lead for _green, lead in alerts)


def test_reverse_resets_both_alert_state_machines():
  helper = make_helper()
  reverse = car.CarState.GearShifter.reverse
  sm = make_sm(gear=reverse, model_distance=10.0)
  run_frames(helper, sm, 1.0)

  sm["modelV2"].position.x = [60.0]
  _, green_alerts = run_frames(helper, sm, 0.6)
  assert not any(green for green, _lead in green_alerts)

  sm["radarState"].leadOne = SimpleNamespace(
    status=True, dRel=8.0, vLead=0.0, radarTrackId=7)
  run_frames(helper, sm, 1.0)
  sm["radarState"].leadOne.dRel = 10.0
  sm["radarState"].leadOne.vLead = 2.0
  _, lead_alerts = run_frames(helper, sm, 0.6)
  assert not any(lead for _green, lead in lead_alerts)


def test_track_change_does_not_look_like_lead_departure():
  helper = make_helper()
  sm = make_sm(lead_status=True, lead_distance=12.0, lead_track_id=4)
  run_frames(helper, sm, 0.9)

  sm["radarState"].leadOne = SimpleNamespace(
    status=True, dRel=22.0, vLead=8.0, radarTrackId=5)
  _, alerts = run_frames(helper, sm, 0.5)

  assert not any(lead for _green, lead in alerts)


def test_disallowed_trigger_does_not_leak_one_frame_alert():
  state, alert = E2EAlertsHelper.update_state_machine(
    E2EStates.ARMED, enabled=True, allowed=False, triggered=True)

  assert state == E2EStates.INACTIVE
  assert not alert
