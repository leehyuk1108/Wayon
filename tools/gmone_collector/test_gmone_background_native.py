"""Dependency-free native state/locking smoke test; makes no network requests."""
import tempfile
from pathlib import Path
import unittest

try:
  from openpilot.tools.gmone_collector import gmone_background as bg
except ModuleNotFoundError:
  import gmone_background as bg


class NativeStateTest(unittest.TestCase):
  def test_restart_and_delivery(self):
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / "state.json"
      now = 1793190000.0
      state = bg.State(path, "a" * 64)
      self.assertTrue(state.offer({"fLvl": 42}, now, "gmone-direct", now))
      self.assertFalse(state.reserve_active(now))
      self.assertTrue(state.reserve_active(now, bg.iso(now - 1)))
      state = bg.State(path, "a" * 64)
      self.assertFalse(state.reserve_active(now + 30))
      self.assertEqual(state.upload(lambda _: {"ok": True}, now), "stored")
      self.assertNotIn("pending", bg.State(path, "a" * 64).data)

  def test_native_lock(self):
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / "lock"
      with bg.instance_lock(path):
        with self.assertRaises(OSError):
          with bg.instance_lock(path):
            pass

  def test_failed_request_retries_and_server_ack_survives_restart(self):
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / "state.json"
      now = 1793691700.0
      request = bg.iso(now-1)
      state = bg.State(path, "a"*64)
      self.assertTrue(state.reserve_active(now, request))
      state.failed_read(now, "AuthenticationError")
      state = bg.State(path, "a"*64)
      self.assertFalse(state.reserve_active(now+299, request))
      self.assertTrue(state.reserve_active(now+300, request))
      self.assertEqual(state.data["activeCount"], 2)
      state.observe_refresh({"pending":False,"requestedAt":request,"completedAt":bg.iso(now+301)})
      state = bg.State(path, "a"*64)
      self.assertFalse(state.reserve_active(now+600, request))
      self.assertEqual(state.data["lastReadFailure"]["code"], "AuthenticationError")

  def test_legacy_state_recovers_without_budget_reset(self):
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / "state.json"
      now = 1793691700.0
      state = bg.State(path, "a"*64)
      state.data.update(handledRequest=now-1,lastActive=now-300,activeCount=35,budgetStart=now-600)
      state.save()
      state = bg.State(path, "a"*64)
      self.assertTrue(state.reserve_active(now,bg.iso(now-1)))
      self.assertEqual(state.data["activeCount"],36)
      self.assertFalse(state.reserve_active(now+300,bg.iso(now-1)))


if __name__ == "__main__":
  unittest.main()
