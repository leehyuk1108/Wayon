import ast
import http.client
import json
from pathlib import Path
from types import SimpleNamespace
import threading

import pytest

from openpilot.system.wayon_remote_control import (
  RemoteControlMode,
  RemoteControlState,
  RemoteControlServer,
  RemoteWideCamera,
  clamp,
  is_allowed_client,
)
from openpilot.system.wayon_remote_auth import RemotePasswordAuthorizer, RemotePasswordStore


def test_client_network_filter():
  assert is_allowed_client("127.0.0.1")
  assert is_allowed_client("192.168.35.69")
  assert not is_allowed_client("8.8.8.8")
  assert not is_allowed_client("invalid")


def test_clamp():
  assert clamp(-2, -1, 1) == -1
  assert clamp(0.25, -1, 1) == 0.25
  assert clamp(2, -1, 1) == 1


def test_input_requires_armed_owner_and_brake_has_priority():
  state = RemoteControlState()
  state.arm("controller-session-1", now=10.0)
  result = state.update("controller-session-1", 2, 0.8, 0.4, 1, now=10.1)
  assert result["steering"] == 1.0
  assert result["accelerator"] == 0.0
  assert result["brake"] == 0.4
  assert state.axes(now=10.1) == ([-0.4, 1.0], True)
  assert state.owned_by("controller-session-1", now=10.1)
  assert not state.owned_by("controller-session-2", now=10.1)


def test_stale_sequence_and_second_controller_are_rejected():
  state = RemoteControlState()
  state.arm("controller-session-1", now=10.0)
  state.update("controller-session-1", 0, 0.2, 0, 2, now=10.1)
  with pytest.raises(ValueError, match="stale"):
    state.update("controller-session-1", 1, 1, 0, 2, now=10.11)
  with pytest.raises(PermissionError, match="another"):
    state.arm("controller-session-2", now=10.12)


def test_watchdog_zeros_and_disarms():
  state = RemoteControlState(watchdog_timeout=0.25)
  state.arm("controller-session-1", now=10.0)
  state.update("controller-session-1", -0.5, 0.7, 0, 1, now=10.1)
  axes, active = state.axes(now=10.36)
  assert axes == [0.0, 0.0]
  assert not active
  assert not state.snapshot(now=10.36)["armed"]


def test_remote_password_is_salted_hashed_and_session_bound(tmp_path):
  password_path = tmp_path / "password.json"
  store = RemotePasswordStore(password_path, iterations=100_000)
  store.set_password("test-password")
  contents = password_path.read_text(encoding="utf-8")
  assert "test-password" not in contents
  assert password_path.stat().st_mode & 0o777 == 0o600
  assert store.verify("test-password")
  assert not store.verify("wrong-password")

  authorizer = RemotePasswordAuthorizer(store, ttl=60)
  token = authorizer.login("test-password", "controller-session-1", "127.0.0.1", now=10.0)
  assert authorizer.authorized(f"Bearer {token}", "controller-session-1", "127.0.0.1", now=11.0)
  assert not authorizer.authorized(f"Bearer {token}", "controller-session-2", "127.0.0.1", now=11.0)
  assert not authorizer.authorized(f"Bearer {token}", "controller-session-1", "192.168.1.2", now=11.0)

  store.set_password("changed-password")
  assert not authorizer.authorized(f"Bearer {token}", "controller-session-1", "127.0.0.1", now=12.0)
  changed_token = authorizer.login("changed-password", "controller-session-1", "127.0.0.1", now=13.0)
  assert not authorizer.authorized(f"Bearer {changed_token}", "controller-session-1", "127.0.0.1", now=74.0)


def test_remote_control_does_not_import_raw_vehicle_output_modules():
  source_path = Path(__file__).with_name("wayon_remote_control.py")
  tree = ast.parse(source_path.read_text(encoding="utf-8"))
  imported = set()
  for node in ast.walk(tree):
    if isinstance(node, ast.Import):
      imported.update(alias.name.split(".")[0] for alias in node.names)
    elif isinstance(node, ast.ImportFrom) and node.module:
      imported.add(node.module.split(".")[0])
  assert imported.isdisjoint({"opendbc", "panda"})


def test_remote_control_uses_joystickd_without_physical_joystick_producer():
  process_config = Path(__file__).with_name("manager") / "process_config.py"
  source = process_config.read_text(encoding="utf-8")
  assert 'PythonProcess("joystickd", "tools.joystick.joystickd", or_(manual_control, notcar))' in source
  assert 'PythonProcess("joystick", "tools.joystick.joystick_control", and_(joystick, iscar))' in source
  assert 'params.get_bool("JoystickDebugMode") and not os.path.isfile(REMOTE_CONTROL_SESSION)' in source
  assert 'PythonProcess("remote_control_web", "system.wayon_remote_control", always_run' in source


class FakeParams:
  def __init__(self):
    self.values = {"JoystickDebugMode": True}

  def get_bool(self, key):
    return bool(self.values.get(key))

  def put_bool(self, key, value, block=False):
    self.values[key] = value


def test_remote_mode_is_one_shot_across_onroad_cycle(tmp_path):
  boot_id = tmp_path / "boot_id"
  boot_id.write_text("test-boot", encoding="utf-8")
  params = FakeParams()
  mode = RemoteControlMode(tmp_path / "next-drive", params=params, boot_id_path=boot_id)

  mode.activate(onroad=False)
  assert mode.status(onroad=False)["phase"] == "pending"
  assert not params.get_bool("JoystickDebugMode")
  assert mode.observe(onroad=False)
  assert mode.observe(onroad=True)
  assert mode.status(onroad=True)["phase"] == "active"
  assert not mode.observe(onroad=False)
  assert mode.status(onroad=False)["phase"] == "inactive"


def test_remote_mode_rejects_onroad_change_and_previous_boot(tmp_path):
  boot_id = tmp_path / "boot_id"
  boot_id.write_text("new-boot", encoding="utf-8")
  selection = tmp_path / "next-drive"
  selection.write_text(json.dumps({"version": 1, "bootId": "old-boot"}), encoding="utf-8")
  mode = RemoteControlMode(selection, boot_id_path=boot_id)

  assert not mode.observe(onroad=False)
  assert not selection.exists()
  with pytest.raises(PermissionError, match="offroad"):
    mode.activate(onroad=True)


def test_wide_camera_nv12_preview_encodes_jpeg():
  assert RemoteWideCamera().frame_interval == pytest.approx(0.05)
  width, height, stride = 8, 4, 8
  uv_offset = stride * height
  uv_height = 16
  data = bytes([96] * uv_offset + [128] * (stride * uv_height))
  jpeg = RemoteWideCamera._jpeg(SimpleNamespace(width=width, height=height, stride=stride,
                                                uv_offset=uv_offset, data=data))
  assert jpeg.startswith(b"\xff\xd8") and jpeg.endswith(b"\xff\xd9")


def test_web_ui_has_orientation_specific_controls_and_vehicle_info():
  html = Path(__file__).with_name("wayon_remote_control.html").read_text(encoding="utf-8")
  assert "@media (orientation:portrait)" in html
  assert "@media (orientation:landscape)" in html
  assert 'data-control="combined"' in html
  assert 'data-control="pedal"' in html
  assert 'data-control="steer"' in html
  assert 'id="speedValue"' in html
  assert 'id="gearValue"' in html
  assert ".vehicle-ui { position:relative; isolation:isolate;" in html
  assert ".camera img { display:none; position:absolute; z-index:0; inset:0;" in html
  assert "이미 원격제어 주행이 활성화된 상태라면 온로드 중 연결이 끊겨도" in html
  assert "setInterval(updateCamera,50)" in html


class FakeBridge:
  def __init__(self, onroad=True, active=True):
    self.stopped = threading.Event()
    self.engaged = True
    self.onroad = onroad
    self.active = active

  def available(self):
    return self.onroad and self.active

  def status(self):
    return {"onroad": self.onroad, "engaged": self.engaged, "armReady": self.onroad, "speedMps": 3.0, "gear": "D"}

  def mode_status(self):
    phase = "active" if self.active and self.onroad else "pending" if self.active else "inactive"
    return {"phase": phase, "enabled": self.active, "onroad": self.onroad}

  def activate(self):
    if self.onroad:
      raise PermissionError("activation is only available while offroad")
    self.active = True
    return self.mode_status()

  def deactivate(self):
    if self.onroad:
      raise PermissionError("remote mode cannot be changed while onroad")
    self.active = False
    return self.mode_status()

  def run(self):
    self.stopped.wait()

  def stop(self):
    self.stopped.set()


class FakeCamera:
  def __init__(self):
    self.stopped = False

  def frame(self):
    return b"\xff\xd8wide-camera\xff\xd9"

  def stop(self):
    self.stopped = True


def make_authorizer(tmp_path, password="test-password"):
  store = RemotePasswordStore(tmp_path / "password.json", iterations=100_000)
  store.set_password(password)
  return RemotePasswordAuthorizer(store)


def login(connection, password="test-password", session="controller-session-1"):
  body = json.dumps({"password": password})
  connection.request("POST", "/api/login", body=body,
                     headers={"Content-Type": "application/json", "X-Wayon-Control-Session": session})
  response = connection.getresponse()
  payload = json.loads(response.read())
  return response.status, payload


def test_http_api_requires_password_session_and_armed_monotonic_control(tmp_path):
  camera = FakeCamera()
  bridge = FakeBridge(onroad=False, active=False)
  server = RemoteControlServer(("127.0.0.1", 0), state=RemoteControlState(),
                               authorizer=make_authorizer(tmp_path), bridge=bridge, camera=camera)
  server.start_bridge()
  serving = threading.Thread(target=server.serve_forever, daemon=True)
  serving.start()
  connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=2)
  try:
    connection.request("GET", "/api/status")
    unauthorized = connection.getresponse()
    assert unauthorized.status == 401
    unauthorized.read()

    login_status, login_payload = login(connection, password="wrong-password")
    assert login_status == 401
    assert "incorrect" in login_payload["error"]

    login_status, login_payload = login(connection)
    assert login_status == 200
    assert login_payload["mode"]["phase"] == "pending"
    auth = {"Authorization": f"Bearer {login_payload['token']}", "X-Wayon-Control-Session": "controller-session-1"}
    bridge.onroad = True

    connection.request("GET", "/api/status", headers=auth)
    status_response = connection.getresponse()
    assert status_response.status == 200
    status_payload = json.loads(status_response.read())
    assert status_payload["realVehicleControl"]
    assert status_payload["vehicle"]["gear"] == "D"
    assert not status_payload["state"]["ownedBySession"]

    connection.request("GET", "/api/camera.jpg", headers=auth)
    camera_response = connection.getresponse()
    assert camera_response.status == 200
    assert camera_response.getheader("Content-Type") == "image/jpeg"
    assert camera_response.read().startswith(b"\xff\xd8")

    connection.request("POST", "/api/arm", headers=auth)
    arm_response = connection.getresponse()
    assert arm_response.status == 200
    assert json.loads(arm_response.read())["state"]["armed"]

    body = json.dumps({"steering": 0.5, "accelerator": 0.4, "brake": 0.0, "sequence": 1})
    input_headers = {**auth, "Content-Type": "application/json"}
    server.bridge.engaged = False
    connection.request("POST", "/api/input", body=body, headers=input_headers)
    disengaged_response = connection.getresponse()
    assert disengaged_response.status == 409
    disengaged_response.read()

    server.bridge.engaged = True
    connection.request("POST", "/api/input", body=body, headers=input_headers)
    input_response = connection.getresponse()
    assert input_response.status == 200
    assert json.loads(input_response.read())["state"]["accelerator"] == 0.4

    connection.request("POST", "/api/input", body=body, headers=input_headers)
    stale_response = connection.getresponse()
    assert stale_response.status == 400
    stale_response.read()
  finally:
    connection.close()
    server.shutdown()
    serving.join(timeout=1)
    server.server_close()
    assert camera.stopped


def test_http_activation_is_offroad_only(tmp_path):
  bridge = FakeBridge(onroad=False, active=False)
  server = RemoteControlServer(("127.0.0.1", 0), state=RemoteControlState(),
                               authorizer=make_authorizer(tmp_path), bridge=bridge, camera=FakeCamera())
  server.start_bridge()
  serving = threading.Thread(target=server.serve_forever, daemon=True)
  serving.start()
  connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=2)
  try:
    login_status, login_payload = login(connection)
    assert login_status == 200
    assert login_payload["mode"]["phase"] == "pending"
    auth = {"Authorization": f"Bearer {login_payload['token']}", "X-Wayon-Control-Session": "controller-session-1"}

    connection.request("GET", "/api/camera.jpg", headers=auth)
    response = connection.getresponse()
    assert response.status == 409
    response.read()

    bridge.onroad = True
    connection.request("POST", "/api/deactivate", headers=auth)
    response = connection.getresponse()
    assert response.status == 409
    response.read()
  finally:
    connection.close()
    server.shutdown()
    serving.join(timeout=1)
    server.server_close()


def test_http_onroad_login_reconnects_only_active_remote_drive(tmp_path):
  bridge = FakeBridge(onroad=True, active=True)
  authorizer = make_authorizer(tmp_path)
  server = RemoteControlServer(("127.0.0.1", 0), state=RemoteControlState(),
                               authorizer=authorizer, bridge=bridge, camera=FakeCamera())
  server.start_bridge()
  serving = threading.Thread(target=server.serve_forever, daemon=True)
  serving.start()
  connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=2)
  try:
    login_status, login_payload = login(connection, session="reconnected-session-1")
    assert login_status == 200
    assert login_payload["reconnected"] is True
    assert login_payload["mode"]["phase"] == "active"

    auth = {"Authorization": f"Bearer {login_payload['token']}",
            "X-Wayon-Control-Session": "reconnected-session-1"}
    connection.request("POST", "/api/arm", headers=auth)
    response = connection.getresponse()
    assert response.status == 200
    assert json.loads(response.read())["state"]["armed"]

    bridge.active = False
    login_status, login_payload = login(connection, session="new-onroad-session-2")
    assert login_status == 409
    assert "offroad" in login_payload["error"]
  finally:
    connection.close()
    server.shutdown()
    serving.join(timeout=1)
    server.server_close()
