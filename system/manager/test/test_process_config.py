from cereal import car

from openpilot.common.params import Params
from openpilot.system.manager.process_config import RestartOnTransition, managed_processes, wayon_live_streaming


def test_restart_on_each_driving_state_transition():
  condition = RestartOnTransition(lambda _started, _params, _CP: True)
  params = Params()
  CP = car.CarParams.new_message()

  states = [False, False, True, True, False, False]
  assert [condition(started, params, CP) for started in states] == [True, True, False, True, False, True]


def test_wayon_live_stream_processes_are_offroad_only(monkeypatch):
  CP = car.CarParams.new_message()
  params = Params()

  monkeypatch.setattr("openpilot.system.manager.process_config.os.path.isfile", lambda _path: True)
  assert wayon_live_streaming(False, params, CP)
  assert not wayon_live_streaming(True, params, CP)

  monkeypatch.setattr("openpilot.system.manager.process_config.os.path.isfile", lambda _path: False)
  assert not wayon_live_streaming(False, params, CP)

  stream_process = managed_processes["stream_encoderd"]
  assert stream_process.cmdline[:2] == ["/usr/bin/env", "STREAM_BITRATE=5000000"]
