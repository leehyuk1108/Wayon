# Shutdown notification addition

Apply only to the production bundle identified by `BASELINE_SHA256` in `patch.mjs`.
Output is pinned by `OUTPUT_SHA256`. Existing authentication, settings, secrets,
other modules, door events and vehicle controls are preserved. No migration is
required: the existing vehicle_events table holds the accepted notification.

The enrolled device POSTs `eventType: automatic_shutdown`, a unique
`shutdown-<32 lowercase hex>` ID, `reason` (`low_voltage` or `offroad_timeout`),
UTC `occurredAt`, `offroadLimitMinutes` and optional fresh `voltageV`.
Authenticated device scope wins over caller-supplied device IDs. Requests older
than 60 seconds or more than 5 seconds in the future are rejected. `test: true`
labels the notification explicitly as a test that does not power off the device.

Persist one atomic claim before 202, then finish FCM in `ctx.waitUntil`.
notified_count is -1 pending, -2 failed, 0 no registered recipient, or a positive
FCM acceptance count. None is proof of phone receipt. Duplicate IDs do not resend
an uncertain delivery. A cancelled Comma shutdown may still have a pending notice;
the visible message explicitly says recovery/ignition can cancel shutdown.

My Traverse Next v37 creates `wayon_power_alerts`, handles foreground data, and
uses the same title/body as Android background notifications. No home-screen
design changes are included. Phone permissions/network availability still apply.

```sh
WAYON_POWER_BASELINE=/private/background-worker-v2.js node --test notice.test.mjs
WAYON_POWER_BASELINE=/private/background-worker-v2.js \
MINIFLARE_MODULE=/existing/node_modules/miniflare node runtime.mjs
```

20 Node tests pass; real local workerd/D1 checks pass 11 assertions, including
concurrent claims. Production version `0e75c093-0d1d-47e1-bfc1-2295ee789a33`
matches the pinned output and retains all 22 existing bindings/three modules.
Two clearly labelled tests sent by the real Comma were accepted within its
one-second budget and appeared in the target phone's notification records.
Device shutdown itself was not induced.
