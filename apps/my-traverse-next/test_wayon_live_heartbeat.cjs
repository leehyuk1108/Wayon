const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');

const script = fs.readFileSync(`${__dirname}/app/src/main/assets/wayon_live.js`, 'utf8');
function source(name) {
    const match = script.match(new RegExp(`    function ${name}\\([^]*?\\n    }`));
    assert.ok(match, name);
    return match[0];
}

test('WLP1 is exactly four binary bytes immediately and every 3 seconds', () => {
    const sent = [];
    const cleared = [];
    let tick;
    const currentSocket = { readyState: 1, send: value => sent.push(value) };
    const context = vm.createContext({
        socket: currentSocket, heartbeatTimer: 7, videoWatchdogTimer: 0, WebSocket: { OPEN: 1 },
        setInterval(callback, delay) { assert.equal(delay, 3000); tick = callback; return 8; },
        clearInterval(id) { cleared.push(id); },
    });
    vm.runInContext(source('stopHeartbeat') + source('startHeartbeat'), context);
    context.startHeartbeat(currentSocket);
    assert.deepEqual(cleared, [7, 0]);
    assert.equal(sent.length, 1);
    tick();
    assert.equal(sent.length, 2);
    for (const message of sent) {
        assert.equal(ArrayBuffer.isView(message), true, 'Worker must receive a binary WebSocket message');
        assert.equal(message.byteLength, 4);
        assert.deepEqual(Array.from(message), [87, 76, 80, 49]);
        assert.equal(Buffer.from(message).toString('ascii'), 'WLP1');
    }
    currentSocket.readyState = 3;
    tick();
    assert.equal(sent.length, 2, 'closed sockets must not send');
    currentSocket.readyState = 1;
    context.socket = {};
    tick();
    assert.equal(sent.length, 2, 'replaced sockets must not send');
    context.stopHeartbeat();
    assert.equal(context.heartbeatTimer, 0);
    assert.deepEqual(cleared, [7, 0, 8, 0]);
});

test('heartbeat send failures remain contained', () => {
    let warnings = 0;
    const socket = { readyState: 1, send() { throw new Error('closed during send'); } };
    const context = vm.createContext({ socket, heartbeatTimer: 0, videoWatchdogTimer: 0, WebSocket: { OPEN: 1 },
        setInterval: () => 1, clearInterval() {}, console: { warn() { warnings++; } } });
    vm.runInContext(source('stopHeartbeat') + source('startHeartbeat'), context);
    assert.doesNotThrow(() => context.startHeartbeat(socket));
    assert.equal(warnings, 1);
});
