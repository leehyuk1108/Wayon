import {readFileSync} from 'node:fs';
import {dirname, join} from 'node:path';
import {RETAINED_MODULE_SHA256} from './patch.mjs';

export const baselinePath = process.env.WAYON_GALLERY_BASELINE ||
  '/Users/hyuklee/Documents/my-traverse-web-20261102/login-quota-baseline/worker.js';
export const baseline = readFileSync(baselinePath, 'utf8');
export const moduleDir = process.env.WAYON_GALLERY_MODULE_DIR || dirname(baselinePath);
export const retained = Object.fromEntries(Object.keys(RETAINED_MODULE_SHA256)
  .map(name => [name, readFileSync(join(moduleDir, name), 'utf8')]));
