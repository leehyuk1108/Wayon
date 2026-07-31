from types import SimpleNamespace
import unittest

from opendbc.can import CANPacker
from opendbc.can.dbc import DBC
from opendbc.can.parser import get_raw_value
from opendbc.car import structs
from opendbc.car.gm.values import CruiseButtons
from opendbc.sunnypilot.car.gm.icbm import BUTTON_PRESS_FRAMES, IntelligentCruiseButtonManagementInterface

SendButtonState = structs.IntelligentCruiseButtonManagement.SendButtonState


class TestGMIntelligentCruiseButtonManagement(unittest.TestCase):
  def setUp(self):
    self.controller = IntelligentCruiseButtonManagementInterface(SimpleNamespace(), SimpleNamespace())
    self.packer = CANPacker("gm_global_a_powertrain_generated")
    self.dbc_msg = DBC("gm_global_a_powertrain_generated").addr_to_msg[0x1E1]
    self.CS = SimpleNamespace(
      buttons_counter=0,
      cruise_buttons=CruiseButtons.UNPRESS,
      out=SimpleNamespace(cruiseState=SimpleNamespace(enabled=True)),
    )
    self.CC_SP = SimpleNamespace(
      intelligentCruiseButtonManagement=SimpleNamespace(sendButton=SendButtonState.increase),
    )

  def tearDown(self):
    self.controller.close_test_socket()

  def decode(self, can_msg):
    dat = can_msg[1]
    sigs = self.dbc_msg.sigs
    return {
      name: int(get_raw_value(dat, sigs[name]))
      for name in ("ACCButtons", "RollingCounter", "SteeringButtonChecksum")
    }

  def run_counter(self, counter, first_frame):
    messages = []
    self.CS.buttons_counter = counter
    for frame in range(first_frame, first_frame + 3):
      messages.extend(self.controller.update(self.CS, self.CC_SP, self.packer, frame))
    return messages

  def test_route_matched_press_sequence(self):
    messages = []
    for counter in range(4):
      messages.extend(self.run_counter(counter, counter * 3))

    self.assertEqual(BUTTON_PRESS_FRAMES, len(messages))
    decoded = [self.decode(msg) for msg in messages]
    self.assertEqual([0, 1, 2, 3], [msg["RollingCounter"] for msg in decoded])
    self.assertTrue(all(msg["ACCButtons"] == CruiseButtons.RES_ACCEL for msg in decoded))
    self.assertEqual(
      ["000000010020ef", "000000010125de", "00000001022acd", "00000001032fbc"],
      [msg[1].hex() for msg in messages],
    )

    # Repeated control-loop updates and the next stock counter do not create
    # extra frames. The stock UNPRESS frame performs the release.
    self.assertEqual([], self.run_counter(0, 12))

  def test_decrease_uses_set_button(self):
    self.CC_SP.intelligentCruiseButtonManagement.sendButton = SendButtonState.decrease
    messages = self.run_counter(2, 0)
    self.assertEqual(CruiseButtons.DECEL_SET, self.decode(messages[0])["ACCButtons"])

  def test_physical_button_interrupts_sequence(self):
    self.assertEqual(1, len(self.run_counter(0, 0)))
    self.CS.cruise_buttons = CruiseButtons.RES_ACCEL
    self.assertEqual([], self.run_counter(1, 3))
    self.assertEqual(0, self.controller.press_frames_remaining)

  def test_disabled_cruise_blocks_sequence(self):
    self.CS.out.cruiseState.enabled = False
    self.assertEqual([], self.run_counter(0, 0))

  def test_web_command_uses_route_matched_sequence(self):
    self.CC_SP.intelligentCruiseButtonManagement.sendButton = SendButtonState.none
    self.assertTrue(self.controller.queue_test_button("set"))

    messages = []
    for counter in range(4):
      messages.extend(self.run_counter(counter, counter * 3))

    self.assertEqual(BUTTON_PRESS_FRAMES, len(messages))
    self.assertTrue(all(self.decode(msg)["ACCButtons"] == CruiseButtons.DECEL_SET for msg in messages))

  def test_main_web_command_is_rejected(self):
    self.assertFalse(self.controller.queue_test_button("main"))


if __name__ == "__main__":
  unittest.main()
