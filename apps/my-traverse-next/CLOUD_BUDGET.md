# My Traverse New passive refresh

This is the client for `Wayon/Sunnypilot`, not Hylink.

- Passive foreground `/api/json` reads change from 5 s to 30 s (720 to 120
  attempts/hour without failures or user actions).
- Failed automatic reads back off up to five minutes. Explicit refreshes,
  push-triggered refreshes and command-completion reads bypass that backoff.
- The separate 2.5 s GMOne command-status polling, background widget scheduler,
  vehicle commands, notification policy and UI remain unchanged.
- A transition detected only through passive polling can now be observed up to
  about 30 s later; this is a cloud display/refresh tradeoff, not vehicle control.

Standalone policy test (JDK, no Android device required):

```sh
out=$(mktemp -d)
javac -d "$out" app/src/main/java/com/example/carcontroller/CloudRefreshPolicy.java scripts/CloudRefreshPolicyCheck.java
java -cp "$out" com.example.carcontroller.CloudRefreshPolicyCheck
```

This test does not compile the Android Activity or validate APK installation.
The inspected phone has package `com.example.carcontroller.next`, version
`2.0-preview.13` / 22. The installed APK and available local release APK differ,
including their primary DEX. Preserve the installed app and private settings;
reconcile the source/signing baseline before building an update. Do not install
the older `MyTraverse-App` branch over this app merely because its name matches.
