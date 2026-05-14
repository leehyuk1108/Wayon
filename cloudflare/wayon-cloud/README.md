# Wayon Cloud

Wayon Cloud is a lightweight Cloudflare Worker dashboard for a Wayon/openpilot
device. The comma device only pushes low-rate telemetry and occasional offroad
snapshots. The Worker stores live state in D1 and JPEG snapshots in KV.

## Cloudflare Resources

- Worker: `wayon-cloud`
- D1 database: `wayon_cloud`
- KV namespace: `WAYON_SNAPSHOTS`

The dashboard and API are served from the same Worker. API reads and writes are
protected with bearer tokens.

## Deploy

1. Create Cloudflare resources:

   ```sh
   npx wrangler d1 create wayon_cloud
   npx wrangler kv namespace create WAYON_SNAPSHOTS
   ```

2. Copy the generated IDs into `wrangler.toml`.

3. Apply the schema:

   ```sh
   npx wrangler d1 execute wayon_cloud --remote --file=./schema.sql
   ```

4. Set secrets:

   ```sh
   npx wrangler secret put WAYON_UPLOAD_TOKEN
   npx wrangler secret put WAYON_VIEW_TOKEN
   ```

5. Deploy:

   ```sh
   npx wrangler deploy
   ```

## Device Config

Copy `device_config.example.json`, fill in the deployed Worker URL and upload
token, then place it on the device at:

```text
/data/wayon_cloud/config.json
```

The uploader is intentionally quiet when the config file is missing.
