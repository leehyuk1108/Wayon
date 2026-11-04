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

Android v41 and the PWA share the inspection module in the photo gallery. They
render with `textContent`, clear state on account/key changes, cancel stale
requests, use a bounded request timeout, and avoid polling. Uncertain readings
are collapsed, not discarded. Observation time and result update time are
separate. Existing vehicle controls, login, cached vehicle data and push
subscriptions are outside this change.

## Validation Before Deployment

- Mac Python suite: 170 tests passed, including immutable baseline, conflicts,
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
