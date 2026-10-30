"""Submit a local manifest through the authenticated, private parking endpoint."""
import argparse
import base64
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--wait", action="store_true")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8-sig"))
    payload = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    for frame in payload["frames"]:
        path = args.manifest.parent / frame.pop("path")
        frame["imageBase64"] = base64.b64encode(path.read_bytes()).decode()
    base = config.get("endpoint", "http://127.0.0.1:18765")
    headers = {"Authorization": "Bearer " + config["token"], "Content-Type": "application/json"}
    with urlopen(Request(base + "/events", json.dumps(payload).encode(), headers), timeout=30) as response:
        receipt = json.load(response)
    print(json.dumps(receipt), flush=True)
    if args.wait:
        for _ in range(90):
            with urlopen(Request(base + "/jobs/" + receipt["jobId"], headers=headers), timeout=10) as response:
                result = json.load(response)
            if result["status"] in ("completed", "failed"):
                print(json.dumps(result, ensure_ascii=False), flush=True)
                raise SystemExit(0 if result["status"] == "completed" else 1)
            time.sleep(2)
        raise SystemExit("Job still pending; retrieve by jobId, do not resubmit as a new event")


if __name__ == "__main__":
    main()
