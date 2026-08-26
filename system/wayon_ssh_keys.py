import base64
import binascii
from pathlib import Path
import re


AUTHORIZED_KEYS_PATH = Path("/data/wayon_cloud/authorized_keys")
SSH_KEY_RE = re.compile(r"^(ssh-rsa|ssh-ed25519) ([A-Za-z0-9+/]{40,4096}={0,2})(?: [^\r\n]{1,128})?$")


def normalize_ssh_key(value: str) -> str | None:
  value = value.strip()
  match = SSH_KEY_RE.fullmatch(value)
  if match is None:
    return None
  try:
    base64.b64decode(match.group(2), validate=True)
  except (binascii.Error, ValueError):
    return None
  return value


def key_identity(value: str) -> tuple[str, str] | None:
  normalized = normalize_ssh_key(value)
  if normalized is None:
    return None
  algorithm, encoded, *_ = normalized.split()
  return algorithm, encoded


def read_persistent_ssh_keys(path: Path = AUTHORIZED_KEYS_PATH) -> list[str]:
  try:
    values = path.read_text(encoding="utf-8").splitlines()
  except OSError:
    return []
  return [key for value in values if (key := normalize_ssh_key(value)) is not None]


def ensure_persistent_ssh_keys(params, path: Path = AUTHORIZED_KEYS_PATH) -> bool:
  persistent_keys = read_persistent_ssh_keys(path)
  if not persistent_keys:
    return False

  current = params.get("GithubSshKeys") or b""
  if isinstance(current, bytes):
    current = current.decode("utf-8", "replace")
  lines = [line.strip() for line in str(current).splitlines() if line.strip()]
  identities = {identity for line in lines if (identity := key_identity(line)) is not None}
  changed = False
  for key in persistent_keys:
    identity = key_identity(key)
    if identity not in identities:
      lines.append(key)
      identities.add(identity)
      changed = True
  if changed:
    params.put("GithubSshKeys", "\n".join(lines) + "\n", block=True)
  return changed
