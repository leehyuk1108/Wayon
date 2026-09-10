# Hylink Cloud overview — design study 02

Status: interactive design preview, **not a production app replacement**. The first dark/orange refinement was rejected by the user. This proposal starts the layout and visual system again. Do not reinstall on the phone until the user approves the new preview.

Run from repository root:

```sh
python3 -m http.server 4198 --bind 127.0.0.1 --directory .
```

Open `http://127.0.0.1:4198/design/cloud-overview/index.html`. Top controls select parked, driving, warning, impact, stale, and first-connection fixtures. Per user feedback, the Hylink wordmark header and settings button, including its theme/text-size menu, have been removed. Responsive text/theme styles remain available for development checks, not as settings UI. No Wayon credentials, cloud polling, real media, or vehicle commands are used. Public Seoul City Hall coordinates are synthetic demonstration data, not the user's location.

## Information hierarchy

| Priority | Surface | Existing source |
| --- | --- | --- |
| 1 | Conditional attention notice above map | Feed freshness/error; `vehicle.can`, `vehicle.steeringFault`, `openpilot.alert`, `panda.faults/heartbeatLost`, reported critical thermal status; recent impacts |
| 2 | State, speed when available, received time, map | `/api/state`: `onroad`, `ignition`, `updated_at`, latitude/longitude; `raw_json.vehicle.speedKph`, GPS freshness/accuracy |
| 3 | Latest drive, camera shortcuts, records | `/api/trips`, `/api/snapshots`, `/api/impacts`; existing authenticated live session flow to be retained during integration |
| 4 | Vehicle/device details | Voltage, power, device temperatures/usage/network, Panda and vehicle diagnostics |
| 5 | Advanced tools behind a secondary entry | Existing authenticated remote/SSH functionality, not implemented in this preview |

An old error must not look like a current vehicle fault. When data is stale, stale status is first and vehicle-specific fault interpretation is suppressed. Offroad unavailable vehicle values are not displayed as five large empty rows; available device metrics take their place. Missing numbers are not zero, missing flags are not normal, door-open is not door-lock status, and fuel/TPMS support is not assumed.

This is a design model, not an exhaustive safety fault classifier. Exact critical alert taxonomy, connection service timestamps, refresh/cached-history errors and independent GPS timestamps must be carried over from the production adapter before release.

## Apple-design review and choices

- **Layout > Hierarchy:** essential status/attention is above the map; records and diagnosis are progressive detail. Replaced equally prominent diagnostic tiles with a task-based hierarchy.
- **Maps > Best practices:** actual vector map, one clear vehicle marker, reduced city/duplicate bilingual labels, visible attribution and recenter. GPS remains explicitly the last received location.
- **Typography / Color:** restrained type scale and semantic blue action color, neutral surfaces, warning icon plus text (not color alone); explicit light and dark previews.
- **Accessibility:** scalable rem text, 200% layout mode, keyboard-visible focus, native dialog focus containment/Escape, meaningful icon button names, app controls at least 48px tall. Provider attribution control still needs accessibility review before app integration.
- **Feedback:** unreceived/stale/failure are distinct from parked or normal. Live and media actions explicitly say they are inactive in this design preview.

Guidelines consulted through the installed `apple-design` skill: `accessibility.md`, `color.md`, `layout.md`, `typography.md`, `maps.md`, `feedback.md`, `dark-mode.md`, `materials.md`, `branding.md`.

## Map dependency and production gate

Pinned [MapLibre GL JS 5.12.0](https://maplibre.org/maplibre-gl-js/docs/) UMD is loaded from unpkg in this preview. Map style/tiles are [OpenFreeMap Positron](https://openfreemap.org/quick_start/), with label adjustments after style load. OpenFreeMap/OpenMapTiles/OpenStreetMap attribution is retained.

This changes the map provider **only for the synthetic preview**. Before production: bundle and license-audit pinned assets, verify Android WebView/WebGL on the physical phone, review provider capacity/privacy/availability (public instance has no SLA), decide failure fallback, and preserve production API caching/backoff. No extra reverse-geocoding or real location transmission is introduced here.

## Verification

`node scripts/check-cloud-design.mjs`: presentation/priority tests.

`node scripts/capture-cloud-design.mjs`: dedicated local Chrome CDP on port 9338; checks vector features, captures screenshots and tests 320/390/768 CSS px × default/200% text × three tabs. Output is ignored at `output/cloud-design/`. Do not attach to the user's normal Chrome profile.

Real interaction checks use the visible local preview: scenario dialog, warning detail, tab/record navigation, modal close, settings, and keyboard focus. These are not device/vehicle validation.

## Next integration work after design approval

1. Replace fixture adapter with existing native callbacks; preserve secrets, account lifecycle, history pagination/cache/error status, polling and backoff.
2. Wire actual trip route and optional trip reports, authenticated images/video archive, impact media association, live/SSH state machines. Never fill absent reports with sample statistics.
3. Handle loading, refresh failures, stale GPS independent of feed timestamp, unavailable car signals and log-out cleanup.
4. Port semantic theme/font scaling and native status/navigation bars; do a fresh accessibility review and physical Fold cover/unfolded screen checks.
5. Build/sign with the existing key, preserve login on install, and physically validate. My Traverse New, Wayon backend, comma control and carrotpilot/wip remain outside this design change.
