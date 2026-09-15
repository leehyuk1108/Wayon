import json
import tempfile
import unittest
from pathlib import Path

from openpilot.selfdrive.navdy.wayon_tmap_road_limit import read_road_limit_kph, set_target_kph


class TestTmapRoadLimit(unittest.TestCase):
  def test_set_target(self):
    self.assertEqual(set_target_kph(50, 80), 90)
    self.assertEqual(set_target_kph(20, 30), 35)
    self.assertEqual(set_target_kph(80, 80), 80)
    self.assertEqual(set_target_kph(95, 80), 95)

  def test_freshness_and_validation(self):
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / "preview.json"
      sample = {"onroad": True, "monotonic": 100.0,
                "packetAgeMs": 200.0, "roadLimitKph": 80}
      for change, expected in (
          ({}, 80), ({"roadLimitKph": 30}, 30),
          ({"roadLimitKph": 85}, None), ({"roadLimitKph": 0}, None),
          ({"roadLimitKph": True}, None), ({"packetAgeMs": 4001}, None),
          ({"monotonic": 97.0}, None), ({"onroad": False}, None)):
        path.write_text(json.dumps(sample | change), encoding="utf-8")
        self.assertEqual(read_road_limit_kph(str(path), now=100.0), expected)
      self.assertIsNone(read_road_limit_kph(str(path.with_name("missing")), now=100.0))
      path.write_text(json.dumps(sample | {"packetAgeMs": 3500}), encoding="utf-8")
      self.assertIsNone(read_road_limit_kph(str(path), now=100.6))


if __name__ == "__main__":
  unittest.main()
