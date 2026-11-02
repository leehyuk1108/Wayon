# My Traverse Web Account and Controls, 2026-11-02

## Scope

Enable the independently authenticated PWA's original Android remote-control
commands. Preserve Android source/assets, the existing Cloud collector, Comma,
Navdy, driving logic and the original visual design. Private credentials,
cookies, account identifiers and vehicle telemetry remain outside Git.

## Verified Ownership

The existing Windows collector's interactive owner session can read its existing
Credential Manager entry; SSH alone cannot. A bounded, separate scheduled task
used that credential in memory for official read-only login. The original
collector task was not changed. Temporary probe tasks and session-cookie inputs
were removed afterward; passwords were neither exported nor stored in the PWA.

Official login returned a unique account UUID and one vehicle VIN. Their hashes
were pinned independently of the account-email fingerprint. Existing Android's
`gmone-acct-v1` HMAC scope was recomputed with the current Comma Cloud key and
matched the Windows collector and current Cloud vehicle scope. The collector,
Comma configuration, existing Cloud feed and PWA also matched the same device.

Comma's CarVin file was absent and its four retained CarParams variants held a
zero-filled VIN. **No actual Comma VIN match is claimed.** Ownership binding is
based on the official account's single vehicle plus the already-installed
Android account/key scope and registered Comma device. No VIN was synthesized.

The production Worker received the two identity pins and command-enable flag.
All three are server-side settings, not browser storage.

## Corrections

- Native workerd `fetch` rejected a Protocol-instance receiver before sending
  the account request. A detached function call passes actual-runtime tests.
  The first production login failed; after correction, the same owner account
  logged in successfully and advertised all 15 supported controls.
- Match Android's bounded pending-ticket envelopes and empty result polls,
  while requiring an explicit successful final result. Canonical integer
  strings are accepted; null, booleans and malformed values remain rejected.
- Pending controls, account expiry and PWA expiry are separate states. GMOne
  credential rejection does not log out an otherwise-valid PWA session.
- A valid observed remote-engine state selects the STOP button without turning
  a cached snapshot into a live one or bypassing the backend status guard.
- Never interpret an accepted protocol result as physical vehicle completion.
  No optimistic engine/window/lock state is written into the displayed cache.
- Re-read the actual Wayon state after asynchronous engine preflight and before
  dispatch. A new moving, active, stale, missing or mismatched state blocks the
  command. Recheck the account again after the final network operation.
- Known upstream session expiry clears only the exact old encrypted account,
  not a replacement login. Ambiguous dispatched results retain a three-minute
  global cooldown and do not permit immediate reissue with a different UUID.
- Accepted engine commands request one bounded collector refresh. A newly
  observed remote-engine state, not protocol success alone, changes the button.
- The installed Comma publishes `wayon-telemetry-v3`, whereas the first web
  guard accepted only v2. Actual uploader source and Cloud payloads confirmed
  that the security-relevant fields retain their meaning. Accept exactly v2
  and v3, with identical independent freshness, device, motion and engagement
  checks. Unknown and near-match schema versions still fail closed.
- A read-only Cloudflare op21/66 probe measured the GMOne response clock 554 ms
  ahead at receipt. Engine preflight can now wait once, at most 2000 ms, before
  rerunning every guard. It never rewrites timestamps, accepts future timestamps,
  renews the 30-second status lifetime or bypasses a clock rollback.
- The compact trip list preserves null maximum speeds. Android's existing list
  renderer converted the resulting unknown text to zero; a web-only post-render
  adapter restores `--` for unknown list/aggregate maxima, retaining real zero
  and numeric measurements. Full route details are still loaded on demand, not
  819 routes at startup. Android source and styling are unchanged.

## Production Read Failure

Browser `/api/wayon/json` requests failed while separate state, trip-list and
vehicle-status reads worked. Encoding variants initially correlated with the
failure, but pinning internal `Accept-Encoding: identity` did not fix it and was
removed. Actual Wayon tail logs recorded five `exceededCpu` exceptions:
`Worker exceeded CPU time limit.` Do not describe this as a proven gzip defect.

The old export loaded 25 complete trip rows/routes into a roughly 3.35 MB
response. The PWA now composes its initial feed from the existing state API,
25 trip summaries and 24 snapshot records. Original observation timestamps and
`state.raw_json` are preserved; no receipt time becomes vehicle freshness.
Command preflight uses only the state endpoint. The separate full trip list and
on-demand detail APIs remain available, including routes and analysis.

The existing trip-list implementation also parses full route JSON and reproduced
the CPU failure. A hash-pinned Wayon patch adds an owner-authenticated read-only
`/api/mobile/web-trips` endpoint selecting small summary columns directly. The
PWA list uses it; Android's existing endpoints and the detailed trip route remain
unchanged. No database schema, rows, credentials or subscriptions are changed.

The production feed shrank to approximately 82 KB. Three measured authenticated
reads took 782-1013 ms; the full 819-item summary list returned 339 KB in 655 ms,
and one lazy detail returned 14 actual route points. An actual 45-second Wayon
tail observed 11 events and no exceptions after deployment. These are bounded
measurements, not a long-duration service guarantee.

## Verification Status

- Final fresh build: **331/331 PWA tests passed, zero skipped**, including real
  Chromium and workerd/D1. The pinned read-only Wayon patch passed **30/30**.
  Coverage includes all 15 protocol mappings, exact owner/device binding, v2/v3,
  moving/active/stale/unknown denial, CSRF, logout races, final state revalidation,
  pending replies, uncertain-outcome cooldown, no command replay and expiry.
- Production owner login returned HTTP 200, and the authenticated browser
  advertised all 15 commands. Unauthenticated requests, wrong CSRF, unsupported
  commands, missing confirmation and a different account were rejected before
  vehicle dispatch. The wrong-account probe used a non-real test password.
- Production Chromium displayed actual vehicle state, map and controls with no
  horizontal overflow at 390 px. The original Android asset SHA256 remains
  `d26971b235a51fa52aaeda6e1c7e92e7dbb61c0758c8189ab4c49aafebf7e6c5`.
  The deployed history showed 819 records, with all 819 unavailable maxima
  correctly shown as `--`, not zero. The first adapter test used a wrong mock
  container ID; the final fixture derives the real ID from Android HTML, and
  the corrected selector was reverified against the actual deployed DOM.
- A temporary Cloudflare probe ran the real engine preflight with a transport
  allowlist of **only op21/op66**. Its `beforeSend` deliberately returned false.
  Fresh v3/offroad telemetry and direct GMOne engine-off/hood-closed/two-starts
  state reached that hook. An observed 1397 ms server-clock lead was actually
  waited out; no engine op19 was sent. A later read repeated with an 866 ms lead.
- One actual **DOOR_LOCK** request was sent after a fresh direct read confirmed
  engine off, doors already locked and no remote engine, plus current matching
  offroad/inactive/zero-speed Cloud state. It returned HTTP 200,
  `server_responded`, `command_accepted`, result code 0 in about six seconds.
  Exactly one matching persisted command claim contains the same result. No
  duplicate request or automatic retry was issued.
- A subsequent direct read still reported engine off, door locked, hood/trunk
  closed and no remote engine. **Already-locked confirmation and a successful
  protocol reply are not proof of observed mechanical movement.** Start/stop,
  unlocking, windows, trunk, lights, horn and sunroof were not physically tested.
- Temporary read-only Workers were removed in `finally`; the final Cloud
  inventory contains zero probe Workers. One-time Windows tasks and temporary
  cookie inputs were removed. Existing collector tasks, Android app, Comma,
  Navdy, vehicle control software and user data were not modified.

## Deployed Versions and Limits

- PWA: `f94f3b7f-9b78-4413-8abb-6b4ec51dcaa8` at
  `https://my-traverse-web.hyuklee.workers.dev`.
- Wayon: `c144778d-55af-4036-ad00-a0c74563be2e`, main SHA256
  `e37c4b20f633f9a307b97738571e71931fca22b9f45900a26d6f944dfa793ab7`.
  Original companion modules and all 24 bindings were preserved. The dirty
  working-tree main Worker was not deployed; the exact compiled baseline was
  patched. Existing database rows/schema and subscriptions were preserved.
- The single lock and post-lock status checks used the same final server command
  implementation on version `42110f91-acf1-426f-b757-692922e510f1`. Later
  publications changed only the history-display adapter, not command behavior.
- The test browser's GMOne login is separate from the user's iPhone session.
  The iPhone owner must sign into the existing multipack account in Settings.
  Command login lasts at most 15 minutes; server-side expiry can be earlier.
  A Windows status login was followed by one expired old web token during
  testing; a fresh web login restored access. No password is retained for silent
  renewal, and an expired command is not automatically resent.
- The real iPhone previously verified installation and push receipt, not this
  turn's physical vehicle controls. Safari-specific control interaction and
  long-duration/poor-network operation remain unverified.
- Private receipts, read-only probes and screenshots are under
  `Documents/my-traverse-web-20261102` and the ignored PWA Playwright output.
  They are not distributed with source.

The earlier PWA report documents the initial commands-disabled deployment. It
must not be mistaken for this follow-up's current production state.
