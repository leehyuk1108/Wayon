# Wayon AI access

This gateway gives an owner-authorized AI read-only access to Wayon data. It
does not expose vehicle control, SSH, software updates, uploads, locks, steering,
acceleration, or braking.

## Available data

- Current onroad/offroad and ignition state
- Vehicle speed, gear, standstill, steering, cruise, blinkers, BSM, door and CAN health
- OpenPilot enabled/active/engageable state and current alert
- Vehicle bus voltage, measured current, and estimated input power
- comma device and SoM power draw, offroad energy usage, estimated battery capacity
- Numeric CPU, GPU, DSP, memory, modem, PMIC, intake, exhaust, GNSS, and SoC temperatures
- CPU/GPU/memory/storage use, network type/strength, thermal state and fan
- Current/last-known GPS, trips and route points
- Door lock, unlock, and parked-unlocked events
- Offroad impact measurements, capture status, and wide/driver JPEG images
- Firebase vehicle status used by My Traverse

Telemetry upload cadence remains unchanged: normally 15 seconds onroad and 300
seconds offroad. The API reports age and staleness so an AI cannot safely mistake
an old value for live state.

## Authentication

Create a separate random token and set it only as `WAYON_AI_READ_TOKEN`:

```sh
openssl rand -hex 32 | npx wrangler secret put WAYON_AI_READ_TOKEN
```

Do not reuse `WAYON_UPLOAD_TOKEN`, remote SSH credentials, or the mobile push
registration token. Store the client copy outside Git at mode `0600`:

```text
~/.config/wayon/ai.credentials.json
```

```json
{
  "endpoint": "https://wayon-cloud.leehyuk1108-comma.workers.dev",
  "token": "64-character-secret"
}
```

## HTTP and OpenAPI

- OpenAPI: `https://wayon-cloud.leehyuk1108-comma.workers.dev/wayon-ai-openapi.json`
- System prompt: `https://wayon-cloud.leehyuk1108-comma.workers.dev/wayon-ai-prompt.md`
- AI discovery: `https://wayon-cloud.leehyuk1108-comma.workers.dev/llms.txt`

All API requests need `Authorization: Bearer ...`:

```sh
curl -H "Authorization: Bearer $WAYON_AI_READ_TOKEN" \
  'https://wayon-cloud.leehyuk1108-comma.workers.dev/api/ai/context'
```

HTTP endpoints:

- `GET /api/ai/context`
- `GET /api/ai/trips`
- `GET /api/ai/trips/:tripId`
- `GET /api/ai/impacts`
- `GET /api/ai/events`
- `GET /api/ai/snapshots`
- `GET /api/ai/images/:snapshotId`

For a custom GPT/ChatGPT Action, import `wayon-ai-openapi.json`, configure HTTP
Bearer authentication, then use the text from `wayon-ai-prompt.md` in its
instructions.

## MCP

`wayon_mcp_server.mjs` is a dependency-free Node.js stdio MCP server. It reads
the credential file above or `WAYON_AI_ENDPOINT` and `WAYON_AI_READ_TOKEN`.

Codex config (`~/.codex/config.toml`):

```toml
[mcp_servers.wayon]
command = "/opt/homebrew/bin/node"
args = ["/absolute/path/to/cloudflare/wayon-cloud/ai/wayon_mcp_server.mjs"]
startup_timeout_sec = 30
```

Claude Desktop config:

```json
{
  "mcpServers": {
    "wayon": {
      "command": "/opt/homebrew/bin/node",
      "args": [
        "/absolute/path/to/cloudflare/wayon-cloud/ai/wayon_mcp_server.mjs"
      ]
    }
  }
}
```

MCP tools:

- `wayon_get_context`
- `wayon_list_trips`
- `wayon_get_trip`
- `wayon_list_impacts`
- `wayon_list_vehicle_events`
- `wayon_list_snapshots`
- `wayon_get_snapshot_image`

## Security boundary

The AI token is accepted only under `/api/ai/*`, all routes are `GET`, and image
lookups use database snapshot IDs instead of raw KV keys. Revoking one AI does
not change device uploads or remote SSH: replace `WAYON_AI_READ_TOKEN` and update
only that AI's local credential file.
