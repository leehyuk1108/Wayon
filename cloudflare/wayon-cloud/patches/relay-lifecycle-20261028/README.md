# Relay Lifecycle Patch

Apply after `../carrot-trip-coverage-20261028/`. This is a patch against a
private authenticated production export, not the unrelated local dirty Worker.

- Baseline SHA256: `d13f92bb417f302bc29bfd4fe544061a3b2ca2723ead13a608ae8a64340db25d`
- Patched SHA256: `67eccbf0151a79e428244b0e68bc9d800e79215c87d11d64e0b75442188633e8`
- Change only `WayonDeviceRelay`; all auth, bindings, schema and other modules
  stay identical. SSH and live retain separate device-and-kind namespaces.
- Select only OPEN sockets. Ignore replaced senders and handle failed handshake
  sends without throwing. Late close callbacks cannot terminate a replacement.
- Preserve the existing per-device authentication and explicit SSH policy.

Do not commit the production export, settings or secrets. Verify exact bytes,
active version and bindings before staging. Activate only the expected version,
verify all modules and bindings, then exercise the real authenticated clients.
Keep the previous version available for rollback on behavioral failure.

The 14 mock tests pin both hashes, reproduce the old failure with a retained
CLOSING socket before an OPEN socket, and cover binary transport, replacement,
ambient/SSH notifications, revocation, errors and close cleanup:

```sh
WAYON_RELAY_BASELINE=/private/path/before.js \
WAYON_RELAY_CANDIDATE=/private/path/after.js \
node --test relay.test.mjs
```

The runtime harness uses real workerd through Miniflare and `ws`, with the
production compatibility date `2026-05-14`. Use local installed modules:

```sh
MINIFLARE_MODULE=/path/to/node_modules/miniflare \
WS_MODULE=/path/to/node_modules/ws \
WAYON_RELAY_CANDIDATE=/private/path/after.js \
node relay-runtime.mjs
```

Verified with workerd 1.20260921.1 / Miniflare 5.20260921.0-alpha. The V4 adapter
supports that installed V5 configuration schema. Assertions cover OPEN=1,
binary heartbeat and 1.1 MB payload identity, viewer/device replacement after
server close callbacks, ambient notification, reopen and 1012 on device loss.
The initial 2.5-second observation deadline was too short for the final runtime
close event; the test uses a bounded 10 seconds, without production timeout
changes. It does not force retained-CLOSING selection or hibernation eviction.

Mock reproduction is not proof that this caused the original live interruption.
Current compatibility already auto-replies to close frames, so a missing close
ACK is not established as the cause. Forced hibernation/wake, concurrent same-role
upgrades and overnight/mobile-network behavior remain separate checks.
