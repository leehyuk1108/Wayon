"""New-completion-only parking recognition outbox; never a phone delivery receipt.

The Cloud acknowledgement is HTTP 202 with claimed=true and status accepted or
duplicate. Evidence carries the validated source hash/time/phase, not image data.
Rows retain event/content tombstones across restarts and job retention cleanup.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
import re
import ssl
import threading
import time
import unicodedata
from http.client import IncompleteRead, RemoteDisconnected
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from service import MAX_FRAMES, identifier, timestamp, validate_result

MAX_BODY = 32_768
MAX_RESPONSE = 8192
MAX_ATTEMPTS = 5
COOLDOWN = 6 * 3600
PARKED_AGE = 30 * 60
COMPLETED_AGE = 10 * 60
MAX_PENDING = 128
LEASE_SECONDS = 60
LOG = logging.getLogger(__name__)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def safe_text(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 32:
        raise ValueError("invalid_notify_text")
    # Includes bidi overrides/isolates and invisible format characters. Never
    # remove them to manufacture a seemingly safe transcription.
    if any(unicodedata.category(c) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for c in value):
        raise ValueError("unsafe_notify_text")
    value = value.strip()
    if not value:
        raise ValueError("empty_notify_text")
    return value


def make_payload(job_id, manifest, result, device, not_before, now):
    if not isinstance(job_id, str) or not re.fullmatch(r"[a-f0-9]{32}", job_id):
        raise ValueError("invalid_notify_job_id")
    if not isinstance(manifest["eventId"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,96}", manifest["eventId"]):
        raise ValueError("invalid_notify_event_id")
    if manifest["deviceId"] != device:
        return None
    parked, completed = timestamp(manifest["parkedAt"]), timestamp(result["completedAt"])
    if not (not_before <= parked <= completed <= now
            and now - parked <= PARKED_AGE and now - completed <= COMPLETED_AGE):
        return None
    frames = manifest["frames"]
    if (not isinstance(frames, list) or not 2 <= len(frames) <= MAX_FRAMES
            or result["frames"] != frames):
        raise ValueError("notify_provenance_mismatch")
    # Reuse the service's actual schema, box, image-distinctness and >=0.5s gates.
    validate_result(result["analysis"], len(frames), frames)
    readings, phases, approaches = [], set(), []
    for reading in result["analysis"]["readings"]:
        if reading["status"] != "readable" or reading["kind"] not in {"floor", "zone", "pillar", "bay"}:
            continue
        text = safe_text(reading["text"])
        evidence = []
        for source in reading["evidence"]:
            frame = frames[source["frameIndex"]]
            phase = frame.get("phase")
            # Legacy untagged frames cannot truthfully supply a phaseHint.
            if phase not in {"approach", "parked"}:
                evidence = []
                break
            captured = timestamp(frame["capturedAt"])
            if (not re.fullmatch(r"[a-f0-9]{64}", frame["sha256"])
                    or frame["camera"] not in {"road", "wide"}
                    or not parked - 120 <= captured <= min(parked + 60, completed)
                    or (phase == "approach" and captured > parked)):
                raise ValueError("invalid_notify_source")
            evidence.append({"frameIndex": source["frameIndex"], "box": source["box"],
                             "capturedAt": frame["capturedAt"], "sha256": frame["sha256"], "phase": phase})
        if not evidence:
            continue
        phases.update(e["phase"] for e in evidence)
        approaches.extend(timestamp(e["capturedAt"]) for e in evidence if e["phase"] == "approach")
        readings.append({"kind": reading["kind"], "text": text, "status": "readable", "evidence": evidence})
    if not readings:
        return None
    content = sorted({(r["kind"], " ".join(unicodedata.normalize("NFKC", r["text"]).casefold().split()))
                      for r in readings})
    digest = hashlib.sha256(json.dumps(content, ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()
    payload = {"eventId": manifest["eventId"], "jobId": job_id, "deviceId": device,
               "parkedAt": manifest["parkedAt"], "completedAt": result["completedAt"],
               "readings": readings, "phaseHint": next(iter(phases)) if len(phases) == 1 else "mixed", "test": False}
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    if len(encoded.encode()) > MAX_BODY:
        raise ValueError("notify_body_too_large")
    return payload, encoded, digest, min(approaches) if approaches else None


def load_settings(service):
    config = service.config["parkingNotify"]
    path = Path(config["credentialsFile"])
    if not path.is_absolute() or path.resolve().parent != service.root.parent:
        raise ValueError("notify_credentials_must_be_in_private_root")
    cloud_path = service.config.get("cloud", {}).get("credentialsFile")
    if cloud_path and path.resolve() == Path(cloud_path).resolve():
        raise ValueError("notify_dedicated_credentials_required")
    if os.name != "nt" and path.stat().st_mode & 0o077:
        raise ValueError("notify_private_permissions_required")
    with path.open("rb") as source:
        raw = source.read(MAX_RESPONSE + 1)
    if len(raw) > MAX_RESPONSE:
        raise ValueError("notify_credentials_too_large")
    credentials = json.loads(raw.decode("utf-8-sig"))
    endpoint, token = credentials["endpoint"], credentials["token"]
    if (not isinstance(endpoint, str) or len(endpoint) > 2048
            or any(ord(c) <= 32 or ord(c) >= 127 for c in endpoint) or "\\" in endpoint):
        raise ValueError("notify_https_origin_required")
    parts = urlsplit(endpoint)
    if (parts.scheme != "https" or not parts.hostname or parts.username is not None
            or parts.password is not None or parts.query or parts.fragment or parts.path not in ("", "/")
            or parts.port == 0):
        raise ValueError("notify_https_origin_required")
    if (not isinstance(token, str) or not 32 <= len(token) <= 512
            or any(ord(c) <= 32 or ord(c) >= 127 for c in token)
            or token == service.config.get("token")):
        raise ValueError("notify_dedicated_token_required")
    return endpoint.rstrip("/"), token, identifier(credentials["deviceId"]), timestamp(config["notBefore"])


class ParkingNotifier:
    def __init__(self, service):
        self.service = service
        self.endpoint, self.token, self.device, self.not_before = load_settings(service)
        self.opener = build_opener(NoRedirect(), ProxyHandler({}))
        self.clock = time.time
        self.stop_event = threading.Event()
        self.thread = None
        self.start_lock = threading.Lock()
        with service.lock, service.db:
            service.db.execute("""CREATE TABLE IF NOT EXISTS parking_notify_outbox (
                device TEXT NOT NULL, event TEXT NOT NULL, job TEXT NOT NULL,
                content_hash TEXT NOT NULL, parked REAL NOT NULL, completed REAL NOT NULL,
                created REAL NOT NULL, expires REAL NOT NULL, payload TEXT,
                state TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                next_attempt REAL NOT NULL, lease_until REAL NOT NULL DEFAULT 0, reason TEXT,
                PRIMARY KEY(device,event))""")
            service.db.execute("CREATE INDEX IF NOT EXISTS parking_notify_due ON parking_notify_outbox(state,next_attempt)")
            service.db.execute("CREATE INDEX IF NOT EXISTS parking_notify_content ON parking_notify_outbox(device,content_hash,created)")

    def enqueue_completed(self, job_id, manifest, result):
        """Called with service.lock held, inside the job-completion transaction.

        The savepoint isolates optional notification failures from completed jobs.
        It deliberately never scans jobs or opens a network connection.
        """
        db = self.service.db
        db.execute("SAVEPOINT parking_notification")
        try:
            self._enqueue(job_id, manifest, result)
        except Exception:
            db.execute("ROLLBACK TO parking_notification")
            LOG.warning("parking_notify_enqueue_failed")
        finally:
            db.execute("RELEASE parking_notification")

    def _enqueue(self, job_id, manifest, result):
        db, now = self.service.db, self.clock()
        row = db.execute("SELECT status,created,device,event,parked FROM jobs WHERE id=?", (job_id,)).fetchone()
        if (not row or row[0] != "completed" or not self.not_before <= row[1] <= now
                or (row[2], row[3], row[4]) != (self.device, manifest["eventId"], timestamp(manifest["parkedAt"]))):
            return
        if db.execute("SELECT 1 FROM parking_notify_outbox WHERE device=? AND event=?",
                      (self.device, manifest["eventId"])).fetchone():
            return
        prepared = make_payload(job_id, manifest, result, self.device, self.not_before, now)
        if prepared is None:
            return
        payload, encoded, digest, approach_at = prepared
        parked, completed = timestamp(payload["parkedAt"]), timestamp(payload["completedAt"])
        previous = db.execute("""SELECT MAX(parked) FROM parking_notify_outbox
            WHERE device=? AND content_hash=? AND created>? AND state!='suppressed'""",
                              (self.device, digest, now - COOLDOWN)).fetchone()[0]
        # An uncited approach image or a recycled session cannot bypass cooldown.
        suppressed = previous is not None and not (approach_at is not None and approach_at > previous and parked > previous)
        pending = db.execute("SELECT COUNT(*) FROM parking_notify_outbox WHERE state IN ('pending','sending')").fetchone()[0]
        reason = "content_cooldown" if suppressed else "outbox_full" if pending >= MAX_PENDING else None
        db.execute("""INSERT INTO parking_notify_outbox
            (device,event,job,content_hash,parked,completed,created,expires,payload,state,next_attempt,reason)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                   (self.device, payload["eventId"], job_id, digest, parked, completed, now,
                    min(parked + PARKED_AGE, completed + COMPLETED_AGE), None if reason else encoded,
                    "suppressed" if reason else "pending", now, reason))

    def send(self, payload):
        """Return acknowledged/retry/terminal plus a fixed, secret-free reason."""
        if len(payload.encode()) > MAX_BODY:
            return "terminal", "request_too_large"
        request = Request(self.endpoint + "/api/parking/recognition", data=payload.encode(), method="POST",
                          headers={"Authorization": "Bearer " + self.token,
                                   "User-Agent": "Wayon-ParkingVision/1.0", "Content-Type": "application/json"})
        try:
            with self.opener.open(request, timeout=10) as response:
                status = response.status
                if status == 429 or 500 <= status <= 599:
                    return "retry", "http_retryable"
                if status != 202:
                    return "terminal", "http_terminal"
                raw = response.read(MAX_RESPONSE + 1)
                if len(raw) > MAX_RESPONSE:
                    return "terminal", "ack_too_large"
                ack = json.loads(raw)
                if (not isinstance(ack, dict) or ack.get("claimed") is not True
                        or ack.get("status") not in ("accepted", "duplicate")
                        or ack.get("eventId") != json.loads(payload)["eventId"]):
                    return "terminal", "invalid_ack"
                return "acknowledged", "cloud_" + ack["status"]
        except HTTPError as exc:
            status = exc.code
            exc.close()
            return ("retry", "http_retryable") if status == 429 or 500 <= status <= 599 else ("terminal", "http_terminal")
        except ssl.SSLCertVerificationError:
            return "terminal", "tls_verification_failed"
        except URLError as exc:
            if isinstance(exc.reason, ssl.SSLCertVerificationError):
                return "terminal", "tls_verification_failed"
            if isinstance(exc.reason, OSError):
                return "retry", "network_failure"
            return "terminal", "unclassified_transport_failure"
        except (TimeoutError, ConnectionError, IncompleteRead, RemoteDisconnected):
            return "retry", "network_failure"
        except (ValueError, UnicodeError):
            return "terminal", "invalid_ack"

    def once(self):
        db, now = self.service.db, self.clock()
        with self.service.lock, db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""UPDATE parking_notify_outbox SET state='expired',payload=NULL,reason='expired'
                WHERE state='pending' AND (expires<? OR parked<? OR created<? OR completed>? OR created>?)""",
                       (now, self.not_before, self.not_before, now, now))
            # A crash after sending/acknowledgement is not a confirmed network
            # failure. Preserve the tombstone and do not guess that it failed.
            db.execute("""UPDATE parking_notify_outbox SET state='terminal',payload=NULL,reason='delivery_unknown'
                WHERE state='sending' AND lease_until<=?""", (now,))
            db.execute("""UPDATE parking_notify_outbox SET state='terminal',payload=NULL,reason='attempt_limit'
                WHERE state='pending' AND attempts>=?""", (MAX_ATTEMPTS,))
            row = db.execute("""SELECT event,payload,attempts,expires FROM parking_notify_outbox
                WHERE state='pending' AND device=? AND next_attempt<=? ORDER BY created,event LIMIT 1""",
                             (self.device, now)).fetchone()
            if row is None:
                return False
            event, payload, attempts, expires = row
            attempts += 1
            db.execute("""UPDATE parking_notify_outbox SET state='sending',attempts=?,lease_until=?
                WHERE device=? AND event=?""", (attempts, now + LEASE_SECONDS, self.device, event))
        # The claim and job completion are committed, and no service lock is held.
        try:
            state, reason = self.send(payload)
        except Exception:
            state, reason = "terminal", "unexpected_transport_failure"
        now = self.clock()
        next_attempt = now + min(60, 15 * 2 ** (attempts - 1))
        if state == "retry":
            if attempts >= MAX_ATTEMPTS:
                state, reason = "terminal", "attempt_limit"
            elif next_attempt > expires:
                state, reason = "expired", "expired"
            else:
                state = "pending"
        with self.service.lock, db:
            db.execute("""UPDATE parking_notify_outbox SET state=?,reason=?,next_attempt=?,payload=?,lease_until=0
                WHERE device=? AND event=? AND state='sending' AND attempts=?""",
                       (state, reason, next_attempt, payload if state == "pending" else None, self.device, event, attempts))
        LOG.info("parking_notify state=%s reason=%s", state, reason)
        return True

    def work(self):
        while not self.stop_event.is_set():
            try:
                self.once()
            except Exception:
                LOG.warning("parking_notify_worker_failed")
            self.stop_event.wait(1)

    def start(self):
        with self.start_lock:
            if self.thread is None:
                self.thread = threading.Thread(target=self.work, name="parking-notify", daemon=True)
                self.thread.start()
            return self.thread


def configure(service):
    config = service.config.get("parkingNotify")
    if not isinstance(config, dict) or config.get("enabled") is not True:
        return None
    try:
        return ParkingNotifier(service)
    except Exception:
        LOG.warning("parking_notify_disabled_invalid_config_or_storage")
        return None
