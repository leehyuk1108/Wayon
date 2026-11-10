# Parking re-read, parking place and trip history (2026-11-10)

Owner requests on the same evening:

1. A shop sign (AMBER'S ENGLISH) clearly visible in all three parked photos ended as a
   one-photo candidate, while a slogan next to it became the photo title.
2. When no sign is read, show the parking environment instead of "주차 표지 확인 필요":
   indoor/outdoor, underground/ground, parking lot or street.
3. Long drives (2026-11-08, 200 km) drew only part of their route; the Android app missed
   some trips that the iPhone web app showed.

## 1. One-photo shop sign (server, `cloudflare/wayon-cloud/parking`)

Job `709c429a…` (15:31 KST): the first scene pass marked the sign wall in frame 0 only, so
its crop existed for one photo; the overview tile covering it in frames 0 and 2 filled the
former four reading slots with three unreadable marks and the slogan. The sign was read in
one crop and stayed ambiguous by the two-distinct-photo rule.

- A surface marked in one parked frame is cropped again at the same pixels from the parked
  frame of the same camera, size and distinct hash that is farthest in capture time. A read
  in that companion crop joins only when its box matches the other frame's (`same_box`).
- Six readings per crop, clear text first; same-place spelling conflicts demote a crop text
  before the 16-reading cap; corroborated text sorts ahead of unreadable marks.
- Display fusion (`parking_inspection.collapse_display_duplicates`), after the baseline
  comparison and for kind=unknown only: one row per confirmed text (parked evidence kept),
  candidates whose every text is confirmed dropped, conflict rows always kept.
- Apps: a digit-only reading of unknown purpose (a shop phone number) never titles the photo
  over a worded one.

## 2. Parking place

Both full-frame passes classify `{setting, level, area}` from parked-phase frames only; the
verification pass does it without seeing the first answer and only agreeing fields survive.
No parked frame → unknown. Underground needs an explicit cue (B-level sign, ramp down).
`inspection.place` goes to the display; the apps title the photo with it when no sign is read
(e.g. 지하 주차장, 야외 주차장, 지상 실내 주차장, 길가 주차) and add a "주차 환경" section.
Cloud: `patches/parking-place-20261110` allowlists the three enum fields.

## 3. Trip history (cloud, `patches/trip-history-20261110`)

- Detail: the Wayon server copy of the 200 km drive held 07:24–07:57 (629 points) and
  overwrote the D1 route 07:24–09:52 (720 points). The merge now keeps whichever route spans
  more time (ties keep the server copy).
- List: `limit=1000` failed with 1101 while 500 worked; summaries read all route_json values
  (866 trips, 38.7 MB) at once only for a maximum speed. The Android app retries
  1000 → 600 → 300, so it showed only part of the list. First fix: routes read 90 at a time
  (same `maxRouteSpeedMps`); it still took 25-27 s and repeated requests returned 503, so the
  Galaxy fell back to 600 trips (7,824 km). Second fix (`patches/trip-list-sql-max-20261110`):
  SQLite takes the maximum for plain routes (every object point has a numeric speedMps or no
  speed key; json_each type checked first, no abs()); only odd routes are parsed in the Worker.
  Production: 866 trips, 0 odd routes, ~1 s of SQL.
- Partial server summaries (`patches/trip-partial-server-20261110`): the server copies of the
  long drives ended after ~33 minutes and also overwrote the list/detail timing and distance
  (200.7 km / 2 h 28 min shown as 19.5 km / 33 min; Galaxy total 10,342 km vs D1 11,470 km).
  When a server copy spans more than a minute less than the D1 trip, D1 timing, distance,
  positions and speeds win (missing D1 speeds derived, not nulled; the maximum from the route
  actually shown); the route keeps its own longer-span rule.
- Remaining: list responses are large (100 trips 8.7 MB, 300+ about 15.5 MB, mostly drive
  reports), so a full list takes ~20-25 s to download; the iPhone web uses the light
  `/api/mobile/web-trips` list (350 KB, 1.3 s). Why the Wayon server keeps only ~33 minutes
  of long drives was not investigated.

## Verification

- Codex cross-review: parking 3 rounds (1: 4 findings, 2: 3 findings, all fixed), trip patch
  2 rounds (1: 3 findings on an SQL approach, replaced).
- Tests: server 188 (Mac) / 188 with 1 platform skip (Windows candidate), apps 121,
  cloud parking-place 3, trip-history 3 (output identical to the old bundle for list inputs).
- Real-photo replays on the Windows server in an isolated candidate folder (no production
  job, DB, notification or display change), final code:
  - `709c429a…` street, 15:31: AMBER'S ENGLISH and 010.7317.6725 confirmed in frames 0 and 2;
    the app titles AMBER'S ENGLISH. Place agreed only on outdoor/ground (야외 주차). The model
    misread the small slogan ("아이를 국어로 키우다.") and the verifier accepted it; earlier
    replays read it as "영어를 국어로 배우다(.)" — a model accuracy limit, not a fusion rule.
  - `340a64b6…` six approach + three parked frames: place outdoor/ground/street (길가 주차) from
    the parked frames.
  - Earlier candidate replays: `2eab619a…` (day street, no sign) 길가 주차; `8f50f50b…`
    (indoor garage) 실내·지하·주차 건물 under the previous underground cue.

## Deployment

- Windows ParkingVision: idle-only install of five files (`parking_scene.py`,
  `parking_inspection.py`, `instructions-scene.txt` and two tests), backup
  `backup-20261110-recheck` (files, SQLite copy, task XML), task restart. Health ok, workers
  alive, queue 0; config/credentials and existing notification rows unchanged; installed-path
  tests 188 with 1 platform skip. Applies from the next parking event; stored results are not
  re-analysed.
- wayon-cloud, each step staged then activated with 25 bindings equal field by field and the
  other modules byte-identical: `4fefd1dc` (parking-place + trip-history, `dff10502…`, previous
  `51eba5be`) → `44b04625` (trip-partial-server, `d522bc55…`) → `87dc9cf8` (trip-list-sql-max,
  `f7ca6716…`). Two superseded candidates (`95f795fd`, `6cd19e56`) were staged but never
  activated. From the comma (its key stays on the device): the 2026-11-08 drives return
  200.7 km / 8,884 s / 07:24–09:52, 218.5 km / 9,591 s and 48.5 km / 3,982 s with 720-point
  routes; `/api/trips?limit=1000` returned 200 five times in a row with 866 trips totalling
  11,470.4 km (= D1); `/api/parking/latest` still 200.
- Codex reviews of the trip patches: trip-history 2 rounds, trip-partial-server 3 rounds
  (2 + 2 findings fixed), trip-list-sql-max 2 rounds (1 finding fixed).
- Android My Traverse Next v67 (`2.0-preview.58-parking-place`, original signing certificate
  55a14240…) installed on the Fold7; web app `4a4cb47d` (11 secrets kept).
- Fold7 (unlocked by the owner at 18:05): the extras tab renders the stored result; the
  2026-11-08 16:24 detail drew all 720 points; after `44b04625` the 19:09 detail showed
  218.54 km, 2:39:51, 82/186 km/h and the full Gunsan–Incheon route. The list then held 600
  trips (7,824 km) because that refresh got a 503 before `87dc9cf8`.
- Not verified: the Galaxy list after `87dc9cf8` (the phone locked again), the iPhone screen, a
  new real parking event through the deployed server, and the place label on a real display.
