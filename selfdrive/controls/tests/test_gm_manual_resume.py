import json
import socket
from tempfile import TemporaryDirectory

import pytest

from openpilot.sunnypilot.selfdrive.controls.lib import gm_manual_resume as resume


@pytest.fixture
def socket_path():
  # Darwin's Unix socket limit is shorter than pytest's default temp paths.
  with TemporaryDirectory(prefix="gm-resume-", dir="/tmp") as directory:
    yield directory + "/r.sock"


@pytest.fixture
def channel(socket_path, monkeypatch):
  now = [10_000_000_000]
  monkeypatch.setattr(resume.time, "monotonic_ns", lambda: now[0])
  receiver = resume.ManualResumeReceiver(socket_path)
  yield receiver, now
  receiver.close()


def send(receiver, issued, request_id="1" * 32, **kwargs):
  payload = {"schema": resume.SCHEMA, "id": request_id, "issuedAtMonoNs": issued, **kwargs}
  with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
    sock.sendto(json.dumps(payload).encode(), receiver.path)


def test_one_click_is_consumed_once_and_cannot_wait_for_eligibility(channel):
  receiver, now = channel
  assert resume.request_manual_resume(receiver.path)
  assert not receiver.poll(False)
  assert not receiver.poll(True)
  now[0] += 10_000_000
  assert resume.request_manual_resume(receiver.path)
  assert receiver.poll(True)
  assert not receiver.poll(True)


@pytest.mark.parametrize("offset", [-1, -250_000_001, 1])
def test_stale_future_and_pre_receiver_requests_are_discarded(channel, offset):
  receiver, now = channel
  send(receiver, now[0] + offset)
  assert not receiver.poll(True)
  now[0] += 1_000_000_000
  assert not receiver.poll(True)


def test_ttl_expires_while_receiver_is_busy(channel):
  receiver, now = channel
  assert resume.request_manual_resume(receiver.path)
  now[0] += resume.REQUEST_TTL_NS + 1
  assert not receiver.poll(True)


def test_rate_limit_and_duplicate_ids_prevent_repeated_launches(channel):
  receiver, now = channel
  send(receiver, now[0])
  assert receiver.poll(True)
  now[0] += 10_000_000
  send(receiver, now[0], "2" * 32)
  assert not receiver.poll(True)
  now[0] += resume.REQUEST_INTERVAL_NS
  send(receiver, now[0])
  assert not receiver.poll(True)
  send(receiver, now[0], "3" * 32)
  assert receiver.poll(True)


@pytest.mark.parametrize("payload", [b"broken", b"[]", b"null", b"{}", b"\xff", b"x" * 600])
def test_malformed_requests_do_not_interrupt_controls(channel, payload):
  receiver, _ = channel
  with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
    sock.sendto(payload, receiver.path)
  assert not receiver.poll(True)


@pytest.mark.parametrize("issued", [True, 1.5, "10000000000", None])
def test_timestamp_must_be_integer_nanoseconds(channel, issued):
  receiver, _ = channel
  send(receiver, issued)
  assert not receiver.poll(True)


def test_unavailable_receiver_is_reported_without_persisting_a_request(socket_path):
  path = socket_path
  assert not resume.request_manual_resume(path)
  receiver = resume.ManualResumeReceiver(path)
  try:
    assert not receiver.poll(True)
  finally:
    receiver.close()


def test_second_receiver_cannot_steal_an_active_socket(channel):
  receiver, _ = channel
  with pytest.raises(OSError):
    resume.ManualResumeReceiver(receiver.path)
  assert resume.request_manual_resume(receiver.path)
  assert receiver.poll(True)
