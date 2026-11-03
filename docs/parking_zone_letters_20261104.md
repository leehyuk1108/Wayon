# Parking zone letters, 2026-11-04

## Scope

The Windows ParkingVision transcription now explicitly reviews small alphabetic
zone marks around numbered signs. The existing `zone` schema and notification
contract already supported letters; the previous general prompt omitted the
small adjacent mark in a reviewed real parking burst. This is a prompt/input-
metadata change, not a new OCR model or an accuracy guarantee.

- Read separately printed zone letters and pillar numbers independently, with
  separate evidence. Preserve continuous alphanumeric identifiers as printed.
- Unclear letters remain `ambiguous`, `text: null`; readable numbers survive.
- Do not interpret a generic parking P symbol, logo or badge color as a zone.
- Provide original image width/height and explicitly require full-image boxes.
- Preserve two distinct images at least 0.5 seconds apart for every readable
  claim, all freshness/notification safeguards, and exact-location disclaimer.
- No image enhancement, extra production model call, changed capture budget,
  Cloudflare deployment, app update, vehicle action or old-result resend.

## Verification

- Local parking suite: 89 tests pass.
- Windows candidate: 89 tests run, 88 pass and one existing POSIX-only test skips.
- Existing isolated workerd/D1/FCM contract suite: 28 tests pass, including new
  combined zone-letter/pillar notification text coverage. No live notification.
- Negative cases cover ambiguous letters, independent valid numbers, one-frame
  letters, source/time validation, unknown signs and unchanged deduplication.
- Two bounded real Codex CLI calls on the server, using the candidate source
  and existing official login, without constructing the production Service:
  - Clearly labeled synthetic two-frame signs: `zone D`, `pillar 417`, both
    readable; a separate generic parking P pictogram was not labeled a zone.
    Duration 12.062 seconds. This is a controlled capability test, not road data.
  - The reviewed three-frame real parked burst: `pillar 203` readable and an
    additional zone reading ambiguous with null text. Duration 12.687 seconds.
    The letter was not asserted as readable or included in any notification.
- The real replay's six evidence crops were visually inspected. They now cover
  the small blue letter panel and neighboring digits, instead of the previous
  erroneous rectangle on the adjacent vehicle. This single corrected example
  is not an independent production pixel-content validator.

## Deployment and Limits

Only `service.py`, `instructions.txt` and their two test files were installed on
the Windows service, after verifying the exact baseline and candidate hashes.
The task was stopped only after a SQLite-protected idle check. Its original
files, task definition and database were backed up privately. Configuration and
both credential files were unchanged. The service restarted healthy; the old
notification receipt and attempt count were unchanged.

Private photos, original event identifiers, CLI output and rollout evidence stay
outside Git under the owner's parking-recognition review directory and private
server candidate/backup directories. The old production result remains intact.

Next real parking events use the new transcription. A new real parking event,
physical phone display and sustained letter-recognition accuracy have not been
verified by this change. Faint characters can still be unreadable; neither
prompt wording nor schema validation can reconstruct missing image detail.
