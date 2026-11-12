"""Authenticate one approved phone before storing a parked enrollment."""

import base64
import hmac
import os
import stat
import tempfile
import time
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa

PAIR_DIRECTORY = Path("/data/wayon-door")
KEY_BYTES = 32
DOMAIN = b"wayon-door-pair-v1\n"
MAX_AGE_S = 90


def private_directory(directory):
  info = directory.lstat()
  if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
    raise ValueError("invalid enrollment directory")


def enroll(directory, key):
  if len(key) != KEY_BYTES:
    raise ValueError("invalid enrollment")
  private_directory(directory)
  target = directory / "proximity.key"
  data = key.hex().encode("ascii") + b"\n"
  fd, name = tempfile.mkstemp(dir=directory, prefix=".pair-")
  try:
    with os.fdopen(fd, "wb") as f:
      f.write(data)
      f.flush()
      os.fsync(f.fileno())
    try:
      os.link(name, target, follow_symlinks=False)
    except FileExistsError:
      old = os.open(target, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
      with os.fdopen(old, "rb") as f:
        info = os.fstat(f.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o600:
          raise ValueError("invalid enrollment file")
        return hmac.compare_digest(f.read(len(data) + 1), data)
    directory_fd = os.open(directory, os.O_DIRECTORY)
    try:
      os.fsync(directory_fd)
    finally:
      os.close(directory_fd)
    return True
  finally:
    os.unlink(name)


def read_private_file(directory, name):
  fd = os.open(directory / name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
  with os.fdopen(fd, "rb") as f:
    info = os.fstat(f.fileno())
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o600:
      raise ValueError("invalid enrollment configuration")
    data = f.read(4097)
  if len(data) > 4096:
    raise ValueError("invalid enrollment configuration")
  return data


def authorize(directory, envelope, now=None):
  """Verify the approved Android public key before decrypting the proposed key."""
  now = int(time.time()) if now is None else now
  stamp, encrypted, proof = (envelope.get(x) for x in ("at", "box", "proof"))
  if (type(stamp) is not int or not now - MAX_AGE_S <= stamp <= now + 15 or
      not isinstance(encrypted, str) or len(encrypted) != 344 or
      not isinstance(proof, str) or not 80 <= len(proof) <= 104):
    raise InvalidSignature()
  box = base64.b64decode(encrypted, validate=True)
  signature = base64.b64decode(proof, validate=True)
  private_directory(directory)
  phone = serialization.load_der_public_key(read_private_file(directory, "pair-phone.der"))
  if not isinstance(phone, ec.EllipticCurvePublicKey) or not isinstance(phone.curve, ec.SECP256R1):
    raise ValueError("invalid phone public key")
  phone.verify(signature, DOMAIN + str(stamp).encode("ascii") + b"\n" + box, ec.ECDSA(hashes.SHA256()))
  receiver = serialization.load_pem_private_key(read_private_file(directory, "pair-receiver.pem"), password=None)
  if not isinstance(receiver, rsa.RSAPrivateKey) or receiver.key_size != 2048:
    raise ValueError("invalid receiver private key")
  key = receiver.decrypt(box, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
  if len(key) != KEY_BYTES:
    raise InvalidSignature()
  return key
