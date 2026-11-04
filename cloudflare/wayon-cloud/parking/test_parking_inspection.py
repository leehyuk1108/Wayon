import copy
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

import parking_inspection as p
import parking_scene as scene
from test_parking_scene import frames, reading, observation, crop_result


def analysis(readings):
    return {"readings": readings, "exactParkingSpotKnown": False}


def extra(readings=None, **details):
    return {"analysis": analysis(readings or []), "scene": details}


class Fusion(unittest.TestCase):
    def test_silent_enrichment_never_erases_baseline(self):
        baseline = analysis([reading()])
        original = copy.deepcopy(baseline)
        result = p.merge_inspection(baseline, extra(), frames())
        self.assertEqual(baseline, original)
        self.assertEqual(result["readings"][0], {**reading(), "confidence": "baseline"})

    def test_unknown_kind_matches_identical_sign_not_another_pillar(self):
        result = p.merge_inspection(analysis([reading()]), extra([reading(kind="unknown")]), frames())
        self.assertEqual(len(result["readings"]), 1)
        self.assertEqual(result["readings"][0]["kind"], "pillar")
        self.assertEqual(result["readings"][0]["confidence"], "corroborated")
        result = p.merge_inspection(analysis([reading()]), extra([reading(box=[.7,.3,.8,.4])]), frames())
        self.assertEqual(len(result["readings"]), 2)
        self.assertEqual(result["readings"][0]["confidence"], "baseline")

    def test_conflicting_text_and_semantics_are_not_voted_away(self):
        for other in (reading("201"), reading(kind="zone"),
                      {**reading(), "status":"ambiguous", "text":None, "alternatives":["201"]}):
            with self.subTest(other=other):
                result = p.merge_inspection(analysis([reading()]), extra([other]), frames())
                self.assertIsNone(result["readings"][0]["text"])
                self.assertEqual(result["readings"][0]["confidence"], "conflict")
                self.assertIn("203", result["readings"][0]["alternatives"])

    def test_additional_zone_never_joins_pillar(self):
        result = p.merge_inspection(analysis([reading()]), extra([reading("C", "zone", [.6,.3,.65,.4])]), frames())
        self.assertEqual([r["text"] for r in result["readings"]], ["203", "C"])
        self.assertEqual(result["readings"][1]["confidence"], "additional")
        self.assertNotIn("C203", json.dumps(result))

    def test_environment_cannot_supply_free_text(self):
        feature = {"type":"vent", "color":"gray", "label":"malicious text", "evidence":reading()["evidence"]}
        result = p.merge_inspection(analysis([]), extra(surroundings=[feature]), frames())
        self.assertEqual(result["surroundings"][0]["label"], "사진 왼쪽 회색 환기구")
        self.assertNotIn("malicious", json.dumps(result))

    def test_report_read_never_changes_persisted_baseline_and_is_job_local(self):
        baseline = {"analysis":analysis([reading()]), "frames":frames()}
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            self.assertIs(p.attach_inspection(baseline, job), baseline)
            content = json.dumps({"status":"completed", "result":extra()})
            (job / "scene-comparison.json").write_text(content)
            result = p.attach_inspection(baseline, job)
            self.assertEqual(result["analysis"], baseline["analysis"])
            self.assertNotIn("inspection", baseline)
            self.assertEqual((job / "scene-comparison.json").read_text(), content)
            for malformed in ("invalid", "[]", '{"status":"completed","result":{}}',
                              json.dumps({"status":"completed", "result": {"analysis":analysis([]), "scene":[]}})):
                (job / "scene-comparison.json").write_text(malformed)
                self.assertIs(p.attach_inspection(baseline, job), baseline)

    def test_coverage_is_bounded_and_never_promises_completeness(self):
        result = p.merge_inspection(analysis([]), extra(coverage={
            "completeSceneGuaranteed":True, "overviewViews":12, "targetsRequested":1000,
            "targetsInspected":True, "private":"discard"}), frames())
        self.assertEqual(result['coverage'], {'completeSceneGuaranteed':False, 'overviewViews':12})


class BalancedViews(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.job = Path(self.tmp.name)
        for i in range(3):
            Image.new("RGB", (400, 240), (i * 30, 70, 120)).save(self.job / f"frame-{i:02d}.jpg")

    def test_overview_budget_survives_many_target_proposals(self):
        targets = [{"surface":"pillar", "evidence":reading(box=[i/40,.1,(i+1)/40,.2])["evidence"]} for i in range(16)]
        views = scene.make_views(self.job, frames(), targets, coverage=True)
        self.assertLessEqual(len(views), 24)
        self.assertEqual(sum(v["purpose"] == "overview" for v in views), 12)
        boxes = [v["sourcePixelBox"] for v in views if v["purpose"] == "overview" and v["sourceFrameIndex"] == 0]
        for y in range(240):
            for x in range(400):
                self.assertTrue(any(a <= x < c and b <= y < d for a,b,c,d in boxes))

    def test_unknown_kind_in_one_crop_does_not_split_corroboration(self):
        obj = observation()
        views = scene.make_views(self.job, frames(), obj["inventory"])
        output = crop_result(obj, views)
        output["views"][1]["readings"][0]["kind"] = "unknown"
        result = scene.collect_crop_results(output, views, frames(), obj["inventory"])
        self.assertEqual(result["readings"], [reading()])

    def test_target_repeat_pixels_do_not_manufacture_sources(self):
        views = scene.make_views(self.job, frames(), observation()["inventory"], coverage=True)
        total = 0
        for view in views:
            with Image.open(self.job / view["name"]) as crop, Image.open(self.job / f"frame-{view['sourceFrameIndex']:02d}.jpg") as full:
                scale = view["pixelRepeatScale"]
                expected = full.crop(view["sourcePixelBox"])
                expected = expected.resize((expected.width*scale, expected.height*scale), Image.Resampling.NEAREST)
                self.assertEqual(crop.tobytes(), expected.tobytes())
                total += crop.width*crop.height
        self.assertLessEqual(total, scene.MAX_CROP_PIXELS)


if __name__ == "__main__":
    unittest.main()
