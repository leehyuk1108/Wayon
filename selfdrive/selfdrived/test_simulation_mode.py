import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from selfdrive.selfdrived.simulation_mode import get_simulation_ignore_phone_dm, put_simulation_ignore_phone_dm


class FakeParams:
  def __init__(self, known):
    self.known = known
    self.values = {}

  def check_key(self, key):
    if not self.known:
      raise RuntimeError(key)

  def get_bool(self, key):
    self.check_key(key)
    return self.values.get(key, False)

  def put_bool(self, key, value):
    self.check_key(key)
    self.values[key] = value


def test_simulation_phone_dm_uses_native_param_when_known(tmp_path):
  params = FakeParams(known=True)
  put_simulation_ignore_phone_dm(True, params, tmp_path)
  assert get_simulation_ignore_phone_dm(params, tmp_path)


def test_simulation_phone_dm_falls_back_to_file(tmp_path):
  params = FakeParams(known=False)
  put_simulation_ignore_phone_dm(True, params, tmp_path)
  assert get_simulation_ignore_phone_dm(params, tmp_path)
