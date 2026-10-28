const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');

const script = fs.readFileSync(`${__dirname}/app/src/main/assets/wayon_live.js`, 'utf8');
function source(name) {
    const match = script.match(new RegExp(`    (?:async )?function ${name}\\([^]*?\\n    }`));
    assert.ok(match, name);
    return match[0];
}

function fixture() {
    let time = 0;
    let nextTimer = 0;
    let nativeRequests = 0;
    let messageVisible = false;
    const timers = new Map();
    const sockets = [];
    const encoders = [];
    const traces = [];
    const errors = [];
    const toasts = [];
    const events = [];
    const buttons = new Map();
    function button(id) {
        if (!buttons.has(id)) buttons.set(id, {
            disabled: false, listeners: new Map(),
            addEventListener(name, listener) { this.listeners.set(name, listener); },
            click() { if (!this.disabled) return this.listeners.get('click')?.(); },
        });
        return buttons.get(id);
    }
    const photoButton = button('btnWayonLivePhoto');
    const clip10Button = button('btnWayonLiveClip10');
    const clip30Button = button('btnWayonLiveClip30');
    const classes = new Set(['active']);
    const classList = {
        contains: name => classes.has(name),
        add: name => classes.add(name),
        remove: (...names) => names.forEach(name => classes.delete(name)),
    };
    class FakeSocket {
        static OPEN = 1;
        constructor() { this.readyState = 0; this.sent = []; this.closes = []; this.bufferedAmount = 0; sockets.push(this); }
        send(value) {
            assert.equal(this.readyState, 1);
            const packet = ArrayBuffer.isView(value)
                ? Buffer.from(value.buffer, value.byteOffset, value.byteLength) : Buffer.from(value);
            this.sent.push({ at: time, packet });
        }
        close(code, reason) { this.readyState = 3; this.closes.push({ code, reason }); }
        open() { this.readyState = 1; this.onopen(); }
        drop() { this.readyState = 3; this.onclose({ code: 1006, reason: '' }); }
    }
    const schedule = (callback, delay, repeat = false) => {
        const id = ++nextTimer;
        timers.set(id, { callback, due: time + delay, interval: repeat ? delay : 0 });
        return id;
    };
    const gl = new Proxy({
        getParameter: () => 4096, checkFramebufferStatus: () => 1, FRAMEBUFFER_COMPLETE: 1,
        createFramebuffer: () => ({}), createTexture: () => ({}),
    }, { get: (target, key) => key in target ? target[key] : () => {} });
    const context = vm.createContext({
        socket: null, heartbeatTimer: 0, startupTimer: 0, reconnectTimer: 0,
        intentionalClose: false, sessionRequestPending: false, terminalState: null,
        reconnectAttempts: 0, MAX_RECONNECT_ATTEMPTS: 6, receiveBuffer: new Uint8Array(),
        photoCaptureBusy: false, photoCaptureController: null, photoCaptureSequence: 0,
        Uint8Array, ArrayBuffer, DataView, Blob, AbortController, TextDecoder, WebSocket: FakeSocket,
        CustomEvent: class { constructor(type, options) { this.type = type; this.detail = options.detail; } },
        FRAME_METADATA: 0,
        streams: { wide: { ready: false }, driver: { ready: false } },
        wideExposureReady: false, wideFirstFrameAt: 0, driverFirstFrameAt: 0,
        nextWideExposureSampleAt: 0, wideExposureSamples: 0, wideMeasuredExposureGain: 1,
        WIDE_READY_TIMEOUT_MS: 3000, savedPlayback: null, glState: { gl, textures: { wide: {}, driver: {} } },
        metadata: { width: 16 }, yaw: 0, pitch: 0, viewFov: 1, canvas: { width: 16, height: 16 },
        photoButton, clip10Button, clip30Button, CONTROL_MAGIC: [87, 76, 67, 49], CONTROL_PHOTO: 1, CONTROL_CLIP: 2,
        document: { createElement: () => ({
            getContext: () => ({ createImageData: (width, height) => ({ data: new Uint8Array(width * height * 4) }), putImageData() {} }),
            toBlob(callback) { encoders.push(callback); },
        }) },
        overlay: { classList, setAttribute() {} }, status: { classList },
        pointers: new Map(), pinchStart: null, animationFrame: 0,
        window: { Android: { requestWayonLiveSession() { nativeRequests++; } }, dispatchEvent: event => events.push(event) },
        setInterval: (callback, delay) => schedule(callback, delay, true),
        clearInterval: id => timers.delete(id), setTimeout: schedule, clearTimeout: id => timers.delete(id),
        performance: { now: () => time },
        console: {
            info: value => traces.push(JSON.parse(value.replace('[WayonCapture] ', ''))),
            warn: (...values) => errors.push(values), error: (...values) => errors.push(values),
        },
        setStatus() {}, showMessage() { messageVisible = true; }, hideMessage() { messageVisible = false; },
        showSaveToast: text => toasts.push(text), appendChunk() {}, sampleFrameEdges() {}, drawPanorama() {},
        clearSavedPlayback() {}, cancelAnimationFrame() {}, hideSaveToast() {}, hideImpactPanel() {}, suspendNativeRefresh() {},
    });
    for (const name of ['resetStartupExposureState', 'clearStartupTimer', 'traceCapture', 'updateCaptureControls',
        'cancelPhotoCapture', 'closeDecoders', 'stopHeartbeat', 'startHeartbeat', 'connect', 'requestSession',
        'sendClientControl', 'jpegBlob', 'capturePanoramaPhoto', 'requestClip', 'uploadFrame', 'handleCaptureStatus', 'handleControl']) {
        vm.runInContext(source(name), context);
    }
    const stop = script.match(/    window\.stopWayonLiveView = \(\) => \{[^]*?\n    };/);
    assert.ok(stop);
    vm.runInContext(stop[0], context);
    for (const name of ['photoButton', 'clip10Button', 'clip30Button']) {
        const binding = script.match(new RegExp(`    ${name}\\.addEventListener\\("click",[^\\n]+`));
        assert.ok(binding, name);
        vm.runInContext(binding[0], context);
    }
    context.updateCaptureControls();
    function open(ready = false) {
        classList.add('active');
        context.requestSession(false);
        context.connect('/local-test', 'test-protocol');
        const socket = sockets.at(-1);
        socket.open();
        if (ready) {
            context.clearStartupTimer();
            context.streams.wide.ready = true;
            context.streams.driver.ready = true;
            context.updateCaptureControls();
        }
        return socket;
    }
    function advance(delta) {
        const end = time + delta;
        for (;;) {
            const entry = [...timers.entries()].filter(([, timer]) => timer.due <= end)
                .sort((a, b) => a[1].due - b[1].due || a[0] - b[0])[0];
            if (!entry) break;
            const [id, timer] = entry;
            time = timer.due;
            if (timer.interval) timer.due += timer.interval;
            else timers.delete(id);
            timer.callback();
        }
        time = end;
    }
    function complete(index, value = { size: 4, arrayBuffer: async () => Uint8Array.from([255, 216, 255, 217]).buffer }) {
        encoders[index](value);
    }
    return { context, open, advance, complete, sockets, photoButton, clip10Button, clip30Button,
        traces, errors, toasts, encoders, events, nativeRequests: () => nativeRequests, messageVisible: () => messageVisible };
}

const controls = socket => socket.sent.filter(({ packet }) => packet.subarray(0, 4).toString() === 'WLC1');

test('12-second no-video notice preserves the socket and 3-second heartbeat until explicit close', () => {
    const f = fixture();
    const socket = f.open();
    f.advance(15000);
    assert.equal(socket.closes.length, 0);
    assert.equal(f.context.socket, socket);
    assert.deepEqual(socket.sent.map(item => item.at), [0, 3000, 6000, 9000, 12000, 15000]);
    assert.equal(f.traces.filter(trace => trace.stage === 'video-wait').length, 1);
    assert.equal(f.photoButton.disabled, true);
    assert.equal(f.clip10Button.disabled, true);
    assert.equal(f.nativeRequests(), 1);
    f.context.window.stopWayonLiveView();
    f.advance(15000);
    assert.equal(socket.sent.length, 6);
    assert.equal(f.context.heartbeatTimer, 0);
    assert.equal(socket.closes[0].reason, 'viewer closed');
});

test('late close from an old socket cannot cancel the new heartbeat or its active photo', async () => {
    const f = fixture();
    const a = f.open(true);
    const b = f.open(true);
    const capture = f.photoButton.click();
    a.onclose({ code: 1000 });
    f.advance(3000);
    assert.equal(f.context.socket, b);
    assert.equal(f.context.photoCaptureBusy, true);
    assert.equal(b.sent.length, 2);
    f.complete(0);
    await capture;
    assert.equal(controls(b).length, 1);
});

test('a never-called toBlob cannot strand the disabled photo button after full close/reopen', async () => {
    const f = fixture();
    const a = f.open(true);
    const firstCapture = f.photoButton.click();
    assert.equal(f.context.photoCaptureBusy, true);
    assert.equal(f.photoButton.disabled, true);
    assert.equal(f.clip10Button.disabled, false, 'photo encoding must not disable the working clip path');
    const clicks = f.traces.filter(trace => trace.stage === 'photo-click').length;
    assert.equal(f.photoButton.click(), undefined, 'disabled DOM buttons do not deliver clicks');
    assert.equal(f.traces.filter(trace => trace.stage === 'photo-click').length, clicks);
    f.context.window.stopWayonLiveView();
    await firstCapture;
    assert.equal(f.context.photoCaptureBusy, false);
    assert.equal(f.photoButton.disabled, true, 'disconnected controls stay disabled');
    const b = f.open(true);
    assert.equal(f.photoButton.disabled, false);
    const secondCapture = f.photoButton.click();
    f.complete(0);
    await Promise.resolve();
    assert.equal(f.context.photoCaptureBusy, true, 'late old callback cannot unlock the new capture');
    assert.equal(controls(a).length, 0);
    assert.equal(controls(b).length, 0);
    f.complete(1);
    await secondCapture;
    assert.equal(controls(b).length, 1);
    assert.equal(f.context.photoCaptureBusy, false);
    assert.equal(f.photoButton.disabled, false);
    assert.equal(f.errors.length, 0);
});

test('automatic reconnect cancels an unresolved encoder without submitting its old photo', async () => {
    const f = fixture();
    const a = f.open(true);
    const capture = f.photoButton.click();
    a.drop();
    await capture;
    assert.equal(f.context.photoCaptureBusy, false);
    f.advance(1000);
    const b = f.open(true);
    f.complete(0);
    await Promise.resolve();
    assert.equal(controls(a).length, 0);
    assert.equal(controls(b).length, 0);
});

test('late blob bytes from A cannot enter B or unlock B while a new photo is encoding', async () => {
    const f = fixture();
    const a = f.open(true);
    const firstCapture = f.photoButton.click();
    let resolveBytes;
    f.complete(0, { size: 4, arrayBuffer: () => new Promise(resolve => { resolveBytes = resolve; }) });
    await Promise.resolve();
    const b = f.open(true);
    const secondCapture = f.photoButton.click();
    resolveBytes(new ArrayBuffer(4));
    await firstCapture;
    assert.equal(controls(a).length, 0);
    assert.equal(controls(b).length, 0);
    assert.equal(f.context.photoCaptureBusy, true);
    assert.equal(f.photoButton.disabled, true);
    f.complete(1);
    await secondCapture;
    assert.equal(controls(b).length, 1);
});

test('normal photo event queues one unchanged WLC1 JPEG and distinguishes local queuing from server upload', async () => {
    const f = fixture();
    const socket = f.open(true);
    const capture = f.photoButton.click();
    f.complete(0);
    await capture;
    const packets = controls(socket);
    assert.equal(packets.length, 1);
    assert.equal(packets[0].packet.toString('hex'), '574c43310100000004ffd8ffd9');
    assert.match(f.toasts.at(-1), /차량 응답 대기/);
    assert.ok(f.traces.some(trace => trace.stage === 'photo-queued' && trace.bytes === 4));
    assert.ok(f.traces.some(trace => trace.stage === 'photo-readpixels-start'));
    assert.ok(f.traces.some(trace => trace.stage === 'photo-encode-start'));
    assert.ok(f.traces.length < 15, 'diagnostics are bounded per action, not per frame or heartbeat');
});

test('null or throwing toBlob restores the photo control and never sends a command', async () => {
    for (const mode of ['null', 'throw']) {
        const f = fixture();
        const socket = f.open(true);
        if (mode === 'throw') {
            const create = f.context.document.createElement;
            f.context.document.createElement = () => ({ ...create(), toBlob() { throw new Error('encoding unavailable'); } });
        }
        const capture = f.photoButton.click();
        if (mode === 'null') f.complete(0, null);
        await capture;
        assert.equal(f.context.photoCaptureBusy, false);
        assert.equal(f.photoButton.disabled, false);
        assert.equal(controls(socket).length, 0);
        assert.equal(f.errors.length, 1);
    }
});

test('disconnected controls do not dispatch; connected 10s/30s clips retain exact packet bytes', () => {
    const f = fixture();
    assert.equal(f.photoButton.disabled, true);
    assert.equal(f.clip10Button.disabled, true);
    f.photoButton.click();
    f.clip10Button.click();
    assert.equal(f.encoders.length, 0);
    const socket = f.open(true);
    f.clip10Button.click();
    f.clip30Button.click();
    assert.deepEqual(controls(socket).map(item => item.packet.toString('hex')),
        ['574c433102000000010a', '574c433102000000011e']);
    socket.drop();
    f.photoButton.click();
    f.clip30Button.click();
    assert.equal(controls(socket).length, 2);
    assert.equal(f.photoButton.disabled, true);
});

test('server WLV1 capture responses have a separate bounded trace and saved refresh behavior', () => {
    const f = fixture();
    f.open(true);
    for (const captureState of ['uploading', 'buffering', 'error', 'saved']) {
        f.context.handleControl(3, Buffer.from(JSON.stringify({ state: 'capture', captureState, kind: 'clip', durationSeconds: 10 })));
    }
    assert.deepEqual(f.traces.filter(trace => trace.stage === 'capture-status').map(trace => trace.captureState),
        ['uploading', 'buffering', 'error', 'saved']);
    assert.equal(f.events.length, 1);
    assert.equal(f.events[0].type, 'wayon-live-capture-saved');
    assert.equal(f.toasts.length, 4);
});

test('reconnect resets exposure readiness and fresh frames can dismiss the loading message', () => {
    const f = fixture();
    f.context.wideExposureReady = true;
    f.context.wideFirstFrameAt = 1;
    f.context.driverFirstFrameAt = 1;
    f.open();
    assert.equal(f.context.wideExposureReady, false);
    assert.equal(f.context.wideFirstFrameAt, 0);
    for (const at of [1000, 5000]) {
        for (const name of ['wide', 'driver']) {
            f.context.streams[name].frame = { close() {} };
            f.context.uploadFrame(name, 0, at);
        }
    }
    assert.equal(f.messageVisible(), false);
    assert.equal(f.context.streams.wide.ready, true);
    assert.equal(f.context.streams.driver.ready, true);
    assert.equal(f.photoButton.disabled, false);
});
