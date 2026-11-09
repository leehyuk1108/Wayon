# Web Push Service Binding Patch (2026-11-10)

The web fanout (`web-push-20261102`) posts to `https://my-traverse-web.hyuklee.workers.dev`
with a public `fetch`. Production D1 `push_claims` held only the three 2026-11-02 test
claims, all posted directly from a Mac, and none from wayon-cloud afterwards. The active
version had no service binding to the web Worker and no `global_fetch_strictly_public`
flag, so same-account workers.dev subrequests are the likely reason nothing arrived.

This one-line patch sends the same request through `env.MY_TRAVERSE_WEB` when that
service binding exists, and otherwise keeps the original public `fetch` unchanged.

- Baseline SHA256 (active 3c8dd130, parking-display candidate):
  `5d4724e39018dd23e26ad52ba458da7d1cd469307e96fb99756cb38da9539c20`
- Candidate SHA256: `050963dbfa69677fa15ac62f1aa5c06315b8cc616c0967609457fe6bb341e65a`
- Deployment: new version inheriting all 24 bindings from the pinned baseline version,
  plus `MY_TRAVERSE_WEB` (service `my-traverse-web`); companion modules byte-identical.
  Never deploy the dirty repository `src/worker.js`.

`runtime.test.mjs` runs the patched active bundle in workerd: with the binding, door-lock
and impact notifications reach the binding beside FCM and no public fetch is made;
without it the original public fetch is attempted. It needs the private copy of the
active modules (`WAYON_ACTIVE_MODULE_DIR`).
