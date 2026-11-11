# Trip maximum and average speed from the vehicle (2026-11-11)

Owner request: show the maximum and average speed from vehicle values instead of GPS, for
trips saved from now on; existing records stay as they are.

## Why

The 2026-11-10 23:11 trip (5.11 km) showed a maximum of 112 km/h although the owner reached
about 150 km/h in a tunnel. GPS route points stop in tunnels: two gaps of 25 s and 27 s, each
followed by a GPS accuracy drop from ~2 m to 40–60 m. The drive report's carState timeline
(5 s samples) holds 145–146 km/h at 23:16 and 148.6 km/h at 23:20, inside those gaps. The list
and detail took the maximum from route points, and the average from GPS distance over time.

The comma already sends `maxSpeedMps` as the carState maximum over every sample (cluster speed,
what the speedometer shows) and the report's `fuel.odometerDistanceKm` (Traverse CAN odometer).
The cloud stored neither; `trips.avg_speed_mps` and `max_speed_mps` were NULL for all 899 rows.

## Change (cloud only; the comma is unchanged)

- `patches/trip-speed-compat-20261111` (`d522bc55…` → `850417f4…`): `parseTripRoute` drops the
  internal `speed_stats` column, so every `SELECT *` response stays the same with or without it.
  Deployed first; it is the rollback target.
- `patches/trip-vehicle-speed-20261111/migration.sql`: `ALTER TABLE trips ADD COLUMN speed_stats
  INTEGER` (existing rows NULL).
- `patches/trip-vehicle-speed-20261111` (`850417f4…` → `23c4a225…`), in `handleTrip`:
  - Maximum: when the report saw carState samples, the larger of `maxSpeedMps` and the timeline
    maximum (0–120 m/s). A later upload of the same trip can only raise it.
  - Average: odometer distance / trip time, only when the odometer covered the trip: within
    0.85–1.10× the carState timeline integral (cluster speed reads a few percent high) when the
    timeline spans the trip, else 0.9–1.3× the GPS distance (timeline truncated after 100 min);
    at least 60 s and 300 m, `fuel.partial === false`, and not above the maximum. Otherwise NULL,
    and the previous GPS average is shown.
  - `speed_stats` = seconds covered by the stored average (0 if none yet); only rows with it set
    take later values, and the average changes only for an upload covering at least as long.
    Rows from before the change keep NULL and never change.
  - Lists use the stored values first (routes are no longer read for trips with a stored
    maximum), details add `vehicle_max_speed_mps`/`vehicle_avg_speed_mps`, and the merge with a
    Wayon server copy keeps the stored values.
- Apps: the Android Kotlin list and the web bridge already prefer `avg/max_speed_mps`; the trip
  detail (`fetchWayonTripDetail`) now shows the vehicle values before route-point speeds.

## Verification

- Codex cross-review: 4 rounds (3 + 2 + 1 findings fixed, then none). Cloud tests: compat 1,
  vehicle-speed 7 (old trips identical before, during and after the migration; partial,
  window-mismatched, short and inconsistent evidence; retries that never lower the maximum or
  replace the average with a shorter one). App tests 125/125 including the detail display.
- Deployment: compat `663653d5` → migration (899 rows, none marked) → `8b3496d4` (`23c4a225…`),
  25 bindings equal, other modules byte-identical. From the comma: state, trips and parking
  return 200; the 2026-11-10 23:11 trip detail has no `speed_stats` or `vehicle_*` field.
  Android v69 (`2.0-preview.60-vehicle-speed`) installed on the Fold7; web app `457c5efd`.
- Not verified: a new real trip uploaded through the new code (applies from the next upload),
  the phone screens for such a trip, and the iPhone.
- Odometer distance resolution in the current comma code was not re-checked; very short trips
  fall back to the GPS average by the 60 s / 300 m rule.

## Related incident (2026-11-10/11)

`patches/trip-list-sql-max-20261110` (wayon-cloud `87dc9cf8`) computed list maxima with
`json_each` over every route and read ~412k D1 rows per list request; the account exceeded the
D1 free tier (5M rows/day) and every cloud API returned 1101 until 00:00 UTC. It was rolled back
to `44b04625` and stays inactive. This change adds no D1 reads.
