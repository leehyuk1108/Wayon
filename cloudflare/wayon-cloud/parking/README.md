# Parking sign transcription

Private Windows service for transcribing visible parking floor, zone, pillar and
bay signs from multiple exterior camera frames. This is a visual clue service,
not a GPS replacement or proof of the exact parking space. No app layout or
vehicle control code is changed.

## Flow

1. The explicit parking contract carries up to six approach captures and three
   parked wide captures from Comma, spanning at most 120 seconds of actual capture
   time. The collector also supports older three-shot parked bursts without
   explicit metadata. Comma capture/ring changes and Cloudflare metadata transport
   are separate components; this directory implements the server consumer only.
2. Wide images retain their native width up to 1928 pixels, without upscaling,
   and use JPEG quality 92 with 4:4:4 chroma. Existing brightness correction
   remains. Driver images stay at most 960 pixels and JPEG quality 72; only one
   is uploaded per burst, and none is supplied to the recognition model.
3. Existing Cloudflare snapshot storage and its owner-authorized read API carry
   the photos. No Worker replacement, new public endpoint, firewall rule or
   inbound connection to the server is needed.
4. The collector polls every 60 seconds, for the configured device only. Every
   member must be captured at/after activation and within the last two hours.
   It waits two minutes after the final parked capture before accepting a complete
   explicit group. Legacy bursts still require exactly three wide photos within
   five seconds. Partial or inconsistent groups are not analyzed. Consumed
   snapshot IDs persist eight days, including after restart or list truncation.
   Failed groups do not block later groups, and transfer retries are bounded.
5. One Codex CLI job analyzes the group with the server owner's existing ChatGPT
   OAuth login. Shell, browser, apps, MCP, image-generation and other agent tools
   are disabled. The CLI is pinned by deployment, with a 150-second deadline,
   bounded queue and a maximum of 24 new jobs per rolling day.
6. Results and source frames are stored privately for seven days. Results keep
   capture times, optional approach/parked phase, dimensions, hashes and per-frame sign boxes. Ambiguous readings
   have null text. Bare numbers do not imply a floor, and every result has
   `exactParkingSpotKnown: false` and `machine_read_not_human_verified`.

## Zone letters

The transcription reviews small alphabetic zone badges around each numbered
sign, not just the larger digits. Separately printed zone letters and pillar
numbers remain separate readings with their own evidence boxes. A continuous
alphanumeric identifier stays as printed; neither a blue badge nor a generic
parking P pictogram alone proves a zone.

Readable zone letters use the same two-distinct-images/0.5-second requirement as
numbers. A visible but unclear letter is recorded as ambiguous with null text;
an independently readable number can still be notified. Existing notifications
already support both zone and pillar labels, so this change needs no phone or
Cloudflare deployment. Old jobs are not replayed or notified automatically.

The model receives original image dimensions and is instructed to locate each
sign in those full-image coordinates. Box validation checks structure, source
identity and timing, not whether pixels actually contain the claimed text.
Prompt instructions are not an independent visual verification mechanism.

## Explicit group contract

Each wide entry from `GET /api/ai/snapshots` may have this optional metadata:

```json
{
  "id": "snapshot-id",
  "deviceId": "device-id",
  "camera": "wide",
  "capturedAt": "2026-10-30T12:00:00Z",
  "parking": {
    "version": 1,
    "eventId": "parking-event-id",
    "parkedAt": "2026-10-30T12:01:00Z",
    "index": 0,
    "count": 3,
    "phase": "approach"
  }
}
```

- IDs use the existing ASCII identifier syntax `[A-Za-z0-9][A-Za-z0-9_.-]{0,95}`.
  Version, index and count must be integers, not booleans or floats. The wire
  bound is 2-12 frames, with exactly one of every index `0..count-1` and unique
  snapshot IDs. Comma's sender budget remains six approach plus three parked.
- All members must agree on device, event ID, count and the `parkedAt` instant.
  ISO timestamps require timezones; equivalent offsets represent the same
  instant. Listing order is irrelevant, but index order must have strictly
  increasing, distinct actual `capturedAt` times within a 120-second span.
- Zero or more approach frames must precede all parked frames. At least one
  parked frame is required. `parkedAt` equals the **last parked snapshot capture
  time, not measured gear-P time**. It is neither upload time nor a substitute
  timestamp for earlier approach images.
- A corrupt, stale, future or out-of-window member claiming the same device and
  event invalidates that listed group. Partial sessions are never combined across
  events/devices or filled from legacy snapshots. Reused event IDs with conflicting
  parked references are rejected, not split into apparently complete sessions.
- A present but malformed `parking` value (including null) never falls back to
  the legacy heuristic. Repeated snapshot IDs, even repeated identical listing
  rows, fail closed. Only entries with no `parking` key are eligible for legacy
  grouping (three frames, 0.5-second minimum gaps, at most 2.5 seconds per gap,
  total span 2-5 seconds, and the same wait/window limits).
  Cloud ingestion must reject invalid supplied metadata, never silently strip
  it into a legacy entry. The server cannot reconstruct omitted provenance.
  A nine-frame group's three-photo parked tail is still incomplete, not legacy.
- Explicit jobs preserve the supplied event ID. Legacy jobs retain
  `snapshot-<first snapshot ID>`. The existing persistent consumed-ID table,
  retention and retry limits are unchanged. The collector does not cache partial
  groups between polls; all members must be visible together in the listing.

The local `POST /events` frame object still requires `capturedAt`, `camera` and
`imageBase64`, and now optionally accepts `phase: "approach" | "parked"`.
Existing manual road/wide requests without phase keep their sorting and image
deduplication behavior. Missing phase stays unspecified, never assumed parked.
For requests containing phase, all capture records survive image normalization,
even when identical pixels recur across phases. Their phase and real capture time
are included in the manifest, signature, result and model attachment provenance.
Every request still needs two distinct decoded images. A readable claim requires
evidence from two distinct image hashes at least 0.5 seconds apart; duplicates
cannot corroborate one another. One-frame or uncertain clues may be ambiguous
with null text. Approach signs are nearby route clues, never proof of the exact
parked location; parked-phase images also do not establish an exact bay.

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

Run `python -B -m unittest discover -s code -p 'test_*.py' -v` in the venv.
`test_explicit_parking.py` uses synthetic images and mocked cloud/model calls;
it covers corrupt/partial/mismatched groups, ordering, timezone and clock
boundaries, provenance, consumed IDs, retry spacing and failure recovery.
The existing HTTP test uses an ephemeral loopback server only.
Comma tests are `openpilot/system/test_parking_snapshot.py` together with the
existing camera and uploader tests, under the target's Python environment.

- Recognition uses ChatGPT account quotas; it is not a free/unlimited API.
  Expired/revoked OAuth or usage limits produce a failed job, never a successful
  old result. Re-authenticate through the official CLI when necessary.
- Explicit metadata describes claimed capture provenance, not cryptographic
  attestation. Legacy grouping remains a strict time heuristic. This server
  change alone neither enables Comma's approach buffer nor deploys the matching
  cloud metadata transport; those require separate verification.
- Stationary frames may not be independent viewpoints. A complete group can
  remain unavailable if the 100-entry listing truncates its members or they age
  past the two-hour window. Missing frames are never synthesized or borrowed.
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
