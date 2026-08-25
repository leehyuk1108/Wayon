#!/usr/bin/env python3
import unittest

from opendbc.car.gm.values import GMSafetyFlags
from opendbc.car.structs import CarParams
from opendbc.safety.tests.libsafety import libsafety_py
import opendbc.safety.tests.common as common
from opendbc.safety.tests.common import CANPackerSafety

from opendbc.sunnypilot.car.gm.values_ext import GMSafetyFlagsSP


class Buttons:
  UNPRESS = 1
  RES_ACCEL = 2
  DECEL_SET = 3
  CANCEL = 6


class GmLongitudinalBase(common.CarSafetyTest, common.LongitudinalGasBrakeSafetyTest):

  RELAY_MALFUNCTION_ADDRS = {0: (0x180, 0x2CB), 2: (0x184,)}  # ASCMLKASteeringCmd, ASCMGasRegenCmd, PSCMStatus

  MAX_POSSIBLE_BRAKE = 2 ** 12
  MAX_BRAKE = 400

  MAX_POSSIBLE_GAS = 4000  # reasonably excessive limits, not signal max
  MIN_POSSIBLE_GAS = -4000

  PCM_CRUISE = False  # openpilot can control the PCM state if longitudinal

  def _send_brake_msg(self, brake):
    values = {"FrictionBrakeCmd": -brake}
    return self.packer_chassis.make_can_msg_safety("EBCMFrictionBrakeCmd", self.BRAKE_BUS, values)

  def _send_gas_msg(self, gas):
    values = {"GasRegenCmd": gas}
    return self.packer.make_can_msg_safety("ASCMGasRegenCmd", 0, values)

  # override these tests from CarSafetyTest, GM longitudinal uses button enable
  def _pcm_status_msg(self, enable):
    raise NotImplementedError

  def test_disable_control_allowed_from_cruise(self):
    pass

  def test_enable_control_allowed_from_cruise(self):
    pass

  def test_cruise_engaged_prev(self):
    pass

  def test_set_resume_buttons(self):
    """
      SET and RESUME enter controls allowed on their falling and rising edges, respectively.
    """
    for btn_prev in range(8):
      for btn_cur in range(8):
        with self.subTest(btn_prev=btn_prev, btn_cur=btn_cur):
          self._rx(self._button_msg(btn_prev))
          self.safety.set_controls_allowed(0)
          for _ in range(10):
            self._rx(self._button_msg(btn_cur))

          should_enable = btn_cur != Buttons.DECEL_SET and btn_prev == Buttons.DECEL_SET
          should_enable = should_enable or (btn_cur == Buttons.RES_ACCEL and btn_prev != Buttons.RES_ACCEL)
          should_enable = should_enable and btn_cur != Buttons.CANCEL
          self.assertEqual(should_enable, self.safety.get_controls_allowed())

  def test_cancel_button(self):
    self.safety.set_controls_allowed(1)
    self._rx(self._button_msg(Buttons.CANCEL))
    self.assertFalse(self.safety.get_controls_allowed())


class TestGmSafetyBase(common.CarSafetyTest, common.DriverTorqueSteeringSafetyTest):
  STANDSTILL_THRESHOLD = 10 * 0.0311
  # Ensures ASCM is off on ASCM cars, and relay is not malfunctioning for camera-ACC cars
  RELAY_MALFUNCTION_ADDRS = {0: (0x180,), 2: (0x184,)}  # ASCMLKASteeringCmd, PSCMStatus
  BUTTONS_BUS = 0  # rx or tx
  BRAKE_BUS = 0  # tx only

  MAX_RATE_UP = 10
  MAX_RATE_DOWN = 15
  MAX_TORQUE_LOOKUP = [0], [300]
  MAX_RT_DELTA = 128
  DRIVER_TORQUE_ALLOWANCE = 65
  DRIVER_TORQUE_FACTOR = 4

  PCM_CRUISE = True  # openpilot is tied to the PCM state if not longitudinal

  EXTRA_SAFETY_PARAM = 0

  def setUp(self):
    self.packer = CANPackerSafety("gm_global_a_powertrain_generated")
    self.packer_chassis = CANPackerSafety("gm_global_a_chassis")
    self.safety = libsafety_py.libsafety
    self.safety.set_safety_hooks(CarParams.SafetyModel.gm, 0)
    self.safety.init_tests()

  def _pcm_status_msg(self, enable):
    if self.PCM_CRUISE:
      values = {"CruiseState": enable}
      return self.packer.make_can_msg_safety("AcceleratorPedal2", 0, values)
    else:
      raise NotImplementedError

  def _speed_msg(self, speed):
    values = {"%sWheelSpd" % s: speed for s in ["RL", "RR"]}
    return self.packer.make_can_msg_safety("EBCMWheelSpdRear", 0, values)

  def _user_brake_msg(self, brake):
    # GM safety has a brake threshold of 8
    values = {"BrakePedalPos": 8 if brake else 0}
    return self.packer.make_can_msg_safety("ECMAcceleratorPos", 0, values)

  def _user_gas_msg(self, gas):
    values = {"AcceleratorPedal2": 1 if gas else 0}
    if self.PCM_CRUISE:
      # Fill CruiseState with expected value if the safety mode reads cruise state from gas msg
      values["CruiseState"] = self.safety.get_controls_allowed()
    return self.packer.make_can_msg_safety("AcceleratorPedal2", 0, values)

  def _torque_driver_msg(self, torque):
    # Safety tests assume driver torque is an int, use DBC factor
    values = {"LKADriverAppldTrq": torque * 0.01}
    return self.packer.make_can_msg_safety("PSCMStatus", 0, values)

  def _torque_cmd_msg(self, torque, steer_req=1):
    values = {"LKASteeringCmd": torque, "LKASteeringCmdActive": steer_req}
    return self.packer.make_can_msg_safety("ASCMLKASteeringCmd", 0, values)

  def _button_msg(self, buttons):
    values = {"ACCButtons": buttons}
    return self.packer.make_can_msg_safety("ASCMSteeringButton", self.BUTTONS_BUS, values)


class TestGmEVSafetyBase(TestGmSafetyBase):
  EXTRA_SAFETY_PARAM = GMSafetyFlags.EV

  # existence of _user_regen_msg adds regen tests
  def _user_regen_msg(self, regen):
    values = {"RegenPaddle": 2 if regen else 0}
    return self.packer.make_can_msg_safety("EBCMRegenPaddle", 0, values)


class TestGmAscmSafety(GmLongitudinalBase, TestGmSafetyBase):
  TX_MSGS = [[0x180, 0], [0x409, 0], [0x40A, 0], [0x2CB, 0], [0x370, 0],  # pt bus
             [0xA1, 1], [0x306, 1], [0x308, 1], [0x310, 1],  # obs bus
             [0x315, 2]]  # ch bus
  FWD_BLACKLISTED_ADDRS: dict[int, list[int]] = {}
  RELAY_MALFUNCTION_ADDRS = {0: (0x180, 0x2CB)}  # ASCMLKASteeringCmd, ASCMGasRegenCmd
  FWD_BUS_LOOKUP: dict[int, int] = {}
  BRAKE_BUS = 2

  MAX_GAS = 1018
  MIN_GAS = -650  # maximum regen
  INACTIVE_GAS = -650

  def setUp(self):
    self.packer = CANPackerSafety("gm_global_a_powertrain_generated")
    self.packer_chassis = CANPackerSafety("gm_global_a_chassis")
    self.safety = libsafety_py.libsafety
    self.safety.set_safety_hooks(CarParams.SafetyModel.gm, self.EXTRA_SAFETY_PARAM)
    self.safety.init_tests()


class TestGmAscmEVSafety(TestGmAscmSafety, TestGmEVSafetyBase):
  pass


class TestGmCameraSafetyBase(TestGmSafetyBase):
  def _user_brake_msg(self, brake):
    values = {"BrakePressed": brake}
    return self.packer.make_can_msg_safety("ECMEngineStatus", 0, values)


class TestGmCameraSafety(TestGmCameraSafetyBase):
  TX_MSGS = [[0x180, 0],  # pt bus
             [0x184, 2]]  # camera bus
  FWD_BLACKLISTED_ADDRS = {2: [0x180], 0: [0x184]}  # block LKAS message and PSCMStatus
  BUTTONS_BUS = 2  # tx only

  def setUp(self):
    self.packer = CANPackerSafety("gm_global_a_powertrain_generated")
    self.packer_chassis = CANPackerSafety("gm_global_a_chassis")
    self.safety = libsafety_py.libsafety
    self.safety.set_current_safety_param_sp(0)
    self.safety.set_safety_hooks(CarParams.SafetyModel.gm, GMSafetyFlags.HW_CAM | self.EXTRA_SAFETY_PARAM)
    self.safety.init_tests()

  def test_buttons(self):
    # Only CANCEL button is allowed while cruise is enabled
    self.safety.set_controls_allowed(0)
    for btn in range(8):
      self.assertFalse(self._tx(self._button_msg(btn)))

    self.safety.set_controls_allowed(1)
    for btn in range(8):
      self.assertFalse(self._tx(self._button_msg(btn)))

    for enabled in (True, False):
      self._rx(self._pcm_status_msg(enabled))
      self.assertEqual(enabled, self._tx(self._button_msg(Buttons.CANCEL)))


class TestGmCameraICBMButtons(common.SafetyTestBase):
  TX_MSGS = None

  def setUp(self):
    self.packer = CANPackerSafety("gm_global_a_powertrain_generated")
    self.safety = libsafety_py.libsafety
    self.safety.set_current_safety_param_sp(GMSafetyFlagsSP.ICBM)
    self.safety.set_safety_hooks(CarParams.SafetyModel.gm, GMSafetyFlags.HW_CAM)
    self.safety.init_tests()

  def tearDown(self):
    self.safety.set_current_safety_param_sp(0)

  def _pcm_status_msg(self, enable):
    values = {"CruiseState": enable}
    return self.packer.make_can_msg_safety("AcceleratorPedal2", 0, values)

  def _button_msg(self, button):
    values = {"ACCButtons": button}
    return self.packer.make_can_msg_safety("ASCMSteeringButton", 2, values)

  def test_buttons(self):
    self._rx(self._pcm_status_msg(False))
    for btn in range(8):
      self.assertFalse(self._tx(self._button_msg(btn)))

    self._rx(self._pcm_status_msg(True))
    self.safety.set_controls_allowed(False)
    for btn in range(8):
      self.assertEqual(btn == Buttons.CANCEL, self._tx(self._button_msg(btn)))

    self.safety.set_controls_allowed(True)
    allowed_buttons = (Buttons.UNPRESS, Buttons.RES_ACCEL, Buttons.DECEL_SET, Buttons.CANCEL)
    for btn in range(8):
      self.assertEqual(btn in allowed_buttons, self._tx(self._button_msg(btn)))


class TestGmCameraEVSafety(TestGmCameraSafety, TestGmEVSafetyBase):
  pass


class TestGmCameraLongitudinalSafety(GmLongitudinalBase, TestGmCameraSafetyBase):
  TX_MSGS = [[0x180, 0], [0x315, 0], [0x2CB, 0], [0x370, 0],  # pt bus
             [0x184, 2]]  # camera bus
  FWD_BLACKLISTED_ADDRS = {2: [0x180, 0x2CB, 0x370, 0x315], 0: [0x184]}  # block LKAS, ACC messages and PSCMStatus
  RELAY_MALFUNCTION_ADDRS = {0: (0x180, 0x2CB, 0x370, 0x315), 2: (0x184,)}
  BUTTONS_BUS = 0  # rx only

  MAX_GAS = 1346
  MIN_GAS = -540  # maximum regen
  INACTIVE_GAS = -500

  def setUp(self):
    self.packer = CANPackerSafety("gm_global_a_powertrain_generated")
    self.packer_chassis = CANPackerSafety("gm_global_a_chassis")
    self.safety = libsafety_py.libsafety
    self.safety.set_safety_hooks(CarParams.SafetyModel.gm, GMSafetyFlags.HW_CAM | GMSafetyFlags.HW_CAM_LONG | self.EXTRA_SAFETY_PARAM)
    self.safety.init_tests()


class TestGmCameraLongitudinalEVSafety(TestGmCameraLongitudinalSafety, TestGmEVSafetyBase):
  pass


class TestGmSdgmLongitudinalSafety(TestGmCameraLongitudinalSafety):
  TX_MSGS = [[0x180, 0], [0x2CB, 0], [0x370, 0],  # pt bus
             [0x1E1, 2], [0x315, 2], [0x184, 2]]  # camera bus
  FWD_BLACKLISTED_ADDRS = {2: [0x180, 0x2CB, 0x370], 0: [0x184]}
  RELAY_MALFUNCTION_ADDRS = {0: (0x180, 0x2CB, 0x370), 2: (0x184,)}
  BRAKE_BUS = 2

  def setUp(self):
    self.packer = CANPackerSafety("gm_global_a_powertrain_generated")
    self.packer_chassis = CANPackerSafety("gm_global_a_chassis")
    self.safety = libsafety_py.libsafety
    safety_param = GMSafetyFlags.HW_CAM | GMSafetyFlags.HW_CAM_LONG | GMSafetyFlags.HW_SDGM | self.EXTRA_SAFETY_PARAM
    self.safety.set_safety_hooks(CarParams.SafetyModel.gm, safety_param)
    self.safety.init_tests()

  def test_gm_auto_hold_brake_is_stationary_and_bounded(self):
    self.safety.set_current_safety_param_sp(GMSafetyFlagsSP.GM_AUTO_HOLD)
    safety_param = GMSafetyFlags.HW_CAM | GMSafetyFlags.HW_CAM_LONG | GMSafetyFlags.HW_SDGM | self.EXTRA_SAFETY_PARAM
    self.safety.set_safety_hooks(CarParams.SafetyModel.gm, safety_param)
    self.safety.init_tests()

    self.safety.set_controls_allowed(False)
    self._rx(self._speed_msg(0))
    self._rx(self._user_gas_msg(False))
    self.assertTrue(self._tx(self._send_brake_msg(80)))
    self.assertFalse(self._tx(self._send_brake_msg(81)))

    self._rx(self._speed_msg(1.0))
    self.assertFalse(self._tx(self._send_brake_msg(80)))

    self._rx(self._speed_msg(0))
    self._rx(self._user_gas_msg(True))
    self.assertFalse(self._tx(self._send_brake_msg(80)))
    self.safety.set_current_safety_param_sp(0)

  def test_sng_resume_keeps_active_gas_under_normal_longitudinal_safety(self):
    self.safety.set_current_safety_param_sp(GMSafetyFlagsSP.AUTO_RESUME_SNG)
    safety_param = GMSafetyFlags.HW_CAM | GMSafetyFlags.HW_CAM_LONG | GMSafetyFlags.HW_SDGM | self.EXTRA_SAFETY_PARAM
    self.safety.set_safety_hooks(CarParams.SafetyModel.gm, safety_param)
    self.safety.init_tests()

    def gas_msg(gas, active):
      values = {"GasRegenCmd": gas, "GasRegenCmdActive": active}
      return self.packer.make_can_msg_safety("ASCMGasRegenCmd", 0, values)

    self.safety.set_controls_allowed(False)
    self._rx(self._speed_msg(0))
    self._rx(self._user_gas_msg(False))
    self._rx(self._user_brake_msg(False))

    self.assertFalse(self._tx(gas_msg(235, False)))
    self.assertFalse(self._tx(gas_msg(235, True)))
    self.safety.set_controls_allowed(True)
    self.assertTrue(self._tx(gas_msg(235, True)))
    self.assertTrue(self._tx(gas_msg(950, True)))
    self.assertFalse(self._tx(gas_msg(self.MAX_GAS + 1, True)))
    self.safety.set_current_safety_param_sp(0)

  def test_sng_resume_button_is_only_allowed_while_engaged_at_low_creep_speed(self):
    self.safety.set_current_safety_param_sp(GMSafetyFlagsSP.AUTO_RESUME_SNG)
    safety_param = GMSafetyFlags.HW_CAM | GMSafetyFlags.HW_CAM_LONG | GMSafetyFlags.HW_SDGM | self.EXTRA_SAFETY_PARAM
    self.safety.set_safety_hooks(CarParams.SafetyModel.gm, safety_param)
    self.safety.init_tests()

    resume = self.packer.make_can_msg_safety("ASCMSteeringButton", 2, {"ACCButtons": Buttons.RES_ACCEL})
    release = self.packer.make_can_msg_safety("ASCMSteeringButton", 2, {"ACCButtons": Buttons.UNPRESS})
    set_button = self.packer.make_can_msg_safety("ASCMSteeringButton", 2, {"ACCButtons": Buttons.DECEL_SET})
    powertrain_resume = self.packer.make_can_msg_safety("ASCMSteeringButton", 0, {"ACCButtons": Buttons.RES_ACCEL})
    powertrain_release = self.packer.make_can_msg_safety("ASCMSteeringButton", 0, {"ACCButtons": Buttons.UNPRESS})
    self._rx(self._speed_msg(0))
    self._rx(self._user_gas_msg(False))
    self._rx(self._user_brake_msg(False))

    self.safety.set_controls_allowed(True)
    self.assertTrue(self._tx(resume))
    self.assertTrue(self._tx(release))
    self.assertTrue(self._tx(powertrain_resume))
    self.assertTrue(self._tx(powertrain_release))
    self.assertFalse(self._tx(set_button))

    self.safety.set_controls_allowed(False)
    self.assertFalse(self._tx(resume))
    self.assertFalse(self._tx(powertrain_resume))

    self.safety.set_controls_allowed(True)
    # The successful physical Traverse press occurred at about 5.7 km/h.
    self._rx(self._speed_msg(5.7))
    self.assertTrue(self._tx(resume))
    self.assertTrue(self._tx(powertrain_resume))

    self._rx(self._speed_msg(7.1))
    self.assertFalse(self._tx(resume))
    self.assertFalse(self._tx(powertrain_resume))

    self._rx(self._speed_msg(0))
    self.safety.set_controls_allowed(True)
    self._rx(self._user_brake_msg(True))
    self.assertFalse(self._tx(resume))
    self.assertFalse(self._tx(powertrain_resume))

    self._rx(self._user_brake_msg(False))
    self.safety.set_controls_allowed(True)
    self._rx(self._user_gas_msg(True))
    self.assertFalse(self._tx(resume))
    self.assertFalse(self._tx(powertrain_resume))
    self.safety.set_current_safety_param_sp(0)

  def test_sng_resume_temporarily_replaces_only_stock_button_frames(self):
    self.safety.set_current_safety_param_sp(GMSafetyFlagsSP.AUTO_RESUME_SNG)
    safety_param = GMSafetyFlags.HW_CAM | GMSafetyFlags.HW_CAM_LONG | GMSafetyFlags.HW_SDGM | self.EXTRA_SAFETY_PARAM
    self.safety.set_safety_hooks(CarParams.SafetyModel.gm, safety_param)
    self.safety.init_tests()
    self.safety.set_timer(100)
    self.safety.set_controls_allowed(True)
    self._rx(self._speed_msg(0))
    self._rx(self._user_gas_msg(False))
    self._rx(self._user_brake_msg(False))

    resume = self.packer.make_can_msg_safety("ASCMSteeringButton", 2, {"ACCButtons": Buttons.RES_ACCEL})
    release = self.packer.make_can_msg_safety("ASCMSteeringButton", 2, {"ACCButtons": Buttons.UNPRESS, "RollingCounter": 2})
    wrong_stock_release = self.packer.make_can_msg_safety("ASCMSteeringButton", 0,
                                                          {"ACCButtons": Buttons.UNPRESS, "RollingCounter": 1})
    stock_release = self.packer.make_can_msg_safety("ASCMSteeringButton", 0,
                                                    {"ACCButtons": Buttons.UNPRESS, "RollingCounter": 2})

    self.assertEqual(2, self.safety.safety_fwd_hook(0, 0x1E1))
    self.assertTrue(self._tx(resume))
    self.assertEqual(-1, self.safety.safety_fwd_hook(0, 0x1E1))
    self.assertEqual(2, self.safety.safety_fwd_hook(0, 0x123))

    self.assertTrue(self._tx(release))
    self.assertEqual(-1, self.safety.safety_fwd_hook(0, 0x1E1))
    self._rx(wrong_stock_release)
    self.assertEqual(-1, self.safety.safety_fwd_hook(0, 0x1E1))
    self._rx(stock_release)
    self.assertEqual(2, self.safety.safety_fwd_hook(0, 0x1E1))
    self.safety.set_current_safety_param_sp(0)

  def test_sng_button_filter_aborts_on_timeout_and_driver_inputs(self):
    self.safety.set_current_safety_param_sp(GMSafetyFlagsSP.AUTO_RESUME_SNG)
    safety_param = GMSafetyFlags.HW_CAM | GMSafetyFlags.HW_CAM_LONG | GMSafetyFlags.HW_SDGM | self.EXTRA_SAFETY_PARAM
    self.safety.set_safety_hooks(CarParams.SafetyModel.gm, safety_param)
    self.safety.init_tests()
    self.safety.set_controls_allowed(True)
    self._rx(self._speed_msg(0))
    self._rx(self._user_gas_msg(False))
    self._rx(self._user_brake_msg(False))
    resume = self.packer.make_can_msg_safety("ASCMSteeringButton", 2, {"ACCButtons": Buttons.RES_ACCEL})

    self.safety.set_timer(100)
    self.assertTrue(self._tx(resume))
    self.assertEqual(-1, self.safety.safety_fwd_hook(0, 0x1E1))
    self.safety.set_timer(500_101)
    self.assertEqual(2, self.safety.safety_fwd_hook(0, 0x1E1))

    self.safety.set_controls_allowed(True)
    self.safety.set_timer(600_000)
    self.assertTrue(self._tx(resume))
    self._rx(self._user_brake_msg(True))
    self.assertEqual(2, self.safety.safety_fwd_hook(0, 0x1E1))

    self._rx(self._user_brake_msg(False))
    self.safety.set_controls_allowed(True)
    self.assertTrue(self._tx(resume))
    self._rx(self._speed_msg(7.1))
    self.assertEqual(2, self.safety.safety_fwd_hook(0, 0x1E1))
    self.safety.set_current_safety_param_sp(0)

  def test_sng_driver_cancel_is_always_relayable_on_camera_bus(self):
    self.safety.set_current_safety_param_sp(GMSafetyFlagsSP.AUTO_RESUME_SNG)
    safety_param = GMSafetyFlags.HW_CAM | GMSafetyFlags.HW_CAM_LONG | GMSafetyFlags.HW_SDGM | self.EXTRA_SAFETY_PARAM
    self.safety.set_safety_hooks(CarParams.SafetyModel.gm, safety_param)
    self.safety.init_tests()
    cancel = self.packer.make_can_msg_safety("ASCMSteeringButton", 2, {"ACCButtons": Buttons.CANCEL})
    self.safety.set_controls_allowed(False)
    self.assertTrue(self._tx(cancel))
    self.safety.set_current_safety_param_sp(0)

  def test_gm_auto_hold_does_not_reenable_resume_button_spam(self):
    self.safety.set_current_safety_param_sp(GMSafetyFlagsSP.GM_AUTO_HOLD)
    safety_param = GMSafetyFlags.HW_CAM | GMSafetyFlags.HW_CAM_LONG | GMSafetyFlags.HW_SDGM | self.EXTRA_SAFETY_PARAM
    self.safety.set_safety_hooks(CarParams.SafetyModel.gm, safety_param)
    self.safety.init_tests()

    self.safety.set_controls_allowed(True)
    self._rx(self._speed_msg(0))
    self._rx(self._user_brake_msg(False))
    for button in range(8):
      msg = self.packer.make_can_msg_safety("ASCMSteeringButton", 2, {"ACCButtons": button})
      self.assertFalse(self._tx(msg))

    self.safety.set_current_safety_param_sp(0)


class TestGmCameraNonACCSafety(TestGmCameraSafety):

  def setUp(self):
    self.packer = CANPackerSafety("gm_global_a_powertrain_generated")
    self.packer_chassis = CANPackerSafety("gm_global_a_chassis")
    self.safety = libsafety_py.libsafety
    self.safety.set_current_safety_param_sp(GMSafetyFlagsSP.NON_ACC)
    self.safety.set_safety_hooks(CarParams.SafetyModel.gm, GMSafetyFlags.HW_CAM | self.EXTRA_SAFETY_PARAM)
    self.safety.init_tests()

  def _pcm_status_msg(self, enable):
    values = {"CruiseActive": enable}
    return self.packer.make_can_msg_safety("ECMCruiseControl", 0, values)


class TestGmCameraEVNonACCSafety(TestGmCameraNonACCSafety, TestGmEVSafetyBase):
  pass


class TestGmIgnition(unittest.TestCase):
  TX_MSGS: list = []

  def setUp(self):
    self.safety = libsafety_py.libsafety
    self.safety.init_tests()
    self.packer = CANPackerSafety("gm_global_a_powertrain_generated")

  def _msg(self, mode):
    return self.packer.make_can_msg_safety("BCMGeneralPlatformStatus", 0, {"SystemPowerMode": mode})

  # SystemPowerMode 2=Run, 3=Crank Request
  def test_ignition_on(self):
    self.safety.ignition_can_hook(self._msg(2))
    self.assertTrue(self.safety.get_ignition_can())

  def test_ignition_off(self):
    self.safety.ignition_can_hook(self._msg(2))
    self.assertTrue(self.safety.get_ignition_can())
    self.safety.ignition_can_hook(self._msg(0))
    self.assertFalse(self.safety.get_ignition_can())


if __name__ == "__main__":
  unittest.main()
