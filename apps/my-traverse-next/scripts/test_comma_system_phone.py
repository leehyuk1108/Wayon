from pathlib import Path
import tempfile
import unittest
from contextlib import nullcontext
from unittest.mock import AsyncMock, patch

from comma_rssi_receiver import Receiver
from comma_system_phone import PhoneNotSeen, configured_address, parse_link_rssi


class SystemPhoneTest(unittest.IsolatedAsyncioTestCase):
  def test_address_must_be_private_and_not_a_placeholder(self):
    with tempfile.TemporaryDirectory() as temp:
      path = Path(temp) / "phone"
      path.write_text("A0:00:00:00:00:01\n")
      path.chmod(0o600)
      self.assertEqual(configured_address(path), "A0:00:00:00:00:01")
      path.chmod(0o644)
      with self.assertRaises(ValueError):
        configured_address(path)
      path.chmod(0o600)
      path.write_text("02:00:00:00:00:00")
      with self.assertRaises(ValueError):
        configured_address(path)

  def test_signal_is_relative_and_unavailable_is_not_zero(self):
    for value in (-128, -31, 0, 12, 126):
      self.assertEqual(parse_link_rssi(f"RSSI return value: {value}\n".encode()), value)
    for output in (b"", b"RSSI return value: 127\n", b"fake -50\n"):
      self.assertIsNone(parse_link_rssi(output))

  async def test_no_probe_while_driving_or_measuring_and_no_saved_row(self):
    now = [100.]
    parked = [False]
    receiver = Receiver("test", None, is_parked=lambda: parked[0], clock=lambda: now[0])
    with patch("comma_rssi_receiver.diagnostic_priority", return_value=nullcontext(True)), \
         patch("comma_system_phone.phone_rssi", new_callable=AsyncMock) as probe:
      self.assertEqual((await receiver.system_phone())[1], 409)
      probe.assert_not_called()
      parked[0] = True
      receiver.active = object()
      self.assertEqual((await receiver.system_phone())[1], 409)
      probe.assert_not_called()
      receiver.active = None
      probe.return_value = -31
      self.assertEqual(await receiver.system_phone(), ({"source": "comma", "linkRssi": -31}, 200))
      self.assertEqual(receiver.runs, [])
      self.assertEqual((await receiver.system_phone())[1], 429)
      now[0] += 6.
      probe.side_effect = PhoneNotSeen()
      self.assertEqual(await receiver.system_phone(), ({"error": "phone_not_seen"}, 409))
