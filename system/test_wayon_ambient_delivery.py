import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("delivery", Path(__file__).with_name("wayon_ambient_delivery.py"))
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)


class TestAmbientDelivery(unittest.TestCase):
  def test_startup_then_idle_without_cloud_reads(self):
    with tempfile.TemporaryDirectory() as directory:
      scheduler = delivery.AmbientCommandDelivery(Path(directory) / "wake")
      calls = []
      for second in range(86400):
        scheduler.run(second, lambda: calls.append(second))
      self.assertEqual(calls, [0])

  def test_notifications_coalesce_and_request_race_is_retained(self):
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / "wake"
      scheduler = delivery.AmbientCommandDelivery(path)
      scheduler.run(0, lambda: None)
      delivery.notify_ambient_command(path)
      delivery.notify_ambient_command(path)
      self.assertTrue(scheduler.run(1, lambda: delivery.notify_ambient_command(path)))
      self.assertTrue(scheduler.run(2, lambda: None))
      self.assertFalse(scheduler.run(3, lambda: self.fail("idle request")))

  def test_failure_retries_without_losing_notification(self):
    with tempfile.TemporaryDirectory() as directory:
      scheduler = delivery.AmbientCommandDelivery(Path(directory) / "wake")
      def fail():
        raise OSError("offline")
      with self.assertRaises(OSError):
        scheduler.run(0, fail)
      self.assertFalse(scheduler.run(4, fail))
      self.assertTrue(scheduler.run(5, lambda: None))
      self.assertFalse(scheduler.run(6, fail))


if __name__ == "__main__":
  unittest.main()
