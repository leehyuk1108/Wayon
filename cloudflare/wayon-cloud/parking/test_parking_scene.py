import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from PIL import Image
from jsonschema import ValidationError

import service as s
import parking_scene as p


def frames():
    return [{"camera": "wide", "phase": "parked", "width": 400, "height": 240,
             "capturedAt": f"2026-11-04T00:00:0{i}+00:00", "sha256": str(i)*64} for i in range(3)]


def evidence(box=None):
    return [{"frameIndex": i, "box": list(box or [.2, .3, .3, .4])} for i in (0, 2)]


def reading(text="203", kind="pillar", box=None):
    return {"kind": kind, "text": text, "status": "readable", "alternatives": [], "evidence": evidence(box)}


def observation(readings=None):
    return {"readings": [reading()] if readings is None else readings, "exactParkingSpotKnown": False,
            "inventory": [{"surface": "pillar", "legibility": "partial", "evidence": evidence()}],
            "features": [{"type": "vent", "color": "gray", "evidence": evidence([.6,.2,.8,.4])}]}


def verdict(proposals):
    return {"decisions": [{"id": item["id"], "confirmed": True, "evidence": item["evidence"]} for item in proposals]}


def crop_result(obj, views, sources=None):
    sources=sources or frames()
    output=[]
    for view in views:
        frame=sources[view["sourceFrameIndex"]]
        left,top,right,bottom=view["sourcePixelBox"]
        entry={"viewIndex":view["viewIndex"],"readings":[],"features":[]}
        for key in ("readings","features"):
            for item in obj[key]:
                for ev in item["evidence"]:
                    if ev["frameIndex"]!=view["sourceFrameIndex"]: continue
                    x0,y0,x1,y1=ev["box"]
                    if x0*frame["width"]<left or x1*frame["width"]>right or y0*frame["height"]<top or y1*frame["height"]>bottom: continue
                    entry[key].append({**{k:v for k,v in item.items() if k!="evidence"}, "box":[
                        (x0*frame["width"]-left)/(right-left),(y0*frame["height"]-top)/(bottom-top),
                        (x1*frame["width"]-left)/(right-left),(y1*frame["height"]-top)/(bottom-top)]})
        output.append(entry)
    return {"views":output}


class Contracts(unittest.TestCase):
    def test_invalid_environment_does_not_discard_valid_signs(self):
        obj = observation()
        obj["features"].append({"type":"pipe","color":"gray","evidence":evidence([0,0,1,.5])})
        obj["readings"].append(reading("B2", "floor", [0,0,1,1]))
        rejected=[]
        result=p.filter_observation(obj,frames(),rejected)
        self.assertEqual(result["readings"],[reading()])
        self.assertEqual(len(result["features"]),1)
        self.assertEqual(len(rejected),2)
        self.assertNotIn("B2",json.dumps(rejected))

    def test_strict_coordinates_and_missing_sources(self):
        for box in ([1,1,1,1], [0,0,1,1], [0,.2,.4,.1], [-1,0,.3,.3]):
            obj = observation()
            obj["readings"][0]["evidence"][0]["box"] = box
            with self.assertRaises((ValueError, ValidationError)):
                p.validate_observation(obj, frames())
        obj = observation(); obj["readings"][0]["evidence"][0]["frameIndex"] = 3
        with self.assertRaises(ValueError):
            p.validate_observation(obj, frames())

    def test_original_time_and_hash_contract_not_relaxed(self):
        for key, value in (("sha256", "0"*64), ("capturedAt", "2026-11-04T00:00:00.499999+00:00")):
            source = frames(); source[2][key] = value
            with self.assertRaises(ValueError):
                p.validate_observation(observation(), source)
        self.assertEqual(p.validate_observation(observation(), frames()), observation())

    def test_environment_cannot_smuggle_text_or_vehicle_identification(self):
        for change in ({"description": "C203"}, {"type": "license_plate"}, {"color": "C"}):
            obj = observation(); obj["features"][0].update(change)
            with self.assertRaises(ValidationError):
                p.validate_observation(obj, frames())

    def test_one_frame_surface_allowed_but_not_confirmed_text_feature(self):
        obj = observation(); obj["inventory"][0]["evidence"] = evidence()[:1]
        p.validate_observation(obj, frames())
        for section in ("readings", "features"):
            obj = observation(); obj[section][0]["evidence"] = evidence()[:1]
            with self.assertRaises(ValueError):
                p.validate_observation(obj, frames())

    def test_bare_number_cannot_be_floor(self):
        with self.assertRaises(ValueError):
            p.validate_observation(observation([reading(kind="floor")]), frames())


class Shadow(unittest.TestCase):
    def setUp(self):
        from test_service import bundle, readable
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config={"dataDir":self.tmp.name,"codexExe":"unused","token":"t"*48,"sceneShadow":True}
        self.service=s.Service(self.config,lambda *args:{"analysis":readable()})
        self.addCleanup(self.service.db.close)
        self.job,_=self.service.submit(bundle())
        self.path=Path(self.tmp.name)/self.job
        self.manifest=json.loads((self.path/"manifest.json").read_text())
        self.now=s.timestamp(self.manifest["parkedAt"])+180

    def run_shadow(self, effect=None):
        with patch.object(s.time,"time",return_value=self.now), patch.object(s,"run_parking",side_effect=effect) as model:
            self.service.process_one()
        self.assertFalse(self.service.scene_active)
        return model,json.loads((self.path/"scene-comparison.json").read_text())

    def test_primary_completion_and_notification_precede_shadow(self):
        notifier=Mock()
        self.service.parking_notify=notifier
        def check(*args, **kwargs):
            self.assertEqual(self.service.get(self.job)["status"],"completed")
            notifier.enqueue_completed.assert_called_once()
            self.assertTrue(self.service.scene_active)
            return {"analysis":{"readings":[],"exactParkingSpotKnown":False}}
        model,report=self.run_shadow(check)
        model.assert_called_once()
        self.assertEqual(report["status"],"completed")
        self.assertFalse(report["affectsNotification"])
        self.assertTrue(self.service.get(self.job)["result"]["analysis"]["readings"])
        self.assertEqual(json.loads((self.path/"result.json").read_text()),self.service.get(self.job)["result"])
        notifier.enqueue_completed.assert_called_once()

    def test_failure_preserves_primary_and_has_no_secret_text(self):
        _,report=self.run_shadow(RuntimeError("private credential detail"))
        self.assertEqual(report["reason"],"invalid_result_or_runtime")
        self.assertNotIn("credential",json.dumps(report))
        self.assertEqual(self.service.get(self.job)["status"],"completed")

    def test_unexpected_shadow_exception_cannot_fail_completed_job(self):
        with patch.object(self.service,"compare_scene",side_effect=ValueError("test")):
            self.service.process_one()
        self.assertEqual(self.service.get(self.job)["status"],"completed")
        self.assertFalse(self.service.scene_active)

    def test_periodic_snapshot_does_not_run_shadow(self):
        self.manifest['eventId']='snapshot-test'
        with patch.object(s.time,'time',return_value=self.now),patch.object(s,'run_parking') as model:
            self.service.compare_scene(self.job,self.manifest)
        model.assert_not_called()
        self.assertEqual(json.loads((self.path/'scene-comparison.json').read_text())['reason'],'not_parking_event')

    def test_recent_baseline_failure_preserves_budget(self):
        self.service.queue.get_nowait()
        self.service.db.execute("UPDATE jobs SET error='codex_failed_auth_limit_or_runtime',created=? WHERE id=?",
                                (self.now-60,self.job))
        self.service.db.commit()
        with patch.object(s.time,'time',return_value=self.now),patch.object(s,'run_parking') as model:
            self.service.compare_scene(self.job,self.manifest)
        model.assert_not_called()
        self.assertFalse((Path(self.tmp.name)/'scene-budget.json').exists())
        self.assertEqual(json.loads((self.path/'scene-comparison.json').read_text())['reason'],
                         'recent_baseline_runtime_failure')

    def test_expiry_and_queue_skip_extra_calls(self):
        from test_service import bundle
        for reason in ("expired","new_job_waiting"):
            with self.subTest(reason=reason):
                if reason=="expired": self.now=s.timestamp(self.manifest["parkedAt"])+1200.01
                else:
                    self.now=s.timestamp(self.manifest["parkedAt"])+180
                    self.service.submit(bundle("another"))
                with patch.object(s.time,"time",return_value=self.now),patch.object(s,"run_parking") as model:
                    self.service.compare_scene(self.job,self.manifest)
                model.assert_not_called()
                self.assertEqual(json.loads((self.path/"scene-comparison.json").read_text())["reason"],reason)

    def test_daily_budget_persists_across_failure_and_restart(self):
        self.config["sceneMaxJobsPerDay"]=1
        model,_=self.run_shadow(RuntimeError("model_timeout"))
        model.assert_called_once()
        self.service.db.close()
        self.service=s.Service(self.config)
        self.addCleanup(self.service.db.close)
        with patch.object(s.time,"time",return_value=self.now),patch.object(s,"run_parking") as model:
            self.service.compare_scene(self.job,self.manifest)
        model.assert_not_called()
        self.assertEqual(json.loads((self.path/"scene-comparison.json").read_text())["reason"],"daily_limit")

    def test_corrupt_budget_never_resets_or_invokes(self):
        budget=Path(self.tmp.name)/"scene-budget.json"
        budget.write_text('{"day":"tomorrow","attempts":-1}')
        model,report=self.run_shadow()
        model.assert_not_called()
        self.assertEqual(report["status"],"failed")
        self.assertEqual(json.loads(budget.read_text())["attempts"],-1)

    def test_active_mode_expired_job_does_not_infer(self):
        self.service.runner=s.run_parking
        with patch.object(s.time,"time",return_value=self.now+1200),patch.object(p,"run_scene") as model:
            self.service.process_one()
        model.assert_not_called()
        self.assertEqual(self.service.get(self.job)["error"],"parking_job_expired")


class Agreement(unittest.TestCase):
    def test_two_passes_and_verifier_required(self):
        a, b = observation(), observation()
        proposals = p.candidate_pairs(a, b, frames())
        result, detail = p.reconcile(a, b, proposals, verdict(proposals), frames())
        self.assertEqual(result["readings"], [reading()])
        self.assertEqual(detail["surroundings"][0]["label"], "사진 오른쪽 회색 환기구")
        self.assertFalse(result["exactParkingSpotKnown"])
        self.assertFalse(detail["humanVerified"])
        rejected = verdict(proposals); rejected["decisions"][0].update(confirmed=False, evidence=[])
        result, _ = p.reconcile(a, b, proposals, rejected, frames())
        self.assertTrue(all(r["status"] == "ambiguous" for r in result["readings"]))

    def test_unknown_kind_does_not_erase_independently_agreed_number(self):
        a, b = observation([reading(kind="unknown")]), observation()
        proposals = p.candidate_pairs(a, b, frames())
        self.assertEqual(proposals[0]["kind"], "pillar")
        result, _ = p.reconcile(a, b, proposals, verdict(proposals), frames())
        self.assertEqual(result["readings"][0]["kind"], "pillar")

    def test_no_majority_vote_for_conflicting_text(self):
        a, b = observation(), observation([reading("201")])
        self.assertFalse(any(r["category"] == "reading" for r in p.candidate_pairs(a, b, frames())))

    def test_ambiguity_and_partial_identifiers_block_confirmation(self):
        for other in (reading("03"), {**reading(), "status": "ambiguous", "text": None, "alternatives": ["201"]}):
            a, b = observation([reading(), other]), observation()
            self.assertFalse(any(r["category"] == "reading" for r in p.candidate_pairs(a, b, frames())))

    def test_new_crop_read_does_not_borrow_other_pillar_evidence(self):
        a, b = observation(), observation([reading(box=[.7,.3,.8,.4])])
        prop=p.candidate_pairs(a,b,frames())[0]
        self.assertEqual(prop["evidence"],b["readings"][0]["evidence"])

    def test_different_signs_not_concatenated(self):
        a = observation([reading(), reading("C", "zone", [.1,.3,.15,.4])])
        props = p.candidate_pairs(a, copy.deepcopy(a), frames())
        result, _ = p.reconcile(a, a, props, verdict(props), frames())
        self.assertEqual([r["text"] for r in result["readings"]], ["C", "203"])

    def test_verifier_boxes_must_match_both_prior_passes(self):
        obj = observation(); props = p.candidate_pairs(obj, obj, frames()); check = verdict(props)
        check["decisions"][0]["evidence"] = evidence([.7,.3,.8,.4])
        result, _ = p.reconcile(obj, obj, props, check, frames())
        self.assertEqual(result["readings"][0]["status"], "ambiguous")

    def test_missing_duplicate_and_invented_ids_rejected(self):
        obj = observation(); props = p.candidate_pairs(obj, obj, frames()); original = verdict(props)
        for decisions in (original["decisions"]*2,
                          [*original["decisions"], {"id":"r99","confirmed":False,"evidence":[]}]):
            with self.assertRaises((ValueError, ValidationError)):
                p.reconcile(obj, obj, props, {"decisions": decisions}, frames())

    def test_missing_or_uncorroborated_verdict_preserves_other_readings(self):
        obj=observation([reading(),reading("Z","zone",[.7,.3,.75,.4])])
        props=p.candidate_pairs(obj,obj,frames())
        check=verdict(props); check["decisions"][1]["evidence"]=check["decisions"][1]["evidence"][:1]
        for decisions in (check["decisions"],check["decisions"][:1]):
            result,_=p.reconcile(obj,obj,props,{"decisions":decisions},frames())
            self.assertEqual([r["text"] for r in result["readings"] if r["status"]=="readable"],["203"])

    def test_wide_join_of_separate_signs_rejected_without_banning_real_identifiers(self):
        a=observation([reading("AB","zone",[.2,.3,.22,.32]),reading("12","pillar",[.7,.3,.72,.32])])
        b=observation([reading("AB12","pillar",[.19,.29,.73,.34])])
        self.assertFalse(any(x["category"]=="reading" for x in p.candidate_pairs(a,b,frames())))
        self.assertTrue(any(x["category"]=="reading" for x in p.candidate_pairs(b,b,frames())))

    def test_no_claim_of_independent_viewpoints(self):
        f = frames(); f[0]["phase"] = "approach"
        d = p.evidence_detail(evidence(), f)
        self.assertEqual(d["phases"], ["approach", "parked"])
        self.assertEqual(d["viewpointIndependence"], "not_established")
        self.assertEqual(d["distinctHashes"], 2)


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.job = Path(self.tmp.name)
        (self.job/"manifest.json").write_text(json.dumps({"frames": frames()}))
        for i in range(3):
            Image.new("RGB", (400,240), (i*30,70,120)).save(self.job/f"frame-{i:02d}.jpg")

    def test_three_bounded_calls_second_not_anchored_on_answers(self):
        obj = observation(); props = p.candidate_pairs(obj, obj, frames()); calls=[]
        def runner(exe, directory, prompt, model, timeout, **kwargs):
            calls.append((directory, prompt, timeout, kwargs))
            if len(calls)==1: result=copy.deepcopy(obj)
            elif len(calls)==2:
                targets=[{"surface":"other","evidence":r["evidence"]} for r in obj["readings"]]+obj["inventory"]
                targets += [{"surface":"other","evidence":f["evidence"]} for f in obj["features"]]
                views=p.make_views(self.job,frames(),targets)
                result=crop_result(obj,views)
            else: result=verdict(props)
            return result, {"input_tokens": 10}
        result = p.run_scene("not-executed", self.job, 3, runner=runner)
        self.assertEqual(len(calls), 3)
        self.assertNotIn("203", calls[1][1])
        self.assertNotIn('"readings"', calls[1][1])
        self.assertTrue(all(0 < call[2] <= p.PASS_TIMEOUT for call in calls))
        self.assertEqual(result["usage"]["input_tokens"], 30)
        self.assertEqual(result["analysis"]["readings"], [reading()])
        self.assertTrue(all(view["sourceFrameIndex"] in range(3) for view in result["scene"]["views"]))
        self.assertTrue(all(path.name.startswith("crop-") for path in calls[1][3]["images"]))
        self.assertTrue(all(path.name.startswith("frame-") for path in calls[2][3]["images"]))

    def test_empty_scene_does_not_spend_extra_calls(self):
        obj = observation([]); obj["features"] = []; obj["inventory"] = []
        runner = Mock(return_value=(obj, {}))
        result = p.run_scene("not-executed", self.job, 3, runner=runner)
        self.assertEqual(runner.call_count, 1)
        self.assertEqual(result["analysis"]["readings"], [])

    def test_new_baseline_job_preempts_before_next_pass(self):
        runner=Mock(return_value=(observation(),{}))
        with self.assertRaisesRegex(RuntimeError,'new_job_waiting'):
            p.run_scene('unused',self.job,3,runner=runner,cancel=Mock(side_effect=[False,True]))
        self.assertEqual(runner.call_count,1)
        self.assertFalse((self.job/'scene-pass-02').exists())

    def test_cancel_before_first_pass_does_not_call_model(self):
        runner=Mock()
        with self.assertRaisesRegex(RuntimeError,'new_job_waiting'):
            p.run_scene('unused',self.job,3,runner=runner,cancel=lambda:True)
        runner.assert_not_called()

    def test_partial_failure_never_promotes_unverified_first_pass(self):
        runner = Mock(side_effect=[(observation(), {}), RuntimeError("model_timeout")])
        with self.assertRaisesRegex(RuntimeError, "model_timeout"):
            p.run_scene("not-executed", self.job, 3, runner=runner)
        self.assertFalse((self.job/"result.json").exists())
        self.assertEqual(runner.call_count, 2)

    def test_total_deadline_and_bad_count(self):
        for count in (0, 2, 4, 13):
            with self.assertRaises(ValueError):
                p.run_scene("unused", self.job, count)
        with self.assertRaisesRegex(RuntimeError, "model_timeout"):
            p.run_scene("unused", self.job, 3, timeout=0)

    def test_crops_preserve_original_pixels_and_have_finite_budget(self):
        inventory = [{"surface": "pillar", "legibility": "unreadable",
                      "evidence": evidence([i/40, .1, (i+1)/40, .2])} for i in range(16)]
        views = p.make_views(self.job, frames(), inventory)
        self.assertLessEqual(len(views), p.MAX_CROPS)
        total=0
        for view in views:
            with Image.open(self.job/view["name"]) as crop, Image.open(self.job/f"frame-{view['sourceFrameIndex']:02d}.jpg") as full:
                expected=full.crop(view["sourcePixelBox"])
                self.assertEqual(crop.size, expected.size)
                self.assertEqual(crop.tobytes(), expected.tobytes())
                total += crop.width*crop.height
        self.assertLessEqual(total, p.MAX_CROP_PIXELS)

    def test_crop_roundtrip_and_duplicate_crops_not_independent(self):
        obj=observation()
        views=p.make_views(self.job,frames(),obj["inventory"])
        result=crop_result(obj,views)
        second=p.collect_crop_results(result,views,frames(),obj["inventory"])
        self.assertEqual(second["readings"],[reading()])
        single=[views[0],{**views[0],"viewIndex":1}]
        second=p.collect_crop_results(crop_result(obj,single),single,frames(),obj["inventory"])
        self.assertEqual(second["readings"][0]["status"],"ambiguous")

    def test_wrong_box_crop_has_no_letters_then_cannot_be_confirmed(self):
        obj=observation()
        views=p.make_views(self.job,frames(),obj["inventory"])
        empty={"views":[{"viewIndex":v["viewIndex"],"readings":[],"features":[]} for v in views]}
        second=p.collect_crop_results(empty,views,frames(),obj["inventory"])
        props=p.candidate_pairs(obj,second,frames())
        self.assertEqual(props,[])
        analysis,_=p.reconcile(obj,second,props,{"decisions":[]},frames())
        self.assertEqual(analysis["readings"][0]["status"],"ambiguous")

    def test_crop_missing_and_forged_view_indices_rejected(self):
        views=p.make_views(self.job,frames(),observation()["inventory"])
        self.assertEqual(p.collect_crop_results({"views":[]},views,frames(),[])["readings"],[])
        for bad in ({"views":[{"viewIndex":23,"readings":[],"features":[]}]},):
            with self.assertRaises(ValueError):
                p.collect_crop_results(bad,views,frames(),[])

    def test_same_text_on_different_targets_cannot_supply_two_frame_proof(self):
        sources=frames()
        targets=[{"surface":"pillar","evidence":[evidence()[0]]},
                 {"surface":"pillar","evidence":[evidence([.7,.3,.8,.4])[1]]}]
        views=p.make_views(self.job,sources,targets)
        obj=observation([reading("Z","zone"),reading("Z","zone",[.7,.3,.8,.4])])
        result=p.collect_crop_results(crop_result(obj,views),views,sources,[])
        self.assertEqual(len(result["readings"]),2)
        self.assertTrue(all(r["status"]=="ambiguous" for r in result["readings"]))
        paired=[{"surface":"pillar","evidence":r["evidence"]} for r in obj["readings"]]
        views=p.make_views(self.job,sources,paired)
        result=p.collect_crop_results(crop_result(obj,views),views,sources,[])
        self.assertEqual(len(result["readings"]),2)
        self.assertTrue(all(r["status"]=="readable" for r in result["readings"]))

    def test_large_crop_and_bad_reading_are_local_rejections(self):
        obj=observation()
        views=p.make_views(self.job,frames(),obj["inventory"])
        bad=crop_result(obj,views)
        bad["views"][0]["readings"].append({**bad["views"][0]["readings"][0],"alternatives":["205"]})
        rejected=[]
        result=p.collect_crop_results(bad,views,frames(),[],rejected)
        self.assertEqual(result["readings"],[reading()])
        self.assertTrue(rejected)

    def test_unsafe_text_is_not_sent_to_verifier(self):
        for text in ("C\u202e203","x\ny"):
            with self.assertRaises(ValueError):
                p.validate_observation(observation([reading(text)]),frames())

    def test_changed_dimensions_fail_before_model(self):
        Image.new("RGB", (80,80)).save(self.job/"frame-00.jpg")
        runner=Mock()
        with self.assertRaisesRegex(ValueError, "source_dimensions_changed"):
            p.run_scene("unused", self.job, 3, runner=runner)
        runner.assert_not_called()

    def test_service_feature_switch_preserves_legacy_default(self):
        for enabled, expected in ((False, s.run_codex), (True, s.run_parking), ("true", s.run_codex)):
            with tempfile.TemporaryDirectory() as tmp:
                service=s.Service({"dataDir":tmp,"multiStage":enabled})
                self.assertIs(service.runner, expected)
                service.db.close()

    def test_enabled_pipeline_requires_its_instructions_at_startup(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(s,"ROOT",Path(tmp)):
            with self.assertRaisesRegex(ValueError,"scene_instructions_missing"):
                s.Service({"dataDir":tmp,"sceneShadow":True})
            self.assertFalse((Path(tmp)/"parking.sqlite").exists())


class RunnerSecurity(unittest.TestCase):
    def test_cli_transport_warning_is_not_a_tool_but_needs_completed_turn(self):
        warning={"type":"item.completed", "item":{"type":"error","message":"Falling back from WebSockets to HTTPS transport. stream disconnected"}}
        complete={"type":"turn.completed","usage":{}}
        tool={"type":"item.completed","item":{"type":"command_execution"}}
        scenarios=[([warning,complete], True), ([warning], False), ([tool,complete], False),
                   ([{"type":"turn.failed"},complete], False),
                   ([{"type":"item.completed","item":{"type":"error","message":"auth failed"}},complete],False)]
        for events, ok in scenarios:
            with self.subTest(events=events), tempfile.TemporaryDirectory() as tmp:
                job=Path(tmp)
                process=Mock(returncode=0)
                def communicate(*_args, **_kwargs):
                    (job/"answer.json").write_text('{}')
                    (job/"codex-events.jsonl").write_text('\n'.join(json.dumps(e) for e in events))
                process.communicate.side_effect=communicate
                with patch.object(s.subprocess, "Popen", return_value=process):
                    if ok:
                        self.assertEqual(s.run_model("unused", job, "test"), ({},{}))
                    else:
                        with self.assertRaises(RuntimeError):
                            s.run_model("unused", job, "test")

    def test_stage_uses_original_restricted_cli(self):
        args=s.codex_args("codex",Path("stage"),images=[Path("source.jpg")],instructions=s.ROOT/"instructions-scene.txt")
        for value in ("--ignore-user-config", "--ignore-rules", "read-only", "approval_policy=\"never\"", "mcp_servers={}", "shell_tool", "web_search=\"disabled\""):
            self.assertIn(value,args)
        self.assertEqual(args.count("--image"),1)


if __name__ == "__main__":
    unittest.main()
