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

The view token is stored only in the browser's local storage. Existing users
keep the same `wayonViewToken` key when the dashboard UI is updated.

## Cloudflare Resources

- Worker: `wayon-cloud`
- D1 database: `wayon_cloud`
- KV namespace: `WAYON_SNAPSHOTS`

The dashboard and API are served from the same Worker. API reads and writes are
protected with bearer tokens.

## Offroad Remote SSH

`remote/wayon_remote_supervisor.sh` runs the Cloudflare Tunnel only while the
comma is offroad. The tunnel is stored outside `/data/openpilot`, so it remains
available when a Sunnypilot update fails. The Worker uses a tunnel-scoped
Workers VPC binding and exposes a credential-authenticated WebSocket bridge.
`POST /api/remote/session` exchanges the Wayon username and password for a
60-second signed protocol token; `/api/remote/ssh` uses that token and connects
only to `127.0.0.1:22`.

The Mac connects through the included SSH `ProxyCommand` client:

```sshconfig
Host wayon-comma
  HostName wayon-comma
  User comma
  ProxyCommand /opt/homebrew/bin/node /path/to/remote/wayon_ssh_proxy.mjs
```

Store the gateway login at `~/.config/wayon/ssh.credentials.json` with mode
`0600`:

```json
{"username":"comma","password":"strong-password"}
```

Any client with those credentials and the proxy script can connect from the
internet. The offroad-only `wayon_remote_installer` fetches the tunnel token
with the device's existing upload credential, verifies the pinned cloudflared
binary, and installs everything under `/data/wayon-remote`. The token remains
mode `0600` and is never stored in Git. The tunnel starts only after six seconds
of confirmed offroad state and stops as soon as `IsOnroad` changes.

## JSON API

Read requests use the view token:

```sh
curl -H "Authorization: Bearer $WAYON_VIEW_TOKEN" \
  https://wayon-cloud.leehyuk1108-comma.workers.dev/api/json
```

Available read endpoints:

- `GET /api/json`: combined JSON feed for external visualizers
- `GET /api/export`: alias of `/api/json`
- `GET /api/state`: latest state plus recent snapshots
- `GET /api/trips`: recent trip summaries
- `GET /api/trips/:id`: one trip with route points
- `GET /api/snapshot?key=...`: JPEG snapshot object

GPS is used for current position and route history. Live speed is stored as
`state.speed_mps` from the vehicle `carState` dashboard/cluster speed path, not
from GPS speed.

The JSON endpoints include CORS headers, so another browser-based visualizer can
fetch them with an `Authorization: Bearer ...` header.

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
