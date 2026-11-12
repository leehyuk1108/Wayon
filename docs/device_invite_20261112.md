# Registering another comma with a one-time invite (2026-11-12)

Owner request: let Carrot Web register another comma to the My Traverse cloud, instead of copying the
Traverse key (which would mix both commas into one device).

## Change

- Cloud `patches/device-invite-20261112` (`23c4a225…` → `25508494…`), migration adds
  `wayon_device_invites` (code hash, creator, times, use) and `wayon_device_origins` (invited devices).
  - `POST /api/devices/invites` (device key): 32-character base32 code (160 bits), 30 minutes, one use;
    only its SHA-256 is stored. At most three unused codes and ten in any 24 hours per creator, checked
    in the INSERT itself; refusals say `invite_limit`, `invite_daily_limit` or `invite_retry`. A device in
    `wayon_device_origins` (registered with an invite) may not create codes.
  - `POST /api/devices/register {deviceId, key, invite}` for a new device ID: one D1 batch spends the code
    (unused, unexpired, creator still active, ID free), creates the device and records its origin; the later
    statements depend on the spend, so a refused request writes nothing. A key already used elsewhere hits
    the production `key_hash UNIQUE` and rolls the batch back. Existing devices, the legacy upload token,
    same-key retries and reissue are unchanged.
- Carrot Web (carrotpilot branch `claude/wayon-invite-20261112`): the My Traverse key page makes a code
  (string `mtinv1.` + base64url JSON of cloud address and code) on a registered comma, and on a comma with
  no key file accepts it: the comma makes its own key, keeps it in `register.pending.json` (0600, made durable
  before the cloud is contacted), registers its DongleId and then publishes `config.json` with a hard link
  (never overwrites). The new config holds only endpoint, key, device ID and `vehicle_status_url: ""` (the
  uploader otherwise defaults to the owner car's external status feed).

## Limits (stated, not solved)

An invite authorizes a registration; it does not prove the comma owns its DongleId. The cloud address in an
invite is not signed; the confirmation shows the host. No page to cancel codes or remove devices.

## Verification

- Codex: failure scenarios and acceptance criteria before implementation (60 scenarios), then three review
  rounds (8 findings, then 2, then none), all fixed.
- Cloud Miniflare with the production DDL (read from `sqlite_master`, no data): 15/15, including races,
  revoked creators, the UNIQUE rollback, index use and owner responses byte-identical (asserted 200 first).
- Carrot server: 100 tests pass (2 existing frame tests fail on the Mac only: `opendbc` missing in the
  sparse checkout). Web: 27/27. New tests fail on the previous code.
- Production: migration applied (additive), wayon-cloud `28f55d41` (`25508494…`) active, 25 bindings equal,
  other modules unchanged. From the Traverse comma: state, trips and parking 200; the new module (temp copy)
  read the real DongleId, created a real invite (stored as a 64-hex hash, unused, expired 06:24Z), and the
  cloud refused a wrong code and no code without writing.
- Not verified: Carrot Web on a device (not pushed or installed), a real second comma registering, its
  uploads and phone app.
