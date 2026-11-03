# Multi-stage parking inspection, 2026-11-04

## Release policy

The new scene pipeline is installed as **comparison-only**, not as the source
of phone notifications. Real saved-photo trials withheld previously readable
pillar text, including 203. This is a regression in useful output, not evidence
that the old result is necessarily wrong. The requested C zone is not proven.

The existing single-pass result, notification payload, freshness conditions,
authentication and push subscriptions remain the production contract.
`multiStage` is not enabled. `sceneShadow=true` starts additional analysis only
after a new baseline job has committed and enqueued its existing notification.
Old jobs are not replayed automatically and no historical alert is resent.
Periodic `snapshot-` jobs do not start comparisons. The original legacy prompt
is preserved; the strict CLI completion/parser change is independently audited.

## Pipeline

1. Inventory sign-bearing surfaces across all original photos, including other
   pillars. Separate floor, zone, pillar and bay readings from fixed structures.
2. Inspect lossless, padded crops without supplying previous character guesses.
   Map crop-relative evidence back into the original photo coordinates.
3. Verify proposed readings and fixed structures against the original photos.
   Conflicts and unreadable marks remain ambiguous, never guessed or joined
   into a made-up location code.

Every confirmed reading requires distinct source hashes at least 0.5 seconds
apart and local evidence. Repeated crops of one photo do not count as independent
photos. Different photos are still not proof of independent viewpoints.
Surface association is model-provided, not geometric tracking. Structural labels
use a restricted vocabulary and photo-left/center/right, not inferred addresses,
vehicle identity, people or exact parking spaces.

## Bounds and isolation

- At most 24 crops, 16 million crop pixels, 240 seconds per pass and 600 seconds
  per comparison. At most three inference calls; no automatic comparison retry.
- Persistent daily comparison-attempt budget: default 8, hard maximum 24.
  Failed attempts consume budget. Corrupt budget state fails closed; a backward
  clock cannot reset it. This is an attempt limit, not a token-cost guarantee.
- Skip a comparison if another job is already queued or the parking observation
  is too old to finish inside the existing 30-minute freshness envelope.
- Check the queue again before every pass. A recent baseline authentication,
  quota or runtime failure suppresses comparison work for 24 hours.
- One worker is retained. A job arriving during an active comparison pass can
  still wait up to that pass's remaining 240 seconds plus shutdown/I/O time.
  No subsequent pass is started while the new job waits. Completed-job delivery
  is handled independently, but zero effect on future-job latency is not claimed.
- Comparison result is a private `scene-comparison.json`, not the DB baseline
  result or notification outbox. `scene-budget.json` contains only day/count.
- Inference has no shell, browser, file tools or MCP. Existing OAuth storage is
  reused without copying credentials. Exact CLI transport fallback notice is
  accepted only with a completed turn; errors and actual tool use are rejected.

## Verification

- Mac: 133 server unit tests pass, including corrupt budgets, failed comparison,
  preserved baseline/outbox, expired jobs, missing assets, per-target grouping,
  crop coordinate mapping, separate-sign concatenation and partial failures.
- Windows final candidate: 132 pass, 1 platform-specific skip. The restored
  legacy prompt is AST-identical to the baseline. Its real isolated OAuth call
  through the refactored runner completes in 20.750 seconds and keeps readable
  203. It touches no production DB and sends no notification.
- All 27 retained successful jobs from the previous seven days pass the new
  completion-event parser; none are missing logs and none are newly rejected.
  This replay uses saved CLI events and makes zero new model calls.
- The pre-final r3 scene trial completes 7 of 8 saved-photo jobs; one malformed
  crop text fails the job. The final candidate rejects such a reading locally.
  All seven completed r3 jobs still have zero confirmed readings, with 0-2
  environmental descriptions. This is why active promotion is explicitly blocked.
- Final scene-parser r4 inference: two actual saved cases complete in 127.844
  and 95.594 seconds, including the previously failing case. They still confirm
  zero readings, with 0 and 2 environmental clues. Later queue-only safeguards
  are tested separately; these timings are not a latency or accuracy guarantee.
- Comma diagnostics are a separate WIP-FR change; its actual isolated runtime
  passes 113 tests. Replay of 18 recorded qlogs / 5 drives / 9,114 input samples
  gives zero differences in the existing capture-eligibility predicate.
- Private photo experiments and actual server inference are deliberately kept
  out of Git. Schema success is not visual ground truth or accuracy.

## Remaining limits

Small, blurred letters remain unresolved. The new stricter pipeline can reject
readings the baseline kept. Crop ordering/budgets can omit later targets; whole
scene coverage is an inspection objective, not a guarantee. Environmental
results are private comparison data and are not yet displayed by the phone app.
No new physical parking event, long-duration capture load or improved recognition
rate is established by unit tests or saved-image replay.

## Deployment contract

Back up the Windows files, configuration, SQLite DB and scheduled-task definition.
Require idle queue/outbox and exact baseline/candidate hashes. Restart only the Parking
Vision task; retain configuration except the two explicit comparison settings,
and verify credentials, config ACL and existing notification states unchanged. Roll back the
scoped files/configuration if startup fails. No Cloudflare redeploy, schema
migration, phone update, vehicle command or Comma system reboot is required.
