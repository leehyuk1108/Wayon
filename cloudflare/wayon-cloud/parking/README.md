# Parking sign transcription

Private Windows service for transcribing visible parking floor, zone, pillar and
bay signs from multiple exterior camera frames. This is a visual clue service,
not a GPS replacement or proof of the exact parking space. No app layout or
vehicle control code is changed.

## Flow

1. Comma's existing offroad camera guard and lease permit a snapshot. With
   `parking_multiframe_enabled` in its private cloud config, the first successful
   snapshot after uploader startup or an onroad-to-offroad transition has three
   wide frames, at least one second apart. Later hourly snapshots stay single.
2. Wide images retain their native width up to 1928 pixels, without upscaling,
   and use JPEG quality 92 with 4:4:4 chroma. Existing brightness correction
   remains. Driver images stay at most 960 pixels and JPEG quality 72; only one
   is uploaded per burst, and none is supplied to the recognition model.
3. Existing Cloudflare snapshot storage and its owner-authorized read API carry
   the photos. No Worker replacement, new public endpoint, firewall rule or
   inbound connection to the server is needed.
4. The collector polls every 60 seconds, for the configured device only and only
   photos captured after activation. It waits two minutes for uploads to finish
   and accepts exactly three wide photos within five seconds. Interrupted
   one/two-photo uploads are not analyzed. Consumed snapshot IDs persist eight
   days, including after restart or list truncation. Failed groups do not block
   later groups, and transfer retries are bounded.
5. One Codex CLI job analyzes the group with the server owner's existing ChatGPT
   OAuth login. Shell, browser, apps, MCP, image-generation and other agent tools
   are disabled. The CLI is pinned by deployment, with a 150-second deadline,
   bounded queue and a maximum of 24 new jobs per rolling day.
6. Results and source frames are stored privately for seven days. Results keep
   capture times, dimensions, hashes and per-frame sign boxes. Ambiguous readings
   have null text. Bare numbers do not imply a floor, and every result has
   `exactParkingSpotKnown: false` and `machine_read_not_human_verified`.

## Server installation

Copy this directory into a dedicated `ParkingVision/code` folder. Install the
official Codex CLI and log in using its official `codex.cmd login --device-auth`
flow as the same Windows user. Never copy OAuth credential files to this repo.
Run `install_server.ps1`. It creates an isolated venv, owner/SYSTEM-only ACLs,
a random local API token and the limited-user S4U scheduled task
`Parking Vision Codex`. The service listens only on `127.0.0.1:18765`.

The private config can enable the read-only collector:

```json
{
  "cloud": {
    "enabled": true,
    "credentialsFile": "C:\\Users\\USER\\ParkingVision\\cloud.credentials.json",
    "deviceId": "YOUR_DEVICE_ID",
    "notBefore": "2026-10-31T00:00:00Z"
  }
}
```

The credentials file must be inside the private root, with `endpoint` (an HTTPS
origin) and the existing owner read-only `token`. It is never passed to Codex.
The current Cloudflare token can also read other owner data; the collector itself
only requests wide snapshots for the selected device. A narrower cloud token is
a future hardening improvement, not an implemented permission boundary.

Authenticated local API: `GET /health`, `POST /events`, `GET /jobs/<id>` and
`POST /jobs/<id>/retry`. A failed job allows at most two manual retries. Inspect
`data/service.log` and `bootstrap.log` for bounded, secret-free diagnostics.
`submit_bundle.py --help` describes manual validation from local image paths.
Stop only this task before upgrading its source, and start it after tests pass.

## Tests and limits

Run `python -m unittest discover -s code -p test_service.py -v` in the venv.
Comma tests are `openpilot/system/test_parking_snapshot.py` together with the
existing camera and uploader tests, under the target's Python environment.

- Recognition uses ChatGPT account quotas; it is not a free/unlimited API.
  Expired/revoked OAuth or usage limits produce a failed job, never a successful
  old result. Re-authenticate through the official CLI when necessary.
- The current uploader has no explicit cloud burst ID. Grouping is a strict
  time heuristic, not authenticated capture provenance. The API field
  `parkedAt` is the last photo's capture time, **not a measured gear-P time**.
- Three stationary frames help reject transient noise, but are not independent
  viewpoints. There is no moving/pre-parking frame buffer in this implementation.
- Better compression cannot recover letters that are out of view, blurred or
  too small. Results must not be used to infer an unobserved floor or bay.
- The model supplies boxes and transcription. Schema and repeated-frame checks
  do not prove visual correctness. Human review remains necessary.
- Burst photos appear as additional existing gallery entries, without changing
  app UI code. They use more cloud storage. The seven-day local retention does
  not delete existing Cloudflare originals or change provider retention.
- Turning off `parking_multiframe_enabled` restores one-shot cadence, not old
  lower image quality. Reverting the two scoped Comma source files restores that.
- Disabling `cloud.enabled` stops automatic recognition on the next service
  restart; original snapshots and other vehicle services continue normally.
