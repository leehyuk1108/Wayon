import json
from pathlib import Path

import pytest

from cereal import car, custom
from opendbc.can import CANPacker
from opendbc.can.dbc import DBC
from opendbc.can.parser import get_raw_value
from opendbc.car import Bus, gen_empty_fingerprint
from opendbc.car.gm import gmcan
from opendbc.car.gm.interface import CarInterface
from opendbc.car.gm.values import CAR, CanBus, CruiseButtons


BASE_NS = 10_000_000_000
LongCtrlState = car.CarControl.Actuators.LongControlState
BUTTON_DBC = DBC("gm_global_a_powertrain_generated").addr_to_msg[0x1E1]
BRAKE_DBC = DBC("gm_global_a_chassis").name_to_msg["EBCMFrictionBrakeCmd"]


def make_interface(candidate=CAR.CHEVROLET_TRAVERSE):
  fingerprint = gen_empty_fingerprint()
  CP = CarInterface.get_params(candidate, fingerprint, [], True, False, False)
  CP_SP = CarInterface.get_params_sp(CP, candidate, fingerprint, [], True, False, False)
  return CarInterface(CP, CP_SP)


def decode_buttons(sends):
  messages = [msg for msg in sends if msg[0] == 0x1E1]
  if messages:
    assert len(messages) == 2
    assert {msg[2] for msg in messages} == {CanBus.POWERTRAIN, CanBus.CAMERA}
    assert messages[0][1] == messages[1][1]
  return [(get_raw_value(msg[1], BUTTON_DBC.sigs["ACCButtons"]),
           get_raw_value(msg[1], BUTTON_DBC.sigs["RollingCounter"])) for msg in messages if msg[2] == CanBus.CAMERA]


@pytest.fixture
def resume():
  CI = make_interface()
  CS = CI.CS
  # Initialize the ordinary parser-derived controller inputs, then provide the
  # stopped, engaged vehicle state used by these scheduling tests.
  CS.update(CS.get_can_parsers(CI.CP, CI.CP_SP))
  CS.out = car.CarState.new_message()
  CS.out.canValid = True
  CS.out.standstill = True
  CS.out.gearShifter = car.CarState.GearShifter.drive
  CS.out.cruiseState.enabled = True
  CS.out.cruiseState.standstill = True
  CS.cruise_buttons = CruiseButtons.UNPRESS
  CS.buttons_counter = 2
  CS.buttons_ts_nanos = BASE_NS - 23_584_000
  CC = car.CarControl.new_message()
  CC.enabled = True
  CC.longActive = True
  CC.cruiseControl.resume = True
  CC.actuators.longControlState = LongCtrlState.starting
  CC.actuators.accel = 0.35
  # Scheduling unit tests start after a zero brake command. The full-controller
  # test below verifies that this evidence can only be established by output.
  CI.CC.sng_brake_release_ns = BASE_NS - 1_000_000
  return CI, CS, CC


def tick(resume, now_ms, source_ms=None, counter=None):
  CI, CS, CC = resume
  if source_ms is not None:
    CS.buttons_ts_nanos = BASE_NS + round(source_ms * 1e6)
  if counter is not None:
    CS.buttons_counter = counter
  CI.CC.frame = round(now_ms / 10)
  sends = []
  CI.CC.update_sng_resume(CC, CS, CC.actuators, sends, BASE_NS + round(now_ms * 1e6))
  return decode_buttons(sends)


def collect_trace(resume, originals):
  outputs = []
  for now_ms in range(0, 181, 10):
    original = max((x for x in originals if x[0] <= now_ms), key=lambda x: x[0])
    for button, counter in tick(resume, now_ms, *original):
      outputs.append((now_ms, button, counter))
  return outputs


def test_recorded_phase_does_not_reuse_prearm_frame_or_compress_first_res(resume):
  fixture = json.loads((Path(__file__).parent / "fixtures/traverse_resume_49_7.json").read_text())
  original = [(x["offset_ms"], x["counter"]) for x in fixture["original_frames"]]
  outputs = collect_trace(resume, original)
  assert outputs == [(10, 2, 0), (40, 2, 1), (70, 2, 2), (100, 2, 3), (130, 1, 0)]
  assert resume[0].CC.sng_resume_attempted
  assert resume[0].CC.sng_resume_frame == -1


@pytest.mark.parametrize("initial_age_ms", [1, 5, 10, 19, 23.584, 29])
def test_original_phase_does_not_change_press_length_or_counter_continuity(resume, initial_age_ms):
  originals = [(30 * i - initial_age_ms, (2 + i) % 4) for i in range(8)]
  outputs = collect_trace(resume, originals)
  presses = [(t, counter) for t, button, counter in outputs if button == CruiseButtons.RES_ACCEL]
  assert len(presses) == 4
  assert presses[0][0] > 0
  assert all(b[0] - a[0] >= 25 for a, b in zip(presses, presses[1:], strict=False))
  assert [counter for _, counter in presses] == [0, 1, 2, 3]
  assert outputs[-1][1:] == (CruiseButtons.UNPRESS, 0)


def start_one_press(resume):
  assert tick(resume, 0) == []
  assert tick(resume, 10, 6.879, 3) == [(CruiseButtons.RES_ACCEL, 0)]


def test_early_new_frame_waits_without_becoming_a_twenty_ms_burst(resume):
  start_one_press(resume)
  assert tick(resume, 30, 26.879, 0) == []
  assert tick(resume, 40) == [(CruiseButtons.RES_ACCEL, 1)]
  assert tick(resume, 50) == []


def test_next_counter_while_waiting_aborts_instead_of_catching_up(resume):
  start_one_press(resume)
  assert tick(resume, 30, 26.879, 0) == []
  assert tick(resume, 40, 36.879, 1) == [(CruiseButtons.UNPRESS, 1)]
  assert resume[0].CC.sng_resume_frame == -1


@pytest.mark.parametrize("now, source, counter", [
  (40, 36.8, 1),  # skipped counter
  (40, 36.8, 3),  # repeated counter with a new timestamp
  (40, 6.879, 0),  # counter changed without a new receive timestamp
  (40, 5.0, 0),  # timestamp moved backwards
  (40, 45.0, 0),  # future timestamp
  (50, 26.0, 0),  # a new frame arrived too late to use
  (140, 126.879, 3),  # complete rolling-counter wrap does not conceal missing frames
])
def test_invalid_source_aborts_and_does_not_retry_the_same_stop(resume, now, source, counter):
  start_one_press(resume)
  assert tick(resume, now, source, counter) == [(CruiseButtons.UNPRESS, 1)]
  resume[2].cruiseControl.resume = False
  assert tick(resume, now + 10, now + 6, (counter + 1) % 4) == []
  resume[2].cruiseControl.resume = True
  assert tick(resume, now + 40, now + 36, (counter + 2) % 4) == []
  assert resume[0].CC.sng_resume_attempted


def test_missing_source_aborts_even_without_a_counter_change(resume):
  start_one_press(resume)
  assert tick(resume, 60) == [(CruiseButtons.UNPRESS, 1)]
  assert tick(resume, 70) == []


def test_withdrawn_request_at_stop_allows_a_fresh_explicit_retry(resume):
  start_one_press(resume)
  assert tick(resume, 60) == [(CruiseButtons.UNPRESS, 1)]
  assert resume[0].CC.sng_resume_attempted

  CC = resume[2]
  CC.cruiseControl.resume = False
  CC.actuators.longControlState = LongCtrlState.stopping
  assert tick(resume, 70) == []
  assert not resume[0].CC.sng_resume_attempted

  # The caller has accepted a new explicit request. Its current original frame
  # is only an arm snapshot; it cannot bootstrap another RES immediately.
  CC.cruiseControl.resume = True
  CC.actuators.longControlState = LongCtrlState.starting
  assert tick(resume, 80, 76.824, 1) == []
  assert tick(resume, 90) == []
  assert tick(resume, 110, 106.853, 2) == [(CruiseButtons.RES_ACCEL, 3)]
  assert tick(resume, 140, 136.853, 3) == [(CruiseButtons.RES_ACCEL, 0)]
  assert tick(resume, 170, 166.853, 0) == [(CruiseButtons.RES_ACCEL, 1)]
  assert tick(resume, 200, 196.853, 1) == [(CruiseButtons.RES_ACCEL, 2)]
  assert tick(resume, 230, 226.853, 2) == [(CruiseButtons.UNPRESS, 3)]
  assert resume[0].CC.sng_resume_attempted


@pytest.mark.parametrize("state, resume_requested", [
  (LongCtrlState.starting, False),
  (LongCtrlState.pid, False),
  (LongCtrlState.stopping, True),
])
def test_retry_requires_both_request_withdrawal_and_stopping(resume, state, resume_requested):
  start_one_press(resume)
  assert tick(resume, 60) == [(CruiseButtons.UNPRESS, 1)]
  CC = resume[2]
  CC.cruiseControl.resume = resume_requested
  CC.actuators.longControlState = state
  assert tick(resume, 70) == []
  assert resume[0].CC.sng_resume_attempted

  CC.cruiseControl.resume = True
  CC.actuators.longControlState = LongCtrlState.starting
  assert tick(resume, 80, 76.824, 1) == []
  assert tick(resume, 110, 106.853, 2) == []
  assert resume[0].CC.sng_resume_attempted


def test_stale_source_cannot_arm(resume):
  assert tick(resume, 0, -60, 2) == []
  assert tick(resume, 10, 6.879, 3) == []
  assert resume[0].CC.sng_resume_attempted


@pytest.mark.parametrize("field,value", [
  ("brakePressed", True), ("gasPressed", True), ("regenBraking", True),
  ("parkingBrake", True), ("canValid", False), ("accFaulted", True),
  ("gearShifter", car.CarState.GearShifter.reverse),
])
def test_vehicle_overrides_and_invalid_state_end_the_burst(resume, field, value):
  start_one_press(resume)
  setattr(resume[1].out, field, value)
  assert tick(resume, 20) == [(CruiseButtons.UNPRESS, 1)]
  assert resume[0].CC.sng_resume_frame == -1


@pytest.mark.parametrize("change", ["disabled", "long_inactive", "request_withdrawn", "state_stopping", "pcm_inactive", "pcm_ack"])
def test_control_and_pcm_transitions_end_the_burst(resume, change):
  start_one_press(resume)
  _, CS, CC = resume
  if change == "disabled":
    CC.enabled = False
  elif change == "long_inactive":
    CC.longActive = False
  elif change == "request_withdrawn":
    CC.cruiseControl.resume = False
  elif change == "state_stopping":
    CC.actuators.longControlState = LongCtrlState.stopping
  elif change == "pcm_inactive":
    CS.out.cruiseState.enabled = False
  else:
    CS.out.cruiseState.standstill = False
  assert tick(resume, 20) == [(CruiseButtons.UNPRESS, 1)]
  assert resume[0].CC.sng_resume_frame == -1


@pytest.mark.parametrize("button", [CruiseButtons.RES_ACCEL, CruiseButtons.DECEL_SET, CruiseButtons.MAIN])
def test_manual_button_is_not_overlaid_with_synthetic_release_or_retried(resume, button):
  start_one_press(resume)
  resume[1].cruise_buttons = button
  assert tick(resume, 40, 36.824, 0) == []
  assert resume[0].CC.sng_resume_frame == -1
  resume[1].cruise_buttons = CruiseButtons.UNPRESS
  resume[2].cruiseControl.resume = False
  assert tick(resume, 50) == []
  resume[2].cruiseControl.resume = True
  assert tick(resume, 70, 66.853, 1) == []


def test_cancel_relays_next_counter_without_waiting_for_timing(resume):
  start_one_press(resume)
  resume[1].cruise_buttons = CruiseButtons.CANCEL
  assert tick(resume, 11) == [(CruiseButtons.CANCEL, 1)]
  assert tick(resume, 12) == []


def test_pending_attempt_allows_bounded_creep_and_stops_at_limit(resume):
  start_one_press(resume)
  resume[1].out.standstill = False
  resume[1].out.vEgo = 0.3
  assert tick(resume, 40, 36.824, 0) == [(CruiseButtons.RES_ACCEL, 1)]
  resume[1].out.vEgo = 1.5
  assert tick(resume, 50) == [(CruiseButtons.UNPRESS, 2)]


def test_brake_reapplication_aborts(resume):
  start_one_press(resume)
  resume[0].CC.apply_brake = 400
  assert tick(resume, 20) == [(CruiseButtons.UNPRESS, 1)]


def test_full_controller_emits_brake_release_before_arming_then_waits_for_original(resume):
  CI, CS, CC = resume
  CI.CC.apply_brake = 400
  CI.CC.sng_brake_release_ns = 0
  CC_SP = custom.CarControlSP.new_message()
  CI.CC.frame = 0
  _, sends = CI.CC.update(CC.as_reader(), CC_SP.as_reader(), CS, BASE_NS)
  assert decode_buttons(sends) == []
  brakes = [msg for msg in sends if msg[0] == 0x315]
  assert len(brakes) == 1
  assert get_raw_value(brakes[0][1], BRAKE_DBC.sigs["FrictionBrakeCmd"]) == 0
  assert CI.CC.sng_brake_release_ns == BASE_NS
  assert CI.CC.sng_resume_frame == -1
  assert tick(resume, 10, 6.879, 3) == []  # Arm after release; this original is the snapshot.
  assert tick(resume, 20) == []
  assert tick(resume, 40, 36.824, 0) == [(CruiseButtons.RES_ACCEL, 1)]


def test_acknowledged_low_speed_motion_allows_the_next_stop_attempt(resume):
  start_one_press(resume)
  CS = resume[1]
  CS.out.vEgo = 0.3
  CS.out.cruiseState.standstill = False
  assert tick(resume, 20) == [(CruiseButtons.UNPRESS, 1)]
  assert not resume[0].CC.sng_resume_attempted
  CS.out.vEgo = 0.0
  CS.out.cruiseState.standstill = True
  assert tick(resume, 40, 36.824, 0) == []
  assert tick(resume, 70, 66.853, 1) == [(CruiseButtons.RES_ACCEL, 2)]


def test_creep_alone_does_not_reset_attempt_even_above_the_resume_limit(resume):
  start_one_press(resume)
  resume[1].out.vEgo = 1.6
  assert tick(resume, 40, 36.824, 0) == [(CruiseButtons.UNPRESS, 1)]
  assert resume[0].CC.sng_resume_attempted
  resume[1].out.vEgo = 0.0
  resume[2].cruiseControl.resume = False
  assert tick(resume, 50) == []
  resume[2].cruiseControl.resume = True
  assert tick(resume, 70, 66.853, 1) == []


@pytest.mark.parametrize("raw_state", range(8))
def test_traverse_accepts_only_known_pcm_active_states(raw_state):
  CI = make_interface()
  parsers = CI.CS.get_can_parsers(CI.CP, CI.CP_SP)
  CI.CS.update(parsers)
  packer = CANPacker("gm_global_a_powertrain_generated")
  msg = packer.make_can_msg("AcceleratorPedal2", 0, {"CruiseState": raw_state})
  parsers[Bus.pt].update([(BASE_NS, [msg])])
  state, _ = CI.CS.update(parsers)
  assert state.cruiseState.enabled == (raw_state in (1, 4))
  assert state.cruiseState.standstill == (raw_state == 4)
  assert state.accFaulted == (raw_state == 3)


def test_other_gm_pcm_enabled_behavior_is_unchanged():
  CI = make_interface(CAR.CHEVROLET_BOLT_EUV)
  parsers = CI.CS.get_can_parsers(CI.CP, CI.CP_SP)
  CI.CS.update(parsers)
  packer = CANPacker("gm_global_a_powertrain_generated")
  parsers[Bus.pt].update([(BASE_NS, [packer.make_can_msg("AcceleratorPedal2", 0, {"CruiseState": 3})])])
  state, _ = CI.CS.update(parsers)
  assert state.cruiseState.enabled
  assert state.accFaulted


def test_button_timestamp_tracks_original_can_receives_not_state_updates():
  CI = make_interface()
  parsers = CI.CS.get_can_parsers(CI.CP, CI.CP_SP)
  CI.CS.update(parsers)
  packer = CANPacker("gm_global_a_powertrain_generated")
  parsers[Bus.pt].update([(BASE_NS, [gmcan.create_buttons(packer, 0, 3, CruiseButtons.UNPRESS)])])
  CI.CS.update(parsers)
  assert CI.CS.buttons_ts_nanos == BASE_NS
  assert CI.CS.buttons_counter == 3
  parsers[Bus.pt].update([])
  CI.CS.update(parsers)
  assert CI.CS.buttons_ts_nanos == BASE_NS
  parsers[Bus.pt].update([(BASE_NS + 30_000_000, [gmcan.create_buttons(packer, 0, 0, CruiseButtons.UNPRESS)])])
  CI.CS.update(parsers)
  assert CI.CS.buttons_ts_nanos == BASE_NS + 30_000_000
  assert CI.CS.buttons_counter == 0
