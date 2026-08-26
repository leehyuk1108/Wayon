# Wayon Cloud

Wayon Cloud is a lightweight Cloudflare Worker dashboard for a Wayon/openpilot
device. The comma device pushes low-rate vehicle telemetry, GPS location for
current position and route history, and occasional offroad snapshots. The Worker
stores live state in D1 and JPEG snapshots in KV.

The responsive dashboard combines Wayon telemetry and Firebase vehicle status
in three views:

- Overview: live position, driving state, range, fuel, odometer, vehicle health,
  and comma power/thermal status.
- Trips: 31-day statistics, recent routes, and a speed-colored route map.
- Cameras: filterable wide and driver snapshot history.

Each comma registers its Dongle ID with one randomly generated Wayon Cloud Key.
Only the SHA-256 key hash is stored in D1. The same key authorizes telemetry,
app reads, push registration, 360 Live, and remote SSH for that device.

## Cloudflare Resources

- Worker: `wayon-cloud`
- D1 database: `wayon_cloud`
- KV namespace: `WAYON_SNAPSHOTS`

The dashboard and API are served from the same Worker. API reads and writes are
protected with bearer tokens.

## Offroad Remote SSH and Live

`system.wayon_remote_relay` runs only while the comma is offroad. It opens
device-authenticated outbound WebSockets to one Durable Object per Dongle ID.
`POST /api/remote/session` exchanges the Wayon Cloud Key for a 60-second signed
protocol token containing that Dongle ID. The relay opens local port 22 or 8765
only while an SSH or 360 Live client is connected.

When the session request includes the client's public key, the Worker forwards
it only to the relay for the Wayon-key-matched Dongle ID. The comma appends that
key to its existing authorized keys for 90 seconds and then removes the exact
session entry. Existing user SSH keys are preserved, raw Wayon keys never reach
the SSH daemon, and client text frames cannot forge relay control messages.
Hylink performs this exchange automatically, so the Wayon Cloud Key is the only
credential the user enters.

The Mac can also create an ephemeral SSH identity automatically and connect with
only the stored Wayon Cloud Key:

```sh
node /path/to/remote/wayon_ssh.mjs
```

For an existing SSH identity, the lower-level `ProxyCommand` remains available:

```sshconfig
Host wayon-comma
  HostName wayon-comma
  User comma
  ProxyCommand /opt/homebrew/bin/node /path/to/remote/wayon_ssh_proxy.mjs
```

Store the same Wayon Cloud Key at `~/.config/wayon/ssh.credentials.json` with mode
`0600`:

```json
{"key":"wayon_..."}
```

The key can also be viewed and copied on the same LAN at
`http://COMMA_IP:1108` while the device is offroad. That local page and both
relay channels stop as soon as `IsOnroad` changes.

## JSON API

Read requests use the device's Wayon Cloud Key:

```sh
curl -H "Authorization: Bearer $WAYON_CLOUD_KEY" \
  https://wayon-cloud.hyuklee.workers.dev/api/json
```

Available read endpoints:

- `GET /api/json`: combined JSON feed for external visualizers
- `GET /api/export`: alias of `/api/json`
- `GET /api/state`: latest state plus recent snapshots
- `GET /api/trips`: recent trip summaries
- `GET /api/trips/:id`: one trip with route points
- `GET /api/snapshot?key=...`: JPEG snapshot object

Trip reads use the private HYUKLEE Server PostgreSQL mirror first. The Worker
reaches it through a Cloudflare Tunnel VPC service and authenticates with the
dedicated server-sync token. If the server, tunnel, response schema, or request
fails within 5 seconds, the same endpoint automatically reads from D1 instead.
Trip lists use a route-free server summary; a full route is fetched only when a
specific trip is opened.
The comma upload path never depends on the server, so collection continues
during a server outage. Trip responses include `x-wayon-history-source:
server|d1` for operational verification.

GPS is used for current position and route history. Live speed is stored as
`state.speed_mps` from the vehicle `carState` dashboard/cluster speed path, not
from GPS speed.

The JSON endpoints include CORS headers, so another browser-based visualizer can
fetch them with an `Authorization: Bearer ...` header.

## Long-term trip sync

The HYUKLEE Server mirror uses a dedicated read-only token and an ascending,
opaque cursor. It never shares the dashboard view token and does not affect
device uploads.

```sh
curl -H "Authorization: Bearer $WAYON_SERVER_SYNC_TOKEN" \
  "https://wayon-cloud.hyuklee.workers.dev/api/server-sync/trips?limit=100"
```

The response uses schema `wayon-trip-sync-v1` and contains full trip records,
including route points, `nextCursor`, and `hasMore`. A consumer must commit the
whole page before persisting `nextCursor`. On any HTTP or database failure it
must retry from the previous cursor. Trip IDs remain the idempotency key.
When no newer rows exist, the endpoint returns the supplied cursor unchanged
instead of resetting it to `null`.

The server mirror exposes its read API only through the private VPC service.
PostgreSQL has no host or public port. Existing D1 data remains as the ingestion
buffer and automatic read fallback.

## AI access

Wayon also provides a separate read-only AI gateway. It exposes normalized live
telemetry with freshness, numeric comma temperatures and power, trip history,
vehicle events, impact measurements, and authorized impact JPEGs. The AI token
cannot upload data, open remote SSH, update software, or control the vehicle.

- Setup and MCP: [`ai/README.md`](ai/README.md)
- OpenAPI: [`public/wayon-ai-openapi.json`](public/wayon-ai-openapi.json)
- System prompt: [`public/wayon-ai-prompt.md`](public/wayon-ai-prompt.md)

## Deploy

1. Create Cloudflare resources:

   ```sh
   npx wrangler d1 create wayon_cloud
   npx wrangler kv namespace create WAYON_SNAPSHOTS
   ```

2. Copy the generated IDs into `wrangler.toml`.

3. Apply the schema:

   ```sh
   npx wrangler d1 execute wayon_cloud --remote --file=./schema.sql
   ```

4. Set secrets:

   ```sh
   npx wrangler secret put WAYON_UPLOAD_TOKEN
   npx wrangler secret put WAYON_VIEW_TOKEN
   npx wrangler secret put WAYON_SERVER_SYNC_TOKEN
   ```

5. Deploy:

   ```sh
   npx wrangler deploy
   ```

## Device Config

Copy `device_config.example.json`, fill in the deployed Worker URL and upload
token, then place it on the device at:

```text
/data/wayon_cloud/config.json
```

The uploader is intentionally quiet when the config file is missing.
