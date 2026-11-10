"""Read-only display fusion; never changes a job's baseline or its notification."""
from __future__ import annotations

import copy
import json

from jsonschema import ValidationError

import parking_scene as scene
import service

MAX_REPORT = 196_608


def same_surface(left, right):
    # Containment alone is not identity: a small letter badge can sit beside a number.
    compatible = left['kind'] == right['kind'] or 'unknown' in (left['kind'], right['kind'])
    threshold = .65 if compatible else .9
    for a in left['evidence']:
        for b in right['evidence']:
            if a['frameIndex'] != b['frameIndex']:
                continue
            x, y = a['box'], b['box']
            overlap = max(0, min(x[2], y[2])-max(x[0], y[0])) * max(0, min(x[3], y[3])-max(x[1], y[1]))
            union = (x[2]-x[0])*(x[3]-x[1]) + (y[2]-y[0])*(y[3]-y[1]) - overlap
            if union > 0 and overlap / union >= threshold:
                return True
    return False


def has_parked_evidence(item, frames):
    return any(frames[e["frameIndex"]].get("phase") == "parked" for e in item["evidence"])


def collapse_display_duplicates(readings, frames):
    """Display cleanup after every place was compared with the baseline, for kind=unknown only.

    Shop signs and slogans read again from another crop group are one row, keeping the parked-photo
    evidence when a duplicate has it; their one-photo candidates whose every candidate text is already
    confirmed add nothing to check. Floor/zone/pillar/bay rows stay separate (two pillars can share a
    number), and conflict rows always stay, since they carry a baseline disagreement."""
    kept, rows = [], {}
    for item in readings:
        if item["kind"] == "unknown" and item["status"] == "readable" and item["confidence"] != "conflict":
            key = scene.canonical(item["text"])
            if key in rows:
                if has_parked_evidence(item, frames) and not has_parked_evidence(kept[rows[key]], frames):
                    kept[rows[key]] = item
                continue
            rows[key] = len(kept)
        kept.append(item)
    confirmed = {scene.canonical(item["text"]) for item in kept if item["status"] == "readable" and item["kind"] == "unknown"}
    return [item for item in kept if not (
        item["kind"] == "unknown" and item["status"] != "readable" and item["confidence"] == "uncertain" and item["text"] is None
        and item["alternatives"] and all(scene.canonical(text) in confirmed for text in item["alternatives"]))]


def merge_inspection(baseline, extra, frames):
    service.validate_result(baseline, len(frames), frames)
    service.validate_result(extra["analysis"], len(frames), frames)
    readings = []
    supplementary = extra["analysis"]["readings"]
    for item in supplementary:
        for text in [item["text"], *item["alternatives"]]:
            scene.safe_reading_text(text)
    consumed = set()
    for base in baseline["readings"]:
        item = copy.deepcopy(base)
        for text in [item["text"], *item["alternatives"]]:
            scene.safe_reading_text(text)
        matches = [(i, r) for i, r in enumerate(supplementary)
                   if same_surface(base, r)]
        conflicts = [r for _, r in matches if (
            (base["text"] and r["text"] and scene.canonical(base["text"]) != scene.canonical(r["text"]))
            or (base["kind"] != "unknown" and r["kind"] != "unknown" and base["kind"] != r["kind"])
            or (base["text"] and any(scene.canonical(t) != scene.canonical(base["text"]) for t in r["alternatives"])))]
        if base["text"] and scene.joined_separate_signs(base, supplementary):
            # A combined label is uncertain; unrelated scene labels are not its alternatives.
            conflicts.append({"text": None, "alternatives": []})
        agreed = [(i, r) for i, r in matches if r["status"] == "readable" and base["status"] == "readable"
                  and scene.canonical(r["text"]) == scene.canonical(base["text"])]
        item["confidence"] = "baseline" if base["status"] == "readable" else "uncertain"
        if conflicts:
            alternatives = ([base["text"]] if base["text"] else []) + base["alternatives"]
            for r in conflicts:
                alternatives += ([r["text"]] if r["text"] else []) + r["alternatives"]
            item.update(status="ambiguous", text=None, confidence="conflict",
                        alternatives=list(dict.fromkeys(alternatives))[:4])
            consumed.update(i for i, _ in matches)
        elif agreed:
            item["confidence"] = "corroborated"
            consumed.update(i for i, _ in matches)
            if item["kind"] == "unknown":
                kinds = {r["kind"] for _, r in agreed if r["kind"] != "unknown"}
                if len(kinds) == 1:
                    item["kind"] = next(iter(kinds))
        readings.append(item)
    for index, reading in enumerate(supplementary):
        if index in consumed:
            continue
        if any(scene.common_evidence(reading["evidence"], r["evidence"])
               and reading["status"] == "ambiguous" and not reading["alternatives"] for r in readings):
            continue
        item = copy.deepcopy(reading)
        for text in [item["text"], *item["alternatives"]]:
            scene.safe_reading_text(text)
        item["confidence"] = "additional" if item["status"] == "readable" else "uncertain"
        readings.append(item)
    readings = collapse_display_duplicates(readings, frames)
    details = extra.get("scene", {})
    if not isinstance(details, dict) or not isinstance(details.get("surroundings", []), list):
        raise ValueError("invalid_scene_details")
    surroundings = []
    for feature in details.get("surroundings", [])[:3]:
        if not isinstance(feature, dict):
            raise ValueError("invalid_environment_feature")
        if feature.get("type") not in scene.FEATURES or feature.get("color") not in scene.COLORS:
            continue
        scene.validate_evidence(feature["evidence"], frames, True)
        surroundings.append({"type": feature["type"], "color": feature["color"],
                             "label": scene.environment_label(feature), "evidence": feature["evidence"]})
    coverage = {"completeSceneGuaranteed": False}
    source = details.get("coverage", {})
    if not isinstance(source, dict):
        raise ValueError("invalid_coverage")
    for key in ("overviewViews", "overviewExpected", "targetsRequested", "targetsInspected"):
        value = source.get(key)
        if type(value) is int and 0 <= value <= 96:
            coverage[key] = value
    # Two blind full-frame classifications already had to agree per field in the scene run.
    source_place = details.get("place", scene.UNKNOWN_PLACE)
    if not isinstance(source_place, dict):
        raise ValueError("invalid_place")
    place = {key: source_place.get(key, "unknown") for key in scene.PLACE_VALUES}
    if any(value not in scene.PLACE_VALUES[key] for key, value in place.items()):
        raise ValueError("invalid_place")
    return {"version": 1, "status": "completed", "readings": readings[:32], "surroundings": surroundings,
            "coverage": coverage, "place": place,
            "exactParkingSpotKnown": False, "humanVerified": False,
            "interpretation": "nearby_clues_not_exact_parking_space"}


def attach_inspection(result, job):
    """The bounded comparison file belongs to this job, never the latest other job."""
    path = job / "scene-comparison.json"
    try:
        if not path.is_file() or path.stat().st_size > MAX_REPORT:
            return result
        report = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(report, dict):
            return result
        if report.get("status") == "completed":
            inspection = merge_inspection(result["analysis"], report["result"], result["frames"])
        elif report.get("status") in {"failed", "skipped"}:
            inspection = {"version": 1, "status": report["status"], "readings": [], "surroundings": [],
                          "exactParkingSpotKnown": False, "humanVerified": False}
        else:
            return result
        return {**result, "inspection": inspection}
    except (OSError, ValueError, KeyError, TypeError, ValidationError):
        return result
