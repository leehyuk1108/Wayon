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
