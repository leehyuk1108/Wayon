import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import sharp from 'sharp';

const root = new URL('../', import.meta.url);
const launcher = new URL('../my-traverse-next/app/src/main/res/mipmap-xxxhdpi/ic_launcher.webp', root);

test('install icons use the original Android launcher artwork at each required size', async () => {
  for (const size of [180, 192, 512]) {
    const actual = await readFile(new URL(`public/app-icon-v2-${size}.png`, root));
    const expected = await sharp(await readFile(launcher)).resize(size, size)
      .flatten({background: '#242424'}).png().toBuffer();
    assert.deepEqual(actual, expected);
    const metadata = await sharp(actual).metadata();
    assert.equal(metadata.width, size);
    assert.equal(metadata.height, size);
    assert.equal(metadata.hasAlpha, false);
  }
});

test('Apple home screen, manifest, login, and push reference the versioned launcher icons', async () => {
  const html = await readFile(new URL('public/index.html', root), 'utf8');
  assert.match(html, /rel="apple-touch-icon" href="\/app-icon-v2-180.png"/);
  assert.match(html, /rel="icon" href="\/app-icon-v2-192.png"/);
  const manifest = JSON.parse(await readFile(new URL('public/manifest.webmanifest', root), 'utf8'));
  assert.deepEqual(manifest.icons.map(icon => icon.src), ['/app-icon-v2-192.png', '/app-icon-v2-512.png']);
  const sw = await readFile(new URL('public/sw.js', root), 'utf8');
  assert.match(sw, /traverse-shell-v2/);
  assert.match(sw, /icon: '\/app-icon-v2-192.png'/);
  const pwa = await readFile(new URL('public/pwa.js', root), 'utf8');
  assert.ok(pwa.includes('/app-icon-v2-192.png'));
});
