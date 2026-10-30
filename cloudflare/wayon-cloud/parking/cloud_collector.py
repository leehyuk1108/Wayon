"""Read only new exterior snapshot bursts from the existing owner-authorized API."""
import base64
import json
import logging
from pathlib import Path
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit, quote
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

from service import MAX_FRAME, identifier, timestamp


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def groups(snapshots, not_before, now):
    exterior = []
    for frame in snapshots:
        try:
            captured = timestamp(frame["capturedAt"])
            identifier(frame["id"])
            identifier(frame["deviceId"])
            if frame["camera"] != "wide" or frame.get("impact"):
                continue
            if not_before <= captured <= now and now - captured <= 7200:
                exterior.append((frame["deviceId"], captured, frame["id"], frame))
        except (KeyError, TypeError, ValueError):
            continue
    exterior.sort(key=lambda row: row[:3])
    grouped = []
    for device, captured, _, frame in exterior:
        if not grouped or grouped[-1][0]["deviceId"] != device or captured - timestamp(grouped[-1][-1]["capturedAt"]) > 2.5:
            grouped.append([])
        grouped[-1].append(frame)
    # Accept only a complete three-shot burst. An interrupted upload is not a batch.
    return [g for g in grouped if len(g) == 3 and now - timestamp(g[-1]["capturedAt"]) >= 120
            and 2 <= timestamp(g[-1]["capturedAt"]) - timestamp(g[0]["capturedAt"]) <= 5
            and all(timestamp(b["capturedAt"]) - timestamp(a["capturedAt"]) >= 0.5 for a, b in zip(g, g[1:]))]


class Collector:
    def __init__(self, service):
        self.service = service
        config = service.config["cloud"]
        path = Path(config["credentialsFile"]).resolve()
        if path.parent != self.service.root.parent:
            raise ValueError("credentials_must_be_in_private_root")
        credentials = json.loads(path.read_text(encoding="utf-8-sig"))
        self.endpoint = credentials["endpoint"].rstrip("/")
        parts = urlsplit(self.endpoint)
        if parts.scheme != "https" or parts.username or parts.password or parts.query or parts.fragment or parts.path:
            raise ValueError("https_origin_required")
        self.token = credentials["token"]
        self.not_before = timestamp(config["notBefore"])
        self.device = identifier(config["deviceId"])
        self.opener = build_opener(NoRedirect, ProxyHandler({}))
        self.deferred = {}

    def mark(self, group, event, outcome):
        with self.service.lock:
            self.service.db.executemany("INSERT OR IGNORE INTO cloud_frames VALUES (?,?,?,?)",
                                       [(f["id"], event, time.time(), outcome) for f in group])
            self.service.db.commit()

    def get(self, path, max_bytes):
        req = Request(self.endpoint + path, headers={"Authorization": "Bearer " + self.token,
                                                    "User-Agent": "Wayon-ParkingVision/1.0"})
        with self.opener.open(req, timeout=20) as response:
            data = response.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise ValueError("cloud_response_too_large")
            return data

    def once(self):
        listing = json.loads(self.get("/api/ai/snapshots?limit=100", 512_000))
        now = time.time()
        self.deferred = {key: value for key, value in self.deferred.items() if value[0] > now - 7200}
        snapshots = [f for f in listing.get("snapshots", []) if isinstance(f, dict) and f.get("deviceId") == self.device]
        for group in groups(snapshots, self.not_before, now):
            event = "snapshot-" + group[0]["id"]
            if self.deferred.get(event, (0, 0))[0] > now:
                continue
            with self.service.lock:
                exists = self.service.db.execute("SELECT id FROM jobs WHERE device=? AND event=?",
                                                 (group[0]["deviceId"], event)).fetchone()
                used = any(self.service.db.execute("SELECT 1 FROM cloud_frames WHERE id=?", (f["id"],)).fetchone() for f in group)
            if exists or used:
                self.mark(group, event, "already_received")
                continue
            try:
                frames = []
                for snapshot in group:
                    raw = self.get("/api/ai/images/" + quote(snapshot["id"], safe=""), MAX_FRAME)
                    frames.append({"capturedAt": snapshot["capturedAt"], "camera": "wide",
                                   "imageBase64": base64.b64encode(raw).decode()})
                # The API's parkedAt is a burst reference, NOT the actual gear-P timestamp.
                payload = {"eventId": event, "deviceId": group[0]["deviceId"],
                           "parkedAt": group[-1]["capturedAt"], "frames": frames}
                job_id, created = self.service.submit(payload)
                self.mark(group, event, "received")
                logging.info("cloud_burst_received id=%s frames=%d created=%s", job_id, len(frames), created)
            except Exception as exc:
                code = str(exc) if type(exc) is ValueError and str(exc) in {
                    "frame_too_large", "invalid_image", "cloud_response_too_large", "daily_limit", "queue_full",
                    "need_two_distinct_frames", "event_conflict", "invalid_dimensions"} else "cloud_transfer_failed"
                attempts = self.deferred.get(event, (0, 0))[1] + 1
                if (code not in {"cloud_transfer_failed", "daily_limit", "queue_full"}
                        or isinstance(exc, HTTPError) and exc.code == 404 or attempts >= 5):
                    self.mark(group, event, "failed_" + code)
                else:
                    self.deferred[event] = (now + min(1800, 60 * 2 ** attempts), attempts)
                logging.warning("cloud_burst_failed event=%s code=%s class=%s", event, code, type(exc).__name__)

    def run(self):
        while True:
            try:
                self.once()
            except Exception as exc:
                logging.warning("cloud_poll_failed class=%s", type(exc).__name__)
            time.sleep(60)


def start(service):
    collector = Collector(service)
    thread = threading.Thread(target=collector.run, name="parking-cloud-collector", daemon=True)
    thread.start()
    return thread
