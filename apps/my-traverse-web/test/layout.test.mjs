import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

test('web layout overrides follow native styles and permit zoom without modifying the source', async () => {
  const original = await readFile(new URL('../../my-traverse-next/app/src/main/assets/main.html', import.meta.url), 'utf8');
  const html = await readFile(new URL('../public/index.html', import.meta.url), 'utf8');
  assert.ok(html.lastIndexOf('/pwa.css') > html.lastIndexOf('</style>'));
  assert.equal((html.match(/href="\/pwa.css"/g) || []).length, 1);
  assert.ok(!html.includes('user-scalable=no'));
  assert.ok(original.includes('user-scalable=no'));
  assert.ok(html.includes(original.slice(original.indexOf('<style>'), original.lastIndexOf('</style>') + 8)));
});

test('web home layout preserves finder and accounts for viewport and safe insets', async () => {
  const css = await readFile(new URL('../client/pwa.css', import.meta.url), 'utf8');
  assert.match(css, /height: 100dvh/);
  assert.match(css, /#tab-control:not\(\.finder-open\)/);
  for (const side of ['top', 'bottom', 'left', 'right']) assert.ok(css.includes(`env(safe-area-inset-${side}, 0px)`));
  assert.match(css, /home-sunroof-actions \.action-button-grouped \{ min-height: 44px/);
});
