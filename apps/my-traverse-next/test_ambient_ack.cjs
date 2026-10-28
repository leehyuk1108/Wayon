const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');

const html = fs.readFileSync(`${__dirname}/app/src/main/assets/main.html`, 'utf8');
function source(name) {
    const match = html.match(new RegExp(`        function ${name}\\([^]*?\\n        }`));
    assert.ok(match, name);
    return match[0];
}
function fixture(target = 'manual', mode = 'manual') {
    const classes = new Set(['success']);
    const removedKeys = [];
    const state = { textContent: '', classList: {
        remove: (...values) => values.forEach(value => classes.delete(value)),
        add: value => classes.add(value),
    } };
    const context = vm.createContext({
        ambientCommandTarget: target,
        ambientPendingMode: { mode, expiresAt: 1234, durationSeconds: 900 },
        AMBIENT_MANUAL_MODE_KEY: 'wayonAmbientManualModeV1',
        ambientCommandState: state, ambientProfileCommandState: state,
        btnAmbientApply: {}, btnAmbientAuto: {}, btnAmbientProfileApply: {}, btnAmbientProfileReset: {},
        localStorage: { setItem() { assert.fail('ACK must not persist an applied mode'); },
            removeItem(key) { removedKeys.push(key); } },
        renderAmbientModeSummary() { assert.fail('ACK must not render an applied mode'); },
    });
    for (const name of ['ambientDurationText', 'setAmbientEditorBusy', 'onAmbientCommandResult']) {
        vm.runInContext(source(name), context);
    }
    return { context, state, classes, removedKeys };
}

test('accepted/null ACKs describe Comma storage, not confirmed Navdy application', () => {
    for (const target of ['manual', 'profile']) {
        for (const mode of ['manual', 'auto']) {
            for (const raw of [null, JSON.stringify({ command: { status: 'acknowledged', result: { accepted: true, applied: null } } })]) {
                const { context, state, classes, removedKeys } = fixture(target, mode);
                context.onAmbientCommandResult(raw, 'acknowledged');
                assert.match(state.textContent, /콤마.*저장됨/);
                assert.match(state.textContent, /Navdy 적용 미확인/);
                assert.equal(classes.has('success'), false);
                assert.equal(classes.has('failed'), false);
                assert.equal(context.ambientPendingMode, null);
                assert.deepEqual(removedKeys, target === 'manual' && mode === 'auto' ? ['wayonAmbientManualModeV1'] : [],
                    'accepted auto clears the obsolete manual marker without confirming Navdy application');
            }
        }
    }
});

test('auto command does not clear the manual marker before acknowledgment or on failure', () => {
    for (const status of ['sending', 'pending', 'delivered', 'failed', 'expired']) {
        const { context, removedKeys } = fixture('manual', 'auto');
        context.onAmbientCommandResult(null, status);
        assert.deepEqual(removedKeys, [], status);
    }
});

test('ACK without pending mode is also unconfirmed, including malformed raw payloads', () => {
    const { context, state, classes } = fixture();
    context.ambientPendingMode = null;
    context.onAmbientCommandResult('{', 'acknowledged');
    assert.match(state.textContent, /Navdy 적용 미확인/);
    assert.equal(classes.has('success'), false);
});

test('sending, pending, delivered, failure and expiry keep existing busy/reset behavior', () => {
    for (const target of ['manual', 'profile']) {
        const { context, state, classes } = fixture(target);
        context.onAmbientCommandResult(null, 'sending');
        assert.equal(context.btnAmbientApply.disabled, target === 'manual');
        assert.equal(context.btnAmbientProfileApply.disabled, target === 'profile');
        assert.equal(context.btnAmbientProfileReset.disabled, target === 'profile');
        for (const status of ['pending', 'delivered']) {
            context.onAmbientCommandResult(null, status);
            assert.equal(state.textContent, '콤마 응답 대기 중');
            assert.equal(context.btnAmbientApply.disabled, false);
            assert.equal(context.btnAmbientProfileApply.disabled, false);
        }
        for (const status of ['failed', 'expired']) {
            context.onAmbientCommandResult(null, status);
            assert.equal(classes.has('failed'), true);
            assert.equal(classes.has('success'), false);
            assert.equal(context.ambientPendingMode, null);
        }
    }
});
