"""Share the automation's latest link reading and protect threshold updates."""

import base64
import json
import os
from pathlib import Path
import tempfile
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from wayon_door_pair import private_directory, read_private_file

DIRECTORY = Path("/data/wayon-door")
RUNTIME = Path(f"/dev/shm/wayon-link-rssi-{os.geteuid()}")
PROFILE = "system-unlock.json"
LIVE = "sample.json"
MAX_REVISION = 2**31 - 1
MAX_AGE_MS = 2500
MAX_STATE_AGE_MS = 12_000
MIN_GAP_DB = 3


def valid_thresholds(near, far):
  return type(near) is int and type(far) is int and -128 <= far <= near - MIN_GAP_DB and near <= 126


def profile(directory=DIRECTORY):
  data = json.loads(read_private_file(directory, PROFILE))
  if not isinstance(data, dict) or not valid_thresholds(data.get("near"), data.get("far")):
    raise ValueError("invalid thresholds")
  revision = data.get("thresholdRevision", 0)
  if type(revision) is not int or not 0 <= revision <= MAX_REVISION:
    raise ValueError("invalid threshold revision")
  return data, revision


def _replace(directory, name, value, durable=False):
  fd, temp = tempfile.mkstemp(dir=directory, prefix=".link-rssi-")
  try:
    with os.fdopen(fd, "w", encoding="ascii") as stream:
      json.dump(value, stream, separators=(",", ":"), ensure_ascii=True)
      if durable:
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, directory / name)
    if durable:
      fd = os.open(directory, os.O_DIRECTORY)
      try:
        os.fsync(fd)
      finally:
        os.close(fd)
  finally:
    Path(temp).unlink(missing_ok=True)


def publish(revision, reading, status, runtime=RUNTIME):
  runtime.mkdir(mode=0o700, exist_ok=True)
  private_directory(runtime)
  _replace(runtime, LIVE, {"revision": revision, "rssi": reading, "status": status,
                            "stamp": time.monotonic_ns() // 1_000_000})


def snapshot(directory=DIRECTORY, runtime=RUNTIME, *, parked):
  data, revision = profile(directory)
  result = {"source": "comma", "kind": "classic_link", "revision": revision, "near": data["near"],
            "far": data["far"], "applied": False, "linkRssi": None, "sampleId": None,
            "ageMs": None, "status": "unavailable" if parked else "park_required"}
  try:
    private_directory(runtime)
    sample = json.loads(read_private_file(runtime, LIVE))
    stamp = sample["stamp"]
    reading = sample["rssi"]
    if sample["revision"] != revision or type(stamp) is not int:
      return result
    age = time.monotonic_ns() // 1_000_000 - stamp
    if not 0 <= age <= MAX_STATE_AGE_MS:
      return result
    result["applied"] = True
    if parked:
      status = sample["status"]
      if status == "received" and age <= MAX_AGE_MS and type(reading) is int and -128 <= reading <= 126:
        result.update(status=status, linkRssi=reading, sampleId=stamp, ageMs=age)
      elif status in ("not_seen", "link_error", "park_required"):
        result["status"] = status
  except (OSError, ValueError, TypeError, KeyError):
    pass
  return result


def update(command, parked, directory=DIRECTORY):
  near, far, expected, proof = (command.get(name) for name in ("near", "far", "revision", "proof"))
  if (not valid_thresholds(near, far) or type(expected) is not int or not 0 <= expected < MAX_REVISION or
      not isinstance(proof, str) or not 80 <= len(proof) <= 104):
    return {"error": "invalid_thresholds"}, 400
  if not parked():
    return {"error": "ignition_not_confirmed_off"}, 409
  try:
    private_directory(directory)
    approved = serialization.load_der_public_key(read_private_file(directory, "pair-phone.der"))
    if not isinstance(approved, ec.EllipticCurvePublicKey) or not isinstance(approved.curve, ec.SECP256R1):
      raise ValueError("invalid phone key")
    signature = base64.b64decode(proof, validate=True)
    approved.verify(signature, f"wayon-link-thresholds-v1\n{expected}\n{near}\n{far}\n".encode("ascii"),
                    ec.ECDSA(hashes.SHA256()))
    data, revision = profile(directory)
    if revision != expected:
      return {"error": "threshold_conflict"}, 409
    if not parked():
      return {"error": "ignition_not_confirmed_off"}, 409
    data.update(near=near, far=far, thresholdRevision=revision + 1)
    _replace(directory, PROFILE, data, durable=True)
  except (InvalidSignature, FileNotFoundError):
    return {"error": "phone_not_approved"}, 403
  except (ValueError, OSError):
    return {"error": "receiver_unavailable"}, 503
  return {"source": "comma", "kind": "classic_link", "revision": revision + 1, "near": near, "far": far}, 200
