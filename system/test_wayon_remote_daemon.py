import subprocess

from openpilot.system import wayon_remote_daemon as daemon


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
