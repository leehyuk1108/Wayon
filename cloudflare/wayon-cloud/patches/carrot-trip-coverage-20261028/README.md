# Carrot Trip Coverage Patch

This patch was made against the actual deployed worker, not the unrelated dirty
`src/worker.js`. Do not deploy that whole source file to reproduce this change.

- Baseline SHA256: `10a24bb45918761edf2a5b34c63a1034c74fc9125b1adc236fac29146d437f3e`
- Patched SHA256: `d13f92bb417f302bc29bfd4fe544061a3b2ca2723ead13a608ae8a64340db25d`
- Changes: authenticated-device trip union, trip-detail identity validation,
  report-dependent health-cache invalidation and compare-and-swap cache writes.
- All existing bindings and both supporting modules must remain unchanged.

Obtain the authenticated production export privately, verify the baseline hash,
then apply `worker.patch` to that export. Never commit production settings,
tokens or the export's private account identifiers. A newer production version
requires a fresh comparison, not force-applying this patch.

Run the 19 focused tests with a recent Node version supporting `node:sqlite`:

```sh
WAYON_WORKER_BASELINE=/private/path/baseline.js \
WAYON_WORKER_CANDIDATE=/private/path/candidate.js \
node --test worker-trip-merge.test.mjs
```

The tests pin the exact baseline and verify only these scoped differences.
They include actual handlers, cross-device rejection, deterministic union and
SQLite cache races. Authentication and remote-control transports are unchanged.
