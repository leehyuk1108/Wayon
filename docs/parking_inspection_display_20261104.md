# Parking inspection display, 2026-11-04

## Scope

Keep the original parking analysis and notification outbox unchanged. Add a
read-only inspection view that preserves baseline readings, distinguishes
corroboration, additional readings, conflicts and uncertainty, and shows nearby
fixed environmental clues. These are photo clues, not an exact parking bay.

The capture code on Comma remains the diagnostics revision c6bff812. No model,
vehicle control, camera restart, thermal or memory gate is changed here.

## Processing

- The separate scene comparison examines the whole image even if its initial
  inventory finds no sign. Twelve overview views and up to twelve targeted
  views share a 16-megapixel budget. Native crops use integer nearest-neighbor
  enlargement, not generated detail.
- At most three model calls, 600 seconds total, 240 seconds per call. Existing
  daily eight-attempt, queue-yield and authentication/quota backoff rules remain.
- A crop is not an independent frame. Existing distinct-image, capture-time,
  evidence and matching-surface checks remain.
- `sceneDisplay` attaches a bounded comparison to GET results without rewriting
  stored baseline analysis. Extra silence does not erase a baseline number;
  contradictory readings are labelled uncertain. Source coordinates remain AI
  estimates, not independently calibrated physical sign locations.
- `multiStage` stays disabled. `sceneShadow` stays enabled. The baseline remains
  the notification source; old photos are not re-notified.

## Delivery

`ParkingExport` reads only the configured notification owner's latest non-snapshot
job. It sends changed content using the existing dedicated parking notification
credential, with bounded responses, one background writer and retry backoff.
Credentials and image bytes are not included in display data. Atomic private
generation and acknowledgement files preserve ordering across retries/restarts.
Daily refresh renews KV retention without changing the content generation time.

The hash-pinned Cloud patch adds `/api/parking/display` for this server-only
credential and `/api/parking/latest` for an authenticated owner's device key.
Device revocation remains enforced. Caller-supplied owner identifiers cannot
select another account. The payload is validated and stored under a separate
SNAPSHOTS KV key with seven-day TTL; no D1 writes, schema changes, push sends or
vehicle commands are added. Failed/newer jobs replace the whole observation,
not selected fields from an older success. Test/simulation/snapshot records are
rejected. KV is eventually consistent, not an atomic compare-and-swap store;
single-writer generation checks reduce regressions but cannot eliminate a brief
old read across regions.

The running Docker API differs from the old checkout on disk. It is explicitly
not rebuilt or restarted. Deploy only the pinned patch to the downloaded live
Cloud bundle, preserving its other modules and all existing bindings.

Android v42 and the PWA share the inspection module in the photo gallery. They
render with `textContent`, clear state on account/key changes, cancel stale
requests, use a bounded request timeout, and avoid polling. Uncertain readings
are collapsed, not discarded. Observation time and result update time are
separate. Existing vehicle controls, login, cached vehicle data and push
subscriptions are outside this change.

## Validation Before Deployment

- Mac Python suite: 173 tests passed, including immutable baseline, conflicts,
  owner scope, latest-failure handling, changed-only publication, retry backoff,
  persistent generation and no image-byte export.
- Candidate code also tested in the actual Windows Python environment without
  constructing a production Service or modifying its jobs/outbox.
- Eight saved-photo runs completed in 55.5-141.8 seconds. They reuse some places
  and are not eight independent parking locations. The original readable `203`
  remains in the fused result. No new letter was confirmed; specifically, the
  user's faint C remains unconfirmed.
- Eleven environmental proposals were produced. Direct crop review supports
  several pipes, doors, shutters and fencing, but one fencing/framework proposal
  is uncertain. Display them as AI candidates, not verified surroundings.
- These replays prove the bounded pipeline and preservation behavior, not a
  recognition-accuracy increase, zero omissions, or a new physical parking event.

Deployment receipts, actual photo evidence, device identifiers, credentials,
runtime backups and signed APK artifacts are private, not part of this repo.
Final deployment and installed-device checks are recorded separately below.

## Deployment And Actual Checks

Source commits `cc119dbd2`, `3382f7b829` and `f99f4ab41` are published to
`wayon/codex/my-traverse-source`. Only task files were committed; the unrelated
dirty app, uploader, Navdy and Cloud source files remain untouched.

- Cloud: active version `3c8dd130-8a4e-4ee3-8522-0e64a486e5b7`, exact candidate
  SHA256 from the patch README. The other two modules and all 24 bindings match
  the previous deployment. The rollback version and exact-byte checks are
  retained privately.
- Windows: idle-only installation, configuration/ACL, source and SQLite backup,
  then restart of only the Parking Vision task. Installed hashes match the
  reviewed code. The installed suite ran 173 cases: 172 passed, one POSIX file
  permission case skipped on Windows. Existing notification rows and credential
  files were unchanged.
  The display publisher acknowledged the first real payload after startup.
  The pre-existing Docker API was not rebuilt or restarted.
- PWA: final version `35dac14c-e71e-4b0e-8022-2393ffa08a88`, replacing the initial
  inspection deployment `644c40ed-74cb-42b2-a453-e8bbe4467c3b`; all 15 bindings preserved,
  no schema change. The deployed 46-file input manifest and source commit were
  checked before deployment. The PWA suite passed 338 tests with three browser
  skips; separate Cloud/native-workerd tests passed all 25 and UI tests all 28.
- Android: v42 (`2.0-preview.33-parking-inspection`) installed with `install -r`
  and the original signing certificate, without clearing app data. The APK read
  back from the Fold7 matches SHA256
  `10facbbf8f8895ade89bcc9216f63cb76c6e3e9b6bc41b09d2480261b106b034`.
  Existing login and actual vehicle information remained available. The real
  app rendered the latest observation, its update time, one environmental
  candidate and the collapsed/expanded eleven uncertain readings. Existing
  photo viewing also worked. Screenshots and the UI hierarchy remain private.
  The first v41 physical test exposed click propagation from inspection refresh
  and disclosure controls into the parent photo card. The actual-handler
  regression failed before the fix and passed after it. v42 excludes inspection
  targets from that parent listener; physical disclosure, refresh and normal
  photo opening were each checked again. No app data or login reset was needed.
- Comma: installed `c6bff812` capture code still matches the pushed WIP-FR
  revision. This display change required no additional Comma restart or patch.

Bounded live reads verified unauthenticated rejection, owner scope, `no-store`,
fresh PWA login/session and equal Cloud/PWA inspection payloads. The successful
final sample took 0.405 seconds directly and 0.309 seconds through PWA. An earlier
PWA request timed out during a network change; these two timings do not establish
continuous latency or network reliability. The default Python user agent was
blocked while browser-agent requests and the actual Windows publisher succeeded.

The first final-PWA deployment preflight stopped on an expired OAuth token
before any upload. Wrangler refreshed the existing login; the retry revalidated
the unchanged active version, input hashes and bindings before publishing.
This was a deployment credential issue, not an app login failure.

WebKit and Chrome at 390x844 rendered the real inspection without overflow or
JavaScript exceptions, with two inspection reads and zero mutation requests each.
Both checked that disclosure and refresh leave the photo overlay closed.
Other gallery APIs were stubbed in that browser test to limit database load;
it is not a full-gallery or physical-iPhone verification. The Android screen
verification used the actual authenticated app and existing gallery.

Read-only database inspection found two new non-snapshot parking jobs after
deployment. Both completed baseline and scene comparison with three parked
frames, without changing the notification source. The latest observation at
12:53 KST reached the Cloud and app after its comparison completed at 12:57 KST.
Neither new job established a readable sign; the latest inspection retains
eleven uncertain items and one environmental candidate. This is real pipeline
completion, not evidence of an accuracy increase or a confirmed zone letter.

Claude's static review identified the nested-badge fusion issue, PWA source
pinning, owner-scope verification and rollback prerequisites; these were
addressed and checked before/after deployment. A final review found no defect in
the click-isolation patch and its actual-handler regression. Its review did not independently
execute tests or access the devices. Late KV writes and eventual consistency
remain limitations despite serialized publication and retry generations.

The faint C from the earlier parking remains unconfirmed. Exact parking-bay
identification, zero omissions and recognition of every visible letter are not
guaranteed. Thermal/memory capture guards, vehicle controls and original push
notification behavior were not weakened to improve recognition counts.
