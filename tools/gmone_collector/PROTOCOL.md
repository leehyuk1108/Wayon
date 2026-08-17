# GMOne / MultiPack Connected protocol inventory

This document records the behavior recovered from the official Android app
`kr.co.gmone.multipack_connected_v2`. It is intended for the Wayon headless
collector and is not a claim of a public GMOne API.

No account password, session token, REST access key, Firebase token, VIN, IMEI,
ICCID, or modem number belongs in this repository.

## Transport and session

- Server: `https://mp.gmone.co.kr:28354`
- Login: `POST /b1_init`, operation `8`
- Authenticated operations: `POST /b1_connect_m`
- Envelope:

```json
{
  "header": {"id": 21, "ticket_id": 0, "revision": 0},
  "login": {"uuid": "<runtime>", "token_key": "<runtime>"},
  "body": {}
}
```

The login request uses `email` and `password` instead of `uuid` and
`token_key`. `ticket_id` is an 8-bit rolling request identifier in the app.

## Where the latest status really comes from

The app merges three sources instead of treating Realtime Database as the only
source of truth:

1. Manual refresh calls operation `21` with `refresh_dtc` and
   `last_received_time`.
2. A successful response updates the in-memory account state and local
   SharedPreferences.
3. Foreground and background FCM `CarStatusData` pushes also update the same
   local status.
4. The app may subscribe to Firebase RTDB and accepts that value only when its
   timestamp is newer than the value already held by the app.

The local key is composed as
`mc_car_status_data;<user_uuid>;<vin>`. Consequently, a current value visible in
the phone app can be newer than the authenticated RTDB node. A headless service
must persist the last successful direct result and must never overwrite it with
an older RTDB value.

The official RTDB status path is
`users/{firebase_uid}/car_status/status/{vin}`. The account currently inspected
had an old value at that path, so it is only a guarded fallback.

## Read-only operations implemented by the collector

| ID | Name | Request body | Main response data |
|---:|---|---|---|
| 8 | `REQ_LOGIN` | Login credentials | Session, account and vehicle registration |
| 21 | `REQ_CAR_CONTROL_STATUS` | `refresh_dtc`, `last_received_time` | `car_status`, new running cycles |
| 45 | `REQ_RUNNING_CYCLE_DATA` | `last_received_time` | `running_cycles_data` |
| 59 | `REQ_READ_MULTIPACK_SETTING_V2` | empty | `multipack_option` |
| 63 | `REQ_MULTIPACK_INFO` | empty | `multipack_info` |
| 70 | `REQ_EV_BATTERY_CHARGE_DATA` | `last_received_time` | `ev_charge_data` when supported |

Operation `21` is the official app's vehicle refresh command. It does not
guarantee a result while the in-vehicle module is asleep. Result `3` means
`INSIDE_NOT_CONNECTED`; it does not mean that the account or vehicle is
unregistered.

## Vehicle status fields

The `car_status` object can contain the following raw fields. Availability
depends on the vehicle, installed module options, and current connection state.

| Area | Fields |
|---|---|
| 12 V battery | `volt`, `btChrg`, `btHlth`, `btTmp` |
| Fuel and range | `fCap`, `fLvl`, `fRng` |
| Odometer and oil | `odo`, `olLfe` |
| Tire pressure | `trPrsLf`, `trPrsRf`, `trPrsLr`, `trPrsRr` |
| Closures | `door`, `hood`, `trunk`, `srf`, `winLf`, `winRf`, `winLr`, `winRr` |
| Vehicle state | `eng`, `light`, `hrnStats` |
| Diagnostics | `dtc`, `dtcCnt` |
| DEF | `defLvl`, `defRmngDis` |
| EV charging | `evChgrCplrStats`, `evChgrPwrLvl`, `evChgrSysStats`, `evChrgCpltTm`, `evChrgCpltTmSet`, `evChrgStTm`, `evChrgStTmSet`, `evChrgStat` |
| EV range | `evRngAvg`, `evRngMax`, `evRngMin` |
| Remote start | `rsiLvl`, `rvsRmng`, `rvsRmngTm`, `rvsRmngTmVld` |

Running-cycle entries observed from the server contain `time`, `dis`, `drvTm`,
and `fuse`. They must be deduplicated by their server timestamp instead of
replacing the entire history with only the most recent page.

## Vehicle controls

Vehicle controls use operation `19`, with body fields `control_type` and
`request_option`. They are intentionally not allowed by the background
collector. A separate command service must require explicit enablement,
authentication, idempotency protection, rate limiting, and an audit record.

The mapping below is present in both the recovered Android application and the
official iOS application version 1.13.1. The iOS Siri intent definition exposes
the same controls, with trunk open/close handled by a separate intent. This is
the complete user-facing actuator list found in those builds; enum names that
are not wired to an app action are not treated as usable commands.

| App command | Control type | Request option |
|---|---:|---:|
| `REMOTESTART_ON` | 0 | 2 |
| `REMOTESTART_OFF` | 0 | 0 |
| `DOOR_LOCK` | 1 | 0 |
| `DOOR_UNLOCK` | 1 | 1 |
| `TRUNK_CLOSE` | 2 | 0 |
| `TRUNK_OPEN` | 2 | 1 |
| `PANIC_ON` | 3 | 1 |
| `WINDOWS_CLOSE` | 5 | 0 |
| `WINDOWS_OPEN` | 5 | 1 |
| `SUNROOF_CLOSE` | 6 | 0 |
| `SUNROOF_OPEN` | 6 | 1 |
| `SUNROOF_TILT` | 6 | 3 |

The app also defines control type `4` for lights, but no corresponding command
was present in the recovered command list. It must not be guessed or exposed.
There is likewise no verified panic-off command. `PANIC_ON` is the only panic
action exposed by the app. Trunk close is documented by the official intent as
being available only on vehicles with an automatic liftgate.

Control responses can complete immediately or return `ticket_uuid` and
`wait_response`. The app then obtains completion through FCM or polls operation
`66` (`REQ_RESULT_FETCH`) with `ticket_uuid`.

### MultiPack configuration commands

These settings are read with operation `59` and written with operation `61`.
They are module configuration, not vehicle actuator commands, and their raw
option values must be read before constructing a write request. The current
official app contains settings for:

- automatic door locking and the door-lock speed
- automatic door unlock behavior by gear state
- engine cooldown duration
- mirror folding and unfolding behavior
- shock sensor enable/disable, delay enable, and delay duration
- automatic window close behavior
- blind-threat alert speed, chime enable, chime count, and chime sound

The app also supports firmware update, DTC read/clear, modem registration, and
REST API credential management. Those operations have separate safety and
credential implications and must not share the vehicle-control allowlist.

## Time and freshness fields

The app has several independent timestamps. They are not interchangeable and a
headless client must retain their meanings instead of presenting the newest
numeric value as the vehicle's last update.

| Time | Storage or payload field | Meaning |
|---|---|---|
| Server response time | top-level `timestamp` | Time GMOne created the HTTP response; it can be current even when no vehicle status was returned |
| Vehicle status time | official RTDB `car_status/status/{vin}/time` | Time associated with the cached vehicle status |
| UI refresh time | `SharedCarStatusData.refresh_time` | Time the app accepted and saved a status into its local shared preferences |
| Status request cursor | request `last_received_time` | Cursor sent with status/history requests; it is not a user-visible refresh time |
| Last running cycle | `mc_last_running_cycle_received_time` and `running_cycles.start_time` | Latest driving-cycle cursor and each trip's start time |
| Last EV charge record | `mc_last_ev_battery_charge_data_received_time` and charge-record start/completion fields | Latest EV history cursor and individual charging times |
| Command request time | `user_command_results.time` or `mc_widget_last_command_start_timestamp` | When an app or widget submitted a control command |
| Command completion time | asynchronous command response/FCM and stored command result | When the server or vehicle completed the command; may be later than request time |
| Remote-start inference time | `mc_engine_not_remote_start_time` | App bookkeeping used to distinguish a normally started engine from remote start |
| Shock time | official RTDB `users/{uid}/shock` record timestamp | Time recorded for a shock event |
| Notification time | FCM message/OS delivery metadata | Push receipt or display time; this is not persisted as the vehicle status time in every build |
| Remote-config fetch time | Firebase `lastSuccessfulFetchTime` | App configuration refresh only; unrelated to vehicle freshness |

A direct refresh that returns `INSIDE_NOT_CONNECTED` therefore updates only the
server-response/attempt time. It must not advance the vehicle-status or UI
refresh time.

## Other official app operations

These operations exist in the app but are not suitable for the read-only
collector. Some mutate the account or the installed module and some return
secrets.

| ID | Name | Category |
|---:|---|---|
| 1 | `REQ_REGISTER` | Account creation |
| 4 | `REQ_CHANGE_PW` | Password mutation |
| 6 | `REQ_FORGOT_PW` | Account recovery |
| 10 | `REQ_EMAIL_CHECK` | Registration validation |
| 12 | `REQ_PRIVATE_CODE_CHECK` | Verification |
| 14 | `REQ_NICK_CHECK` | Registration validation |
| 19 | `REQ_CAR_CONTROL` | Vehicle mutation |
| 23, 58 | `REG_PUSH_TOKEN`, `REG_PUSH_TOKEN_V2` | FCM registration |
| 30 | `REQ_MULTIPACK_FIRMWARE_UPDATE` | Module mutation |
| 34 | `REQ_READ_DTC` | Legacy diagnostic read |
| 37 | `REQ_UNREGISTER` | Account/module mutation |
| 43 | `REQ_ACCOUNT_LOCK` | Account mutation |
| 47 | `REQ_CLEAR_DTC` | Vehicle diagnostic mutation |
| 49 | `REQ_FIREBASE_AUTH_TOKEN` | Returns Firebase credential material |
| 51 | `REQ_CHANGE_USER_RECORD` | Account mutation |
| 53 | `REQ_PASSWORD_VERIFY` | Sensitive verification |
| 55 | `REQ_FORGOT_ID` | Account recovery |
| 57 | `REQ_REGISTER_MODEM_V2` | Module registration |
| 61 | `REQ_WRITE_MULTIPACK_SETTING_V2` | Module configuration mutation |
| 65 | `REQ_PRIVATE_CODE_REQUEST` | Sends verification code |
| 66 | `REQ_RESULT_FETCH` | Asynchronous command result read |
| 67 | `REQ_CHANGE_NICK` | Account mutation |
| 68 | `REQ_CHANGE_SUB_EMAIL` | Account mutation |
| 69 | `REQ_CHANGE_PHONE_NUMBER` | Account mutation |
| 71 | `REQ_SET_REST_API_ENABLE` | REST access mutation |
| 72 | `REQ_NEW_REST_API_KEY` | Rotates a secret |
| 73 | `REQ_GET_REST_API_DATA` | Returns REST access configuration/secret |

Legacy operations for reading VIN, module version, settings, and modem
registration are still present in the enum, but the current V2 app flow uses
the operations listed above.

## Result handling

Common vehicle-operation results recovered from the app are:

| Code | Meaning |
|---:|---|
| 0 | Success |
| 1 | Failed |
| 2 | MultiPack not connected |
| 3 | In-vehicle module not connected |
| 4 | In-vehicle module not found |
| 5 | Vehicle not in Park |
| 6 | Function disabled |
| 7 | Previous operation not finished |
| 8 | Vehicle communication failed |
| 9 | Vehicle power is not off |
| 10 | No remote-start time remaining |
| 11 | Remote start is not running |
| 12 | Vehicle busy |
| 13 | Request accepted |
| 14 | Not executed |

## Headless Wayon design

The server replacement should use the following boundaries:

- A read-only collector owns login, status refresh, cycle synchronization,
  local persistence, and compatibility publishing.
- The latest direct/FCM-equivalent status wins by source timestamp. An older
  RTDB value is never allowed to replace it.
- A command service is a separate process or module and is disabled unless an
  administrator explicitly enables it.
- Command endpoints accept named commands only, never raw operation numbers or
  arbitrary request bodies.
- Session tokens and REST keys stay in memory or an OS secret store. Logs show
  only command name, outcome, and a non-secret request ID.
- The Mac implementation is validated against the official app before the same
  package is installed on `HYUKLEE-SERVER`.

## Reverse-engineering confidence

The operation names and app-specific method names were confirmed in the current
2.5.3 binary string table. Request construction, local status persistence, FCM
handling, and command mappings were reconstructed from an ARM64 2.0.10 build
whose protocol structure matches the current names. Read operations `21`, `45`,
`59`, `63`, and `70` were also probed against the live service without issuing
vehicle controls. Any mutation must still be tested separately and deliberately
before production exposure.
