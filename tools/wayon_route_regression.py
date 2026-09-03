#!/usr/bin/env python3
"""Evaluate Wayon trip report JSON without touching vehicle controls."""

import argparse
import json
from pathlib import Path
import sys

# Direct execution from tools/ otherwise omits the repository root from
# sys.path on the comma device.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

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
  parser.add_argument("input", nargs="?", type=Path, help="Trip, state export, or report JSON")
  parser.add_argument("--latest", type=int, metavar="COUNT",
                      help="Analyze the latest COUNT routes directly from the device log root")
  parser.add_argument("--max-age-hours", type=float, default=168.0,
                      help="Maximum route age used with --latest (default: 168)")
  parser.add_argument("--minimum-stop-score", type=int, default=70)
  parser.add_argument("--output", type=Path)
  args = parser.parse_args()

  if args.latest is not None:
    if args.input is not None:
      parser.error("input and --latest cannot be used together")
    if args.latest < 1:
      parser.error("--latest must be at least 1")
    from openpilot.system.wayon_cloud_uploader import recent_route_groups, summarize_route_from_logs

    route_groups = recent_route_groups(max(0.0, args.max_age_hours) * 3600.0)
    payload = [
      report for report in (
        summarize_route_from_logs(group, {}, "local-regression")
        for group in route_groups[:args.latest]
      ) if report is not None
    ]
  elif args.input is not None:
    payload = json.loads(args.input.read_text(encoding="utf-8"))
  else:
    parser.error("provide an input JSON file or --latest COUNT")

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
