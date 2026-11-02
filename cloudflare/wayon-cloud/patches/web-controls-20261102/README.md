# Pinned compact trip-list endpoint

This patch adds only the owner-authenticated, read-only
`GET /api/mobile/web-trips` route. No deployment, migration, binding change,
command dispatch, or modification of the working-tree Worker is included.

## Pins

- Input main: `247511da7b190bbae926b82f9d442293b352ad6b1526b064ad8375b815d0d689`
- Output main: `e37c4b20f633f9a307b97738571e71931fca22b9f45900a26d6f944dfa793ab7`
- `key_diagnostics.mjs`: `1432f3bf0df3e7b73b3fd87c27062db9116230e4526359a6ccfcb85b0e5fbed5`
- `device_reissue.mjs`: `e44ea8791f7b63bcff47cc576f9762a7b3910e670f3932f1e5ee0f0f86cf9f84`

The input is the private `fanout.worker.js`, not `src/worker.js`. Both companion
modules must be retained byte-for-byte. `patchModules()` checks all three inputs.
`patch()` and `unpatch()` pin both main-module versions. Removing the two additive
insertions restores every original byte, including FCM, fanout, and trip details.

## Contract

- Existing registered-device bearer authentication runs first and removes any
  caller-supplied `x-wayon-auth-device`. The handler also calls
  `authorize(request, env, false)` and `authenticatedDeviceId(request)`.
- `deviceId` query parameters and caller device headers never choose the owner.
  SQL binds the authenticated device ID and the bounded limit.
- `limit` reuses existing `boundedLimit`: default 25, maximum 1000. Invalid,
  missing, zero, or negative values use 25; existing integer-prefix parsing is
  preserved. Positive fractional values are truncated. Rows sort by
  `ended_at DESC`, using the existing `(device_id, ended_at DESC)` index.
- Response: `{ "trips": [...] }`, with exactly these original scalar fields:
  `id`, `device_id`, `started_at`, `ended_at`, `duration_s`, `distance_m`,
  `start_lat`, `start_lon`, `end_lat`, `end_lon`, `route_point_count`, `source`,
  `route_name`, `segment_count`, `avg_speed_mps`, `max_speed_mps`.
- SQL values, including null and numeric zero, pass through without coercion.
  Optional history metadata stays nullable. No route/report/analysis/health
  blobs are selected, parsed, recomputed, or fetched. No timestamp or freshness
  evidence is fabricated. Existing JSON headers include `Cache-Control: no-store`.
- Invalid authentication: 401. Authenticated non-GET: 405. Existing global
  OPTIONS behavior: 204. Trip-query failure: generic 503
  `{ "error": "web_trips_unavailable" }`, with no raw error logging or response.
- PWA list calls map here; old `/api/trips/:id` detail calls remain unchanged.
  This endpoint provides history only, not command authorization or current
  vehicle-state evidence.

## Reproduce Locally

From `/Users/hyuklee/Documents/sunnypilot`:

```sh
node --test cloudflare/wayon-cloud/patches/web-controls-20261102/patch.test.mjs cloudflare/wayon-cloud/patches/web-controls-20261102/runtime.test.mjs
```

The tests use the private input and retained modules in
`/Users/hyuklee/Documents/my-traverse-web-20261102/`. Override them with
`WAYON_WEB_CONTROLS_BASELINE` and `WAYON_WEB_CONTROLS_MODULE_DIR` if needed.
`MINIFLARE_MODULE` can select an installed Miniflare package. The default is the
same existing local Miniflare installation as the preceding fanout tests.
There are no dependency installs or remote calls. Native workerd executes the
complete patched main module and both original companions, with local D1/KV and
an outbound blocker. Tests do not execute production commands.

Native checks include owner isolation, spoofed-header rejection, revoked keys,
non-owner service credentials, no persisted mutation, the compact PWA shape,
nullable/zero fields, default/max limits, and existing-index query planning.
A lazy SQLite view makes every legacy JSON column throw if selected; the new
route still succeeds. A separate malformed 1 MiB blob also has no effect.

To generate a new candidate file privately (never overwriting an existing file):

```sh
node cloudflare/wayon-cloud/patches/web-controls-20261102/patch.mjs /Users/hyuklee/Documents/my-traverse-web-20261102/fanout.worker.js /private/new-candidate.worker.js /Users/hyuklee/Documents/my-traverse-web-20261102/baseline
```

The output directory must already exist. The CLI validates the retained modules,
writes only the new main file with mode 0600 and exclusive creation, and prints
only hashes. Package the two unchanged companion modules separately; the CLI
does not copy them or deploy anything. Local tests prove the code path and SQL
projection, not production CPU headroom or physical vehicle behavior.
