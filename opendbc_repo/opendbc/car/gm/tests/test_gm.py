import unittest
from types import SimpleNamespace

from cereal import car, custom
from opendbc.can import CANPacker, CANParser
from opendbc.can.dbc import DBC
from opendbc.can.parser import get_raw_value
from opendbc.car import gen_empty_fingerprint
from opendbc.car.gm.carcontroller import (get_acc_dashboard_speed_kph, get_friction_brake_bus, gm_auto_hold_command,
                                         gm_long_auto_hold_command, gm_uses_auto_hold_sng,
                                         limit_traverse_stopping_brake, update_gm_long_auto_hold_brake,
                                         update_traverse_coasting)
from opendbc.car.gm.carstate import STANDSTILL_THRESHOLD, TRAVERSE_STANDSTILL_THRESHOLD, get_standstill_threshold
from opendbc.car.gm.interface import CarInterface
from opendbc.car.gm.gmcan import create_acc_dashboard_command
from opendbc.car.gm.fingerprints import FINGERPRINTS
from opendbc.car.gm.values import CAMERA_ACC_CAR, CAR, GM_RX_OFFSET, CanBus, CruiseButtons
from opendbc.car.structs import CarControl, CarParams, CarState
from opendbc.testing import parameterized

CAMERA_DIAGNOSTIC_ADDRESS = 0x24b
LongCtrlState = CarControl.Actuators.LongControlState
GearShifter = CarState.GearShifter


class TestGMFingerprint(unittest.TestCase):
  @parameterized("car_model, fingerprints", FINGERPRINTS.items())
  def test_can_fingerprints(self, car_model, fingerprints):
    assert len(fingerprints) > 0

    assert all(len(finger) for finger in fingerprints)

    # The camera can sometimes be communicating on startup
    if car_model in CAMERA_ACC_CAR:
      for finger in fingerprints:
        for required_addr in (CAMERA_DIAGNOSTIC_ADDRESS, CAMERA_DIAGNOSTIC_ADDRESS + GM_RX_OFFSET):
          assert finger.get(required_addr) == 8, required_addr


class TestGMFrictionBrakeBus(unittest.TestCase):
  def test_sdgm_camera_uses_camera_bus(self):
    CP = SimpleNamespace(networkLocation=CarParams.NetworkLocation.fwdCamera, carFingerprint=CAR.CHEVROLET_TRAVERSE)
    self.assertEqual(get_friction_brake_bus(CP), CanBus.CAMERA)

  def test_non_sdgm_camera_uses_powertrain_bus(self):
    CP = SimpleNamespace(networkLocation=CarParams.NetworkLocation.fwdCamera, carFingerprint=CAR.CHEVROLET_BOLT_EUV)
    self.assertEqual(get_friction_brake_bus(CP), CanBus.POWERTRAIN)

  def test_gateway_uses_chassis_bus(self):
    CP = SimpleNamespace(networkLocation=CarParams.NetworkLocation.gateway, carFingerprint=CAR.CHEVROLET_VOLT)
    self.assertEqual(get_friction_brake_bus(CP), CanBus.CHASSIS)


class TestGMAccDashboardSpeed(unittest.TestCase):
  def test_sdgm_uses_inverse_cluster_correction(self):
    CP = SimpleNamespace(carFingerprint=CAR.CHEVROLET_TRAVERSE)
    self.assertEqual(get_acc_dashboard_speed_kph(CP, 70.0), 66.0)
    self.assertEqual(get_acc_dashboard_speed_kph(CP, 100.0), 95.0)

  def test_non_sdgm_is_unchanged(self):
    CP = SimpleNamespace(carFingerprint=CAR.CHEVROLET_BOLT_EUV)
    self.assertEqual(get_acc_dashboard_speed_kph(CP, 70.0), 70.0)


class TestGMAccDashboardFCW(unittest.TestCase):
  def test_preserves_each_stock_fcw_level(self):
    packer = CANPacker("gm_global_a_powertrain_generated")
    parser = CANParser("gm_global_a_powertrain_generated", [("ASCMActiveCruiseControlStatus", 0)], 0)
    hud_control = SimpleNamespace(leadDistanceBars=2, leadVisible=True)

    for alert in range(4):
      msg = create_acc_dashboard_command(packer, 0, True, 80.0, hud_control, alert)
      parser.update([1_000_000_000, [msg]])
      self.assertEqual(parser.vl["ASCMActiveCruiseControlStatus"]["FCWAlert"], alert)


class TestGMTraverseCoasting(unittest.TestCase):
  def setUp(self):
    self.CP = SimpleNamespace(carFingerprint=CAR.CHEVROLET_TRAVERSE)

  def test_enters_and_holds_with_hysteresis(self):
    self.assertTrue(update_traverse_coasting(self.CP, False, True, False, 20.0, -0.25))
    self.assertTrue(update_traverse_coasting(self.CP, True, True, False, 20.0, -0.40))
    self.assertFalse(update_traverse_coasting(self.CP, False, True, False, 20.0, -0.40))
    self.assertFalse(update_traverse_coasting(self.CP, True, True, False, 20.0, -0.50))

  def test_disabled_when_braking_or_below_minimum_speed(self):
    self.assertFalse(update_traverse_coasting(self.CP, True, True, True, 20.0, -0.25))
    self.assertFalse(update_traverse_coasting(self.CP, True, True, False, 4.9, -0.25))
    self.assertFalse(update_traverse_coasting(self.CP, True, False, False, 20.0, -0.25))

  def test_other_gm_cars_are_unchanged(self):
    CP = SimpleNamespace(carFingerprint=CAR.CHEVROLET_BOLT_EUV)
    self.assertFalse(update_traverse_coasting(CP, False, True, False, 20.0, -0.25))


class TestGMTraverseStoppingBrake(unittest.TestCase):
  def setUp(self):
    self.CP = SimpleNamespace(carFingerprint=CAR.CHEVROLET_TRAVERSE)

  def test_tapers_to_soft_release_near_stop(self):
    self.assertEqual(12, limit_traverse_stopping_brake(self.CP, True, 0.8 / 3.6 - 1e-3, 12))
    self.assertEqual(3, limit_traverse_stopping_brake(self.CP, True, 0.5 / 3.6, 12))
    self.assertEqual(1, limit_traverse_stopping_brake(self.CP, True, 0.3 / 3.6, 12))
    self.assertEqual(0, limit_traverse_stopping_brake(self.CP, True, 0.15 / 3.6, 12))
    self.assertEqual(0, limit_traverse_stopping_brake(self.CP, True, 0.0, 12))

  def test_does_not_increase_requested_brake(self):
    self.assertEqual(1, limit_traverse_stopping_brake(self.CP, True, 0.3 / 3.6, 10))
    self.assertEqual(1, limit_traverse_stopping_brake(self.CP, True, 0.3 / 3.6, 1))

  def test_preserves_requested_brake_when_stopping_reserve_is_small(self):
    self.assertEqual(20, limit_traverse_stopping_brake(self.CP, True, 0.3 / 3.6, 20))
    self.assertEqual(60, limit_traverse_stopping_brake(self.CP, True, 0.3 / 3.6, 60))

  def test_only_changes_traverse_final_stopping_phase(self):
    self.assertEqual(132, limit_traverse_stopping_brake(self.CP, False, 0.2, 132))
    self.assertEqual(12, limit_traverse_stopping_brake(self.CP, True, 0.9 / 3.6, 12))
    self.assertEqual(180, limit_traverse_stopping_brake(self.CP, True, 0.2, 180))
    other = SimpleNamespace(carFingerprint=CAR.CHEVROLET_BOLT_EUV)
    self.assertEqual(132, limit_traverse_stopping_brake(other, True, 0.2, 132))


class TestGMStandstillThreshold(unittest.TestCase):
  def test_traverse_requires_zero_wheel_speed_bin(self):
    traverse = SimpleNamespace(carFingerprint=CAR.CHEVROLET_TRAVERSE)
    other = SimpleNamespace(carFingerprint=CAR.CHEVROLET_BOLT_EUV)
    self.assertEqual(TRAVERSE_STANDSTILL_THRESHOLD, get_standstill_threshold(traverse))
    self.assertLess(TRAVERSE_STANDSTILL_THRESHOLD, 0.0311)
    self.assertEqual(STANDSTILL_THRESHOLD, get_standstill_threshold(other))


class TestGMLongAutoHoldBrake(unittest.TestCase):
  def step(self, state, requested=True, regular_brake=14, v_ego_raw=0.0, a_ego=0.0):
    return update_gm_long_auto_hold_brake(requested, *state, regular_brake, v_ego_raw, a_ego)

  def test_waits_for_physical_settle_then_ramps(self):
    state = (False, 0, 0, 0)
    for _ in range(4):
      brake, confirmed, zero, settled, hold_brake = self.step(state)
      self.assertEqual(brake, 14)
      self.assertFalse(confirmed)
      state = (confirmed, zero, settled, hold_brake)

    brake, confirmed, zero, settled, hold_brake = self.step(state)
    self.assertEqual(brake, 46)
    self.assertTrue(confirmed)

    state = (confirmed, zero, settled, hold_brake)
    brake, confirmed, zero, settled, hold_brake = self.step(state)
    self.assertEqual(brake, 78)

  def test_deceleration_does_not_count_as_settled(self):
    state = (False, 0, 0, 0)
    for _ in range(8):
      brake, confirmed, zero, settled, hold_brake = self.step(state, a_ego=-1.0)
      self.assertEqual(brake, 14)
      self.assertFalse(confirmed)
      state = (confirmed, zero, settled, hold_brake)

  def test_noisy_acceleration_uses_bounded_timeout(self):
    state = (False, 0, 0, 0)
    for _ in range(19):
      brake, confirmed, zero, settled, hold_brake = self.step(state, a_ego=0.3)
      self.assertFalse(confirmed)
      state = (confirmed, zero, settled, hold_brake)
    brake, confirmed, *_ = self.step(state, a_ego=0.3)
    self.assertEqual(brake, 46)
    self.assertTrue(confirmed)

  def test_roll_after_hold_request_applies_full_pressure(self):
    state = (False, 1, 0, 0)
    brake, confirmed, *_ = self.step(state, v_ego_raw=0.09, a_ego=0.1)
    self.assertEqual(brake, 400)
    self.assertTrue(confirmed)

  def test_initial_low_speed_hold_request_does_not_jump_to_full_pressure(self):
    brake, confirmed, zero, settled, hold_brake = self.step((False, 0, 0, 0), v_ego_raw=0.085, a_ego=-0.5)
    self.assertEqual((brake, confirmed, zero, settled, hold_brake), (14, False, 0, 0, 0))

  def test_release_resets_state(self):
    brake, confirmed, zero, settled, hold_brake = self.step((True, 8, 5, 200), requested=False, regular_brake=7)
    self.assertEqual((brake, confirmed, zero, settled, hold_brake), (7, False, 0, 0, 0))


class TestGMTraverseAutoHold(unittest.TestCase):
  def setUp(self):
    self.CI = CarInterface.__new__(CarInterface)
    self.CI.CS = SimpleNamespace(
      autoHold=True,
      autoHoldActive=False,
      autoHoldBrakeArmed=False,
      autoHoldBrakeReleased=False,
      autoHoldBrakePressPeak=0,
      autoHoldActivated=False,
      longAutoHoldActive=False,
      brake_pedal_position=8,
      out=SimpleNamespace(
        vEgo=0.0, standstill=True, brakePressed=True, gasPressed=False, regenBraking=False,
        parkingBrake=False, gearShifter=GearShifter.drive,
        cruiseState=SimpleNamespace(enabled=False),
      ),
    )

  def test_enters_and_latches_after_brake_press(self):
    self.CI.CS.brake_pedal_position = 80
    self.CI.update_auto_hold()
    self.assertTrue(self.CI.CS.autoHoldActive)
    self.assertTrue(self.CI.CS.autoHoldActivated)
    self.assertTrue(self.CI.CS.out.brakeHoldActive)

    self.CI.CS.out.brakePressed = False
    self.CI.CS.brake_pedal_position = 0
    self.CI.update_auto_hold()
    self.assertTrue(self.CI.CS.autoHoldActive)
    self.assertTrue(self.CI.CS.autoHoldActivated)

  def test_gas_releases_hold(self):
    self.CI.CS.brake_pedal_position = 80
    self.CI.update_auto_hold()
    self.CI.CS.out.gasPressed = True
    self.CI.update_auto_hold()
    self.assertFalse(self.CI.CS.autoHoldActive)

  def test_light_brake_tap_releases_hold(self):
    self.CI.CS.brake_pedal_position = 80
    self.CI.update_auto_hold()

    # Releasing the original strong press only arms the tap-to-release gesture.
    self.CI.CS.out.brakePressed = False
    self.CI.CS.brake_pedal_position = 0
    self.CI.update_auto_hold()
    self.assertTrue(self.CI.CS.autoHoldActive)

    self.CI.CS.out.brakePressed = True
    self.CI.CS.brake_pedal_position = 20
    self.CI.update_auto_hold()
    self.assertTrue(self.CI.CS.autoHoldActive)

    self.CI.CS.out.brakePressed = False
    self.CI.CS.brake_pedal_position = 0
    self.CI.update_auto_hold()
    self.assertFalse(self.CI.CS.autoHoldActive)
    self.assertFalse(self.CI.CS.out.brakeHoldActive)

  def test_strong_brake_repress_keeps_hold(self):
    self.CI.CS.brake_pedal_position = 80
    self.CI.update_auto_hold()
    self.CI.CS.out.brakePressed = False
    self.CI.CS.brake_pedal_position = 0
    self.CI.update_auto_hold()

    # A press that eventually reaches the activation threshold must keep hold,
    # even though it passes through lower pressure on the way up.
    self.CI.CS.out.brakePressed = True
    self.CI.CS.brake_pedal_position = 20
    self.CI.update_auto_hold()
    self.CI.CS.brake_pedal_position = 80
    self.CI.update_auto_hold()
    self.CI.CS.out.brakePressed = False
    self.CI.CS.brake_pedal_position = 0
    self.CI.update_auto_hold()

    self.assertTrue(self.CI.CS.autoHoldActive)
    self.assertTrue(self.CI.CS.out.brakeHoldActive)

  def test_strong_brake_arms_before_stop_and_activates_at_standstill(self):
    self.CI.CS.out.vEgo = 1.0
    self.CI.CS.out.standstill = False
    self.CI.CS.brake_pedal_position = 80
    self.CI.update_auto_hold()
    self.assertTrue(self.CI.CS.autoHoldBrakeArmed)
    self.assertFalse(self.CI.CS.autoHoldActive)

    self.CI.CS.brake_pedal_position = 10
    self.CI.CS.out.vEgo = 0.0
    self.CI.CS.out.standstill = True
    self.CI.update_auto_hold()
    self.assertTrue(self.CI.CS.autoHoldActive)
    self.assertTrue(self.CI.CS.out.brakeHoldActive)

  def test_gentle_brake_does_not_activate_manual_hold(self):
    self.CI.CS.brake_pedal_position = 79
    self.CI.update_auto_hold()
    self.assertFalse(self.CI.CS.autoHoldBrakeArmed)
    self.assertFalse(self.CI.CS.autoHoldActive)
    self.assertFalse(self.CI.CS.out.brakeHoldActive)

  def test_controller_only_commands_hold_while_disengaged(self):
    CP = SimpleNamespace(carFingerprint=CAR.CHEVROLET_TRAVERSE)
    CC = SimpleNamespace(enabled=False, longActive=False)
    CS = SimpleNamespace(
      autoHold=True,
      autoHoldActive=True,
      out=SimpleNamespace(
        cruiseState=SimpleNamespace(enabled=False), gasPressed=False, regenBraking=False,
        gearShifter=GearShifter.drive, vEgo=0.0, parkingBrake=False,
      ),
    )
    self.assertTrue(gm_auto_hold_command(CP, CC, CS))
    CC.enabled = True
    self.assertFalse(gm_auto_hold_command(CP, CC, CS))

  def test_parking_brake_clears_manual_hold_and_blocks_command(self):
    self.CI.CS.brake_pedal_position = 80
    self.CI.update_auto_hold()
    self.assertTrue(self.CI.CS.autoHoldActive)

    self.CI.CS.out.parkingBrake = True
    self.CI.update_auto_hold()
    self.assertFalse(self.CI.CS.autoHoldActive)
    self.assertFalse(self.CI.CS.autoHoldBrakeArmed)
    self.assertFalse(self.CI.CS.out.brakeHoldActive)

    CP = SimpleNamespace(carFingerprint=CAR.CHEVROLET_TRAVERSE)
    CC = SimpleNamespace(enabled=False, longActive=False)
    self.assertFalse(gm_auto_hold_command(CP, CC, self.CI.CS))

  def test_non_drive_gear_clears_manual_hold(self):
    self.CI.CS.brake_pedal_position = 80
    self.CI.update_auto_hold()
    self.CI.CS.out.gearShifter = GearShifter.park
    self.CI.update_auto_hold()
    self.assertFalse(self.CI.CS.autoHoldActive)
    self.assertFalse(self.CI.CS.out.brakeHoldActive)

  def test_engaged_stop_uses_long_auto_hold(self):
    CP = SimpleNamespace(carFingerprint=CAR.CHEVROLET_TRAVERSE, autoResumeSng=True)
    CC = SimpleNamespace(enabled=True, longActive=True)
    CS = SimpleNamespace(
      longAutoHoldActive=True,
      out=SimpleNamespace(
        standstill=True, gasPressed=False, regenBraking=False,
        gearShifter=GearShifter.drive, parkingBrake=False, vEgo=0.0,
      ),
    )
    actuators = SimpleNamespace(longControlState=LongCtrlState.stopping)
    self.assertTrue(gm_long_auto_hold_command(CP, CC, CS, actuators))

    actuators.longControlState = LongCtrlState.starting
    self.assertFalse(gm_long_auto_hold_command(CP, CC, CS, actuators))
    actuators.longControlState = LongCtrlState.stopping
    CS.out.standstill = False
    CS.out.vEgo = 0.12
    self.assertTrue(gm_long_auto_hold_command(CP, CC, CS, actuators))

    CS.out.vEgo = 0.5
    self.assertFalse(gm_long_auto_hold_command(CP, CC, CS, actuators))

    CS.out.standstill = True
    CS.out.vEgo = 0.0
    CS.out.parkingBrake = True
    self.assertFalse(gm_long_auto_hold_command(CP, CC, CS, actuators))

  def test_only_traverse_sng_suppresses_acc_full_stop(self):
    traverse = SimpleNamespace(carFingerprint=CAR.CHEVROLET_TRAVERSE, autoResumeSng=True)
    bolt = SimpleNamespace(carFingerprint=CAR.CHEVROLET_BOLT_EUV, autoResumeSng=True)
    self.assertTrue(gm_uses_auto_hold_sng(traverse))
    self.assertFalse(gm_uses_auto_hold_sng(bolt))

  def test_interface_marks_engaged_hold_without_changing_manual_latch(self):
    self.CI.CS.out.gearShifter = GearShifter.drive
    self.CI.CS.out.standstill = True
    control = SimpleNamespace(
      longActive=True,
      actuators=SimpleNamespace(longControlState=LongCtrlState.stopping),
    )
    self.CI.update_auto_hold(control)
    self.assertTrue(self.CI.CS.longAutoHoldActive)
    self.assertTrue(self.CI.CS.autoHoldActivated)

    self.CI.CS.out.standstill = False
    self.CI.CS.out.vEgo = 0.12
    self.CI.update_auto_hold(control)
    self.assertTrue(self.CI.CS.longAutoHoldActive)

    self.CI.CS.out.vEgo = 0.5
    self.CI.update_auto_hold(control)
    self.assertFalse(self.CI.CS.longAutoHoldActive)

    self.CI.CS.out.standstill = True
    self.CI.CS.out.vEgo = 0.0
    control.actuators.longControlState = LongCtrlState.starting
    self.CI.update_auto_hold(control)
    self.assertFalse(self.CI.CS.longAutoHoldActive)

  def test_controller_sends_resume_pulse_without_waiting_for_creep(self):
    fingerprint = gen_empty_fingerprint()
    CP = CarInterface.get_params(CAR.CHEVROLET_TRAVERSE, fingerprint, [], True, False, False)
    CP_SP = CarInterface.get_params_sp(CP, CAR.CHEVROLET_TRAVERSE, fingerprint, [], True, False, False)
    CI = CarInterface(CP, CP_SP)

    control = car.CarControl.new_message()
    control.enabled = True
    control.longActive = True
    control.actuators.longControlState = car.CarControl.Actuators.LongControlState.starting
    control.actuators.accel = 0.35
    control.cruiseControl.resume = True

    CS = CI.CS
    CS.out = car.CarState.new_message()
    CS.out.standstill = True
    CS.out.vEgo = 0.0
    CS.out.gearShifter = car.CarState.GearShifter.drive
    CS.out.cruiseState.enabled = True
    CS.out.cruiseState.standstill = True
    CS.longAutoHoldActive = False
    CS.cruise_buttons = CruiseButtons.UNPRESS
    CS.buttons_counter = 0
    CS.loopback_lka_steering_cmd_updated = False
    CS.loopback_lka_steering_cmd_ts_nanos = 0
    CS.pt_lka_steering_cmd_counter = 0
    CS.cam_lka_steering_cmd_counter = 0
    CS.pscm_status = {
      "HandsOffSWDetectionMode": 0,
      "HandsOffSWlDetectionStatus": 0,
      "LKATorqueDeliveredStatus": 0,
      "LKADriverAppldTrq": 0,
      "LKATorqueDelivered": 0,
      "LKATotalTorqueDelivered": 0,
      "RollingCounter": 0,
      "PSCMStatusChecksum": 0,
    }
    CI.CC.frame = 4

    _, stopped_sends = CI.CC.update(control.as_reader(), custom.CarControlSP.new_message().as_reader(), CS, 10_000_000_000)
    button_msg = DBC("gm_global_a_powertrain_generated").addr_to_msg[0x1E1]
    stopped_buttons = [msg for msg in stopped_sends if msg[0] == 0x1E1]
    self.assertEqual(2, len(stopped_buttons))
    self.assertEqual({CanBus.POWERTRAIN, CanBus.CAMERA}, {msg[2] for msg in stopped_buttons})
    self.assertTrue(all(get_raw_value(msg[1], button_msg.sigs["ACCButtons"]) == CruiseButtons.RES_ACCEL
                        for msg in stopped_buttons))

    # Continue the bounded physical-button sequence at the stock frame rate.
    control.cruiseControl.resume = False
    control.actuators.longControlState = car.CarControl.Actuators.LongControlState.pid
    CS.out.vEgo = 0.0
    pulse_sends = []
    for i in range(3):
      CS.buttons_counter = (i + 1) % 4
      CI.CC.frame = 7 + (i * 3)
      _, sends = CI.CC.update(control.as_reader(), custom.CarControlSP.new_message().as_reader(), CS,
                              10_030_000_000 + (i * 30_000_000))
      pulse_sends.extend(msg for msg in sends if msg[0] == 0x1E1)

    self.assertEqual(6, len(pulse_sends))
    self.assertEqual({CanBus.POWERTRAIN, CanBus.CAMERA}, {msg[2] for msg in pulse_sends})
    self.assertTrue(all(get_raw_value(msg[1], button_msg.sigs["ACCButtons"]) == CruiseButtons.RES_ACCEL
                        for msg in pulse_sends))

    CS.buttons_counter = 0
    CI.CC.frame = 16
    _, release_sends = CI.CC.update(control.as_reader(), custom.CarControlSP.new_message().as_reader(), CS, 10_240_000_000)
    release_buttons = [msg for msg in release_sends if msg[0] == 0x1E1]
    self.assertEqual(2, len(release_buttons))
    self.assertEqual(CruiseButtons.UNPRESS, get_raw_value(release_buttons[0][1], button_msg.sigs["ACCButtons"]))

  def test_controller_cancels_armed_resume_on_early_ack(self):
    fingerprint = gen_empty_fingerprint()
    CP = CarInterface.get_params(CAR.CHEVROLET_TRAVERSE, fingerprint, [], True, False, False)
    CP_SP = CarInterface.get_params_sp(CP, CAR.CHEVROLET_TRAVERSE, fingerprint, [], True, False, False)
    controller = CarInterface(CP, CP_SP).CC
    CC = SimpleNamespace(
      enabled=True, longActive=True,
      cruiseControl=SimpleNamespace(resume=True),
    )
    actuators = SimpleNamespace(longControlState=LongCtrlState.starting)
    CS = SimpleNamespace(
      buttons_counter=0, cruise_buttons=CruiseButtons.UNPRESS,
      out=SimpleNamespace(
        brakePressed=False, gasPressed=False, gearShifter=GearShifter.drive, vEgo=0.0,
        cruiseState=SimpleNamespace(standstill=True),
      ),
    )
    sends = []
    controller.frame = 0
    self.assertTrue(controller.update_sng_resume(CC, CS, actuators, sends))
    self.assertEqual(2, len(sends))

    CS.out.cruiseState.standstill = False
    CS.out.vEgo = 0.2
    CC.cruiseControl.resume = False
    actuators.longControlState = LongCtrlState.pid
    controller.frame = 3
    release = []
    self.assertTrue(controller.update_sng_resume(CC, CS, actuators, release))
    self.assertEqual(2, len(release))
    self.assertEqual(-1, controller.sng_resume_frame)

  def test_controller_relays_driver_cancel_with_next_counter(self):
    fingerprint = gen_empty_fingerprint()
    CP = CarInterface.get_params(CAR.CHEVROLET_TRAVERSE, fingerprint, [], True, False, False)
    CP_SP = CarInterface.get_params_sp(CP, CAR.CHEVROLET_TRAVERSE, fingerprint, [], True, False, False)
    controller = CarInterface(CP, CP_SP).CC
    CC = SimpleNamespace(
      enabled=True, longActive=True,
      cruiseControl=SimpleNamespace(resume=True),
    )
    actuators = SimpleNamespace(longControlState=LongCtrlState.starting)
    CS = SimpleNamespace(
      buttons_counter=0, cruise_buttons=CruiseButtons.UNPRESS,
      out=SimpleNamespace(
        brakePressed=False, gasPressed=False, gearShifter=GearShifter.drive, vEgo=0.0,
        cruiseState=SimpleNamespace(standstill=True),
      ),
    )
    button_msg = DBC("gm_global_a_powertrain_generated").addr_to_msg[0x1E1]

    armed = []
    controller.frame = 0
    controller.update_sng_resume(CC, CS, actuators, armed)
    self.assertEqual(2, len(armed))

    CS.buttons_counter = 1
    first = []
    controller.frame = 3
    controller.update_sng_resume(CC, CS, actuators, first)
    self.assertEqual(2, len(first))
    self.assertEqual(CruiseButtons.RES_ACCEL, get_raw_value(first[0][1], button_msg.sigs["ACCButtons"]))

    CS.buttons_counter = 2
    CS.cruise_buttons = CruiseButtons.CANCEL
    cancel = []
    controller.frame = 6
    self.assertTrue(controller.update_sng_resume(CC, CS, actuators, cancel))
    self.assertEqual(2, len(cancel))
    self.assertEqual({CanBus.POWERTRAIN, CanBus.CAMERA}, {msg[2] for msg in cancel})
    self.assertEqual(cancel[0][1], cancel[1][1])
    self.assertEqual(CruiseButtons.CANCEL, get_raw_value(cancel[0][1], button_msg.sigs["ACCButtons"]))
    self.assertEqual(3, get_raw_value(cancel[0][1], button_msg.sigs["RollingCounter"]))
