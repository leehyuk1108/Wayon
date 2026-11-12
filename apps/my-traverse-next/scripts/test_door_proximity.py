from contextlib import nullcontext
import unittest
from unittest.mock import patch

from door_proximity import Beacon, Policy, SERVICE_UUID, authenticate, encode
from gmone_door_control import DoorCommand
from wayon_door_proximity import dispatch, read_sample


KEY = bytes(range(32))
SLOT = 456789012


class ProximityTest(unittest.TestCase):
  def test_matches_android_wire_format_and_rejects_forgery_and_old_slot(self):
    beacon = Beacon(SLOT, -68, -84)
    packet = encode(KEY, beacon)
    self.assertEqual(packet.hex(), "0c14bcac006be5e979600c3c55")
    self.assertEqual(authenticate(KEY, packet, SLOT * 4 + 5), beacon)
    self.assertIsNone(authenticate(KEY, packet, SLOT * 4 + 8))
    self.assertIsNone(authenticate(KEY, packet, (SLOT + 65536) * 4))
    self.assertIsNone(authenticate(KEY, packet, SLOT * 4 - 1))
    self.assertIsNone(authenticate(bytes(32), packet, SLOT * 4))
    self.assertIsNone(authenticate(KEY, packet[:2] + b"\xbf" + packet[3:], SLOT * 4))
    with self.assertRaises(ValueError):
      encode(KEY, Beacon(SLOT, -68, -70))

  def test_closed_and_parked_confirmed_walk_away_and_return(self):
    policy = Policy()
    fired = []
    for second in range(38):
      dbm = -90 if second < 7 or second >= 24 else -55
      cmd = policy.update(Beacon(SLOT + second // 4, -68, -84), dbm, second,
                          parked=True, closed=True)
      if cmd is not None:
        fired.append(cmd)
    self.assertEqual(fired, [DoorCommand.UNLOCK, DoorCommand.LOCK])

  def test_strong_start_loss_of_signal_ignition_and_closed_gate_do_not_actuate(self):
    policy = Policy()
    for second in range(7):
      self.assertIsNone(policy.update(Beacon(SLOT + second // 4, -68, -84), -52, second,
                                      parked=True, closed=True))
    policy.expire(12, True)
    for second in range(12, 20):
      self.assertIsNone(policy.update(Beacon(SLOT + second // 4, -68, -84), -92, second,
                                      parked=True, closed=True))
    for second in range(20, 28):
      self.assertIsNone(policy.update(Beacon(SLOT + second // 4, -68, -84), -52, second,
                                      parked=False, closed=True))
    for second in range(28, 45):
      self.assertIsNone(policy.update(Beacon(SLOT + second // 4, -68, -84),
                                      -52 if second < 35 else -92, second, parked=True, closed=False))

  def test_duplicate_slot_and_profile_changes_cannot_start_unlock(self):
    policy = Policy()
    for second in range(7):
      policy.update(Beacon(SLOT + second // 4, -68, -84), -92, second, parked=True, closed=True)
    for second in range(7, 15):
      self.assertIsNone(policy.update(Beacon(SLOT + 1, -68, -84), -51, second, parked=True, closed=True))
    for second in range(15, 27):
      near = -70 if second < 24 else -72
      self.assertIsNone(policy.update(Beacon(SLOT + second // 4, near, -84), -51, second,
                                      parked=True, closed=True))

  def test_dbus_rejects_rssi_and_authentication_in_separate_updates(self):
    beacon = Beacon(SLOT, -68, -84)
    data = {"ServiceData": ("a{sv}", {SERVICE_UUID: ("ay", encode(KEY, beacon))})}
    rssi = {"RSSI": ("n", -75)}
    wall = SLOT * 4
    self.assertIsNone(read_sample(KEY, data, wall))
    self.assertIsNone(read_sample(KEY, rssi, wall))
    self.assertEqual(read_sample(KEY, data | rssi, wall), (beacon, -75))
    self.assertIsNone(read_sample(KEY, data | rssi, wall + 8))

  def test_unlock_requires_fresh_door_observation(self):
    policy = Policy()
    for second in range(20):
      dbm = -90 if second < 7 else -55
      self.assertIsNone(policy.update(Beacon(SLOT + second // 4, -68, -84), dbm, second,
                                      parked=True, closed=second < 7))

  def test_departure_is_preserved_during_cooldown_and_busy_sender(self):
    policy = Policy()
    fired = []
    for second in range(29):
      dbm = -55 if 7 <= second < 12 else -90
      command = policy.update(Beacon(SLOT + second // 4, -68, -84), dbm, second,
                              parked=True, closed=second != 24, ready=not 21 <= second < 24)
      if command is not None:
        fired.append((second, command))
    self.assertEqual(fired, [(10, DoorCommand.UNLOCK), (25, DoorCommand.LOCK)])

  def test_execution_checks_freshness_again_and_dry_run_uses_no_credentials(self):
    with patch("wayon_door_proximity.one_request", return_value=nullcontext()), \
         patch("wayon_door_proximity.read_credentials", return_value=object()) as credentials, \
         patch("wayon_door_proximity.diagnostic_waiting", return_value=False), \
         patch("wayon_door_proximity.vehicle_check", return_value=None) as check, \
         patch("wayon_door_proximity.time.monotonic", side_effect=[10, 10, 12]), \
         patch("wayon_door_proximity.send_command") as send:
      self.assertEqual(dispatch(DoorCommand.UNLOCK, False, 11), "dry_run")
      credentials.assert_not_called()
      self.assertEqual(dispatch(DoorCommand.UNLOCK, True, 11), "observation_expired")
      check.assert_called_once_with(DoorCommand.UNLOCK, require_closed=True)
      send.assert_not_called()


if __name__ == "__main__":
  unittest.main()
