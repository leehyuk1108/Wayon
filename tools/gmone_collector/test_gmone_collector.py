import json
from urllib import error

import pytest

from openpilot.tools.gmone_collector.gmone_collector import (
  CollectorState,
  GmoneClient,
  OfficialFirebaseClient,
  ProtocolError,
  _json_request,
  _redacted_url,
  build_wayon_payload,
  collect_auxiliary_data,
  collect_running_cycles,
  collector_diagnostic,
  collect_once,
  normalize_car_status,
  publish_wayon,
  resolve_async_response,
  wayon_refresh_pending,
)
from openpilot.tools.gmone_collector.gmone_store import GmoneStore


class TestNormalizeCarStatus:
  def test_maps_official_fields_to_existing_app_schema(self):
    raw = {
      "volt": 126,
      "btChrg": 58,
      "btHlth": 75,
      "odo": 55746,
      "fRng": 582,
      "fLvl": 63,
      "olLfe": 82,
      "trPrsLf": 252,
      "trPrsRf": 240,
      "trPrsLr": 248,
      "trPrsRr": 248,
    }
    result = normalize_car_status(raw, 1786960934000)
    assert result["battery"] == "12.6"
    assert result["battery_level"] == "58"
    assert result["battery_life"] == "75"
    assert result["mileage"] == "55,746"
    assert result["range"] == "582"
    assert result["fuel"] == "63"
    assert result["oil"] == "82"
    assert result["tire_pressure"] == "타이어 정보\n252 kpa\n240 kpa\n248 kpa\n248 kpa"
    assert result["source"] == "gmone-direct"
    assert result["collector_data_source"] == "gmone-direct"

  def test_omits_absent_optional_fields(self):
    result = normalize_car_status({}, 1786960934000)
    assert "fuel" not in result
    assert "tire_pressure" not in result


class TestWayonPublish:
  def test_builds_combined_payload_without_repeating_dtc_in_vehicle(self, tmp_path):
    store = GmoneStore(tmp_path / "gmone.sqlite3")
    store.save_snapshot(
      "car_status",
      "gmone-direct",
      {"fLvl": 63, "dtc": [{"code": "P0001"}], "dtcCnt": 1},
      1_786_960_934,
    )
    store.save_snapshot(
      "dtc",
      "gmone-direct",
      {"count": 1, "records": [{"code": "P0001"}]},
      1_786_960_934,
    )
    store.save_snapshot(
      "refresh_timing",
      "gmone-direct",
      {"response_server_time": 1_786_960_934},
      1_786_960_934,
    )

    result = build_wayon_payload(
      {"fuel": "63", "source": "gmone-direct"},
      {"collector_status": "success"},
      store,
    )
    assert result["schemaVersion"] == "wayon-gmone-v1"
    assert result["status"]["fuel"] == "63"
    assert "dtc" not in result["vehicle"]
    assert result["health"]["count"] == 1
    assert result["vehicleUpdatedAt"].endswith("+00:00")

  def test_publishes_to_dedicated_wayon_endpoint_with_bearer_token(self, monkeypatch):
    captured = {}

    def fake_json_request(url, payload, **kwargs):
      captured.update(url=url, payload=payload, kwargs=kwargs)
      return {"ok": True}

    monkeypatch.setattr("openpilot.tools.gmone_collector.gmone_collector._json_request", fake_json_request)
    publish_wayon("https://wayon.example", "token-value", {"schemaVersion": "wayon-gmone-v1"})
    assert captured["url"] == "https://wayon.example/api/gmone/status"
    assert captured["kwargs"]["headers"] == {"authorization": "Bearer token-value"}

  def test_checks_wayon_refresh_queue(self, monkeypatch):
    captured = {}

    def fake_json_request(url, payload, **kwargs):
      captured.update(url=url, payload=payload, kwargs=kwargs)
      return {"pending": True}

    monkeypatch.setattr("openpilot.tools.gmone_collector.gmone_collector._json_request", fake_json_request)
    assert wayon_refresh_pending("https://wayon.example", "token-value") is True
    assert captured["url"] == "https://wayon.example/api/gmone/refresh"
    assert captured["kwargs"]["method"] == "GET"


class TestReadOnlyProtocol:
  def test_blocks_any_non_read_operation(self):
    client = GmoneClient("https://example.invalid")
    with pytest.raises(ProtocolError):
      client._post("/blocked", 19, {}, {})

  def test_status_request_matches_official_protocol(self, monkeypatch):
    captured = {}

    def fake_json_request(url, payload, **_kwargs):
      captured["url"] = url
      captured["payload"] = payload
      return {"login": {"success": 0}, "body": {"success": 3}}

    monkeypatch.setattr("openpilot.tools.gmone_collector.gmone_collector._json_request", fake_json_request)
    client = GmoneClient()
    client._uuid = "user-uuid"
    client._token = "session-token"
    client.read_car_status(1234, refresh_dtc=True)
    assert captured["url"].endswith("/b1_connect_m")
    assert captured["payload"]["header"]["id"] == 21
    assert captured["payload"]["body"] == {"refresh_dtc": True, "last_received_time": 1234}

  def test_result_fetch_matches_official_protocol(self, monkeypatch):
    captured = {}

    def fake_json_request(url, payload, **_kwargs):
      captured["url"] = url
      captured["payload"] = payload
      return {"login": {"success": 0}, "body": {"success": 2}}

    monkeypatch.setattr("openpilot.tools.gmone_collector.gmone_collector._json_request", fake_json_request)
    client = GmoneClient()
    client._uuid = "user-uuid"
    client._token = "session-token"
    client.fetch_result("ticket-value")
    assert captured["payload"]["header"]["id"] == 66
    assert captured["payload"]["body"] == {"ticket_uuid": "ticket-value"}

  @pytest.mark.parametrize(
    ("method", "operation", "body"),
    (
      ("read_running_cycles", 45, {"last_received_time": 1234}),
      ("read_multipack_option", 59, {}),
      ("read_multipack_info", 63, {}),
      ("read_ev_battery_charge_data", 70, {"last_received_time": 1234}),
    ),
  )
  def test_additional_read_requests_match_official_protocol(self, monkeypatch, method, operation, body):
    captured = {}

    def fake_json_request(url, payload, **_kwargs):
      captured["url"] = url
      captured["payload"] = payload
      return {"login": {"success": 0}, "body": {"success": 0}}

    monkeypatch.setattr("openpilot.tools.gmone_collector.gmone_collector._json_request", fake_json_request)
    client = GmoneClient()
    client._uuid = "user-uuid"
    client._token = "session-token"
    arguments = (1234,) if "last_received_time" in body else ()
    getattr(client, method)(*arguments)
    assert captured["url"].endswith("/b1_connect_m")
    assert captured["payload"]["header"]["id"] == operation
    assert captured["payload"]["body"] == body

  def test_clearing_session_also_clears_vehicle_identity(self):
    client = GmoneClient()
    client._uuid = "user-uuid"
    client._token = "session-token"
    client._vin = "test-vin"
    client.clear_session()
    assert client.authenticated is False
    assert client.vin is None

  def test_error_messages_redact_query_secrets(self, monkeypatch):
    def fail(_request, timeout):
      raise error.HTTPError("https://example.invalid/data.json?auth=secret", 401, "unauthorized", {}, None)

    monkeypatch.setattr("openpilot.tools.gmone_collector.gmone_collector.request.urlopen", fail)
    with pytest.raises(ProtocolError) as exc_info:
      _json_request("https://example.invalid/data.json?auth=secret", None, method="GET")
    assert "secret" not in str(exc_info.value)
    assert "<redacted>" in str(exc_info.value)

  def test_redacts_api_keys_and_tokens(self):
    assert _redacted_url("https://example.invalid/path?key=secret") == "https://example.invalid/path?<redacted>"


class TestOfficialFirebaseFallback:
  def test_reads_cache_when_direct_module_is_asleep(self, tmp_path):
    class DirectClient:
      authenticated = True
      vin = "test-vin"
      user_uuid = "test-user"

      def read_car_status(self, _last_received_time, *, refresh_dtc=False):
        assert refresh_dtc is False
        return {"login": {"success": 0}, "body": {"success": 3}, "timestamp": 1786960934000}

    class CacheClient:
      def read_cached_status(self, email, password, vin, expected_user_uuid=None):
        assert email == "user@example.com"
        assert password == "password"
        assert vin == "test-vin"
        assert expected_user_uuid == "test-user"
        return {"car_status": {"fLvl": 63, "odo": 55746}, "time": 1786960934000}

    state = CollectorState(tmp_path / "state.json")
    normalized, diagnostic = collect_once(
      DirectClient(),
      state,
      "user@example.com",
      "password",
      CacheClient(),
    )
    assert normalized is not None
    assert normalized["fuel"] == "63"
    assert normalized["mileage"] == "55,746"
    assert normalized["source"] == "gmone-official-cache"
    assert normalized["collector_status"] == "success_cached"
    assert normalized["collector_direct_status"] == "inside_not_connected"
    assert diagnostic["collector_status"] == "inside_not_connected"

  def test_rejects_stale_official_cache(self, tmp_path):
    class DirectClient:
      authenticated = True
      vin = "test-vin"
      user_uuid = "test-user"

      def read_car_status(self, _last_received_time, *, refresh_dtc=False):
        assert refresh_dtc is False
        return {"login": {"success": 0}, "body": {"success": 3}, "timestamp": 1786960934000}

    class CacheClient:
      def read_cached_status(self, *_args, **_kwargs):
        return {"car_status": {"fLvl": 99}, "time": 1_700_000_000_000}

    normalized, diagnostic = collect_once(
      DirectClient(),
      CollectorState(tmp_path / "state.json"),
      "user@example.com",
      "password",
      CacheClient(),
      max_cache_age_seconds=60,
    )
    assert normalized is None
    assert diagnostic["collector_cache_status"] == "stale"
    assert "collector_cache_last_update" in diagnostic

  def test_firebase_status_url_uses_authenticated_account_path(self, monkeypatch):
    calls = []

    def fake_json_request(url, payload=None, **kwargs):
      calls.append((url, payload, kwargs))
      if "signInWithPassword" in url:
        return {"idToken": "id-token", "localId": "user-id", "expiresIn": "3600"}
      return {"car_status": {"fLvl": 63}, "time": 1786960934000}

    monkeypatch.setattr("openpilot.tools.gmone_collector.gmone_collector._json_request", fake_json_request)
    client = OfficialFirebaseClient("api-key")
    result = client.read_cached_status("user@example.com", "password", "vin-value", "user-id")
    assert result["car_status"]["fLvl"] == 63
    status_url = calls[-1][0]
    assert "/users/user-id/car_status/status/vin-value.json" in status_url
    assert "auth=id-token" in status_url


class TestAsyncResultFetch:
  def test_resolves_request_success_from_fetched_data(self):
    class Client:
      calls = 0

      def fetch_result(self, ticket_uuid):
        assert ticket_uuid == "ticket-value"
        self.calls += 1
        if self.calls == 1:
          return {"body": {"success": 2}, "timestamp": 20}
        return {
          "body": {
            "success": 0,
            "fetched_data": {
              "header": {"id": 21},
              "body": {"success": 0, "car_status": {"fLvl": 63}},
              "timestamp": 30,
            },
          },
          "timestamp": 31,
        }

    response, timing = resolve_async_response(
      Client(),
      {
        "body": {
          "success": 13,
          "ticket_uuid": "ticket-value",
          "wait_response": True,
        },
        "timestamp": 10,
      },
      timeout_seconds=1,
      poll_seconds=0,
      sleep=lambda _seconds: None,
    )
    assert response["body"]["car_status"]["fLvl"] == 63
    assert timing["request_result_code"] == 13
    assert timing["result_poll_count"] == 2
    assert timing["result_timed_out"] is False

  def test_does_not_repeat_or_fetch_immediate_response(self):
    class Client:
      def fetch_result(self, _ticket_uuid):
        raise AssertionError("fetch_result must not be called")

    immediate = {"body": {"success": 3}, "timestamp": 10}
    response, timing = resolve_async_response(Client(), immediate)
    assert response is immediate
    assert timing["result_poll_count"] == 0


class TestCollectorState:
  def test_persists_only_running_cycle_cursor(self, tmp_path):
    path = tmp_path / "state.json"
    state = CollectorState(path)
    state.update_cycles({"body": {"running_cycles_data": [{"time": 20}, {"time": 10}]}})
    state.save()
    assert json.loads(path.read_text()) == {"last_running_cycle_time": 20}
    assert path.stat().st_mode & 0o777 == 0o600

  def test_offline_diagnostic_does_not_contain_vehicle_nulls(self):
    diagnostic = collector_diagnostic(3, 1786960934000)
    assert diagnostic["collector_status"] == "inside_not_connected"
    assert diagnostic["collector_source"] == "gmone-direct"
    assert "source" not in diagnostic
    assert "fuel" not in diagnostic
    assert "refresh_status" not in diagnostic


def test_auxiliary_reads_store_only_successful_data(tmp_path):
  class Client:
    def read_multipack_option(self):
      return {"body": {"success": 0, "multipack_option": {"feature": True}}, "timestamp": 10}

    def read_multipack_info(self):
      return {"body": {"success": 3}, "timestamp": 10}

    def read_ev_battery_charge_data(self, last_received_time):
      assert last_received_time == 20
      return {"body": {"success": 0, "ev_charge_data": []}, "timestamp": 10}

  store = GmoneStore(tmp_path / "gmone.sqlite3")
  state = CollectorState(tmp_path / "state.json")
  state.last_running_cycle_time = 20
  collect_auxiliary_data(Client(), state, store)
  assert store.latest_snapshot("multipack_option") == {
    "success": 0,
    "multipack_option": {"feature": True},
  }
  assert store.latest_snapshot("multipack_info") is None
  assert store.latest_snapshot("ev_charge_data") == {"success": 0, "ev_charge_data": []}


def test_running_cycles_are_read_and_deduplicated_separately(tmp_path):
  class Client:
    def read_running_cycles(self, last_received_time):
      assert last_received_time == 0
      return {
        "body": {
          "success": 0,
          "running_cycles_data": [
            {"time": 10, "dis": 1.2},
            {"time": 20, "dis": 3.4},
          ],
        },
      }

  state = CollectorState(tmp_path / "state.json")
  store = GmoneStore(tmp_path / "gmone.sqlite3")
  assert collect_running_cycles(Client(), state, store) == 2
  assert state.last_running_cycle_time == 20
  assert store.running_cycle_count() == 2


class TestGmoneStore:
  def test_persists_latest_snapshot_without_identity_data(self, tmp_path):
    path = tmp_path / "gmone.sqlite3"
    store = GmoneStore(path)
    store.save_snapshot("car_status", "gmone-direct", {"fLvl": 63}, 200)
    store.save_snapshot("car_status", "gmone-direct", {"fLvl": 61}, 100)
    assert store.latest_snapshot("car_status") == {"fLvl": 63}
    assert path.stat().st_mode & 0o777 == 0o600

  def test_removes_nested_identity_and_secret_fields(self, tmp_path):
    store = GmoneStore(tmp_path / "gmone.sqlite3")
    store.save_snapshot(
      "multipack_info",
      "gmone-direct",
      {
        "firmware": "1.2.3",
        "VIN": "sensitive",
        "nested": {"token_key": "sensitive", "feature": True},
      },
      100,
    )
    assert store.latest_snapshot("multipack_info") == {
      "firmware": "1.2.3",
      "nested": {"feature": True},
    }

  def test_removes_sensitive_key_variants(self, tmp_path):
    store = GmoneStore(tmp_path / "gmone.sqlite3")
    store.save_snapshot(
      "multipack_option",
      "gmone-direct",
      {
        "door_password": "0000",
        "last_ticket_uuid": "ticket-secret",
        "nested": {
          "firebase_auth_token_value": "token-secret",
          "feature": True,
          "1GNEV9KW2PJ000000": {"firmware": "1.2.3"},
          "identifier": "123e4567-e89b-12d3-a456-426614174000",
        },
      },
      100,
    )
    assert store.latest_snapshot("multipack_option") == {
      "nested": {
        "feature": True,
        "<redacted>": {"firmware": "1.2.3"},
        "identifier": "<redacted>",
      },
    }

  def test_deduplicates_running_cycles_by_server_time(self, tmp_path):
    store = GmoneStore(tmp_path / "gmone.sqlite3")
    cycles = [{"time": 10, "dis": 1.2}, {"time": 20, "dis": 3.4}]
    assert store.save_running_cycles(cycles) == 2
    assert store.save_running_cycles(cycles) == 0
    assert store.running_cycle_count() == 2
