"""Offline Traverse control-chain tests. CAN output is collected, never transmitted."""

from types import SimpleNamespace

import pytest

from cereal import car, custom
from opendbc.can.dbc import DBC
from opendbc.can.parser import get_raw_value
from opendbc.car import gen_empty_fingerprint
from opendbc.car.gm.carcontroller import GM_AUTO_HOLD_BRAKE
from opendbc.car.gm.interface import CarInterface
from opendbc.car.gm.values import CAR, CanBus, CruiseButtons
from openpilot.selfdrive.controls.lib import longcontrol
from openpilot.selfdrive.controls.lib.longcontrol import LongControl, LongCtrlState


class TraverseControlChain:
  """Supply vehicle observations to real LongControl, interface hold and CAN packing."""

  def __init__(self, monkeypatch, tmp_path):
    fingerprint = gen_empty_fingerprint()
    self.cp = CarInterface.get_params(CAR.CHEVROLET_TRAVERSE, fingerprint, [], True, False, False)
    self.cp_sp = CarInterface.get_params_sp(self.cp, CAR.CHEVROLET_TRAVERSE, fingerprint, [], True, False, False)
    self.ci = CarInterface(self.cp, self.cp_sp)
    self.now_ns = 10_000_000_000
    monkeypatch.setattr(longcontrol, "monotonic", lambda: self.now_ns / 1e9)
    # Preserve the real learner while isolating its optional profile from user data.
    learner = longcontrol.LongitudinalResponseLearner
    monkeypatch.setattr(longcontrol, "LongitudinalResponseLearner", lambda delay, enabled:
                        learner(delay, str(tmp_path / "response.json"), enabled=enabled))
    self.loc = LongControl(self.cp, self.cp_sp)
    self.cs = self.ci.CS
    self.cs.out = car.CarState.new_message()
    self.cs.out.canValid = True
    self.cs.out.standstill = True
    self.cs.out.gearShifter = car.CarState.GearShifter.drive
    self.cs.out.cruiseState.enabled = True
    self.cs.out.cruiseState.standstill = True
    self.cs.cruise_buttons = CruiseButtons.UNPRESS
    self.cs.buttons_counter = 0
    self.cs.buttons_ts_nanos = self.now_ns - 5_000_000
    self.cs.pscm_status = dict.fromkeys((
      "HandsOffSWDetectionMode", "HandsOffSWlDetectionStatus", "LKATorqueDeliveredStatus",
      "LKADriverAppldTrq", "LKATorqueDelivered", "LKATotalTorqueDelivered", "RollingCounter", "PSCMStatusChecksum",
    ), 0)
    self.plan = SimpleNamespace(shouldStop=True, aTarget=-0.5, speeds=[0.0] * 33, jTargetNow=0.0)
    self.radar = SimpleNamespace(leadOne=SimpleNamespace(status=True, dRel=6.0, vRel=0.0, vLead=0.0),
                                 leadCutInRisk=None)
    self.custom_control = custom.CarControlSP.new_message().as_reader()
    self.button_signals = DBC("gm_global_a_powertrain_generated").addr_to_msg[0x1E1].sigs
    self.brake_signals = DBC("gm_global_a_chassis").addr_to_msg[0x315].sigs
    self.trace = []

  def step(self, manual_resume=False):
    # A fresh original button frame every 30 ms, observed 5 ms after reception.
    if self.ci.CC.frame % 3 == 0:
      self.cs.buttons_counter = (self.cs.buttons_counter + 1) % 4
      self.cs.buttons_ts_nanos = self.now_ns - 5_000_000
    control = car.CarControl.new_message()
    control.enabled = True
    control.longActive = True
    control.actuators.accel = float(self.loc.update(True, self.cs.out, self.plan, (-3.5, 2.0), self.radar,
                                                   manual_resume=manual_resume))
    # Match controlsd: publish the state that produced this cycle's acceleration.
    control.actuators.longControlState = self.loc.long_control_state
    control.cruiseControl.resume = self.loc.get_resume_request(True, True, self.cs.out, self.plan)
    self.ci.update_auto_hold(control)
    _, sends = self.ci.CC.update(control.as_reader(), self.custom_control, self.cs, self.now_ns)
    entry = SimpleNamespace(time_ns=self.now_ns, state=self.loc.long_control_state,
                            accel=control.actuators.accel, resume=control.cruiseControl.resume,
                            hold=self.cs.autoHoldActivated, sends=sends)
    self.trace.append(entry)
    self.now_ns += 10_000_000
    return entry

  def run(self, frames):
    return [self.step() for _ in range(frames)]

  def depart(self):
    self.plan.shouldStop = False
    self.plan.aTarget = 0.35
    self.plan.speeds = [3.0] * 33
    self.radar.leadOne.dRel = 7.0
    self.radar.leadOne.vRel = 0.8
    self.radar.leadOne.vLead = 0.8

  def buttons(self):
    return [(entry.time_ns, msg[2], get_raw_value(msg[1], self.button_signals["ACCButtons"]), msg[1])
            for entry in self.trace for msg in entry.sends if msg[0] == 0x1E1]

  def brakes(self, entries=None):
    signal = self.brake_signals["FrictionBrakeCmd"]
    commands = []
    for entry in (self.trace if entries is None else entries):
      for msg in entry.sends:
        if msg[0] == 0x315:
          raw = get_raw_value(msg[1], signal)
          signed = raw - (1 << signal.size) if raw & (1 << (signal.size - 1)) else raw
          commands.append((entry.time_ns, -signed))
    return commands


@pytest.fixture
def chain(monkeypatch, tmp_path):
  return TraverseControlChain(monkeypatch, tmp_path)


def test_hold_releases_before_four_fresh_resume_frames(chain):
  chain.run(110)
  assert chain.loc.long_control_state == LongCtrlState.stopping
  assert any(brake == GM_AUTO_HOLD_BRAKE for _, brake in chain.brakes())
  assert chain.buttons() == []

  departure_time = chain.now_ns
  chain.depart()
  chain.run(80)
  buttons = chain.buttons()
  first_resume = next(time for time, _, button, _ in buttons if button == CruiseButtons.RES_ACCEL)
  assert any(departure_time <= time < first_resume and brake == 0 for time, brake in chain.brakes())
  assert all(brake == 0 for time, brake in chain.brakes() if first_resume <= time)
  for bus in (CanBus.POWERTRAIN, CanBus.CAMERA):
    bus_buttons = [(time, button, payload) for time, msg_bus, button, payload in buttons if msg_bus == bus]
    assert [button for _, button, _ in bus_buttons] == [CruiseButtons.RES_ACCEL] * 4 + [CruiseButtons.UNPRESS]
    assert [b[0] - a[0] for a, b in zip(bus_buttons[:-1], bus_buttons[1:], strict=True)] == [30_000_000] * 4
  assert [(t, payload) for t, bus, _, payload in buttons if bus == CanBus.POWERTRAIN] == \
         [(t, payload) for t, bus, _, payload in buttons if bus == CanBus.CAMERA]
  # Sending correctly packed requests is not vehicle acceptance.
  assert chain.cs.out.cruiseState.standstill
  assert not chain.loc.sng_resume_succeeded


def test_creep_without_pcm_ack_times_out_into_regular_stopping(chain):
  chain.run(110)
  chain.depart()
  chain.run(60)
  assert chain.loc.sng_resume_ready
  chain.cs.out.standstill = False
  chain.cs.out.vEgo = chain.cs.out.vEgoRaw = 0.6
  # Keep PCM standstill latched even though the vehicle has begun to creep.
  chain.run(220)
  assert chain.loc.sng_resume_failed
  assert not chain.loc.sng_resume_succeeded
  assert chain.loc.long_control_state == LongCtrlState.stopping
  failed_frames = chain.run(40)
  assert all(entry.state == LongCtrlState.stopping and entry.accel < 0 and not entry.resume for entry in failed_frames)
  assert all(not entry.hold for entry in failed_frames)
  failed_brakes = chain.brakes(failed_frames)
  assert failed_brakes
  assert all(0 < brake < GM_AUTO_HOLD_BRAKE for _, brake in failed_brakes)
  assert len([b for b in chain.buttons() if b[1] == CanBus.POWERTRAIN and b[2] == CruiseButtons.RES_ACCEL]) == 4


def test_valid_pcm_ack_at_zero_prevents_timeout_failure(chain):
  chain.run(110)
  chain.depart()
  chain.run(60)
  # This simulates a received ACTIVE state; CAN output itself never supplies ACK.
  chain.cs.out.cruiseState.standstill = False
  chain.run(220)
  assert chain.cs.out.standstill and chain.cs.out.vEgo == 0
  assert chain.loc.sng_resume_succeeded
  assert not chain.loc.sng_resume_failed
  assert not chain.trace[-1].hold


def test_screen_request_without_lead_retries_only_after_another_tap(chain):
  chain.radar.leadOne.status = False
  chain.run(110)
  chain.plan.shouldStop = False
  chain.run(80)
  assert chain.buttons() == []
  assert chain.trace[-1].hold
  chain.step(manual_resume=True)
  chain.run(80)
  assert chain.loc.sng_ui_resume and chain.loc.sng_resume_ready
  assert len([b for b in chain.buttons() if b[1] == CanBus.CAMERA and b[2] == CruiseButtons.RES_ACCEL]) == 4
  chain.run(300)
  assert chain.loc.sng_resume_failed
  assert chain.trace[-1].hold
  assert len([b for b in chain.buttons() if b[1] == CanBus.CAMERA and b[2] == CruiseButtons.RES_ACCEL]) == 4
  chain.step(manual_resume=True)
  chain.run(80)
  assert not chain.loc.sng_resume_failed
  assert len([b for b in chain.buttons() if b[1] == CanBus.CAMERA and b[2] == CruiseButtons.RES_ACCEL]) == 8
  chain.cs.out.cruiseState.standstill = False
  chain.run(30)
  assert chain.loc.sng_resume_succeeded


@pytest.mark.parametrize("veto", ["planner_stop", "moving", "gas", "brake", "pcm_off", "invalid_can"])
def test_screen_request_preserves_control_vetoes(chain, veto):
  chain.radar.leadOne.status = False
  chain.run(110)
  chain.plan.shouldStop = False
  if veto == "planner_stop":
    chain.plan.shouldStop = True
  elif veto == "moving":
    chain.cs.out.vEgo = 0.2
    chain.cs.out.standstill = False
  elif veto == "gas":
    chain.cs.out.gasPressed = True
  elif veto == "brake":
    chain.cs.out.brakePressed = True
  elif veto == "pcm_off":
    chain.cs.out.cruiseState.enabled = False
  else:
    chain.cs.out.canValid = False
  chain.step(manual_resume=True)
  chain.run(30)
  assert not chain.loc.sng_ui_resume
  assert chain.buttons() == []


def test_screen_resume_stops_if_planner_demands_a_stop(chain):
  chain.run(110)
  chain.radar.leadOne.status = False
  chain.plan.shouldStop = False
  chain.step(manual_resume=True)
  chain.run(30)
  chain.plan.shouldStop = True
  entry = chain.step()
  assert chain.loc.sng_resume_failed
  assert entry.state == LongCtrlState.stopping
  assert not entry.resume
