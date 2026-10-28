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


if __name__ == "__main__":
  unittest.main()
