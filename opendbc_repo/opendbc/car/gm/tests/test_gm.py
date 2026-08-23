import unittest
from types import SimpleNamespace

from opendbc.car.gm.carcontroller import get_acc_dashboard_speed_kph, get_friction_brake_bus, is_soft_hold_driver_braking
from opendbc.car.gm.fingerprints import FINGERPRINTS
from opendbc.car.gm.values import CAMERA_ACC_CAR, CAR, GM_RX_OFFSET, CanBus
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


class TestGMSoftHoldBrakeGuard(unittest.TestCase):
  def test_blocks_actuation_while_driver_holds_brake(self):
    CS = SimpleNamespace(out=SimpleNamespace(brakeHoldActive=True, brakePressed=True))
    self.assertTrue(is_soft_hold_driver_braking(CS))

  def test_allows_actuation_after_brake_release(self):
    CS = SimpleNamespace(out=SimpleNamespace(brakeHoldActive=True, brakePressed=False))
    self.assertFalse(is_soft_hold_driver_braking(CS))
