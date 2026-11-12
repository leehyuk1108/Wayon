from contextlib import nullcontext
from datetime import datetime, timezone
import errno
import json
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from gmone_door_control import DoorCommand
from system_phone_auto_unlock import (
  Approach, CONNECT_NOT_READY, KST, LINK_ERROR, LocalLockEdge, LockGrace, finish_door_action, lock_status, monitor,
  record_intent, secure_sample, UnlockTiming, FAST_PERIOD_S, RECEIVED_PERIOD_S, UNLOCK_TRACE_MAX_SAMPLES,
)

NOW = 1_800_000_000
SCOPE = "a" * 64


def iso(seconds):
  return datetime.fromtimestamp(seconds, timezone.utc).isoformat()


def status(door=0, observed=NOW - 10, collected=NOW - 1, scope=SCOPE):
  return {"vehicleStatus": {
    "ok": True, "stale": False, "source": "gmone-direct", "clientScope": scope,
    "updatedAt": iso(observed), "collectedAt": iso(collected),
    "data": {"last_update": datetime.fromtimestamp(observed, KST).strftime("%Y-%m-%d %H:%M:%S"),
             "gmone_details": {"closures": {"doors": {"raw": door}}}},
  }}


class UnlockTest(unittest.IsolatedAsyncioTestCase):
  def test_status_needs_scoped_recent_vehicle_observation_not_recent_receipt(self):
    self.assertEqual(lock_status(status(), SCOPE, NOW), ("locked", NOW - 10))
    self.assertEqual(lock_status(status(observed=NOW - 121), SCOPE, NOW), ("stale", None))
    for payload in (status(scope="b" * 64), status(door=False), status(observed=NOW + 3), status(door=3)):
      self.assertEqual(lock_status(payload, SCOPE, NOW), ("unknown", None))
    payload = status()
    payload["vehicleStatus"]["updatedAt"] = iso(NOW - 1)
    self.assertEqual(lock_status(payload, SCOPE, NOW), ("unknown", None))

  def test_official_cache_uses_vehicle_observation_not_upload_age(self):
    for age, expected in ((15, "locked"), (121, "stale")):
      payload = status(observed=NOW - age)
      payload["vehicleStatus"]["source"] = "gmone-official-cache"
      self.assertEqual(lock_status(payload, SCOPE, NOW)[0], expected)

  def test_latest_unlocked_or_partial_unlock_cannot_send(self):
    for door in (1, 2):
      self.assertEqual(lock_status(status(door=door), SCOPE, NOW), ("unlocked", None))
    event = {"known": True, "locked": False, "occurredAt": iso(NOW - 5)}
    self.assertEqual(lock_status(status(), SCOPE, NOW, event), ("unlocked", None))
    event["occurredAt"] = iso(NOW - 20)
    self.assertEqual(lock_status(status(), SCOPE, NOW, event), ("locked", NOW - 10))

  def test_real_far_then_first_near_only_once(self):
    p = Approach(-12, -27)
    self.assertFalse(any(p.observe(t, -9) for t in range(6)))
    self.assertFalse(any(p.observe(t, -32) for t in range(6, 11)))
    self.assertEqual([p.observe(t, -10) for t in range(11, 17)], [True, False, False, False, False, False])
    self.assertTrue(p.still_near(17))
    self.assertFalse(p.still_near(19))
    for t in range(17, 22):
      p.observe(t, -34)
    p.observe(22, None)
    self.assertEqual([p.observe(t, -10) for t in range(23, 29)], [True] + [False] * 5)
    with self.assertRaises(ValueError):
      Approach(-25, -27)

  def test_three_db_gap_keeps_two_neutral_values(self):
    p = Approach(-11, -14)
    for t in range(6):
      self.assertIsNone(p.transition(t, -14, enable_lock=True))
    for t, signal in enumerate((-13, -12), 6):
      self.assertIsNone(p.transition(t, signal, enable_lock=True))
    self.assertIs(p.transition(8, -11, enable_lock=True), DoorCommand.UNLOCK)

  def test_confirmed_departure_carries_two_misses_but_not_three_or_a_hard_link_error(self):
    for misses, return_at, expected in (
      ([(5, None)], 6, DoorCommand.UNLOCK),
      ([(5, None), (6, LINK_ERROR)], 7, DoorCommand.UNLOCK),
      ([(5, None), (6, None), (7, None)], 8, None),
      ([(5, None)], 15, None),
      ([(5, LINK_ERROR)], 6, None),
    ):
      with self.subTest(misses=misses, return_at=return_at):
        p = Approach(-8, -12)
        for t in range(5):
          self.assertIsNone(p.transition(t, -12))
        for t, reading in misses:
          soft_error = reading is LINK_ERROR and len(misses) == 2
          self.assertIsNone(p.transition(t, reading, connect_not_ready=soft_error))
        self.assertIs(p.transition(return_at, -8), expected)
        self.assertIsNone(p.transition(return_at + 1, -7))

  def test_manual_lock_discards_retained_departure_until_new_measured_departure(self):
    p = Approach(-8, -12)
    for t in range(5):
      p.transition(t, -12)
    p.transition(5, None)
    p.hold_after_local_lock(5.5)
    self.assertIsNone(p.transition(6, -7))
    self.assertIsNone(p.transition(7, None))
    self.assertIsNone(p.transition(8, -7))
    # A short RSSI dip and another strong sample are not a new departure.
    for t in range(9, 13):
      self.assertIsNone(p.transition(t, -12))
    self.assertIsNone(p.transition(13, -8))
    # Long RF loss alone also must not reopen the local lock.
    for t in (14, 20, 26, 32):
      self.assertIsNone(p.transition(t, None))
    self.assertIsNone(p.transition(34, -7))
    for t in range(35, 41):
      self.assertIsNone(p.transition(t, -12))
    self.assertIsNone(p.transition(41, None))
    self.assertIs(p.transition(42, -8), DoorCommand.UNLOCK)
    self.assertIsNone(p.transition(43, -7))

  def test_local_lock_edges_distinguish_new_external_lock_from_own_and_stale(self):
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / "door-state.json"
      edge = LocalLockEdge(path)

      def write(locked, timestamp):
        path.write_text(json.dumps({"locked": locked, "observedAt": iso(timestamp)}))

      write(True, NOW - 40)
      self.assertFalse(edge.external_lock(NOW))
      write(False, NOW - 1)
      self.assertFalse(edge.external_lock(NOW))
      write(True, NOW)
      self.assertTrue(edge.external_lock(NOW))
      self.assertFalse(edge.external_lock(NOW + 1))
      edge.auto_lock_at = NOW + 2
      write(True, NOW + 6)
      self.assertFalse(edge.external_lock(NOW + 6))
      write(True, NOW + 7)
      self.assertTrue(edge.external_lock(NOW + 7))

  def test_unlock_timing_is_bounded_and_only_repeats_new_blocked_states(self):
    timing = UnlockTiming()
    timing.record(0, 2, "not_seen", None)
    for i in range(1000):
      at = 90 + i / 10
      timing.record(at - .05, at, "received", -12)
    self.assertEqual(len(timing.samples), UNLOCK_TRACE_MAX_SAMPLES)
    timing.record(299.8, 300, "received", -8, "return_not_armed")
    with patch("builtins.print") as log:
      timing.blocked(300, 6, "return_not_armed")
      timing.blocked(321, 6, "return_not_armed")
      timing.blocked(322, 6, "local_lock")
    self.assertEqual(log.call_count, 2)
    trace = json.loads(log.call_args_list[0].args[1])
    self.assertEqual(trace["samples"], [[0, .2, "received", -8, "return_not_armed"]])

  async def test_vehicle_unlock_without_automatic_request_retains_detection_history(self):
    class EndOfSamples(Exception):
      pass

    clock = [0]
    readings = iter([(3, None), (3.01, CONNECT_NOT_READY), (6, -13)])
    edge = SimpleNamespace(last_observed=0, last_locked=None)

    async def sample(_address, _parked):
      item = next(readings, None)
      if item is None:
        raise EndOfSamples
      clock[0], value = item
      return value

    def observe(now):
      if now == NOW + 6:
        edge.last_observed, edge.last_locked = NOW + 5.9, False
      return False

    edge.external_lock = observe
    with patch("system_phone_auto_unlock.asyncio.sleep", new_callable=AsyncMock), \
         patch("system_phone_auto_unlock.time", SimpleNamespace(monotonic=lambda: clock[0], time=lambda: NOW + clock[0])), \
         patch("system_phone_auto_unlock.diagnostic_waiting", return_value=False), \
         patch("system_phone_auto_unlock.secure_sample", side_effect=sample), \
         patch("system_phone_auto_unlock.finish_door_action") as send, patch("builtins.print") as log:
      with self.assertRaises(EndOfSamples):
        await monitor(SimpleNamespace(parked=lambda: True), "fixture", Approach(-8, -12), True, False, lock_edge=edge)
    send.assert_not_called()
    trace = json.loads(log.call_args.args[1])
    self.assertEqual(trace["outcome"], "vehicle_unlock_observed")
    self.assertEqual(trace["vehicle_observed_at"], NOW + 5.9)
    self.assertEqual([row[2] for row in trace["samples"]], ["not_seen", "enotconn", "received"])

  def test_user_thresholds_lock_on_departure_and_keep_unlock_on_return(self):
    p = Approach(-80, -93)
    self.assertEqual([p.transition(t, -80, enable_lock=True) for t in range(4)], [None] * 4)
    self.assertEqual([p.transition(t, -92, enable_lock=True) for t in range(4, 6)], [None] * 2)
    self.assertEqual([p.transition(t, -93, enable_lock=True) for t in range(6, 13)],
                     [None] * 5 + [DoorCommand.LOCK, None])
    self.assertEqual([p.transition(t, -80, enable_lock=True) for t in range(13, 17)],
                     [DoorCommand.UNLOCK] + [None] * 3)

  def test_no_departure_on_startup_disconnect_or_when_lock_disabled(self):
    p = Approach(-80, -93)
    self.assertTrue(all(p.transition(t, -94, enable_lock=True) is None for t in range(9)))
    p.reset()
    for t in range(4):
      p.transition(t, -78, enable_lock=True)
    self.assertTrue(all(p.transition(t, -96) is None for t in range(4, 10)))
    self.assertIsNone(p.transition(10, None, enable_lock=True))
    self.assertTrue(all(p.transition(t, -96, enable_lock=True) is None for t in range(11, 21)))

  def test_one_near_sample_can_unlock_but_cannot_arm_a_lock(self):
    p = Approach(-80, -93)
    self.assertTrue(all(p.transition(t, -93, enable_lock=True) is None for t in range(5)))
    self.assertIs(p.transition(5, -80, enable_lock=True), DoorCommand.UNLOCK)
    self.assertTrue(all(p.transition(t, -93, enable_lock=True) is None for t in range(6, 15)))

  def test_measured_walk_gap_locks_and_reacquired_near_unlocks_once(self):
    p = Approach(-80, -93)
    samples = [(0, -30), (1.4, -13), (2.8, -28), (4.2, -41),
               (8, None), (14, None), (20, None), (26, None), (32, None),
               (38, -30), (39.4, -31), (40.8, -29), (42.2, -28), (43.6, -30)]
    self.assertEqual([p.transition(t, v, enable_lock=True) for t, v in samples],
                     [None] * 5 + [DoorCommand.LOCK] + [None] * 3 + [DoorCommand.UNLOCK] + [None] * 4)

  def test_weakening_signal_then_two_misses_locks_at_five_seconds(self):
    p = Approach(-80, -93)
    trace = [(0, -79), (1, -79), (2, -80), (3, -80), (4, -88), (5, -90),
             (8, None), (9.9, None)]
    self.assertTrue(all(p.transition(t, value, enable_lock=True) is None for t, value in trace))
    self.assertIs(p.transition(10, None, enable_lock=True), DoorCommand.LOCK)
    self.assertIsNone(p.transition(13, None, enable_lock=True))

  def test_quick_return_after_confirmed_loss_unlocks_without_eighteen_seconds(self):
    for auto_lock in (False, True):
      with self.subTest(auto_lock=auto_lock):
        p = Approach(-80, -93)
        trace = [(0, -30), (1, -31), (2, -32), (3, -31), (4, -40), (7, None), (10, None),
                 (11, -32), (12, -30)]
        actions = [p.transition(t, value, enable_lock=auto_lock) for t, value in trace]
        self.assertEqual(actions, [None] * 6 + [DoorCommand.LOCK if auto_lock else None, DoorCommand.UNLOCK, None])

  def test_link_error_or_unobserved_gap_cancels_short_return(self):
    for extra, return_at in (((11, LINK_ERROR), 12), (None, 20)):
      with self.subTest(extra=extra):
        p = Approach(-80, -93)
        for t, value in ((0, -30), (1, -30), (2, -30), (3, -30), (7, None), (10, None)):
          p.transition(t, value)
        if extra:
          p.transition(*extra)
        self.assertIsNone(p.transition(return_at, -30))

  def test_single_miss_startup_and_link_errors_do_not_lock(self):
    cases = (
      [(8, None), (9, -80), (10, -80)],
      [(8, None), (9, LINK_ERROR), (13, None), (18, None)],
      [(8, LINK_ERROR), (13, LINK_ERROR), (18, LINK_ERROR)],
      [(14, None), (19, None)],
    )
    for trace in cases:
      with self.subTest(trace=trace):
        p = Approach(-80, -93)
        for t in range(4):
          p.transition(t, -80, enable_lock=True)
        self.assertTrue(all(p.transition(t, value, enable_lock=True) is None for t, value in trace))
    p = Approach(-80, -93)
    self.assertTrue(all(p.transition(t, None, enable_lock=True) is None for t in range(0, 30, 3)))

  def test_measured_lock_is_not_duplicated_by_later_signal_loss(self):
    p = Approach(-80, -93)
    for t in range(4):
      p.transition(t, -80, enable_lock=True)
    self.assertEqual([p.transition(t, -93, enable_lock=True) for t in range(4, 10)],
                     [None] * 5 + [DoorCommand.LOCK])
    self.assertTrue(all(p.transition(t, None, enable_lock=True) is None for t in (13, 17, 21)))

  async def test_secure_sample_distinguishes_unreachable_from_link_failure(self):
    link = MagicMock()
    link.__enter__.return_value = link
    link.getsockopt.return_value = struct.pack("BB", 4, 16)
    bluetooth = SimpleNamespace(AF_BLUETOOTH=31, SOCK_SEQPACKET=5, BTPROTO_L2CAP=0, socket=lambda *_: link)
    connect = AsyncMock()
    read = AsyncMock(return_value=-31)
    loop = SimpleNamespace(sock_connect=connect)
    for failure, expected in ((TimeoutError(), None), (OSError(errno.EHOSTDOWN, "remote"), None),
                              (OSError(errno.ENOTCONN, "retry"), CONNECT_NOT_READY),
                              (OSError(errno.EACCES, "authentication"), LINK_ERROR),
                              (OSError(errno.ENETDOWN, "adapter"), LINK_ERROR), (None, -31)):
      with self.subTest(failure=failure):
        connect.side_effect = failure
        with patch("system_phone_auto_unlock.socket", bluetooth), \
             patch("system_phone_auto_unlock.asyncio.get_running_loop", return_value=loop), \
             patch("system_phone_auto_unlock.read_link_rssi", read):
          self.assertEqual(await secure_sample("fixture", lambda: True), expected)
    with patch("system_phone_auto_unlock.socket", bluetooth), \
         patch("system_phone_auto_unlock.asyncio.get_running_loop", return_value=loop), \
         patch("system_phone_auto_unlock.read_link_rssi", read):
      link.getsockopt.return_value = struct.pack("BB", 3, 16)
      self.assertIs(await secure_sample("fixture", lambda: True), LINK_ERROR)

  def test_return_needs_continuous_misses(self):
    for samples in (
      [(0, None), (6, None), (12, None), (18, None)],
      [(0, -24), (1, -26), (2, -25), (3, -23), (8, None), (26, None)],
      [(0, -24), (1, -26), (2, -25), (3, -23), (23, None)],
    ):
      with self.subTest(samples=samples):
        p = Approach(-80, -93)
        for t, value in samples:
          self.assertIsNone(p.transition(t, value, enable_lock=True))
        self.assertTrue(all(p.transition(t, -35, enable_lock=True) is None for t in range(29, 36)))

  def test_startup_absence_unlocks_on_first_qualifying_sample_without_prior_near(self):
    p = Approach(-80, -93)
    for t in range(0, 60, 6):
      self.assertIsNone(p.transition(t, None, enable_lock=True))
    self.assertIs(p.transition(60, -25, enable_lock=True), DoorCommand.UNLOCK)
    self.assertIsNone(p.transition(61.3, -20, enable_lock=True))

  def test_startup_absence_requires_full_wait_and_is_not_reopened_by_a_short_gap(self):
    p = Approach(-80, -93)
    for t in (0, 6, 12):
      self.assertIsNone(p.transition(t, None, enable_lock=True))
    self.assertIsNone(p.transition(17.9, -81, enable_lock=True))
    for t in (20, 26, 32, 38):
      self.assertIsNone(p.transition(t, None, enable_lock=True))
    self.assertIsNone(p.transition(44, -80, enable_lock=True))

  def test_first_recovery_sample_below_near_waits_until_threshold(self):
    p = Approach(-80, -93)
    samples = [(0, -40), (1, -41), (2, -42), (3, -40), (8, None), (14, None),
               (20, None), (26, None), (28, -81), (29, -88), (30, None)]
    self.assertTrue(all(p.transition(t, v) is None for t, v in samples))
    self.assertIs(p.transition(34, -80, enable_lock=True), DoorCommand.UNLOCK)
    self.assertIsNone(p.transition(35, -85, enable_lock=True))
    self.assertIsNone(p.transition(36, -80, enable_lock=True))

  def test_return_candidate_expires_if_signal_remains_between_thresholds(self):
    p = Approach(-80, -93)
    samples = [(0, -40), (1, -41), (2, -42), (3, -40), (8, None), (14, None),
               (20, None), (26, None)] + [(t, -86) for t in range(28, 46)] + [(t, -31) for t in range(46, 51)]
    self.assertTrue(all(p.transition(t, v) is None for t, v in samples))

  def test_lock_needs_recent_unlocked_state_and_no_newer_lock_event(self):
    self.assertEqual(lock_status(status(door=1), SCOPE, NOW, expected_locked=False), ("unlocked", NOW - 10))
    self.assertEqual(lock_status(status(door=2), SCOPE, NOW, expected_locked=False), ("unlocked", NOW - 10))
    self.assertEqual(lock_status(status(), SCOPE, NOW, expected_locked=False), ("locked", None))
    self.assertEqual(lock_status(status(door=1, observed=NOW - 121), SCOPE, NOW, expected_locked=False), ("stale", None))
    event = {"known": True, "locked": True, "occurredAt": iso(NOW - 2)}
    self.assertEqual(lock_status(status(door=1), SCOPE, NOW, event, expected_locked=False), ("locked", None))

  def test_lock_grace_cancels_on_near_stale_or_invalid_evidence(self):
    approach = Approach(-6, -14)
    for value, at, reason in ((-6, 19.9, "returned_near"), (-6, 20, "returned_near"),
                              (LINK_ERROR, 18, "evidence_interrupted"), (None, 25.1, "evidence_interrupted"),
                              (-9, 20, "departure_not_confirmed")):
      with self.subTest(value=value, at=at):
        grace = LockGrace()
        self.assertEqual(grace.apply(10, -14, DoorCommand.LOCK, approach), (None, "pending: grace=10s"))
        self.assertEqual(grace.apply(16, None, None, approach), (None, None))
        self.assertEqual(grace.apply(at, value, None, approach), (None, "canceled: " + reason))
        self.assertEqual(grace.apply(26, -14, None, approach), (None, None))

  def test_lock_grace_uses_fresh_away_evidence_at_deadline_only_once(self):
    approach = Approach(-6, -14)
    for value in (None, -14):
      grace = LockGrace()
      grace.apply(10, value, DoorCommand.LOCK, approach)
      self.assertEqual(grace.apply(15, value, None, approach), (None, None))
      self.assertEqual(grace.apply(19.99, value, DoorCommand.LOCK, approach), (None, None))
      self.assertEqual(grace.apply(20, value, None, approach), (DoorCommand.LOCK, None))
      grace.reset()
      self.assertEqual(grace.apply(21, value, None, approach), (None, None))

  async def test_pending_lock_survives_cooldown_but_near_return_cancels_it(self):
    class EndOfSamples(Exception):
      pass

    for returned in (False, True):
      with self.subTest(returned=returned):
        clock = [-1]
        readings = iter([-6] * 4 + [-14] * 17 + ([-6] if returned else [-14]) + [-14] * 4)

        async def sample(_address, _parked):
          clock[0] += 1
          try:
            return next(readings)
          except StopIteration:
            raise EndOfSamples from None

        with patch("system_phone_auto_unlock.asyncio.sleep", new_callable=AsyncMock), \
             patch("system_phone_auto_unlock.time",
                   SimpleNamespace(monotonic=lambda: clock[0], time=lambda: NOW + clock[0])), \
             patch("system_phone_auto_unlock.diagnostic_waiting", return_value=False), \
             patch("system_phone_auto_unlock.secure_sample", side_effect=sample), \
             patch("system_phone_auto_unlock.intent_cooldown_left",
                   side_effect=lambda _p, when, _a: max(0, NOW + 22 - when)), \
             patch("system_phone_auto_unlock.finish_door_action", return_value="http_response") as send:
          with self.assertRaises(EndOfSamples):
            await monitor(SimpleNamespace(parked=lambda: True), "fixture", Approach(-6, -14), True, True)
          expected = (DoorCommand.UNLOCK, True, 21) if returned else (DoorCommand.LOCK, True, 22)
          send.assert_called_once_with(*expected)

  async def test_persisted_race_can_wait_but_unknown_provider_result_is_not_retried(self):
    class EndOfSamples(Exception):
      pass

    clock = [-1]
    readings = iter([-6] * 4 + [-14] * 20)

    async def sample(_address, _parked):
      clock[0] += 1
      try:
        return next(readings)
      except StopIteration:
        raise EndOfSamples from None

    with patch("system_phone_auto_unlock.asyncio.sleep", new_callable=AsyncMock), \
         patch("system_phone_auto_unlock.time", SimpleNamespace(monotonic=lambda: clock[0])), \
         patch("system_phone_auto_unlock.diagnostic_waiting", return_value=False), \
         patch("system_phone_auto_unlock.secure_sample", side_effect=sample), \
         patch("system_phone_auto_unlock.finish_door_action", side_effect=["rate_limited", "unknown"]) as send:
      with self.assertRaises(EndOfSamples):
        await monitor(SimpleNamespace(parked=lambda: True), "fixture", Approach(-6, -14), False, True)
      self.assertEqual([call.args for call in send.call_args_list],
                       [(DoorCommand.LOCK, False, 19), (DoorCommand.LOCK, False, 20)])

  async def test_monitor_waits_ten_seconds_after_measured_departure_without_status_fetch(self):
    class EndOfSamples(Exception):
      pass

    clock = [99]
    samples = iter([-80] * 4 + [-93] * 16 + [-80] * 4)

    async def sample(_address, _parked):
      clock[0] += 1
      value = next(samples, None)
      if value is None:
        raise EndOfSamples
      return value

    car = SimpleNamespace(parked=lambda: True)
    with patch("system_phone_auto_unlock.asyncio.sleep", new_callable=AsyncMock), \
         patch("system_phone_auto_unlock.time", SimpleNamespace(monotonic=lambda: clock[0])), \
         patch("system_phone_auto_unlock.Cloud", side_effect=AssertionError("status lookup is not allowed")) as cloud, \
         patch("system_phone_auto_unlock.diagnostic_waiting", return_value=False), \
         patch("system_phone_auto_unlock.secure_sample", side_effect=sample), \
         patch("system_phone_auto_unlock.finish_door_action", return_value="dry_run") as send:
      with self.assertRaises(EndOfSamples):
        await monitor(car, "fixture", Approach(-80, -93), False, True)
      self.assertEqual([call.args for call in send.call_args_list],
                       [(DoorCommand.LOCK, False, 119), (DoorCommand.UNLOCK, False, 120)])
      cloud.assert_not_called()

  async def test_monitor_reacquires_without_status_fetch_and_resets_when_blocked(self):
    class EndOfSamples(Exception):
      pass

    for interruption in (None, "ignition", "diagnostic"):
      with self.subTest(interruption=interruption):
        clock = [0]
        samples = iter([(0, -35), (1, -35), (2, -35), (3, -35), (8, None), (14, None),
                        (20, None), (26, None), (28, -30), (29, -30), (30, -30), (31, -30)])

        async def sample(_address, parked):
          item = next(samples, None)
          if item is None:
            raise EndOfSamples
          clock[0], value = item
          return value if parked() else None

        car = SimpleNamespace(parked=lambda: not (interruption == "ignition" and clock[0] == 20))
        with patch("system_phone_auto_unlock.asyncio.sleep", new_callable=AsyncMock), \
             patch("system_phone_auto_unlock.time", SimpleNamespace(monotonic=lambda: clock[0])), \
             patch("system_phone_auto_unlock.Cloud", side_effect=AssertionError("status lookup is not allowed")), \
             patch("system_phone_auto_unlock.diagnostic_waiting",
                   side_effect=lambda: interruption == "diagnostic" and clock[0] == 20), \
             patch("system_phone_auto_unlock.secure_sample", side_effect=sample), \
             patch("system_phone_auto_unlock.finish_door_action", return_value="dry_run") as send:
          with self.assertRaises(EndOfSamples):
            await monitor(car, "fixture", Approach(-80, -93), False, False)
          if interruption is None:
            send.assert_called_once_with(DoorCommand.UNLOCK, False, 28)
          else:
            send.assert_not_called()

  async def test_idle_miss_retries_immediately_after_timeout_and_unlocks_on_first_near(self):
    class EndOfSamples(Exception):
      pass

    for elapsed, failure, expected in ((3.0, None, 103.125), (0.0, None, 100.625),
                                       (0.0, CONNECT_NOT_READY, 100.625)):
      with self.subTest(elapsed=elapsed, failure=failure):
        clock = [100.0]
        starts = []
        approach = Approach(-8, -12)
        for t in (81, 87, 93, 99):
          approach.transition(t, None, enable_lock=True)
        readings = iter(((elapsed, failure), (.125, -8), (0.0, LINK_ERROR)))

        async def sample(_address, parked):
          item = next(readings, None)
          if item is None:
            raise EndOfSamples
          self.assertTrue(parked())
          starts.append(clock[0])
          duration, value = item
          clock[0] += duration
          return value

        async def sleep(seconds):
          clock[0] += seconds

        with patch("system_phone_auto_unlock.asyncio.sleep", side_effect=sleep) as pauses, \
             patch("system_phone_auto_unlock.time", SimpleNamespace(monotonic=lambda: clock[0])), \
             patch("system_phone_auto_unlock.diagnostic_waiting", return_value=False), \
             patch("system_phone_auto_unlock.secure_sample", side_effect=sample), \
             patch("system_phone_auto_unlock.finish_door_action", return_value="dry_run") as send, \
             patch.object(approach, "transition", wraps=approach.transition) as transition:
          with self.assertRaises(EndOfSamples):
            await monitor(SimpleNamespace(parked=lambda: True), "fixture", approach, False, True)
        self.assertEqual(starts[1], expected - .125)
        self.assertIs(transition.call_args_list[0].args[1], LINK_ERROR if failure is CONNECT_NOT_READY else None)
        self.assertEqual([c.args[0] for c in pauses.await_args_list], [0 if elapsed else .5, 1.25, 3])
        send.assert_called_once_with(DoorCommand.UNLOCK, False, expected)

  async def test_startup_monitor_only_counts_parked_receive_attempts(self):
    class EndOfSamples(Exception):
      pass

    for pause in (None, 12):
      with self.subTest(pause=pause):
        clock = [0]
        samples = iter([(0, None), (6, None), (12, None), (18, None), (21, -80)])

        async def sample(_address, parked):
          item = next(samples, None)
          if item is None:
            raise EndOfSamples
          clock[0], value = item
          return value if parked() else None

        car = SimpleNamespace(parked=lambda: clock[0] != pause)
        with patch("system_phone_auto_unlock.asyncio.sleep", new_callable=AsyncMock), \
             patch("system_phone_auto_unlock.time", SimpleNamespace(monotonic=lambda: clock[0])), \
             patch("system_phone_auto_unlock.diagnostic_waiting", return_value=False), \
             patch("system_phone_auto_unlock.secure_sample", side_effect=sample), \
             patch("system_phone_auto_unlock.finish_door_action", return_value="dry_run") as send:
          with self.assertRaises(EndOfSamples):
            await monitor(car, "fixture", Approach(-80, -93), False, True)
          if pause is None:
            send.assert_called_once_with(DoorCommand.UNLOCK, False, 21)
          else:
            send.assert_not_called()

  async def test_monitor_uses_external_lock_to_block_short_return_but_allows_a_new_departure(self):
    class EndOfSamples(Exception):
      pass

    readings = iter([(t, -12) for t in range(5)] + [(5, None), (6, CONNECT_NOT_READY), (7, -8), (8, -7)] +
                    [(t, -12) for t in range(9, 15)] + [(15, None), (16, -8), (17, -7)])
    clock = [0]

    async def sample(_address, _parked):
      item = next(readings, None)
      if item is None:
        raise EndOfSamples
      clock[0], value = item
      return value

    edge = SimpleNamespace(external_lock=lambda now: now == NOW + 7)
    with patch("system_phone_auto_unlock.asyncio.sleep", new_callable=AsyncMock), \
         patch("system_phone_auto_unlock.time", SimpleNamespace(monotonic=lambda: clock[0], time=lambda: NOW + clock[0])), \
         patch("system_phone_auto_unlock.diagnostic_waiting", return_value=False), \
         patch("system_phone_auto_unlock.secure_sample", side_effect=sample), \
         patch("system_phone_auto_unlock.finish_door_action", return_value="dry_run") as send:
      with self.assertRaises(EndOfSamples):
        await monitor(SimpleNamespace(parked=lambda: True), "fixture", Approach(-8, -12), False, False, lock_edge=edge)
    self.assertEqual([c.args for c in send.call_args_list], [(DoorCommand.UNLOCK, False, 16)])

  async def test_monitor_dispatches_loss_lock_with_current_evidence_or_blocks_when_not_parked(self):
    class EndOfSamples(Exception):
      pass

    for blocked in (False, True):
      clock = [0]
      samples = iter([(0, -80), (1, -80), (2, -80), (3, -80), (4, -90),
                      (7.4, None), (10.9, None), (16, None), (20.9, None), (24, None)])

      async def sample(_address, parked):
        item = next(samples, None)
        if item is None:
          raise EndOfSamples
        clock[0], value = item
        return value if parked() else LINK_ERROR

      car = SimpleNamespace(parked=lambda: not (blocked and clock[0] == 16))
      with patch("system_phone_auto_unlock.asyncio.sleep", new_callable=AsyncMock) as sleep, \
           patch("system_phone_auto_unlock.time", SimpleNamespace(monotonic=lambda: clock[0])), \
           patch("system_phone_auto_unlock.diagnostic_waiting", return_value=False), \
           patch("system_phone_auto_unlock.secure_sample", side_effect=sample), \
           patch("system_phone_auto_unlock.finish_door_action", return_value="dry_run") as send:
        with self.assertRaises(EndOfSamples):
          await monitor(car, "fixture", Approach(-80, -93), False, True)
        sleep.assert_any_await(.5)
        if blocked:
          send.assert_not_called()
        else:
          send.assert_called_once_with(DoorCommand.LOCK, False, 20.9)

  async def test_monitor_publishes_exact_readings_with_active_revision_after_reload(self):
    class EndOfSamples(Exception):
      pass

    readings = iter([-25, 0, None, LINK_ERROR])

    async def sample(_address, _parked):
      try:
        return next(readings)
      except StopIteration:
        raise EndOfSamples from None

    profiles = [({"near": -80, "far": -93}, 0)] * 2 + [({"near": -25, "far": -44}, 1)] * 3
    with patch("system_phone_auto_unlock.asyncio.sleep", new_callable=AsyncMock), \
         patch("system_phone_auto_unlock.diagnostic_waiting", return_value=False), \
         patch("system_phone_auto_unlock.secure_sample", side_effect=sample), \
         patch("system_phone_auto_unlock.link_settings.profile", side_effect=profiles), \
         patch("system_phone_auto_unlock.link_settings.publish") as publish, \
         patch("system_phone_auto_unlock.finish_door_action") as send:
      with self.assertRaises(EndOfSamples):
        await monitor(SimpleNamespace(parked=lambda: True), "fixture", Approach(-80, -93), False, True, Path("/fixture"))
      self.assertEqual([call.args for call in publish.call_args_list],
                       [(0, -25, "received"), (0, 0, "received"), (1, None, "not_seen"), (1, None, "link_error")])
      send.assert_not_called()

  async def test_quick_reentry_cancels_pending_lock_without_blocking_unlock(self):
    class EndOfSamples(Exception):
      pass

    clock = [0]
    samples = iter([(0, -30), (1, -31), (2, -31), (3, -31), (7, None), (10, None), (11, -31),
                    (12, -31), (13, -31), (14, -31), (18, None), (21, None), (22, -31)])

    async def sample(_address, _parked):
      item = next(samples, None)
      if item is None:
        raise EndOfSamples
      clock[0], value = item
      return value

    with patch("system_phone_auto_unlock.asyncio.sleep", new_callable=AsyncMock), \
         patch("system_phone_auto_unlock.time", SimpleNamespace(monotonic=lambda: clock[0])), \
         patch("system_phone_auto_unlock.diagnostic_waiting", return_value=False), \
         patch("system_phone_auto_unlock.secure_sample", side_effect=sample), \
         patch("system_phone_auto_unlock.finish_door_action", return_value="dry_run") as send:
      with self.assertRaises(EndOfSamples):
        await monitor(SimpleNamespace(parked=lambda: True), "fixture", Approach(-80, -93), False, True)
      self.assertEqual([call.args for call in send.call_args_list],
                       [(DoorCommand.UNLOCK, False, 11), (DoorCommand.UNLOCK, False, 22)])

  async def test_new_departure_can_lock_again_within_old_sixty_second_window(self):
    class EndOfSamples(Exception):
      pass

    clock = [-1]
    readings = iter([-6] * 4 + [-15] * 16 + [-6] * 9 + [-15] * 16)

    async def sample(_address, _parked):
      clock[0] += 1
      try:
        return next(readings)
      except StopIteration:
        raise EndOfSamples from None

    with patch("system_phone_auto_unlock.asyncio.sleep", new_callable=AsyncMock), \
         patch("system_phone_auto_unlock.time", SimpleNamespace(monotonic=lambda: clock[0])), \
         patch("system_phone_auto_unlock.diagnostic_waiting", return_value=False), \
         patch("system_phone_auto_unlock.secure_sample", side_effect=sample), \
         patch("system_phone_auto_unlock.finish_door_action", return_value="dry_run") as send:
      with self.assertRaises(EndOfSamples):
        await monitor(SimpleNamespace(parked=lambda: True), "fixture", Approach(-6, -14), False, True)
      self.assertEqual([call.args for call in send.call_args_list],
                       [(DoorCommand.LOCK, False, 19), (DoorCommand.UNLOCK, False, 20),
                        (DoorCommand.LOCK, False, 44)])

  def test_dispatch_is_unlock_only_and_rechecks_ignition(self):
    with patch("system_phone_auto_unlock.one_request", return_value=nullcontext()), \
         patch("system_phone_auto_unlock.diagnostic_waiting", return_value=False), \
         patch("system_phone_auto_unlock.time.time", return_value=NOW), \
         patch("system_phone_auto_unlock.time.monotonic", return_value=100), \
         patch("system_phone_auto_unlock.read_credentials", return_value=object()), \
         patch("system_phone_auto_unlock.vehicle_check", side_effect=[None, "ignition_not_confirmed_off"]) as check, \
         patch("system_phone_auto_unlock.send_command") as send:
      self.assertEqual(finish_door_action(DoorCommand.UNLOCK, True, 100), "ignition_not_confirmed_off")
      self.assertEqual([args.args for args in check.call_args_list], [(DoorCommand.UNLOCK,)] * 2)
      send.assert_not_called()
      self.assertEqual(finish_door_action(DoorCommand.UNLOCK, True, 96), "observation_expired")

  def test_persisted_intent_prevents_duplicate_use_after_restart(self):
    with tempfile.TemporaryDirectory() as temp:
      path = Path(temp)
      self.assertTrue(record_intent(path, NOW - 5))
      self.assertFalse(record_intent(path, NOW - 5))
      self.assertFalse(record_intent(path, NOW - 6))
      self.assertFalse(record_intent(path, NOW + 2))
      self.assertTrue(record_intent(path, NOW + 3))
      self.assertTrue(record_intent(path, NOW, DoorCommand.LOCK))
      self.assertFalse(record_intent(path, NOW, DoorCommand.LOCK))
      self.assertFalse(record_intent(path, NOW + 9, DoorCommand.LOCK))
      self.assertTrue(record_intent(path, NOW + 10, DoorCommand.LOCK))
      self.assertEqual((path / "system-unlock-last-intent").stat().st_mode & 0o777, 0o600)

  def test_unlock_rechecks_local_lock_before_sending(self):
    with patch("system_phone_auto_unlock.one_request", return_value=nullcontext()), \
         patch("system_phone_auto_unlock.diagnostic_waiting", return_value=False), \
         patch("system_phone_auto_unlock.time.monotonic", return_value=100), \
         patch("system_phone_auto_unlock.vehicle_check", return_value=None), \
         patch("system_phone_auto_unlock.read_credentials", return_value=object()), \
         patch("system_phone_auto_unlock.record_intent") as intent, \
         patch("system_phone_auto_unlock.send_command") as send:
      allowed = iter((True, True, True, False))
      self.assertEqual(finish_door_action(DoorCommand.UNLOCK, True, 100, unlock_allowed=lambda: next(allowed)),
                       "local_lock_guard")
      intent.assert_not_called()
      send.assert_not_called()

  def test_dispatch_is_once_per_action_and_dry_run_never_sends(self):
    with patch("system_phone_auto_unlock.one_request", return_value=nullcontext()), \
         patch("system_phone_auto_unlock.diagnostic_waiting", return_value=False), \
         patch("system_phone_auto_unlock.time.time", return_value=NOW), \
         patch("system_phone_auto_unlock.time.monotonic", return_value=100), \
         patch("system_phone_auto_unlock.read_credentials", return_value=object()), \
         patch("system_phone_auto_unlock.vehicle_check", return_value=None), \
         patch("system_phone_auto_unlock.record_intent", side_effect=[True, False]), \
         patch("system_phone_auto_unlock.send_command", return_value=SimpleNamespace(state="http_response")) as send:
      self.assertEqual(finish_door_action(DoorCommand.UNLOCK, False, 100), "dry_run")
      self.assertEqual(finish_door_action(DoorCommand.UNLOCK, True, 100), "http_response")
      self.assertEqual(finish_door_action(DoorCommand.UNLOCK, True, 100), "rate_limited")
      send.assert_called_once()
      self.assertIs(send.call_args.args[0], DoorCommand.UNLOCK)

  def test_automatic_lock_skips_only_closure_and_rechecks_ignition(self):
    with tempfile.TemporaryDirectory() as temp, \
         patch("system_phone_auto_unlock.PRIVATE_DIR", Path(temp)), \
         patch("system_phone_auto_unlock.one_request", return_value=nullcontext()), \
         patch("system_phone_auto_unlock.diagnostic_waiting", return_value=False), \
         patch("system_phone_auto_unlock.time.time", return_value=NOW), \
         patch("system_phone_auto_unlock.time.monotonic", return_value=100), \
         patch("system_phone_auto_unlock.read_credentials", return_value=object()), \
         patch("system_phone_auto_unlock.vehicle_check") as check, \
         patch("system_phone_auto_unlock.send_command", return_value=SimpleNamespace(state="http_response")) as send:
      self.assertEqual(finish_door_action(DoorCommand.LOCK, True, 100), "observation_expired")
      check.assert_not_called()
      (Path(temp) / "system-lock-enabled").touch()
      check.side_effect = [None, None, "ignition_not_confirmed_off"]
      self.assertEqual(finish_door_action(DoorCommand.LOCK, True, 100), "ignition_not_confirmed_off")
      send.assert_not_called()
      check.side_effect = None
      check.return_value = None
      with patch("system_phone_auto_unlock.time.time", return_value=NOW + 60):
        self.assertEqual(finish_door_action(DoorCommand.LOCK, True, 100), "http_response")
        self.assertEqual(finish_door_action(DoorCommand.LOCK, True, 100), "rate_limited")
      self.assertTrue(all(call.args == (DoorCommand.LOCK,) and call.kwargs == {"require_closed": False}
                          for call in check.call_args_list))
      send.assert_called_once()
      self.assertIs(send.call_args.args[0], DoorCommand.LOCK)

  async def _run_timed_monitor(self, approach, reading, *, execute=False, stop=None, duration=.05,
                               enable_lock=False, unlock_result="http_response", car=None):
    """Drive monitor with a clock that only moves by sample time and requested sleeps."""
    class EndOfSamples(Exception):
      pass

    clock = [0.0]
    starts, pauses, sent = [], [], []

    async def sample(_address, parked):
      if stop is not None and stop(clock[0], sent):
        raise EndOfSamples
      if not parked():
        clock[0] += .001
        return LINK_ERROR
      starts.append(clock[0])
      value = reading(clock[0])
      clock[0] += duration
      return value

    async def sleep(seconds):
      pauses.append(seconds)
      clock[0] += seconds

    def send(action, _execute, observed_at, **_kwargs):
      sent.append((action, observed_at))
      return unlock_result if action is DoorCommand.UNLOCK else "http_response"

    with patch("system_phone_auto_unlock.asyncio.sleep", side_effect=sleep), \
         patch("system_phone_auto_unlock.time", SimpleNamespace(monotonic=lambda: clock[0], time=lambda: NOW + clock[0])), \
         patch("system_phone_auto_unlock.diagnostic_waiting", return_value=False), \
         patch("system_phone_auto_unlock.secure_sample", side_effect=sample), \
         patch("system_phone_auto_unlock.finish_door_action", side_effect=send), \
         patch.object(approach, "transition", wraps=approach.transition) as transition, \
         patch("builtins.print") as log:
      with self.assertRaises(EndOfSamples):
        await monitor(car(clock) if car else SimpleNamespace(parked=lambda: True), "fixture", approach, execute,
                      enable_lock)
    return SimpleNamespace(starts=starts, pauses=pauses, sent=sent, log=log,
                           transitions=[(c.args[0], c.args[1]) for c in transition.call_args_list])

  async def test_fast_near_readings_unlock_between_regular_samples(self):
    def reading(t):
      return -25 if t < 10 else -15 if t < 13.3 else -3

    run = await self._run_timed_monitor(Approach(-8, -12), reading, execute=True,
                                        stop=lambda _t, sent: bool(sent))
    self.assertEqual(len(run.sent), 1)
    action, observed_at = run.sent[0]
    self.assertIs(action, DoorCommand.UNLOCK)
    # Regular 1.3 s sampling would only see -3 at ~14.35 s; the fast reads catch it within one fast period.
    self.assertTrue(13.3 <= observed_at < 13.3 + FAST_PERIOD_S + .06, observed_at)
    far_gaps = [b - a for a, b in zip(run.starts, run.starts[1:]) if b < 10]
    self.assertGreaterEqual(min(far_gaps), RECEIVED_PERIOD_S)
    self.assertGreaterEqual(sum(10 <= t < 13.3 for t in run.starts), 12)
    # Fast readings below the unlock threshold never reach the band/departure state machine.
    self.assertLessEqual(sum(value == -15 for _now, value in run.transitions), 4)
    self.assertEqual(run.pauses[-1], RECEIVED_PERIOD_S)
    traces = [json.loads(c.args[1]) for c in run.log.call_args_list if c.args[:1] == ("system phone unlock timing:",)]
    decisions = [row[4] for row in traces[-1]["samples"]]
    self.assertIn("fast", decisions)
    self.assertEqual(decisions[-1], "candidate")

  async def test_fast_reads_only_while_a_near_reading_could_unlock(self):
    # In the car (near from startup, never armed) the regular cadence is kept and nothing is sent.
    run = await self._run_timed_monitor(Approach(-8, -12), lambda _t: -3, stop=lambda t, _sent: t > 12)
    self.assertEqual(run.sent, [])
    self.assertTrue(all(pause == RECEIVED_PERIOD_S for pause in run.pauses))
    # Armed at the desk but below the fast zone (near - 10): regular cadence as well.
    run = await self._run_timed_monitor(Approach(-8, -12), lambda _t: -19, stop=lambda t, _sent: t > 12)
    self.assertEqual(run.sent, [])
    self.assertTrue(all(pause == RECEIVED_PERIOD_S for pause in run.pauses))

  async def test_miss_during_fast_reads_is_handled_as_a_regular_sample(self):
    def reading(t):
      return -25 if t < 10 else -15 if t < 10.9 else None if t < 11.2 else -15

    run = await self._run_timed_monitor(Approach(-8, -12), reading, stop=lambda t, _sent: t > 13)
    miss_at = [now for now, value in run.transitions if value is None]
    self.assertEqual(len(miss_at), 1)
    index = run.starts.index(next(t for t in run.starts if reading(t) is None))
    self.assertAlmostEqual(run.pauses[index], .45)
    self.assertEqual(run.sent, [])

  def test_unlock_ready_mirrors_the_near_unlock_conditions(self):
    p = Approach(-8, -12)
    for t in range(5):
      p.transition(t, -20)
    self.assertTrue(p.unlock_ready(4.5))
    self.assertFalse(p.unlock_ready(4 + 6.5))  # regular evidence gap too old
    p.far_at = 4 - 46
    self.assertFalse(p.unlock_ready(4.5))  # departure too old
    p.far_at = 4
    p.hold_after_local_lock(4.2)
    self.assertFalse(p.unlock_ready(4.5))
    q = Approach(-8, -12)
    for t in (0, 6, 12, 18):
      q.transition(t, None)
    self.assertIsNone(q.transition(19, -15))
    self.assertTrue(q.unlock_ready(25))
    self.assertFalse(q.unlock_ready(19 + 15.5))

  def _arrive_with_one_near_sample(self, p):
    """Measured far approach, then a single near reading unlocks (no 3 s near run)."""
    for t in range(5):
      p.transition(t, -20, enable_lock=True)
    self.assertIs(p.transition(5, -10, enable_lock=True), DoorCommand.UNLOCK)

  def test_auto_unlock_arms_walk_away_lock_without_near_run(self):
    for presence in (False, True):
      with self.subTest(presence=presence):
        p = Approach(-12, -15)
        self._arrive_with_one_near_sample(p)
        if presence:
          p.note_unlock(5)
        # Lingering beside the car between thresholds for a minute keeps the arrival evidence fresh.
        self.assertEqual([p.transition(t, -13, enable_lock=True) for t in range(6, 66)], [None] * 60)
        actions = [p.transition(t, -20, enable_lock=True) for t in range(66, 75)]
        self.assertEqual(actions.count(DoorCommand.LOCK), 1 if presence else 0)
        if presence:
          self.assertEqual(actions.index(DoorCommand.LOCK), 5)  # 3 far readings over 3 s, then 5 s away
          self.assertIsNone(p.presence_at)

  def test_auto_unlock_then_signal_loss_locks(self):
    for presence in (False, True):
      with self.subTest(presence=presence):
        p = Approach(-12, -15)
        self._arrive_with_one_near_sample(p)
        if presence:
          p.note_unlock(5)
        self.assertIsNone(p.transition(6, -13, enable_lock=True))
        actions = [p.transition(t, None, enable_lock=True) for t in (9.5, 13, 16.5)]
        self.assertEqual(actions, [None, DoorCommand.LOCK, None] if presence else [None] * 3)

  def test_arrival_evidence_is_dropped_by_external_lock_or_reset(self):
    p = Approach(-12, -15)
    self._arrive_with_one_near_sample(p)
    p.note_unlock(5)
    p.hold_after_local_lock(6)
    self.assertNotIn(DoorCommand.LOCK, [p.transition(t, -20, enable_lock=True) for t in range(7, 20)])
    p = Approach(-12, -15)
    self._arrive_with_one_near_sample(p)
    p.note_unlock(5)
    p.reset()
    self.assertNotIn(DoorCommand.LOCK, [p.transition(t, -20, enable_lock=True) for t in range(6, 20)])
    # The hold after an external lock also keeps a later unlock from re-arming presence.
    p = Approach(-12, -15)
    p.hold_after_local_lock(0)
    p.note_unlock(1)
    self.assertIsNone(p.presence_at)

  async def test_monitor_locks_after_walking_away_from_an_automatic_unlock(self):
    def reading(t):
      return -20 if t < 6 else -10 if t < 7 else -13 if t < 40 else -22

    for result, locks in (("http_response", 1), ("unknown", 1), ("not_confirmed", 0)):
      with self.subTest(result=result):
        run = await self._run_timed_monitor(Approach(-12, -15), reading, enable_lock=True, unlock_result=result,
                                            stop=lambda t, _sent: t > 65)
        actions = [action for action, _at in run.sent]
        self.assertEqual(actions.count(DoorCommand.UNLOCK), 1)
        self.assertEqual(actions.count(DoorCommand.LOCK), locks)
        if locks:
          lock_at = run.sent[actions.index(DoorCommand.LOCK)][1]
          # 5 s of measured departure plus the 10 s grace after leaving at 40 s.
          self.assertTrue(40 + 5 + 10 <= lock_at < 40 + 5 + 10 + 2.6, lock_at)

  def test_guard_reset_keeps_only_a_recent_arrival_when_asked(self):
    p = Approach(-12, -15)
    p.note_unlock(5)
    p.guard_reset(keep_presence=True)
    self.assertEqual((p.presence_at, p.loss_near_at, p.seen_near), (5, 5, True))
    self.assertIsNone(p.last)
    p.guard_reset(keep_presence=False)
    self.assertEqual((p.presence_at, p.loss_near_at, p.seen_near), (None, None, False))

  async def test_short_park_guard_blip_after_unlock_keeps_walk_away_lock(self):
    def reading(t):
      return -20 if t < 6 else -10 if t < 7 else -13 if t < 40 else -22

    for blocked_until, locks in ((10, 1), (30, 0)):
      with self.subTest(blocked_until=blocked_until):
        def car(clock):
          return SimpleNamespace(parked=lambda: not 7 <= clock[0] < blocked_until,
                                 ignition=SimpleNamespace(reason="stale_or_invalid_panda"))
        run = await self._run_timed_monitor(Approach(-12, -15), reading, enable_lock=True, car=car,
                                            stop=lambda t, _sent: t > 65)
        actions = [action for action, _at in run.sent]
        self.assertEqual(actions.count(DoorCommand.UNLOCK), 1)
        self.assertEqual(actions.count(DoorCommand.LOCK), locks)
        if locks:
          self.assertTrue(55 <= run.sent[actions.index(DoorCommand.LOCK)][1] < 57.6)

  async def test_park_guard_logs_its_reason_once_per_block(self):
    def car(clock):
      return SimpleNamespace(parked=lambda: not 3 <= clock[0] < 9, ignition=SimpleNamespace(reason="ignition_on"))
    run = await self._run_timed_monitor(Approach(-12, -15), lambda _t: -20, execute=True, car=car,
                                        stop=lambda t, _sent: t > 14)
    lines = [" ".join(map(str, c.args)) for c in run.log.call_args_list if "park guard" in str(c.args[0])]
    self.assertEqual(len(lines), 2, lines)
    self.assertIn("blocked reason=ignition_on", lines[0])
    self.assertIn("cleared after=", lines[1])

  async def test_lock_dispatch_reports_the_samples_before_it(self):
    def reading(t):
      return -20 if t < 6 else -10 if t < 7 else -13 if t < 20 else -22

    with patch("system_phone_auto_unlock.intent_cooldown_left", return_value=0):
      run = await self._run_timed_monitor(Approach(-12, -15), reading, execute=True, enable_lock=True,
                                          stop=lambda _t, sent: len(sent) >= 2)
    self.assertEqual([action for action, _at in run.sent], [DoorCommand.UNLOCK, DoorCommand.LOCK])
    traces = [json.loads(c.args[1]) for c in run.log.call_args_list if c.args[:1] == ("system phone unlock timing:",)]
    self.assertEqual([trace["outcome"] for trace in traces], ["http_response", "lock_http_response"])
    values = [row[3] for row in traces[-1]["samples"]]
    self.assertIn(-13, values)
    self.assertEqual(values[-1], -22)

  def _armed_on_plateau(self, p, level=-28, until=10.4):
    t, out = 0.0, []
    while t < until:
      out.append(p.transition(t, level, enable_lock=True))
      t = round(t + 1.3, 3)
    self.assertNotIn(DoorCommand.UNLOCK, out)
    return t

  def test_sudden_rise_unlocks_before_the_near_threshold(self):
    p = Approach(-14, -17)
    t = self._armed_on_plateau(p)
    self.assertIs(p.transition(t, -15, enable_lock=True), DoorCommand.UNLOCK)
    self.assertEqual(p.unlock_trigger, "rise")
    # A slow drift (1 dB per reading) is not a step: it waits for the near threshold.
    p = Approach(-14, -17)
    t = self._armed_on_plateau(p)
    for value in range(-27, -14):
      self.assertIsNone(p.transition(t, value, enable_lock=True), value)
      t = round(t + 1.3, 3)
    self.assertIs(p.transition(t, -14, enable_lock=True), DoorCommand.UNLOCK)
    self.assertEqual(p.unlock_trigger, "near")

  def test_sudden_rise_needs_arming_floor_history_and_no_manual_hold(self):
    p = Approach(-14, -17)
    for t in (0, 1, 2):  # three weak readings in under 3 s do not confirm a departure
      p.transition(t, -28, enable_lock=True)
    self.assertFalse(p.armed)
    self.assertTrue(p.sudden_rise(2.5, -15))
    self.assertIsNone(p.transition(2.5, -15, enable_lock=True))
    p = Approach(-14, -17)
    t = self._armed_on_plateau(p)
    self.assertIsNone(p.transition(t, -17, enable_lock=True))  # +11 dB but still in the far band
    p = Approach(-14, -17)
    t = self._armed_on_plateau(p)
    p.hold_after_local_lock(t)
    self.assertIsNone(p.transition(t + .1, -15, enable_lock=True))
    p = Approach(-14, -17)
    self.assertEqual(p.rise_floor(), -16)
    p.record(0, -28)
    p.record(1, -28)
    self.assertFalse(p.sudden_rise(2, -15))  # only two earlier readings
    p.record(2, -28)
    self.assertTrue(p.sudden_rise(3, -15))
    self.assertFalse(p.sudden_rise(13.5, -15))  # the earlier readings left the 10 s window
    self.assertEqual(Approach(-12, -15).rise_floor(), -14)

  async def test_fast_reading_can_unlock_on_a_sudden_rise(self):
    def reading(t):
      return -28 if t < 10 else -24 if t < 13.3 else -15  # -24 is inside the fast zone (near - 10)

    run = await self._run_timed_monitor(Approach(-14, -17), reading, execute=True,
                                        stop=lambda t, sent: bool(sent) or t > 30)
    self.assertEqual(len(run.sent), 1)
    self.assertTrue(13.3 <= run.sent[0][1] < 13.3 + FAST_PERIOD_S + .06, run.sent[0][1])
    dispatch = [" ".join(map(str, c.args)) for c in run.log.call_args_list if "unlock dispatch" in str(c.args[0])]
    self.assertEqual(dispatch, ["system phone unlock dispatch: authenticated_rssi=-15 trigger=rise"])

  def test_doorstep_step_of_the_1745_walk_unlocks_at_minus_19(self):
    # 17:45 walk with thresholds -16/-21: plateau, a few seconds around -20..-27 at the door, then -19.
    p = Approach(-16, -21)
    self.assertEqual(p.rise_floor(), -19)
    t = self._armed_on_plateau(p, level=-30)
    readings = [(t + 1.3, -26), (t + 2.6, -23), (t + 2.8, -25), (t + 3.0, -27), (t + 3.2, -24), (t + 3.4, -20)]
    for at, value in readings:
      self.assertIsNone(p.transition(at, value, enable_lock=True), (at, value))
    self.assertIs(p.transition(t + 3.6, -19, enable_lock=True), DoorCommand.UNLOCK)
    self.assertEqual(p.unlock_trigger, "rise")
