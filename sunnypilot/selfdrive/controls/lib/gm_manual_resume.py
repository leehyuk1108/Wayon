"""Short-lived, local UI requests for the normal GM resume control path."""

import json
import os
import socket
import stat
import time
import uuid
from collections import deque

from cereal import car

SOCKET_PATH = "/tmp/gm_manual_resume.sock"
REQUEST_TTL_NS = 250_000_000
REQUEST_INTERVAL_NS = 2_500_000_000
SCHEMA = "gm-manual-resume-v1"


def manual_resume_eligible(CP, CS, enabled, long_active, should_stop):
  return bool(CP.carFingerprint == "CHEVROLET_TRAVERSE" and CP.autoResumeSng and
              CP.openpilotLongitudinalControl and enabled and long_active and not should_stop and
              CS.canValid and CS.standstill and abs(CS.vEgo) < 0.05 and
              CS.cruiseState.enabled and CS.cruiseState.standstill and not CS.accFaulted and
              not CS.brakePressed and not CS.gasPressed and not CS.regenBraking and not CS.parkingBrake and
              CS.gearShifter in (car.CarState.GearShifter.drive, car.CarState.GearShifter.low))


def request_manual_resume(path=SOCKET_PATH):
  payload = json.dumps({"schema": SCHEMA, "id": uuid.uuid4().hex,
                        "issuedAtMonoNs": time.monotonic_ns()}, separators=(",", ":")).encode()
  try:
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
      sock.setblocking(False)
      sock.sendto(payload, path)
    return True  # Queued locally; this is not an ECU acknowledgement.
  except OSError:
    return False


class ManualResumeReceiver:
  def __init__(self, path=SOCKET_PATH):
    self.path = path
    self.started_ns = time.monotonic_ns()
    self.last_accepted_ns = None
    self.seen_ids = deque(maxlen=32)
    self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    self.sock.setblocking(False)
    try:
      if os.path.exists(path) and stat.S_ISSOCK(os.stat(path).st_mode):
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as probe:
          try:
            probe.connect(path)
          except ConnectionRefusedError:
            os.unlink(path)
      self.sock.bind(path)
      os.chmod(path, 0o600)
    except OSError:
      self.sock.close()
      raise

  def poll(self, eligible, now_ns=None):
    now_ns = time.monotonic_ns() if now_ns is None else now_ns
    accepted = False
    # Consume requests even when ineligible; never save a click for a later stop.
    for _ in range(32):
      try:
        payload = self.sock.recv(512)
      except BlockingIOError:
        break
      try:
        request = json.loads(payload)
        issued = request["issuedAtMonoNs"]
        request_id = request["id"]
        if (request["schema"] != SCHEMA or type(issued) is not int or not isinstance(request_id, str) or
            len(request_id) != 32 or any(c not in "0123456789abcdef" for c in request_id)):
          continue
        if request_id in self.seen_ids:
          continue
        self.seen_ids.append(request_id)
        fresh = self.started_ns <= issued <= now_ns and now_ns - issued <= REQUEST_TTL_NS
        rate_ok = self.last_accepted_ns is None or now_ns - self.last_accepted_ns >= REQUEST_INTERVAL_NS
        if eligible and fresh and rate_ok and not accepted:
          accepted = True
          self.last_accepted_ns = now_ns
      except (KeyError, TypeError, ValueError, UnicodeDecodeError):
        continue
    return accepted

  def close(self):
    self.sock.close()
    try:
      os.unlink(self.path)
    except FileNotFoundError:
      pass
