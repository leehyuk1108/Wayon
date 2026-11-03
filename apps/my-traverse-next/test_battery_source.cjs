const assert = require('node:assert/strict');
const fs = require('node:fs');
const test = require('node:test');
const vm = require('node:vm');

const html = fs.readFileSync(process.env.TRAVERSE_VOLTAGE_HTML ||
    `${__dirname}/app/src/main/assets/main.html`, 'utf8');

function renderer() {
    const elements = new Map();
    const get = id => {
        if (!elements.has(id)) elements.set(id, {
            textContent: '', innerHTML: '', style: {},
            classList: { add() {}, remove() {}, toggle() {} },
        });
        return elements.get(id);
    };
    const context = vm.createContext({
        document: { getElementById: get }, window: {},
        latestFirebaseBatteryLevel: null, latestFirebaseBatteryVoltage: null,
        latestWayonCloudVoltage: null, wayonCloudKeyActive: false,
        wayonCloudDataAvailable: false, wayonCloudKeyInput: { value: '' },
        validatedFuelLevel: () => null, renderHomeFuelSummary() {}, updateHeroLocationMap() {},
    });
    for (const name of ['hasMetricValue', 'hasWayonCloudKey', 'healthBar',
        'renderBatterySummary', 'updateInfoVoltsDisplay', 'updateWayonCloudState', 'updateCarStatus']) {
        const source = html.match(new RegExp(`        function ${name}\\([^]*?\\n        }`));
        assert.ok(source, name);
        vm.runInContext(source[0], context);
    }
    return {
        get, context,
        multipack: voltage => context.updateCarStatus('750', voltage, '79', '60000', '90',
            '2026-11-03 17:08:35', '27', '', ''),
        comma: voltage => context.updateWayonCloudState(voltage, '17:08', 'OFFROAD', '0', null, null, ''),
    };
}

function shows(f, voltage) {
    assert.equal(f.get('info-volts').textContent, `${voltage}V`);
    assert.match(f.get('val-battery').innerHTML, new RegExp(`\\(${voltage.replace('.', '\\.')}V\\)`));
}

test('battery voltage uses MultiPack with no Comma connection', () => {
    const f = renderer();
    f.multipack('12.4');
    shows(f, '12.4');
    assert.match(f.get('val-battery').innerHTML, /79%/);
});

for (const order of ['multipack-first', 'comma-first']) {
    test(`battery voltage stays MultiPack in ${order} callback order`, () => {
        const f = renderer();
        if (order === 'comma-first') f.comma('11.9');
        f.multipack('12.4');
        if (order === 'multipack-first') f.comma('11.9');
        shows(f, '12.4');
        for (const voltage of ['12.0', '12.1', '--', null]) f.comma(voltage);
        shows(f, '12.4');
        f.multipack('12.5');
        shows(f, '12.5');
    });
}

test('Comma-only startup leaves MultiPack voltage unknown', () => {
    const f = renderer();
    f.comma('11.9');
    assert.equal(f.get('info-volts').textContent, '--V');
    assert.equal(f.get('val-battery').innerHTML, '--');
});

test('missing MultiPack clears the old voltage without falling back to Comma', () => {
    for (const missing of [null, undefined, '', '--']) {
        const f = renderer();
        f.multipack('12.4');
        f.comma('11.9');
        f.multipack(missing);
        f.comma('12.0');
        assert.equal(f.get('info-volts').textContent, '--V');
        assert.equal(f.get('val-battery').innerHTML, '79%');
    }
});

test('a configured Cloud key does not select the voltage source', () => {
    const f = renderer();
    f.context.wayonCloudKeyInput.value = 'synthetic-view-key';
    f.context.latestWayonCloudVoltage = '11.9';
    f.multipack('12.4');
    shows(f, '12.4');
});
