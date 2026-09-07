#!/usr/bin/env python3
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import threading
import time


PASSWORD_PATH = Path("/data/wayon_remote_control/password.json")
PBKDF2_ITERATIONS = 200_000
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
SESSION_TTL = 60 * 60


class RemotePasswordStore:
  """Store only a salted password verifier on the comma device."""

  def __init__(self, path: Path = PASSWORD_PATH, iterations: int = PBKDF2_ITERATIONS):
    self.path = path
    self.iterations = iterations

  def configured(self) -> bool:
    try:
      payload = self._read()
      return bool(payload)
    except (OSError, TypeError, ValueError):
      return False

  def set_password(self, password: str) -> None:
    if not isinstance(password, str) or not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
      raise ValueError(f"password must be {MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH} characters")
    salt = secrets.token_bytes(16)
    digest = self._derive(password, salt, self.iterations)
    payload = {
      "version": 1,
      "kdf": "pbkdf2-sha256",
      "iterations": self.iterations,
      "salt": base64.b64encode(salt).decode("ascii"),
      "digest": base64.b64encode(digest).decode("ascii"),
    }
    temporary = self.path.with_name(f".{self.path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp")
    self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(self.path.parent, 0o700)
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
      with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(payload, stream, separators=(",", ":"))
        stream.flush()
        os.fsync(stream.fileno())
      os.replace(temporary, self.path)
      os.chmod(self.path, 0o600)
    finally:
      temporary.unlink(missing_ok=True)

  def verify(self, password: str) -> bool:
    try:
      payload = self._read()
      supplied = self._derive(password, payload["salt"], payload["iterations"])
      return hmac.compare_digest(payload["digest"], supplied)
    except (KeyError, OSError, TypeError, ValueError):
      return False

  def revision(self) -> bytes:
    return hashlib.sha256(self.path.read_bytes()).digest()

  def _read(self) -> dict:
    payload = json.loads(self.path.read_text(encoding="utf-8"))
    if payload.get("version") != 1 or payload.get("kdf") != "pbkdf2-sha256":
      raise ValueError("unsupported password verifier")
    iterations = int(payload["iterations"])
    if not 100_000 <= iterations <= 2_000_000:
      raise ValueError("invalid password verifier")
    salt = base64.b64decode(payload["salt"], validate=True)
    digest = base64.b64decode(payload["digest"], validate=True)
    if len(salt) != 16 or len(digest) != 32:
      raise ValueError("invalid password verifier")
    return {"iterations": iterations, "salt": salt, "digest": digest}

  @staticmethod
  def _derive(password: str, salt: bytes, iterations: int) -> bytes:
    if not isinstance(password, str):
      raise TypeError("password must be text")
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


class RemotePasswordAuthorizer:
  """Issue short-lived tokens bound to one browser control session and client IP."""

  def __init__(self, store: RemotePasswordStore | None = None, ttl: float = SESSION_TTL):
    self.store = store or RemotePasswordStore()
    self.ttl = ttl
    self.lock = threading.Lock()
    self.sessions: dict[str, tuple[str, str, float, bytes]] = {}
    self.failures: dict[str, list[float]] = {}

  @staticmethod
  def _valid_session(session: str) -> bool:
    return 16 <= len(session) <= 128 and session.isascii() and all(c.isalnum() or c in "-_" for c in session)

  def login(self, password: str, session: str, client: str, now: float | None = None) -> str:
    now = time.monotonic() if now is None else now
    if not self._valid_session(session):
      raise ValueError("invalid control session")
    if not self.store.configured():
      raise FileNotFoundError("set the remote control password on comma first")
    with self.lock:
      failures = [attempt for attempt in self.failures.get(client, []) if now - attempt < 60]
      self.failures[client] = failures
      if len(failures) >= 5:
        raise RuntimeError("too many password attempts; wait one minute")
    if not self.store.verify(password):
      with self.lock:
        self.failures.setdefault(client, []).append(now)
      raise PermissionError("incorrect remote control password")
    token = secrets.token_urlsafe(32)
    with self.lock:
      self.failures.pop(client, None)
      self._prune(now)
      self.sessions[token] = (session, client, now + self.ttl, self.store.revision())
    return token

  def authorized(self, authorization: str | None, session: str, client: str,
                 now: float | None = None) -> bool:
    now = time.monotonic() if now is None else now
    supplied = authorization.removeprefix("Bearer ") if authorization else ""
    with self.lock:
      self._prune(now)
      record = self.sessions.get(supplied)
      if not record or record[0] != session or record[1] != client:
        return False
      try:
        return hmac.compare_digest(record[3], self.store.revision())
      except OSError:
        return False

  def revoke(self, token: str) -> None:
    with self.lock:
      self.sessions.pop(token, None)

  def _prune(self, now: float) -> None:
    for token, record in list(self.sessions.items()):
      if record[2] <= now:
        self.sessions.pop(token, None)
