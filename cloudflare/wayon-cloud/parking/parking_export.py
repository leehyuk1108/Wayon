"""Changed-only display publication, separate from baseline results and notifications."""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
from datetime import datetime, timezone
from pathlib import Path
import threading
import time
from urllib.request import Request, build_opener, ProxyHandler

from parking_notify import load_settings, NoRedirect
from service import validate_result

MAX_BYTES = 196_608
LOG = logging.getLogger(__name__)


def display_observation(record):
    if record is None:
        return None
    result = record.get("result")
    public = None
    if result is not None:
        validate_result(result['analysis'], len(result['frames']), result['frames'])
        public = {key: result[key] for key in ("analysis", "inspection") if key in result}
        public['frames'] = [{key: frame[key] for key in ('capturedAt', 'camera', 'phase', 'sha256', 'width', 'height')
                             if key in frame} for frame in result['frames']]
    return {key: record[key] for key in ("jobId", "eventId", "parkedAt", "status")} | {"result": public}


class ParkingExport:
    def __init__(self, service, directory: Path):
        self.service = service
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.endpoint, self.token, self.device, _ = load_settings(service)
        self.opener = build_opener(NoRedirect(), ProxyHandler({}))
        self.clock = time.time
        self.lock = threading.Lock()
        self.running = False
        self.failures = 0
        self.next_attempt = 0
        self.last = {}
        self.generation = {}
        path = directory / 'display-ack.json'
        try:
            if path.stat().st_size <= 4096:
                value = json.loads(path.read_text())
                if isinstance(value, dict) and isinstance(value.get('fingerprint'), str) and type(value.get('ackedAt')) in (int, float) and math.isfinite(value['ackedAt']):
                    self.last = value
        except (OSError, ValueError):
            pass
        try:
            path = directory / 'display-generation.json'
            if path.stat().st_size <= 4096:
                value = json.loads(path.read_text())
                if (isinstance(value, dict) and isinstance(value.get('fingerprint'), str)
                        and type(value.get('milliseconds')) is int and 0 < value['milliseconds'] < 253402300799000):
                    self.generation = value
        except (OSError, ValueError):
            pass

    def persist(self, name, value):
        path = self.directory / name
        temporary = path.with_suffix('.pending')
        try:
            with temporary.open('w', encoding='utf-8') as handle:
                json.dump(value, handle, allow_nan=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def status(self):
        return {'running': self.running, 'failures': self.failures,
                'lastAcknowledgedAt': self.last.get('ackedAt'),
                'nextAttemptAt': self.next_attempt}

    def update(self):
        with self.lock:
            if self.running or self.clock() < self.next_attempt:
                return False
            self.running = True
            self.next_attempt = self.clock() + 30
            thread = threading.Thread(target=self.publish, name='parking-display', daemon=True)
            try:
                thread.start()
            except Exception:
                self.running = False
                raise
            return True

    def publish(self):
        try:
            record = self.service.latest(self.device)
            if record is not None and record['deviceId'] != self.device:
                raise ValueError('display_device_mismatch')
            if record is not None and record['eventId'].lower().startswith(('snapshot-', 'test-', 'simulation-', 'replay-')):
                raise ValueError('display_nonparking_event')
            payload = {'schemaVersion': 'wayon-parking-read-v1', 'deviceId': self.device,
                       'observation': display_observation(record)}
            fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=True, allow_nan=False).encode()).hexdigest()
            if self.last.get('fingerprint') == fingerprint and 0 <= self.clock() - self.last.get('ackedAt', 0) < 86400:
                return
            # Persist content order before sending: retries/restarts reuse the same generation.
            if self.generation.get('fingerprint') != fingerprint:
                generation = {'fingerprint': fingerprint,
                              'milliseconds': max(int(self.clock() * 1000), self.generation.get('milliseconds', 0) + 1)}
                self.persist('display-generation.json', generation)
                self.generation = generation
            payload['generatedAt'] = datetime.fromtimestamp(self.generation['milliseconds'] / 1000, timezone.utc).isoformat(timespec='milliseconds')
            data = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode()
            if len(data) > MAX_BYTES:
                raise ValueError('parking_export_too_large')
            request = Request(self.endpoint + '/api/parking/display', data=data, method='POST', headers={
                'Authorization': 'Bearer '+self.token, 'Content-Type': 'application/json', 'User-Agent':'ParkingVision-Display/1'})
            with self.opener.open(request, timeout=5) as response:
                raw = response.read(8193)
                if response.status != 200 or len(raw) > 8192:
                    raise ValueError('invalid_display_ack')
                ack = json.loads(raw)
                if not isinstance(ack, dict) or ack.get('ok') is not True or ack.get('stored') is not True:
                    raise ValueError('invalid_display_ack')
            last = {'fingerprint': fingerprint, 'ackedAt': self.clock()}
            self.persist('display-ack.json', last)
            self.last = last
            self.failures = 0
        except Exception as exc:
            self.failures = min(self.failures + 1, 7)
            self.next_attempt = self.clock() + min(1800, 30 * 2**self.failures)
            LOG.warning('parking_display_publish_failed class=%s', type(exc).__name__)
        finally:
            with self.lock:
                self.running = False
