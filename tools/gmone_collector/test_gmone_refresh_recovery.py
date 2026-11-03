from types import SimpleNamespace

import pytest

from openpilot.tools.gmone_collector import gmone_background as bg

NOW = 1793691700.0
SCOPE = "a" * 64


def make_state(tmp_path):
  return bg.State(tmp_path / "state.json", SCOPE)


class ReadFixture:
  def __init__(self, tmp_path):
    self.now = NOW
    self.refresh = {"pending": True, "requestedAt": bg.iso(NOW-1), "completedAt": None}
    self.calls = []
    self.rejections = 0
    self.upload_failures = 0
    self.cached = {}
    self.posts = []
    self.client = bg.Collector(
      {"accountFingerprint": bg.account_fingerprint("test@example.invalid"),
       "url": "https://wayon-cloud.hyuklee.workers.dev", "deviceId": "test-device"},
      make_state(tmp_path), "test@example.invalid", "unused", "unused", "unused", now=lambda:self.now)
    self.client.cloud = self.cloud
    self.client.cache = SimpleNamespace(read_cached_status=lambda *a, **kw:self.cached, clear_session=lambda:None)
    self.client.client = SimpleNamespace(authenticated=True, vin="v", user_uuid="u",
      login=self.login, clear_session=self.clear, read_car_status=self.read)

  def login(self, *args):
    self.calls.append((self.now, "login"))
    self.client.client.authenticated = True

  def clear(self):
    self.client.client.authenticated = False

  def read(self, **kwargs):
    assert kwargs == {"last_received_time":0,"refresh_dtc":False}
    self.calls.append((self.now, "read"))
    if self.rejections:
      self.rejections -= 1
      raise bg.protocol.AuthenticationError("authenticated_request_rejected")
    return {"login":{"success":0},"body":{"success":0,"car_status":{"fLvl":42}},"timestamp":self.now*1000}

  def cloud(self, path, body=None):
    if body is None:
      return dict(self.refresh)
    assert path == "/api/gmone/status"
    self.posts.append(body)
    if self.upload_failures:
      self.upload_failures -= 1
      raise bg.protocol.ProtocolError("HTTP 503", 503)
    if body.get("refreshStartedAt") and bg.parse_iso(body["refreshStartedAt"]) >= bg.parse_iso(self.refresh["requestedAt"]):
      self.refresh.update(pending=False, completedAt=bg.iso(self.now))
    return {"ok":True}

  def step(self, offset):
    self.now = NOW + offset
    self.client.step()

  @property
  def reads(self):
    return [at for at, call in self.calls if call == "read"]


def test_auth_failure_retries_same_request_after_login_not_marked_done(tmp_path):
  f = ReadFixture(tmp_path)
  f.rejections = 1
  f.step(0)
  assert f.refresh["pending"] and "completedRequest" not in f.client.state.data
  assert f.client.health["collectionError"] == "AuthenticationError"
  f.step(121)
  assert f.client.client.authenticated
  assert f.client.health["collectionError"] == "AuthenticationError"
  f.step(299)
  assert f.reads == [NOW]
  f.step(300)
  assert f.reads == [NOW, NOW+300]
  assert not f.refresh["pending"]
  assert "collectionError" not in f.client.health
  assert f.client.health["lastCollectionFailure"]["code"] == "AuthenticationError"
  f.step(330)
  assert f.client.state.data["completedRequest"] == NOW-1
  f.step(600)
  assert len(f.reads) == 2


def test_fresh_login_immediately_precedes_each_budgeted_read(tmp_path):
  f = ReadFixture(tmp_path)
  f.step(0)
  assert f.calls == [(NOW,"login"),(NOW,"read")]
  f.step(30)
  assert len(f.calls) == 2


def test_unresolved_failure_survives_collector_restart(tmp_path):
  f = ReadFixture(tmp_path)
  f.rejections = 1
  f.step(0)
  restarted = ReadFixture(tmp_path)
  assert restarted.client.health["collectionFailure"] == "AuthenticationError"
  assert restarted.client.health["lastCollectionFailure"]["at"] == bg.iso(NOW)


def test_migrate_legacy_consumed_request_without_resetting_budget(tmp_path):
  s = make_state(tmp_path)
  s.data.update(handledRequest=NOW-60, lastActive=NOW-300, budgetStart=NOW-600, activeCount=12)
  s.save()
  s = make_state(tmp_path)
  assert s.reserve_active(NOW, bg.iso(NOW-60))
  assert s.data["activeCount"] == 13
  assert "completedRequest" not in s.data


def test_repeated_auth_failure_is_bounded_across_restart(tmp_path):
  f = ReadFixture(tmp_path)
  f.rejections = 10
  for offset in (0,121,300,421,600,721,900,1800):
    f.client.state = make_state(tmp_path)
    f.step(offset)
  assert f.reads == [NOW,NOW+300,NOW+600]
  assert f.client.state.data["activeCount"] == 3
  assert f.refresh["pending"]


def test_hourly_failure_retries_without_manual_request(tmp_path):
  f = ReadFixture(tmp_path)
  f.refresh["pending"] = False
  f.rejections = 1
  f.step(0)
  f.step(121)
  f.step(300)
  assert len(f.reads) == 2


@pytest.mark.parametrize("count,delta", [(36,300),(35,299),(36,-1)])
def test_pending_request_never_bypasses_budget_or_time(tmp_path,count,delta):
  s = make_state(tmp_path)
  s.data.update(lastActive=NOW, budgetStart=NOW-10, activeCount=count)
  assert not s.reserve_active(NOW+delta,bg.iso(NOW-1))


def test_new_request_has_own_attempts_but_shares_daily_budget(tmp_path):
  s = make_state(tmp_path)
  for offset in (0,300,600):
    assert s.reserve_active(NOW+offset,bg.iso(NOW-1))
  assert not s.reserve_active(NOW+900,bg.iso(NOW-1))
  assert s.reserve_active(NOW+900,bg.iso(NOW+899))
  assert s.data["activeJob"]["attempts"] == 1 and s.data["activeCount"] == 4


def test_upload_retries_not_vehicle_read_and_passive_cache_keeps_ack(tmp_path):
  f = ReadFixture(tmp_path)
  f.upload_failures = 4
  f.step(0)
  f.cached = {"time":(NOW+60)*1000,"car_status":{"fLvl":43}}
  for offset in (30,90,210,300):
    f.step(offset)
  assert len(f.reads) == 1
  assert f.client.state.data["pending"]["source"] == "gmone-direct"
  assert f.client.state.data["pending"]["vehicleUpdatedAt"] == bg.iso(NOW)
  assert f.refresh["pending"]
  f.step(450)
  assert not f.refresh["pending"]
  assert len(f.reads) == 1
  f.step(480)
  assert f.client.state.data["completedRequest"] == NOW-1


@pytest.mark.parametrize("refresh", [
  {"pending":True,"requestedAt":bg.iso(NOW-1),"completedAt":bg.iso(NOW)},
  {"pending":False,"requestedAt":bg.iso(NOW),"completedAt":bg.iso(NOW-1)},
  {"pending":False,"requestedAt":bg.iso(NOW),"completedAt":None},
])
def test_only_server_confirmed_completion_is_remembered(tmp_path,refresh):
  s = make_state(tmp_path)
  s.observe_refresh(refresh)
  assert "completedRequest" not in s.data


@pytest.mark.parametrize("observed,collected", [(NOW-1,NOW),(NOW+121,NOW),(NOW,NOW+121)])
def test_old_or_out_of_window_status_never_completes_refresh(tmp_path,observed,collected):
  s = make_state(tmp_path)
  assert not s.offer({"fLvl":42},observed,"gmone-direct",collected,NOW)
  assert "pending" not in s.data


def test_valid_direct_ack_can_follow_newer_passive_without_clock_regression(tmp_path):
  s = make_state(tmp_path)
  s.offer({"fLvl":43},NOW+1,"gmone-official-cache",NOW+1)
  assert s.offer({"fLvl":42},NOW,"gmone-direct",NOW+2,NOW)
  assert s.data["latestEpoch"] == NOW+1
  assert s.data["pending"]["refreshStartedAt"] == bg.iso(NOW)


def test_future_and_expired_requests_do_not_wake_a_recent_vehicle(tmp_path):
  s = make_state(tmp_path)
  s.data["latestEpoch"] = NOW-30
  assert not s.reserve_active(NOW,bg.iso(NOW+1))
  assert not s.reserve_active(NOW,bg.iso(NOW-3601))
