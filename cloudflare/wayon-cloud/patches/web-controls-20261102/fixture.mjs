import {readFileSync} from 'node:fs';
import {dirname, join} from 'node:path';
import {RETAINED_MODULE_SHA256} from './patch.mjs';

export const baselinePath = process.env.WAYON_WEB_CONTROLS_BASELINE ||
  '/Users/hyuklee/Documents/my-traverse-web-20261102/fanout.worker.js';
export const baseline = readFileSync(baselinePath, 'utf8');
export const moduleDir = process.env.WAYON_WEB_CONTROLS_MODULE_DIR || join(dirname(baselinePath), 'baseline');
export const retained = Object.fromEntries(Object.keys(RETAINED_MODULE_SHA256)
  .map(name => [name, readFileSync(join(moduleDir, name), 'utf8')]));
export const columns = ['id', 'device_id', 'started_at', 'ended_at', 'duration_s', 'distance_m',
  'start_lat', 'start_lon', 'end_lat', 'end_lon', 'route_point_count', 'source', 'route_name',
  'segment_count', 'avg_speed_mps', 'max_speed_mps'];
