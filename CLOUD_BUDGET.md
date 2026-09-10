# Hylink Dev read budget

Hylink is the intended client for carrotpilot/wip; My Traverse New is the
separate Wayon/Sunnypilot client. Vehicle-side Hylink integration remains pending.

State reads remain at 30 s while the app is visible. Automatic trips, snapshots,
impacts and saved-live lists reuse a per-key in-memory cache for up to five
minutes. Explicit refresh, page initialization and the existing live-save event
force a full refresh. Failed endpoints are not marked fresh. Failure retries
back off up to five minutes, and explicit refresh bypasses that delay.

The full response shape is preserved for the UI, including cached list entries.
Changing the vehicle key invalidates the cache. A failed state request stops
the batch rather than sending four more requests to an unavailable service.
No changes are made to live/SSH authorization or vehicle-control APIs.

For an uninterrupted visible hour with no user actions, policy tests produce
168 calls instead of 600. This is a scheduling model, not measured account usage.

Standalone JDK test:

```sh
out=$(mktemp -d)
javac -d "$out" app/src/main/java/app/hylink/mobile/CloudRefreshPolicy.java scripts/CloudRefreshPolicyCheck.java
java -cp "$out" app.hylink.mobile.CloudRefreshPolicyCheck
```

This does not replace Android compilation, real UI tests, offline recovery tests
or verification of the installed APK's source/signature before an update.

## Device rollout, 2026-09-10

Android build and four unit tests passed. The existing signing certificate was
recovered from the user's Time Machine backup; the installed app was updated
without clearing its data. Final versionCode 5 / `1.3.1-cloud-budget-debug`.
Pulled-back installed APK SHA-256:
`0755d01ce1aa11675d18c90e3464be6fe0f430faebca650b992fa26b2c2137f8`.

Real screen inspection found CARTO's API-key-required watermark on home-map
tiles. Home and trip maps now use the already-supported OpenStreetMap tile
service, visible attribution and the existing identifying Hylink User-Agent.
Default WebView HTTP caching remains enabled; no offline/bulk tile prefetch is
added. See https://operations.osmfoundation.org/policies/tiles/ .
`node scripts/check-map-source.mjs` passed; the updated map and attribution were
visually verified on the phone, along with existing paired cloud state.

This app smoke test used the existing paired Wayon vehicle. It is not proof of
the still-pending carrotpilot/wip vehicle-side port or of live/SSH handover while
entering onroad mode. Do not claim full WIP integration from this installation.
