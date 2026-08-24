import unittest
from types import SimpleNamespace

from cereal import car, custom
from opendbc.can.dbc import DBC
from opendbc.can.parser import get_raw_value
from opendbc.car import gen_empty_fingerprint
from opendbc.car.gm.carcontroller import (get_acc_dashboard_speed_kph, get_friction_brake_bus, gm_auto_hold_command,
                                         gm_long_auto_hold_command, gm_uses_auto_hold_sng, update_traverse_coasting)
from opendbc.car.gm.interface import CarInterface
from opendbc.car.gm.fingerprints import FINGERPRINTS
from opendbc.car.gm.values import CAMERA_ACC_CAR, CAR, GM_RX_OFFSET, CanBus
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


class TestGMTraverseAutoHold(unittest.TestCase):
  def setUp(self):
    self.CI = CarInterface.__new__(CarInterface)
    self.CI.CS = SimpleNamespace(
      autoHold=True,
      autoHoldActive=False,
      autoHoldActivated=False,
      brake_pedal_position=8,
      out=SimpleNamespace(vEgo=0.0, brakePressed=True, gasPressed=False, regenBraking=False),
    )

  def test_enters_and_latches_after_brake_press(self):
    self.CI.update_auto_hold()
    self.assertTrue(self.CI.CS.autoHoldActive)
    self.assertTrue(self.CI.CS.autoHoldActivated)

    self.CI.CS.out.brakePressed = False
    self.CI.CS.brake_pedal_position = 0
    self.CI.update_auto_hold()
    self.assertTrue(self.CI.CS.autoHoldActive)
    self.assertTrue(self.CI.CS.autoHoldActivated)

  def test_gas_releases_hold(self):
    self.CI.update_auto_hold()
    self.CI.CS.out.gasPressed = True
    self.CI.update_auto_hold()
    self.assertFalse(self.CI.CS.autoHoldActive)

  def test_controller_only_commands_hold_while_disengaged(self):
    CP = SimpleNamespace(carFingerprint=CAR.CHEVROLET_TRAVERSE)
    CC = SimpleNamespace(enabled=False, longActive=False)
    CS = SimpleNamespace(
      autoHold=True,
      autoHoldActive=True,
      out=SimpleNamespace(
        cruiseState=SimpleNamespace(enabled=False), gasPressed=False, regenBraking=False,
        gearShifter=GearShifter.drive, vEgo=0.0,
      ),
    )
    self.assertTrue(gm_auto_hold_command(CP, CC, CS))
    CC.enabled = True
    self.assertFalse(gm_auto_hold_command(CP, CC, CS))

  def test_engaged_stop_uses_long_auto_hold(self):
    CP = SimpleNamespace(carFingerprint=CAR.CHEVROLET_TRAVERSE, autoResumeSng=True)
    CC = SimpleNamespace(enabled=True, longActive=True)
    CS = SimpleNamespace(
      longAutoHoldActive=True,
      out=SimpleNamespace(
        standstill=True, gasPressed=False, regenBraking=False,
        gearShifter=GearShifter.drive,
      ),
    )
    actuators = SimpleNamespace(longControlState=LongCtrlState.stopping)
    self.assertTrue(gm_long_auto_hold_command(CP, CC, CS, actuators))

    actuators.longControlState = LongCtrlState.starting
    self.assertFalse(gm_long_auto_hold_command(CP, CC, CS, actuators))
    actuators.longControlState = LongCtrlState.stopping
    CS.out.standstill = False
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

    control.actuators.longControlState = LongCtrlState.starting
    self.CI.update_auto_hold(control)
    self.assertFalse(self.CI.CS.longAutoHoldActive)

  def test_controller_holds_without_full_stop_or_resume_button(self):
    fingerprint = gen_empty_fingerprint()
    CP = CarInterface.get_params(CAR.CHEVROLET_TRAVERSE, fingerprint, [], True, False, False)
    CP_SP = CarInterface.get_params_sp(CP, CAR.CHEVROLET_TRAVERSE, fingerprint, [], True, False, False)
    CI = CarInterface(CP, CP_SP)

    control = car.CarControl.new_message()
    control.enabled = True
    control.longActive = True
    control.actuators.longControlState = car.CarControl.Actuators.LongControlState.stopping
    control.actuators.accel = -1.0

    CS = CI.CS
    CS.out = car.CarState.new_message()
    CS.out.standstill = True
    CS.out.vEgo = 0.0
    CS.out.gearShifter = car.CarState.GearShifter.drive
    CS.out.cruiseState.enabled = True
    CS.out.cruiseState.standstill = True
    CS.longAutoHoldActive = True
    CS.loopback_lka_steering_cmd_updated = False
    CS.loopback_lka_steering_cmd_ts_nanos = 0
    CS.pt_lka_steering_cmd_counter = 0
    CS.cam_lka_steering_cmd_counter = 0
    CS.pscm_status = {}
    CI.CC.frame = 4

    _, sends = CI.CC.update(control.as_reader(), custom.CarControlSP.new_message().as_reader(), CS, 10_000_000_000)
    by_address = {msg[0]: msg for msg in sends}
    self.assertNotIn(0x1E1, by_address)

    gas_msg = DBC("gm_global_a_powertrain_generated").addr_to_msg[0x2CB]
    gas_data = by_address[0x2CB][1]
    self.assertEqual(1, get_raw_value(gas_data, gas_msg.sigs["GasRegenCmdActive"]))
    self.assertEqual(0, get_raw_value(gas_data, gas_msg.sigs["GasRegenFullStopActive"]))

    brake_msg = DBC("gm_global_a_chassis").addr_to_msg[0x315]
    brake_data = by_address[0x315][1]
    self.assertEqual(0xA, get_raw_value(brake_data, brake_msg.sigs["FrictionBrakeMode"]))
    self.assertEqual(0xFFF, get_raw_value(brake_data, brake_msg.sigs["FrictionBrakeCmd"]))

    control.actuators.longControlState = car.CarControl.Actuators.LongControlState.starting
    control.actuators.accel = CP.startAccel
    CS.longAutoHoldActive = False
    CI.CC.frame = 8
    _, launch_sends = CI.CC.update(control.as_reader(), custom.CarControlSP.new_message().as_reader(), CS, 10_100_000_000)
    launch_by_address = {msg[0]: msg for msg in launch_sends}
    self.assertNotIn(0x1E1, launch_by_address)
    launch_gas_data = launch_by_address[0x2CB][1]
    self.assertEqual(0, get_raw_value(launch_gas_data, gas_msg.sigs["GasRegenFullStopActive"]))
    launch_brake_data = launch_by_address[0x315][1]
    self.assertEqual(0, get_raw_value(launch_brake_data, brake_msg.sigs["FrictionBrakeCmd"]))
