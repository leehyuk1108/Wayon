import subprocess
from pathlib import Path

from openpilot.system import wayon_remote_daemon as daemon
from openpilot.system.wayon_ssh_keys import ensure_persistent_ssh_keys, read_persistent_ssh_keys


class FakeProcess:
  def __init__(self):
    self.returncode = None
    self.terminated = False
    self.killed = False

  def poll(self):
    return self.returncode

  def terminate(self):
    self.terminated = True
    self.returncode = 0

  def wait(self, timeout=None):
    return self.returncode

  def kill(self):
    self.killed = True
    self.returncode = -9


def test_supervisor_starts_offroad_and_stops_onroad(monkeypatch):
  processes = []
  monkeypatch.setattr(daemon.time, "monotonic", lambda: 100.0)
  supervisor = daemon.RelaySupervisor(lambda args: processes.append((args, FakeProcess())) or processes[-1][1])

  supervisor.update(True)
  assert processes[0][0] == [daemon.sys.executable, "-m", daemon.RELAY_MODULE]

  supervisor.update(False)
  assert processes[0][1].terminated
  assert supervisor.child is None


def test_supervisor_restarts_crashed_relay_after_backoff(monkeypatch):
  now = [100.0]
  processes = []
  monkeypatch.setattr(daemon.time, "monotonic", lambda: now[0])
  supervisor = daemon.RelaySupervisor(lambda args: processes.append(FakeProcess()) or processes[-1])

  supervisor.update(True)
  supervisor.child.returncode = 1
  supervisor.update(True)
  assert len(processes) == 1

  now[0] += daemon.RESTART_DELAY_SECONDS
  supervisor.update(True)
  assert len(processes) == 2


def test_supervisor_kills_child_that_ignores_terminate():
  child = FakeProcess()

  def wait(timeout=None):
    if not child.killed:
      raise subprocess.TimeoutExpired("relay", timeout)
    return child.returncode

  child.wait = wait
  supervisor = daemon.RelaySupervisor()
  supervisor.child = child

  supervisor.stop()

  assert child.terminated
  assert child.killed


class FakeParams:
  def __init__(self, keys=""):
    self.values = {"GithubSshKeys": keys} if keys else {}

  def get(self, key):
    return self.values.get(key)

  def put(self, key, value, block=False):
    self.values[key] = value


def test_persistent_ssh_key_is_merged_without_replacing_session_key(tmp_path: Path):
  persistent = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIG0q8swD6V0R8M1U+6TXQqNl6UeHj5J6ybbD/1CV owner"
  session = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBJnQxRlWCEFxGXQCbNIB9ddRtJPd1vVY1GcKfK1fc83 owner-session"
  key_file = tmp_path / "authorized_keys"
  key_file.write_text(persistent + "\n")
  params = FakeParams(session + "\n")

  assert ensure_persistent_ssh_keys(params, key_file)
  assert params.values["GithubSshKeys"].splitlines() == [session, persistent]
  assert not ensure_persistent_ssh_keys(params, key_file)


def test_invalid_persistent_ssh_keys_are_ignored(tmp_path: Path):
  key_file = tmp_path / "authorized_keys"
  key_file.write_text("not-a-key\nssh-rsa invalid\n")

  assert read_persistent_ssh_keys(key_file) == []
  assert not ensure_persistent_ssh_keys(FakeParams(), key_file)
