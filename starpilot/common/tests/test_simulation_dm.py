from openpilot.starpilot.common.simulation_dm import (
  SIMULATION_IGNORE_PHONE_DM,
  get_simulation_ignore_phone_dm,
  put_simulation_ignore_phone_dm,
)


class FakeParams:
  def __init__(self, known: bool):
    self.known = known
    self.values = {}

  def check_key(self, key):
    if not self.known:
      raise RuntimeError(key)

  def get_bool(self, key, default=False):
    self.check_key(key)
    return self.values.get(key, default)

  def put_bool(self, key, value):
    self.check_key(key)
    self.values[key] = value


def test_simulation_ignore_phone_dm_uses_native_param_when_known(tmp_path):
  params = FakeParams(known=True)

  put_simulation_ignore_phone_dm(True, params, tmp_path)

  assert get_simulation_ignore_phone_dm(params, tmp_path) is True
  assert not (tmp_path / SIMULATION_IGNORE_PHONE_DM).exists()


def test_simulation_ignore_phone_dm_falls_back_to_raw_file(tmp_path):
  params = FakeParams(known=False)

  put_simulation_ignore_phone_dm(True, params, tmp_path)

  assert get_simulation_ignore_phone_dm(params, tmp_path) is True
  assert (tmp_path / SIMULATION_IGNORE_PHONE_DM).read_text(encoding="utf-8") == "1"


def test_simulation_ignore_phone_dm_defaults_false_without_raw_file(tmp_path):
  params = FakeParams(known=False)

  assert get_simulation_ignore_phone_dm(params, tmp_path) is False
