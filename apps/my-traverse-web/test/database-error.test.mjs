import test from 'node:test';
import assert from 'node:assert/strict';
import {databaseLimitResponse} from '../server/database-error.mjs';
import worker from '../server/worker.mjs';

const PRIVATE = 'PRIVATE_DATA_MUST_NOT_ESCAPE';
const limit = () => new Error('D1_ERROR: Your account has exceeded D1\'s free tier daily row read limit. ' + PRIVATE);

test('known D1 quota errors report only a safe message and the next UTC reset', () => {
  for (const [at, next, seconds] of [
    ['2026-11-02T00:00:00Z','2026-11-03T00:00:00Z',86400],
    ['2026-11-02T23:59:59.999Z','2026-11-03T00:00:00Z',1],
    ['2026-12-31T23:00:00Z','2027-01-01T00:00:00Z',3600],
  ]) {
    const value = databaseLimitResponse(new Error('wrapper', {cause:limit()}), Date.parse(at));
    assert.equal(value.body.retryAt, new Date(next).toISOString());
    assert.equal(value.headers['retry-after'], String(seconds));
    assert.match(value.body.message, /오전 9시/);
    assert.ok(!JSON.stringify(value).includes(PRIVATE));
  }
  assert.ok(databaseLimitResponse(new Error("Your account has exceeded D1's free tier daily row write limit.")));
  for (const error of [new Error('too many queries'), new Error('D1_ERROR: no such table'),
    new Error('7500'), new Error('daily limit'), null, {}]) assert.equal(databaseLimitResponse(error), null);
  const cyclic = new Error('cyclic'); cyclic.cause = cyclic;
  assert.equal(databaseLimitResponse(cyclic), null);
});

test('quota failure never authenticates, clears cookies, sends commands or leaks SQL/account details', async () => {
  const origin = 'https://quota.test';
  let mutations = 0;
  const env = {PUBLIC_ORIGIN:origin, DB:{prepare() { throw limit(); }},
    WAYON:{fetch() { mutations++; throw Error('must not reach upstream'); }}};
  for (const [path, method] of [['/api/session','GET'],['/api/login','POST'],
    ['/api/logout','POST'],['/api/command','POST']]) {
    const response = await worker.fetch(new Request(origin + path, {method,
      headers:{cookie:'__Host-traverse=' + 'q'.repeat(43), origin,
        'content-type':'application/json'}, ...(method === 'POST' ? {body:'{}'} : {})}), env, {});
    assert.equal(response.status,503);
    assert.equal(response.headers.get('set-cookie'),null);
    assert.equal(response.headers.get('clear-site-data'),null);
    assert.equal(response.headers.get('cache-control'),'no-store');
    const data = await response.json();
    assert.equal(data.code,'database_daily_limit');
    assert.equal(data.authenticated,undefined);
    assert.ok(!JSON.stringify(data).includes(PRIVATE));
  }
  assert.equal(mutations,0);
  const denied = await worker.fetch(new Request(origin + '/api/login',{method:'POST',
    headers:{origin:'https://other.test','content-type':'application/json'},body:'{}'}),env,{});
  assert.equal(denied.status,403);
  const noSession = await worker.fetch(new Request(origin + '/api/command',{method:'POST',
    headers:{origin,'content-type':'application/json'},body:'{}'}),env,{});
  assert.equal(noSession.status,401);
  env.DB.prepare = () => { throw new Error('PRIVATE_UNKNOWN_ERROR'); };
  const unknown = await worker.fetch(new Request(origin + '/api/session',{
    headers:{cookie:'__Host-traverse=' + 'q'.repeat(43)}}),env,{});
  assert.equal(unknown.status,400);
  assert.equal((await unknown.json()).error,'request_failed');
});
