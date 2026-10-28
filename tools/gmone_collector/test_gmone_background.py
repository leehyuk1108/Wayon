import io
import json
from types import SimpleNamespace
from urllib import error

import pytest

from openpilot.tools.gmone_collector import gmone_background as bg

NOW = 1793190000.0
SCOPE = "a" * 64


def state(tmp_path):
  return bg.State(tmp_path / "state.json", SCOPE)


@pytest.mark.parametrize("observed", [None, True, "invalid", float("nan"), float("inf"), 0, NOW+121, NOW-86401])
def test_invalid_time_never_promotes_or_uploads(tmp_path, observed):
  s = state(tmp_path)
  assert not s.offer({"fLvl": 42}, observed, "gmone-official-cache", NOW)
  assert "pending" not in s.data


def test_cache_keeps_own_time_and_no_refresh_ack(tmp_path):
  s = state(tmp_path)
  assert s.offer({"fLvl": 42}, (NOW-900)*1000, "gmone-official-cache", NOW)
  p = s.data["pending"]
  assert p["vehicleUpdatedAt"] == bg.iso(NOW-900)
  assert p["collectedAt"] == bg.iso(NOW)
  assert "refreshStartedAt" not in p
  assert p["clientScope"] == SCOPE
  assert p["status"]["last_update"] == p["status"]["collector_last_success"]


def test_retry_persists_without_new_vehicle_sample(tmp_path):
  s = state(tmp_path)
  s.offer({"fLvl": 42}, NOW-1, "gmone-official-cache", NOW)
  def fail(_):
    raise bg.protocol.ProtocolError("HTTP 503", 503)
  with pytest.raises(bg.protocol.ProtocolError):
    s.upload(fail, NOW)
  s = state(tmp_path)
  assert not s.offer({"fLvl": 42}, NOW-1, "gmone-official-cache", NOW+31)
  assert s.upload(lambda _: pytest.fail("backoff"), NOW+29) == "idle"
  sent = []
  assert s.upload(lambda p: sent.append(p) or {"ok": True}, NOW+31) == "stored"
  assert len(sent) == 1
  assert sent[0]["vehicleUpdatedAt"] == bg.iso(NOW-1)
  assert "pending" not in state(tmp_path).data


def test_newest_replaces_pending_and_old_does_not_regress(tmp_path):
  s = state(tmp_path)
  s.offer({"fLvl": 42}, NOW-50, "gmone-official-cache", NOW)
  s.offer({"fLvl": 43}, NOW-20, "gmone-official-cache", NOW)
  assert not s.offer({"fLvl": 41}, NOW-40, "gmone-official-cache", NOW)
  assert s.data["pending"]["status"]["fuel"] == "43"


def test_same_epoch_changed_values_are_not_discarded_locally(tmp_path):
  s = state(tmp_path)
  s.offer({"fLvl": 42}, NOW, "gmone-official-cache", NOW)
  assert s.offer({"fLvl": 43}, NOW, "gmone-official-cache", NOW+1)


def test_409_is_superseded_not_failure_or_relogin(tmp_path):
  s = state(tmp_path)
  s.offer({"fLvl": 42}, NOW, "gmone-direct", NOW)
  def rejected(_):
    raise bg.protocol.ProtocolError("superseded", 409, "snapshot_not_newer")
  assert s.upload(rejected, NOW) == "superseded"
  assert "pending" not in s.data


@pytest.mark.parametrize("reply", [{}, {"ok": False}, {"ok": "true"}])
def test_only_confirmed_ack_removes_pending(tmp_path, reply):
  s = state(tmp_path)
  s.offer({"fLvl": 42}, NOW, "gmone-direct", NOW)
  with pytest.raises(ValueError):
    s.upload(lambda _: reply, NOW)
  assert s.data["pending"]


def test_expired_outbox_never_retimestamped(tmp_path):
  s = state(tmp_path)
  s.offer({"fLvl": 42}, NOW, "gmone-direct", NOW)
  assert s.upload(lambda _: pytest.fail("expired"), NOW+86401) == "expired"


def test_scope_mismatch_fails_closed_and_preserves_file(tmp_path):
  s = state(tmp_path)
  s.save()
  before = s.path.read_bytes()
  with pytest.raises(ValueError):
    bg.State(s.path, "b"*64)
  assert s.path.read_bytes() == before


def test_corrupt_state_does_not_reset_request_budget(tmp_path):
  path = tmp_path / "state.json"
  path.write_text("{")
  with pytest.raises(ValueError):
    state(tmp_path)


def test_restart_does_not_repeat_active_and_hourly_stays_bounded(tmp_path):
  s = state(tmp_path)
  assert s.reserve_active(NOW)
  s = state(tmp_path)
  assert not s.reserve_active(NOW+30)
  assert not s.reserve_active(NOW+3599)
  assert s.reserve_active(NOW+3600)


def test_fresh_passive_data_prevents_unnecessary_active_read(tmp_path):
  s = state(tmp_path)
  s.offer({"fLvl": 42}, NOW-10, "gmone-official-cache", NOW)
  assert not s.reserve_active(NOW)


def test_each_manual_request_once_and_request_burst_limited(tmp_path):
  s = state(tmp_path)
  assert s.reserve_active(NOW, bg.iso(NOW-1))
  assert not state(tmp_path).reserve_active(NOW+300, bg.iso(NOW-1))
  assert not s.reserve_active(NOW+10, bg.iso(NOW+9))
  assert s.reserve_active(NOW+300, bg.iso(NOW+299))


def test_daily_budget_and_backward_clock_do_not_reset_limit(tmp_path):
  s = state(tmp_path)
  s.data.update(budgetStart=NOW, activeCount=36)
  assert not s.reserve_active(NOW+3600, bg.iso(NOW+3599))
  assert not s.reserve_active(NOW-100)
  assert s.reserve_active(NOW+86400)


@pytest.mark.parametrize("operation", [19, 59, 63, 70, 100])
def test_background_rejects_controls_and_auxiliary_reads(operation):
  with pytest.raises(bg.protocol.ProtocolError):
    bg.StatusClient()._post("/", operation, {}, {})


def test_background_rejects_dtc_scan():
  with pytest.raises(bg.protocol.ProtocolError):
    bg.StatusClient()._post("/", 21, {}, {"refresh_dtc": True})


def test_multiple_vehicle_login_fails_closed(monkeypatch):
  response={"login":{"success":0,"user_info_uuid":"u","token_key":"t","car_info":{"a":{},"b":{}}},"body":{"success":0}}
  monkeypatch.setattr(bg.protocol, "_json_request", lambda *a, **kw: response)
  with pytest.raises(bg.protocol.AuthenticationError):
    bg.StatusClient().login("test", "secret")


def test_latest_login_schema_and_identity_supported(monkeypatch):
  response={"login":{"success":0,"user_info_uuid":"u","token_key":"t","car_info":{"a":{}}},"body":{"success":0}}
  monkeypatch.setattr(bg.protocol, "_json_request", lambda *a, **kw: response)
  c=bg.StatusClient(); c.login("test", "secret")
  assert c.user_uuid == "u" and c.vin == "a"


def collector(tmp_path):
  config={"accountFingerprint":bg.account_fingerprint("test@example.invalid"),"url":"https://wayon-cloud.hyuklee.workers.dev","deviceId":"test-device"}
  return bg.Collector(config, state(tmp_path), "test@example.invalid", "secret", "key", "upload", now=lambda:NOW)


def test_cloud_failure_does_not_wake_vehicle_or_clear_session(tmp_path):
  c=collector(tmp_path)
  c.client=SimpleNamespace(authenticated=True,vin="v",user_uuid="u",read_car_status=lambda **kw:pytest.fail("vehicle wake"))
  c.cache=SimpleNamespace(read_cached_status=lambda *a,**kw:{})
  def fail(*a,**kw): raise TimeoutError()
  c.cloud=fail
  c.step()
  assert c.client.authenticated
  assert c.health["cloudError"] == "TimeoutError"


def test_active_read_failure_keeps_prior_data(tmp_path):
  c=collector(tmp_path)
  c.state.offer({"fLvl":42},NOW-7200,"gmone-official-cache",NOW)
  c.cloud=lambda *a,**kw:{"deviceId":"test-device","ok":True,"pending":False}
  c.client=SimpleNamespace(authenticated=True,vin="v",user_uuid="u",read_car_status=lambda **kw:{"login":{"success":0},"body":{"success":3},"timestamp":NOW*1000})
  c.cache=SimpleNamespace(read_cached_status=lambda *a,**kw:{})
  c.step()
  assert c.state.data["latestEpoch"] == NOW-7200
  assert c.health["activeResult"] == 3
  assert c.state.data["activeCount"] == 1


def test_device_identity_mismatch_rejects_ack(tmp_path,monkeypatch):
  c=collector(tmp_path)
  monkeypatch.setattr(bg.protocol,"_json_request",lambda *a,**kw:{"deviceId":"wrong","ok":True})
  with pytest.raises(ValueError): c.cloud("/api/gmone/status",{})


def test_credentials_never_persist_in_snapshot(tmp_path):
  s=state(tmp_path)
  s.offer({"fLvl":42,"token_key":"secret","password":"secret","vin":"1GNEVKKW0NJ123456"},NOW,"gmone-direct",NOW)
  assert "secret" not in s.path.read_text()


def test_duplicate_process_lock(tmp_path):
  with bg.instance_lock(tmp_path/"lock"):
    with pytest.raises(OSError):
      with bg.instance_lock(tmp_path/"lock"): pass


def test_json_timeout_sanitized_and_bounded(monkeypatch):
  def fail(*a, **kw): raise TimeoutError("secret")
  monkeypatch.setattr(bg.protocol,"_open_request",fail)
  with pytest.raises(bg.protocol.ProtocolError) as e:
    bg.protocol._json_request("https://example.invalid/?auth=secret")
  assert "secret" not in str(e.value)


def test_no_redirect_handler():
  assert bg.protocol._NoRedirect().redirect_request(None,None,302,"",{},"https://evil.invalid") is None


def test_other_409_preserves_outbox(tmp_path):
  s = state(tmp_path)
  s.offer({"fLvl":42}, NOW, "gmone-direct", NOW)
  def conflict(_): raise bg.protocol.ProtocolError("other", 409)
  with pytest.raises(bg.protocol.ProtocolError): s.upload(conflict, NOW)
  assert s.data["pending"]


@pytest.mark.parametrize("scope", [None, "", "a"*63, "z"*64])
def test_invalid_scope_rejected(tmp_path, scope):
  with pytest.raises(ValueError): bg.State(tmp_path/"state", scope)


def test_post_requires_read_identity_first(tmp_path, monkeypatch):
  c = collector(tmp_path)
  calls = []
  monkeypatch.setattr(bg.protocol, "_json_request", lambda *a,**kw: calls.append(kw) or {"deviceId":"wrong"})
  with pytest.raises(ValueError): c.cloud("/api/gmone/status", {})
  assert not calls
  with pytest.raises(ValueError): c.cloud("/api/gmone/refresh")
  with pytest.raises(ValueError): c.cloud("/api/gmone/status", {})
  assert len(calls) == 1


def test_firebase_failure_backs_off(tmp_path):
  c = collector(tmp_path)
  clock = [NOW]
  c.now = lambda: clock[0]
  c.client = SimpleNamespace(authenticated=True, vin="v", user_uuid="u")
  c.cloud = lambda *a,**kw: {"pending":False}
  c.state.data["lastActive"] = NOW
  calls = []
  def fail(*a,**kw):
    calls.append(clock[0])
    raise bg.protocol.AuthenticationError("cache login rejected")
  c.cache = SimpleNamespace(read_cached_status=fail)
  for offset in (0, 30, 60, 90, 120, 180, 359, 360):
    clock[0] = NOW + offset
    c.step()
  assert calls == [NOW, NOW+120, NOW+360]
  assert c.next_cache == NOW+840


def test_active_start_excludes_slow_preflight_and_cache(tmp_path):
  c = collector(tmp_path)
  clock = [NOW]
  c.now = lambda: clock[0]
  sent = []
  def cloud(path, body=None):
    if body: sent.append(body)
    return {"ok":True,"pending":True,"requestedAt":bg.iso(NOW-1)}
  c.cloud = cloud
  def cache(*a,**kw):
    clock[0] += 150
    return {}
  def read(**kw):
    assert kw == {"last_received_time":0,"refresh_dtc":False}
    clock[0] += 1
    return {"login":{"success":0},"body":{"success":0,"car_status":{"fLvl":42}},"timestamp":clock[0]*1000}
  c.cache = SimpleNamespace(read_cached_status=cache)
  c.client = SimpleNamespace(authenticated=True,vin="v",user_uuid="u",read_car_status=read)
  c.step()
  assert sent[0]["refreshStartedAt"] == bg.iso(NOW+150)
  assert sent[0]["vehicleUpdatedAt"] == bg.iso(NOW+151)


def test_history_cursor_comes_only_from_server_and_survives_restart(tmp_path):
  c = collector(tmp_path)
  c.cloud = lambda *a,**kw: {"ok":True,"pending":False}
  c.cache = SimpleNamespace(read_cached_status=lambda *a,**kw:{})
  def read(**kw):
    assert kw["last_received_time"] == 0
    return {"login":{"success":0},"timestamp":NOW*1000,"body":{"success":0,"car_status":{"fLvl":42},
      "running_cycles_data":[{"time":20},{"time":10},{"time":True},{"time":-3}]}}
  c.client = SimpleNamespace(authenticated=True,vin="v",user_uuid="u",read_car_status=read)
  c.step()
  c = collector(tmp_path)
  c.now = lambda: NOW+3600
  c.cloud = lambda *a,**kw: {"ok":True,"pending":False}
  c.cache = SimpleNamespace(read_cached_status=lambda *a,**kw:{})
  called = []
  def next_read(**kw):
    called.append(kw["last_received_time"])
    return {"login":{"success":0},"body":{"success":3}}
  c.client = SimpleNamespace(authenticated=True,vin="v",user_uuid="u",read_car_status=next_read)
  c.step()
  assert called == [20]


def test_failure_summary_never_contains_url_or_credential():
  assert bg.failure_code(bg.protocol.ProtocolError("HTTP 400 secret",400)) == "http_400"
  assert bg.failure_code(bg.protocol.ProtocolError("Non-JSON secret")) == "non_json"
  assert bg.failure_code(RuntimeError("secret")) == "RuntimeError"


def test_http_400_reserves_budget_without_losing_cursor_or_session(tmp_path):
  c = collector(tmp_path)
  c.state.data["historyCursor"] = 20
  c.cloud = lambda *a,**kw: {"ok":True,"pending":False}
  c.cache = SimpleNamespace(read_cached_status=lambda *a,**kw:{})
  def read(**kw): raise bg.protocol.ProtocolError("HTTP 400",400)
  c.client = SimpleNamespace(authenticated=True,vin="v",user_uuid="u",read_car_status=read)
  c.step()
  assert state(tmp_path).data["historyCursor"] == 20
  assert state(tmp_path).data["activeCount"] == 1
  assert c.client.authenticated
  assert c.health["collectionFailure"] == "http_400"


def test_oversized_response_fails_before_decode(monkeypatch):
  monkeypatch.setattr(bg.protocol,"_open_request",lambda *a,**kw:io.BytesIO(b" "*(512*1024+1)))
  with pytest.raises(bg.protocol.ProtocolError) as exc:
    bg.protocol._json_request("https://example.invalid/")
  assert bg.failure_code(exc.value) == "response_size"


@pytest.mark.parametrize("error_code", ["snapshot_not_newer", "other", "secret"])
def test_only_allowlisted_http_conflict_code_survives(monkeypatch,error_code):
  def fail(*a,**kw):
    raise error.HTTPError("https://example.invalid/",409,"conflict",{},io.BytesIO(json.dumps({"error":error_code}).encode()))
  monkeypatch.setattr(bg.protocol,"_open_request",fail)
  with pytest.raises(bg.protocol.ProtocolError) as exc:
    bg.protocol._json_request("https://example.invalid/")
  assert exc.value.error_code == (error_code if error_code == "snapshot_not_newer" else None)


def test_authenticated_async_data_without_repeated_login_is_uploaded(tmp_path,monkeypatch):
  c = collector(tmp_path)
  c.client._uuid, c.client._token, c.client._vin = "u", "token", "v"
  sent, operations = [], []
  def post(url, payload, **kw):
    operation = payload["header"]["id"]
    operations.append(operation)
    if operation == 21:
      return {"login":{"success":0},"body":{"success":13,"wait_response":True,"ticket_uuid":"ticket"},"timestamp":NOW*1000}
    assert operation == 66
    return {"login":{"success":0},"body":{"success":0,"fetched_data":{
      "header":{"id":21},"body":{"success":0,"car_status":{"fLvl":42}},"timestamp":NOW*1000}}}
  monkeypatch.setattr(bg.protocol,"_json_request",post)
  resolve = bg.protocol.resolve_async_response
  monkeypatch.setattr(bg.protocol,"resolve_async_response",lambda *a,**kw:resolve(*a,**kw,poll_seconds=0))
  c.cache = SimpleNamespace(read_cached_status=lambda *a,**kw:{})
  c.cloud = lambda path,body=None: (sent.append(body) if body else None) or {"ok":True,"pending":False}
  c.step()
  assert operations == [21,66]
  assert sent[0]["status"]["fuel"] == "42"
  assert sent[0]["source"] == "gmone-direct"
  assert "collectionError" not in c.health
  assert c.health["resultTimedOut"] is False


def test_outer_authentication_failure_cannot_smuggle_nested_success(monkeypatch):
  c = bg.StatusClient()
  c._uuid, c._token = "u", "t"
  monkeypatch.setattr(bg.protocol,"_json_request",lambda *a,**kw:{
    "login":{"success":1},"body":{"success":0,"fetched_data":{"body":{"success":0,"car_status":{"fLvl":42}}}}})
  with pytest.raises(bg.protocol.AuthenticationError): c.fetch_result("ticket")
