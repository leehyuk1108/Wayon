import json
import threading
from urllib.request import Request, urlopen

from openpilot.selfdrive.lane_marking.server import Handler, ThreadingHTTPServer


class FakeService:
  config = {"width": 8, "height": 4, "poly_left": [[0, 0], [1, 1], [0, 2]], "poly_right": []}

  def status(self):
    return {"integrated": True, "model": {"loaded": True}}

  def snapshot(self, stream_type):
    return b"jpeg-" + stream_type.encode()

  def save_config(self, config):
    self.config = config
    return config

  def set_settings(self, settings):
    return settings

  def clear_config(self):
    self.config = {}


def test_port_8082_page_and_configuration_apis():
  Handler.service = FakeService()
  server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
  thread = threading.Thread(target=server.serve_forever, daemon=True)
  thread.start()
  base = f"http://127.0.0.1:{server.server_port}"
  try:
    with urlopen(base + "/", timeout=2) as response:
      assert "V-ASM" in response.read().decode()
    with urlopen(base + "/api/status", timeout=2) as response:
      assert json.load(response)["integrated"] is True
    with urlopen(base + "/api/snapshot?stream=road", timeout=2) as response:
      assert response.read() == b"jpeg-road"

    request = Request(
      base + "/api/settings",
      data=b'{"threshold":0.5}',
      headers={"Content-Type": "application/json"},
      method="POST",
    )
    with urlopen(request, timeout=2) as response:
      assert json.load(response) == {"threshold": 0.5}
  finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)
