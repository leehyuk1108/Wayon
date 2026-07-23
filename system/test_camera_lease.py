import json

from openpilot.system.camera_lease import CameraLease


def test_camera_lease_allows_only_one_owner(tmp_path):
  path = tmp_path / "camera.lease"
  first = CameraLease("live", 30, path)
  second = CameraLease("snapshot", 30, path)

  assert first.acquire()
  assert not second.acquire()

  metadata = json.loads(path.read_text())
  assert metadata["owner"] == "live"
  assert metadata["expiresAt"] > metadata["acquiredAt"]

  first.release()
  assert second.acquire()
  second.release()


def test_camera_lease_context_releases_after_exception(tmp_path):
  path = tmp_path / "camera.lease"

  try:
    with CameraLease("live", 30, path) as lease:
      assert lease.acquired
      raise RuntimeError("stop")
  except RuntimeError:
    pass

  replacement = CameraLease("snapshot", 30, path)
  assert replacement.acquire()
  replacement.release()
