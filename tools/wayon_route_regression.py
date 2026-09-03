#!/usr/bin/env python3
"""Evaluate Wayon trip report JSON without touching vehicle controls."""

import argparse
import json
from pathlib import Path
import sys

from openpilot.system.wayon_drive_quality import evaluate_route_report


def reports_from_payload(payload):
  if isinstance(payload, dict) and "report" in payload:
    return [(str(payload.get("id") or payload.get("routeName") or "route"), payload["report"])]
  if isinstance(payload, dict) and "trips" in payload:
    return [
      (str(item.get("id") or item.get("route_name") or "route"), item.get("report") or {})
      for item in payload["trips"] if isinstance(item, dict)
    ]
  if isinstance(payload, list):
    return [
      (str(item.get("id") or item.get("routeName") or "route"), item.get("report") or item)
      for item in payload if isinstance(item, dict)
    ]
  return [("route", payload if isinstance(payload, dict) else {})]


def main():
  parser = argparse.ArgumentParser(description="Check Wayon route quality regressions")
  parser.add_argument("input", type=Path, help="Trip, state export, or report JSON")
  parser.add_argument("--minimum-stop-score", type=int, default=70)
  parser.add_argument("--output", type=Path)
  args = parser.parse_args()

  payload = json.loads(args.input.read_text(encoding="utf-8"))
  results = [
    {"route": route, **evaluate_route_report(report, args.minimum_stop_score)}
    for route, report in reports_from_payload(payload)
  ]
  result = {
    "schemaVersion": "wayon-route-regression-v1",
    "passed": all(item["passed"] for item in results),
    "routes": results,
  }
  rendered = json.dumps(result, ensure_ascii=False, indent=2)
  if args.output:
    args.output.write_text(rendered + "\n", encoding="utf-8")
  else:
    print(rendered)
  return 0 if result["passed"] else 1


if __name__ == "__main__":
  sys.exit(main())
