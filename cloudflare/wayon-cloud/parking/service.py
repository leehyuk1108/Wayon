"""Private, bounded multi-frame parking-sign transcription through Codex CLI."""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import io
import json
import logging
from logging.handlers import RotatingFileHandler
import math
import os
from pathlib import Path
import queue
import re
import shutil
import sqlite3
import subprocess
import threading
import time
import unicodedata
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from PIL import Image, ImageOps
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
MAX_BODY = 24 * 1024 * 1024
MAX_FRAME = 2 * 1024 * 1024
MAX_FRAMES = 12
MAX_PIXELS = 12_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")
DISABLED = (
    "shell_tool", "unified_exec", "shell_snapshot", "apps", "plugins",
    "remote_plugin", "hooks", "browser_use", "browser_use_external",
    "in_app_browser", "computer_use", "image_generation", "multi_agent",
    "multi_agent_v2", "memories", "skill_search", "skill_mcp_dependency_install",
    "workspace_dependencies", "goals", "tool_suggest", "code_mode_host",
)


def obj(properties):
    return {"type": "object", "properties": properties, "required": list(properties),
            "additionalProperties": False}


SCHEMA = obj({
    "readings": {"type": "array", "maxItems": 16, "items": obj({
        "kind": {"type": "string", "enum": ["floor", "zone", "pillar", "bay", "unknown"]},
        "text": {"type": ["string", "null"], "maxLength": 32},
        "status": {"type": "string", "enum": ["readable", "ambiguous"]},
        "alternatives": {"type": "array", "maxItems": 4, "items": {"type": "string", "maxLength": 32}},
        "evidence": {"type": "array", "minItems": 1, "maxItems": MAX_FRAMES, "items": obj({
            "frameIndex": {"type": "integer", "minimum": 0, "maximum": MAX_FRAMES - 1},
            "box": {"type": "array", "minItems": 4, "maxItems": 4,
                    "items": {"type": "number", "minimum": 0, "maximum": 1}},
        })},
    })},
    "exactParkingSpotKnown": {"type": "boolean", "enum": [False]},
})


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def timestamp(value):
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("invalid_timestamp")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timestamp_timezone_required")
    return dt.timestamp()


def identifier(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError("invalid_id")
    return value


def prepare_bundle(payload):
    if not isinstance(payload, dict) or set(payload) != {"eventId", "deviceId", "parkedAt", "frames"}:
        raise ValueError("invalid_bundle")
    event = identifier(payload["eventId"])
    device = identifier(payload["deviceId"])
    parked = timestamp(payload["parkedAt"])
    if parked > time.time() + 120:
        raise ValueError("future_event")
    frames = payload["frames"]
    if not isinstance(frames, list) or not 2 <= len(frames) <= MAX_FRAMES:
        raise ValueError("need_2_to_12_frames")
    prepared, seen, total = [], set(), 0
    for frame in frames:
        if not isinstance(frame, dict) or set(frame) != {"capturedAt", "camera", "imageBase64"}:
            raise ValueError("invalid_frame")
        captured = timestamp(frame["capturedAt"])
        if not -120 <= captured - parked <= 60:
            raise ValueError("frame_outside_parking_window")
        if frame["camera"] not in ("road", "wide"):
            raise ValueError("exterior_camera_only")
        encoded = frame["imageBase64"]
        if not isinstance(encoded, str) or len(encoded) > (MAX_FRAME + 2) // 3 * 4:
            raise ValueError("frame_too_large")
        try:
            raw = base64.b64decode(encoded, validate=True)
            total += len(raw)
            if not raw or len(raw) > MAX_FRAME or total > 16 * 1024 * 1024:
                raise ValueError("frame_too_large")
            with Image.open(io.BytesIO(raw)) as im:
                if im.format not in ("JPEG", "PNG") or getattr(im, "n_frames", 1) != 1:
                    raise ValueError("jpeg_or_png_only")
                if not 64 <= im.width <= 4096 or not 64 <= im.height <= 4096 or im.width * im.height > MAX_PIXELS:
                    raise ValueError("invalid_dimensions")
                im.load()
                # Normalize orientation and remove metadata; never synthesize detail.
                clean = ImageOps.exif_transpose(im).convert("RGB")
                digest = hashlib.sha256(clean.tobytes() + str(clean.size).encode()).hexdigest()
                if digest in seen:
                    continue
                seen.add(digest)
                output = io.BytesIO()
                clean.save(output, "JPEG", quality=95, subsampling=0)
                prepared.append({"capturedAt": datetime.fromtimestamp(captured, timezone.utc).isoformat(),
                                 "camera": frame["camera"], "width": clean.width, "height": clean.height,
                                 "sha256": digest, "bytes": output.getvalue()})
        except (OSError, Image.DecompressionBombError, SyntaxError) as exc:
            raise ValueError("invalid_image") from exc
    if len(prepared) < 2:
        raise ValueError("need_two_distinct_frames")
    prepared.sort(key=lambda f: f["capturedAt"])
    if timestamp(prepared[-1]["capturedAt"]) - timestamp(prepared[0]["capturedAt"]) > 120:
        raise ValueError("frame_span_too_large")
    metadata = {"eventId": event, "deviceId": device,
                "parkedAt": datetime.fromtimestamp(parked, timezone.utc).isoformat(),
                "frames": [{k: v for k, v in f.items() if k != "bytes"} for f in prepared]}
    signature = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
    return metadata, prepared, signature


def validate_result(result, count, frames=None):
    Draft202012Validator(SCHEMA).validate(result)
    for reading in result["readings"]:
        indices = set()
        for evidence in reading["evidence"]:
            idx = evidence["frameIndex"]
            x1, y1, x2, y2 = evidence["box"]
            if idx >= count or idx in indices or not x1 < x2 or not y1 < y2:
                raise ValueError("invalid_evidence")
            if not all(math.isfinite(v) for v in evidence["box"]):
                raise ValueError("invalid_evidence")
            indices.add(idx)
        text = reading["text"]
        if reading["status"] == "readable":
            if len(indices) < 2 or not text or not text.strip() or reading["alternatives"]:
                raise ValueError("uncorroborated_reading")
            if frames is not None:
                times = [timestamp(frames[i]["capturedAt"]) for i in indices]
                if max(times) - min(times) < 0.5:
                    raise ValueError("insufficient_temporal_evidence")
        elif text is not None:
            raise ValueError("ambiguous_text_must_be_null")
        if reading["kind"] == "floor" and text and unicodedata.normalize("NFKC", text.strip()).isdecimal():
            raise ValueError("numeric_floor_inference")
    return result


def codex_args(executable, job, model=None):
    args = [str(executable), "exec", "--ignore-user-config", "--ignore-rules",
            "--ephemeral", "--skip-git-repo-check", "--sandbox", "read-only", "--json",
            "--color", "never", "-C", str(job), "--output-schema", str(job / "schema.json"),
            "-o", str(job / "answer.json")]
    for key, value in {"approval_policy": '"never"', "web_search": '"disabled"',
                       "tools.view_image": "false", "project_doc_max_bytes": "0",
                       "mcp_servers": "{}", "analytics.enabled": "false",
                       "model_instructions_file": json.dumps(str(ROOT / "instructions.txt")),
                       "model_reasoning_effort": '"medium"',
                       "forced_login_method": '"chatgpt"'}.items():
        args += ["-c", f"{key}={value}"]
    for feature in DISABLED:
        args += ["--disable", feature]
    if model:
        args += ["--model", model]
    for frame in sorted(job.glob("frame-*.jpg")):
        args += ["--image", str(frame)]
    return args + ["-"]


def run_codex(executable, job, count, model=None, timeout=150):
    prompt = (f"Transcribe parking signage from the {count} attached chronological frames, indexed 0 to {count - 1}. "
              "These are nearby visual clues, not proof of the exact parked bay. "
              "Use only the images; return the schema JSON, no tools. Do not guess unreadable characters.")
    env = {k: v for k, v in os.environ.items() if k.upper() not in
           {"OPENAI_API_KEY", "CODEX_API_KEY", "CODEX_ACCESS_TOKEN", "OPENAI_BASE_URL"}}
    # The installed CLI manages OAuth refresh in its original auth store. Never copy token files.
    with (job / "codex-events.jsonl").open("wb") as out, (job / "codex-stderr.log").open("wb") as err:
        process = subprocess.Popen(codex_args(executable, job, model), stdin=subprocess.PIPE,
                                   stdout=out, stderr=err, env=env, cwd=job,
                                   start_new_session=os.name != "nt")
        try:
            process.communicate(prompt.encode(), timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
            else:
                import signal
                os.killpg(process.pid, signal.SIGKILL)
            process.kill()
            process.wait(timeout=15)
            raise RuntimeError("model_timeout")
    if process.returncode:
        raise RuntimeError("codex_failed_auth_limit_or_runtime")
    if (job / "codex-events.jsonl").stat().st_size > 2 * 1024 * 1024:
        raise RuntimeError("unexpected_model_output_size")
    usage = None
    for line in (job / "codex-events.jsonl").read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        item = event.get("item", {})
        if event.get("type") in ("item.started", "item.completed") and item.get("type") not in (
                "agent_message", "reasoning", None):
            raise RuntimeError("unexpected_tool_activity")
        if event.get("type") == "turn.completed":
            usage = event.get("usage")
    answer = job / "answer.json"
    if not answer.exists() or answer.stat().st_size > 32_768:
        raise RuntimeError("missing_or_oversized_answer")
    frames = json.loads((job / "manifest.json").read_text(encoding="utf-8"))["frames"]
    result = validate_result(json.loads(answer.read_text(encoding="utf-8")), count, frames)
    return {"analysis": result, "usage": usage, "provider": "codex-chatgpt-oauth",
            "verification": "machine_read_not_human_verified"}


class Service:
    def __init__(self, config, runner=run_codex):
        self.config, self.runner = config, runner
        self.root = Path(config["dataDir"]).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.lock = threading.Lock()
        self.queue = queue.Queue(maxsize=8)
        self.worker = None
        self.db = sqlite3.connect(self.root / "parking.sqlite", check_same_thread=False)
        self.db.execute("PRAGMA secure_delete=ON")
        self.db.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, device TEXT, event TEXT, parked REAL, signature TEXT, status TEXT, created REAL, result TEXT, error TEXT, UNIQUE(device,event))")
        self.db.execute("CREATE TABLE IF NOT EXISTS attempts (job TEXT PRIMARY KEY, count INTEGER)")
        self.db.execute("CREATE TABLE IF NOT EXISTS cloud_frames (id TEXT PRIMARY KEY, event TEXT, seen REAL, outcome TEXT)")
        # A stopped inference is never silently retried or published as successful.
        self.db.execute("UPDATE jobs SET status='failed',error='service_restarted' WHERE status IN ('queued','running')")
        self.db.commit()

    def retry(self, job_id):
        with self.lock:
            row = self.db.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
            attempts = self.db.execute("SELECT count FROM attempts WHERE job=?", (job_id,)).fetchone()
            if not row or row[0] != "failed":
                raise ValueError("not_failed")
            if attempts and attempts[0] >= 3:
                raise ValueError("retry_limit")
            if self.queue.full():
                raise ValueError("queue_full")
            self.db.execute("UPDATE jobs SET status='queued',error=NULL,result=NULL WHERE id=?", (job_id,))
            self.db.commit()
            self.queue.put_nowait(job_id)

    def submit(self, payload):
        metadata, frames, signature = prepare_bundle(payload)
        with self.lock:
            old = self.db.execute("SELECT id,signature FROM jobs WHERE device=? AND event=?",
                                  (metadata["deviceId"], metadata["eventId"])).fetchone()
            if old:
                if old[1] != signature:
                    raise ValueError("event_conflict")
                return old[0], False
            if self.queue.full():
                raise ValueError("queue_full")
            recent = self.db.execute("SELECT COUNT(*) FROM jobs WHERE created>?", (time.time() - 86400,)).fetchone()[0]
            if recent >= self.config.get("maxJobsPerDay", 24):
                raise ValueError("daily_limit")
            job_id = hashlib.sha256((metadata["deviceId"] + ":" + metadata["eventId"]).encode()).hexdigest()[:32]
            job = self.root / job_id
            if job.exists():
                shutil.rmtree(job)
            job.mkdir(mode=0o700)
            try:
                for i, frame in enumerate(frames):
                    (job / f"frame-{i:02d}.jpg").write_bytes(frame["bytes"])
                (job / "manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
                (job / "schema.json").write_text(json.dumps(SCHEMA), encoding="utf-8")
                self.db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,'queued',?,NULL,NULL)",
                                (job_id, metadata["deviceId"], metadata["eventId"], timestamp(metadata["parkedAt"]), signature, time.time()))
                self.db.commit()
            except Exception:
                self.db.rollback()
                shutil.rmtree(job)
                raise
            self.queue.put_nowait(job_id)
            return job_id, True

    def get(self, job_id):
        with self.lock:
            row = self.db.execute("SELECT id,device,event,parked,status,result,error FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            return None
        return {"jobId": row[0], "deviceId": row[1], "eventId": row[2],
                "parkedAt": datetime.fromtimestamp(row[3], timezone.utc).isoformat(),
                "status": row[4], "result": json.loads(row[5]) if row[5] else None, "error": row[6]}

    def process_one(self):
        job_id = self.queue.get()
        job = self.root / job_id
        try:
            with self.lock:
                self.db.execute("UPDATE jobs SET status='running' WHERE id=?", (job_id,))
                self.db.execute("INSERT INTO attempts VALUES (?,1) ON CONFLICT(job) DO UPDATE SET count=count+1", (job_id,))
                self.db.commit()
            logging.info("job_started id=%s", job_id)
            manifest = json.loads((job / "manifest.json").read_text(encoding="utf-8"))
            result = self.runner(self.config["codexExe"], job, len(manifest["frames"]), self.config.get("model"))
            result.update({"completedAt": utcnow(), "frames": manifest["frames"],
                           "interpretation": "nearby_signs_not_exact_parking_space"})
            encoded = json.dumps(result, ensure_ascii=False)
            (job / "result.json").write_text(encoded, encoding="utf-8")
            with self.lock:
                self.db.execute("UPDATE jobs SET status='completed',result=? WHERE id=?", (encoded, job_id))
                self.db.commit()
            logging.info("job_completed id=%s frames=%d", job_id, len(manifest["frames"]))
        except Exception as exc:
            # No exception contents: errors can contain credential-bearing stderr or image data.
            code = str(exc) if type(exc) is RuntimeError and str(exc) in {
                "model_timeout", "codex_failed_auth_limit_or_runtime", "unexpected_tool_activity",
                "unexpected_model_output_size", "missing_or_oversized_answer"} else "invalid_result_or_runtime"
            with self.lock:
                self.db.execute("UPDATE jobs SET status='failed',error=? WHERE id=?", (code, job_id))
                self.db.commit()
            logging.error("job_failed id=%s code=%s class=%s", job_id, code, type(exc).__name__)
        finally:
            self.queue.task_done()

    def work(self):
        while True:
            self.process_one()

    def cleanup(self):
        with self.lock:
            old = self.db.execute("SELECT id FROM jobs WHERE created<? AND status NOT IN ('queued','running')",
                                  (time.time() - 7 * 86400,)).fetchall()
            for (job_id,) in old:
                shutil.rmtree(self.root / job_id, ignore_errors=True)
                self.db.execute("DELETE FROM jobs WHERE id=?", (job_id,))
                self.db.execute("DELETE FROM attempts WHERE job=?", (job_id,))
            self.db.commit()
            known = {r[0] for r in self.db.execute("SELECT id FROM jobs")}
            for path in self.root.iterdir():
                if path.is_dir() and re.fullmatch(r"[a-f0-9]{32}", path.name) and path.name not in known:
                    if time.time() - path.stat().st_mtime > 86400:
                        shutil.rmtree(path, ignore_errors=True)
            self.db.execute("DELETE FROM cloud_frames WHERE seen<?", (time.time() - 8 * 86400,))
            self.db.commit()


def handler(service):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"

        def setup(self):
            super().setup()
            self.connection.settimeout(15)

        def log_message(self, *_):
            pass

        def reply(self, status, body):
            data = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def authorized(self):
            expected = "Bearer " + service.config["token"]
            return hmac.compare_digest(self.headers.get("Authorization", "").encode(), expected.encode())

        def do_GET(self):
            if not self.authorized():
                return self.reply(401, {"error": "unauthorized"})
            if self.path == "/health":
                alive = service.worker is not None and service.worker.is_alive()
                return self.reply(200 if alive else 503, {"ok": alive, "workerAlive": alive, "service": "parking-codex-v1", "maxFrames": MAX_FRAMES,
                                        "queued": service.queue.qsize(), "authMode": "chatgpt-oauth"})
            if re.fullmatch(r"/jobs/[a-f0-9]{32}", self.path):
                result = service.get(self.path[6:])
                return self.reply(200 if result else 404, result or {"error": "not_found"})
            return self.reply(404, {"error": "not_found"})

        def do_POST(self):
            if not self.authorized():
                return self.reply(401, {"error": "unauthorized"})
            if re.fullmatch(r"/jobs/[a-f0-9]{32}/retry", self.path):
                try:
                    service.retry(self.path[6:-6])
                    return self.reply(202, {"queued": True})
                except ValueError:
                    return self.reply(409, {"error": "not_retryable"})
            if self.path != "/events":
                return self.reply(404, {"error": "not_found"})
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json" or self.headers.get("Transfer-Encoding"):
                return self.reply(415, {"error": "json_content_length_required"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= MAX_BODY:
                    return self.reply(413, {"error": "body_too_large"})
                body = self.rfile.read(size)
                if len(body) != size:
                    return self.reply(400, {"error": "truncated_body"})
                job_id, created = service.submit(json.loads(body))
                return self.reply(202 if created else 200, {"jobId": job_id, "created": created})
            except ValueError as exc:
                code = str(exc)
                if not re.fullmatch(r"[a-z0-9_]{1,64}", code):
                    code = "invalid_request"
                return self.reply(429 if code in ("queue_full", "daily_limit") else 409 if code == "event_conflict" else 400,
                                  {"error": code})
            except Exception as exc:
                logging.error("submit_failed class=%s", type(exc).__name__)
                return self.reply(503, {"error": "storage_unavailable"})
    return Handler


class BoundedServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, *args):
        self.slots = threading.BoundedSemaphore(4)
        super().__init__(*args)

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8-sig"))
    if not isinstance(config.get("token"), str) or len(config["token"]) < 40:
        raise ValueError("private_service_token_required")
    service = Service(config)
    log = RotatingFileHandler(service.root / "service.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8")
    logging.basicConfig(level=logging.INFO, handlers=[log], format="%(asctime)s %(levelname)s %(message)s")
    service.worker = threading.Thread(target=service.work, daemon=True)
    service.worker.start()
    if config.get("cloud", {}).get("enabled") is True:
        from cloud_collector import start
        collector = start(service)
    else:
        collector = None
    server = BoundedServer(("127.0.0.1", int(config.get("port", 18765))), handler(service))
    server.timeout = 2
    cleanup_at = 0
    logging.info("parking-codex-v1 listening on loopback")
    while True:
        server.handle_request()
        if not service.worker.is_alive():
            raise RuntimeError("worker_stopped")
        if collector is not None and not collector.is_alive():
            raise RuntimeError("collector_stopped")
        if time.monotonic() >= cleanup_at:
            service.cleanup()
            cleanup_at = time.monotonic() + 3600


if __name__ == "__main__":
    main()
