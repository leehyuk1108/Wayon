import ast
from pathlib import Path

from openpilot.system.remote_simulation_server import SimulationState, clamp, is_allowed_client


def test_client_network_filter():
  assert is_allowed_client("127.0.0.1")
  assert is_allowed_client("192.168.35.69")
  assert not is_allowed_client("8.8.8.8")
  assert not is_allowed_client("invalid")


def test_clamp():
  assert clamp(-2, -1, 1) == -1
  assert clamp(0.25, -1, 1) == 0.25
  assert clamp(2, -1, 1) == 1


def test_input_is_bounded_and_brake_has_priority():
  state = SimulationState()
  result = state.update(2, 0.8, 0.4, 3, now=10.0)
  assert result["steering"] == 1.0
  assert result["accelerator"] == 0.0
  assert result["brake"] == 0.4
  assert result["sequence"] == 3


def test_watchdog_resets_all_inputs():
  state = SimulationState(watchdog_timeout=0.3)
  state.update(-0.5, 0.7, 0, 1, now=10.0)
  result = state.snapshot(now=10.31)
  assert result["steering"] == 0.0
  assert result["accelerator"] == 0.0
  assert result["brake"] == 0.0


def test_server_has_no_vehicle_control_imports():
  source_path = Path(__file__).with_name("remote_simulation_server.py")
  tree = ast.parse(source_path.read_text(encoding="utf-8"))
  imported = set()
  for node in ast.walk(tree):
    if isinstance(node, ast.Import):
      imported.update(alias.name.split(".")[0] for alias in node.names)
    elif isinstance(node, ast.ImportFrom) and node.module:
      imported.add(node.module.split(".")[0])
  assert imported.isdisjoint({"cereal", "messaging", "opendbc", "panda"})
