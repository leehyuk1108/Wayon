import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url),{derive,number}=require('../design/cloud-overview/model.js');
const now=Date.parse('2026-09-10T07:00:00Z');
const make=(state={},raw={})=>({feed:{state:{updated_at:new Date(now-15000).toISOString(),onroad:0,ignition:0,...state,raw_json:raw}}});
const checks=[
  ['missing values are not zero',()=>{for(const v of [null,undefined,'',' ',false,true])assert.equal(number(v),null)}],
  ['zero remains a valid reading',()=>assert.equal(number(0),0)],
  ['no state is not parked',()=>assert.equal(derive({},now).status,'상태 확인 대기')],
  ['park requires explicit off flags',()=>assert.equal(derive(make({ignition:undefined}),now).status,'상태 확인 중')],
  ['onroad age threshold is 60 seconds',()=>assert.equal(derive(make({onroad:1,updated_at:new Date(now-61000).toISOString()}),now).stale,true)],
  ['offroad heartbeat tolerates 15 minutes',()=>assert.equal(derive(make({updated_at:new Date(now-600000).toISOString()}),now).stale,false)],
  ['CAN warning has priority over records',()=>assert.equal(derive(make({onroad:1},{vehicle:{available:true,can:{valid:false}}}),now).alerts[0].kind,'can')],
  ['missing CAN does not invent warning',()=>assert.equal(derive(make({},{}),now).alerts.length,0)],
  ['offroad ignores unavailable vehicle values',()=>assert.equal(derive(make({},{vehicle:{available:false,can:{valid:false}}}),now).alerts.length,0)],
  ['old faults are not presented as live',()=>{const m=derive(make({updated_at:new Date(now-7200000).toISOString()},{vehicle:{available:true,can:{valid:false}}}),now);assert.deepEqual(m.alerts.map(a=>a.kind),['stale'])}],
  ['GPS range rejects invalid points',()=>assert.equal(derive(make({latitude:91,longitude:0}),now).point,null)],
  ['GPS zero is valid',()=>assert.deepEqual(derive(make({latitude:0,longitude:0}),now).point,[0,0])],
  ['raw JSON parsing is guarded',()=>assert.doesNotThrow(()=>derive(make({},'invalid'),now))],
  ['scalar raw JSON is not telemetry',()=>{for(const value of ['null','1','[]'])assert.doesNotThrow(()=>derive(make({},value),now))}],
  ['reported device warnings are surfaced',()=>assert.equal(derive(make({},{panda:{heartbeatLost:true}}),now).alerts[0].kind,'device')],
  ['reported critical thermal state is surfaced',()=>assert.equal(derive(make({},{device:{thermal:{status:'red'}}}),now).alerts[0].kind,'thermal')],
  ['future timestamp cannot imply freshness',()=>assert.equal(derive(make({updated_at:new Date(now+120000).toISOString()}),now).age,null)],
  ['recent impact is discoverable',()=>{const d=make();d.impacts={impacts:[{detected_at:new Date(now-500000).toISOString()}]};assert.equal(derive(d,now).alerts[0].kind,'impact')}],
];
for(const [label,test]of checks){test();console.log('PASS',label)}
console.log(`${checks.length} data-priority checks passed`);
