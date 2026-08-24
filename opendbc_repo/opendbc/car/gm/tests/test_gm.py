import unittest
from types import SimpleNamespace

from opendbc.can import CANPacker
from opendbc.can.dbc import DBC
from opendbc.can.parser import get_raw_value
from opendbc.car.gm.carcontroller import (CarController, VOLT_RESUME_MAX_BUTTONS, get_acc_dashboard_speed_kph,
                                         get_friction_brake_bus, gm_auto_hold_command, update_traverse_coasting)
from opendbc.car.gm.interface import CarInterface
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


class TestGMTraverseAutoResume(unittest.TestCase):
  def setUp(self):
    self.controller = CarController.__new__(CarController)
    self.controller.CP = SimpleNamespace(autoResumeSng=True)
    self.controller.packer_pt = CANPacker("gm_global_a_powertrain_generated")
    self.controller.frame = 0
    self.controller.auto_resume_window_frame = None
    self.controller.auto_resume_last_button_frame = None
    self.controller.auto_resume_button_count = 0
    self.controller.auto_resume_button_counter = None
    self.controller.auto_resume_last_request = False
    self.controller.auto_resume_started = False
    self.controller.auto_resume_brake_tick_pending = False
    self.CC = SimpleNamespace(longActive=True, cruiseControl=SimpleNamespace(resume=True))
    self.CS = SimpleNamespace(
      buttons_counter=0,
      cruise_buttons=CruiseButtons.UNPRESS,
      out=SimpleNamespace(
        standstill=True,
        brakePressed=False,
        gasPressed=False,
        vEgo=0.0,
        cruiseState=SimpleNamespace(enabled=True, standstill=True),
      ),
    )
    self.actuators = SimpleNamespace(longControlState=LongCtrlState.starting)
    self.dbc_msg = DBC("gm_global_a_powertrain_generated").addr_to_msg[0x1E1]

  def decode(self, msg):
    return {
      name: int(get_raw_value(msg[1], self.dbc_msg.sigs[name]))
      for name in ("ACCButtons", "RollingCounter")
    }

  def test_volt_two_press_sequence_and_accel_window(self):
    messages, active, brake_tick = self.controller.update_auto_resume(self.CC, self.CS, self.actuators)
    self.assertEqual(1, len(messages))
    self.assertTrue(active)
    self.assertTrue(brake_tick)

    self.CC.cruiseControl.resume = False
    for frame in range(1, 12):
      self.controller.frame = frame
      next_messages, active, brake_tick = self.controller.update_auto_resume(self.CC, self.CS, self.actuators)
      messages.extend(next_messages)
      self.assertTrue(active)
      self.assertFalse(brake_tick)

    self.controller.frame = 12
    next_messages, active, _ = self.controller.update_auto_resume(self.CC, self.CS, self.actuators)
    messages.extend(next_messages)
    self.assertTrue(active)
    self.assertEqual(VOLT_RESUME_MAX_BUTTONS, len(messages))
    self.assertTrue(all(msg[2] == CanBus.CAMERA for msg in messages))
    decoded = [self.decode(msg) for msg in messages]
    self.assertEqual([1, 2], [msg["RollingCounter"] for msg in decoded])
    self.assertTrue(all(msg["ACCButtons"] == CruiseButtons.RES_ACCEL for msg in decoded))

  def test_reopens_after_volt_retry_delay_while_starting(self):
    self.controller.update_auto_resume(self.CC, self.CS, self.actuators)
    self.CC.cruiseControl.resume = False
    self.controller.frame = 28
    messages, active, brake_tick = self.controller.update_auto_resume(self.CC, self.CS, self.actuators)
    self.assertEqual(1, len(messages))
    self.assertTrue(active)
    self.assertTrue(brake_tick)

  def test_driver_input_cancels_pending_press(self):
    self.assertEqual(1, len(self.controller.update_auto_resume(self.CC, self.CS, self.actuators)[0]))
    self.CS.out.gasPressed = True
    messages, active, _ = self.controller.update_auto_resume(self.CC, self.CS, self.actuators)
    self.assertEqual([], messages)
    self.assertFalse(active)
    self.assertIsNone(self.controller.auto_resume_window_frame)


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
