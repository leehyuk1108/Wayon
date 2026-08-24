import unittest
from types import SimpleNamespace

from opendbc.can import CANPacker
from opendbc.can.dbc import DBC
from opendbc.can.parser import get_raw_value
from opendbc.car.gm.carcontroller import (CarController, SNG_RESUME_BUTTON_FRAMES, get_acc_dashboard_speed_kph,
                                         get_friction_brake_bus, update_traverse_coasting)
from opendbc.car.gm.fingerprints import FINGERPRINTS
from opendbc.car.gm.values import CAMERA_ACC_CAR, CAR, GM_RX_OFFSET, CanBus, CruiseButtons
from opendbc.car.structs import CarParams
from opendbc.testing import parameterized

CAMERA_DIAGNOSTIC_ADDRESS = 0x24b


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
    self.controller.sng_resume_button_frames = 0
    self.controller.sng_resume_last_stock_counter = None
    self.controller.sng_resume_last = False
    self.CC = SimpleNamespace(longActive=True, cruiseControl=SimpleNamespace(resume=True))
    self.CS = SimpleNamespace(
      buttons_counter=0,
      cruise_buttons=CruiseButtons.UNPRESS,
      out=SimpleNamespace(standstill=True, brakePressed=False, gasPressed=False),
    )
    self.dbc_msg = DBC("gm_global_a_powertrain_generated").addr_to_msg[0x1E1]

  def decode(self, msg):
    return {
      name: int(get_raw_value(msg[1], self.dbc_msg.sigs[name]))
      for name in ("ACCButtons", "RollingCounter")
    }

  def test_uses_route_matched_four_frame_camera_bus_press(self):
    messages = []
    for counter in range(4):
      self.CS.buttons_counter = counter
      messages.extend(self.controller.update_sng_resume_button(self.CC, self.CS))

    self.assertEqual(SNG_RESUME_BUTTON_FRAMES, len(messages))
    self.assertTrue(all(msg[2] == CanBus.CAMERA for msg in messages))
    decoded = [self.decode(msg) for msg in messages]
    self.assertEqual([0, 1, 2, 3], [msg["RollingCounter"] for msg in decoded])
    self.assertTrue(all(msg["ACCButtons"] == CruiseButtons.RES_ACCEL for msg in decoded))

  def test_repeated_counter_does_not_duplicate_button_frame(self):
    self.assertEqual(1, len(self.controller.update_sng_resume_button(self.CC, self.CS)))
    self.assertEqual([], self.controller.update_sng_resume_button(self.CC, self.CS))

  def test_driver_input_cancels_pending_press(self):
    self.assertEqual(1, len(self.controller.update_sng_resume_button(self.CC, self.CS)))
    self.CS.out.gasPressed = True
    self.assertEqual([], self.controller.update_sng_resume_button(self.CC, self.CS))
    self.assertEqual(0, self.controller.sng_resume_button_frames)
