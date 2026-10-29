const assert = require('node:assert/strict');
const fs = require('node:fs');
const test = require('node:test');
const vm = require('node:vm');
const html = fs.readFileSync(`${__dirname}/app/src/main/assets/main.html`, 'utf8');
function body(name) {
  const match = html.match(new RegExp(`        function ${name}\\([^]*?\\n        }`));
  assert.ok(match, name);
  return match[0];
}
function events() {
  const listeners = new Map();
  return {
    on(event, fn) { listeners.set(event, [...(listeners.get(event) || []), fn]); return this; },
    once(event, fn) {
      const one = (...args) => { this.off(event, one); fn(...args); };
      return this.on(event, one);
    },
    off(event, fn) { listeners.set(event, (listeners.get(event) || []).filter(f => f !== fn)); return this; },
    fire(event) { for (const fn of [...(listeners.get(event) || [])]) fn({}); },
  };
}
const flush = () => new Promise(resolve => setImmediate(resolve));
function fixture({ vector = true, cached = false, hero = true, rejectStyle = false, glFailure = false } = {}) {
  const surface = { classList: new Set() };
  const container = { isConnected: true, closest: () => hero ? surface : null };
  const layers = new Set();
  const map = { ...events(), getContainer: () => container, hasLayer: layer => layers.has(layer),
    removeLayer(layer) { layers.delete(layer); } };
  const fallback = { ...events(), addTo() {
    layers.add(this);
    if (cached) { this.fire('tileload'); this.fire('load'); }
    return this;
  } };
  const gl = { ...events(), loaded: () => false };
  const vectorContainer = { style: {} };
  const vectorLayer = { addTo() { layers.add(this); if (glFailure) throw new Error('WebGL unavailable'); return this; },
    getContainer: () => vectorContainer, getMaplibreMap: () => gl };
  const context = { L: { tileLayer: () => fallback }, heroMapElement: () => surface,
    openFreeMapNoLabelsStyle: () => rejectStyle ? Promise.reject(new Error('offline')) : Promise.resolve({}),
    console: { warn() {}, info() {} }, performance: { now: () => 0 },
    setTimeout() { throw new Error('Do not hide a usable map behind a fixed timer'); }, clearTimeout() {} };
  if (vector) context.L.maplibreGL = () => vectorLayer;
  vm.runInNewContext(body('addNoLabelDarkBaseMap'), context);
  context.addNoLabelDarkBaseMap(map);
  return { surface, container, layers, map, fallback, gl, vectorContainer, vectorLayer };
}

test('ready raster is visible immediately while vector is pending', async () => {
  const f = fixture();
  await flush();
  assert.equal(f.vectorContainer.style.opacity, '0');
  f.fallback.fire('tileload');
  f.fallback.fire('load');
  assert.ok(f.surface.classList.has('map-surface-ready'));
  assert.ok(f.layers.has(f.fallback));
  f.gl.fire('load');
  assert.equal(f.vectorContainer.style.opacity, '1');
  assert.ok(!f.layers.has(f.fallback));
});

test('cached raster loads are observed before addTo, including no WebGL support', () => {
  for (const vector of [true, false]) {
    const f = fixture({ vector, cached: true });
    assert.ok(f.surface.classList.has('map-surface-ready'));
  }
});

test('failed raster tiles do not expose an empty surface', () => {
  const f = fixture({ vector: false });
  f.fallback.fire('tileerror');
  f.fallback.fire('load');
  assert.ok(!f.surface.classList.has('map-surface-ready'));
  f.fallback.fire('tileload');
  f.fallback.fire('load');
  assert.ok(f.surface.classList.has('map-surface-ready'));
});

test('vector initial error preserves raster; later ready events cannot remove it', async () => {
  const f = fixture({ cached: true });
  await flush();
  f.gl.fire('error');
  f.gl.fire('load');
  f.gl.fire('idle');
  assert.ok(f.layers.has(f.fallback));
  assert.ok(!f.layers.has(f.vectorLayer));
  assert.ok(f.surface.classList.has('map-surface-ready'));
});

test('style failure leaves raster usable', async () => {
  const f = fixture({ cached: true, rejectStyle: true });
  await flush();
  assert.ok(f.layers.has(f.fallback));
  assert.ok(f.surface.classList.has('map-surface-ready'));
});

test('WebGL construction failure removes the partial layer covering the fallback', async () => {
  const f = fixture({ cached: true, glFailure: true });
  await flush();
  assert.ok(f.layers.has(f.fallback));
  assert.ok(!f.layers.has(f.vectorLayer));
  assert.ok(f.surface.classList.has('map-surface-ready'));
});

test('vendored Leaflet adapter can remove a layer whose WebGL constructor failed', () => {
  const adapter = fs.readFileSync(`${__dirname}/app/src/main/assets/vendor/maplibre/leaflet-maplibre-gl.js`, 'utf8');
  const source = adapter.match(/onRemove: (function\(map\) \{[^]*?\n\t\t\})/)[1];
  const remove = vm.runInNewContext(`(${source})`);
  let removed = 0;
  const map = { options: {}, getPane: () => ({ removeChild() { removed++; } }) };
  remove.call({ _map: map, _container: {}, getPaneName: () => 'tilePane' }, map);
  assert.equal(removed, 1);
  let glRemoved = 0;
  remove.call({ _map: map, _container: {}, getPaneName: () => 'tilePane',
    _glMap: { remove() { glRemoved++; } } }, map);
  assert.equal(glRemoved, 1);
});

test('trip detail readiness cannot expose the home map loading shield', async () => {
  const f = fixture({ cached: true, hero: false });
  await flush();
  f.gl.fire('load');
  assert.ok(!f.surface.classList.has('map-surface-ready'));
});

test('removed map cannot acquire a late vector layer or expose its surface', async () => {
  const f = fixture();
  f.map.fire('unload');
  await flush();
  f.fallback.fire('tileload');
  f.fallback.fire('load');
  assert.ok(!f.layers.has(f.vectorLayer));
  assert.ok(!f.surface.classList.has('map-surface-ready'));
});

test('style fetch retries after failure, keeps shared cache and independent style objects', async () => {
  let calls = 0;
  const context = { openFreeMapNoLabelsStylePromise: null, OPENFREEMAP_DARK_STYLE_URL: 'https://example.invalid/style',
    fetch: async () => { calls++; return { ok: calls > 1, status: 503,
      json: async () => ({ layers: [{ id: 'water', type: 'fill' }, { id: 'label', type: 'symbol' }] }) }; } };
  vm.runInNewContext(body('openFreeMapNoLabelsStyle'), context);
  await assert.rejects(context.openFreeMapNoLabelsStyle());
  const [a, b] = await Promise.all([context.openFreeMapNoLabelsStyle(), context.openFreeMapNoLabelsStyle()]);
  assert.equal(calls, 2);
  assert.equal(a.layers.length, 1);
  assert.equal(a.layers[0].paint['fill-color'], 'rgb(19,21,23)');
  a.layers[0].id = 'changed';
  assert.equal(b.layers[0].id, 'water');
});

test('home creates no tiles before coordinates and uses the vehicle position on its first request', () => {
  let maps = 0;
  const centers = [];
  const context = { heroLeafletMap: null, latestVehicleLocation: null, heroMapZoom: 15,
    heroLeafletElement: () => ({}), heroMapElement: () => ({ classList: { remove() {} } }),
    L: { map: () => { maps++; return { on() {}, setView: () => assert.fail('wrong initial view') }; },
      latLng: (lat, lon) => ({ lat, lon }) },
    setHeroVehicleView: (map, point) => centers.push(point), addNoLabelDarkBaseMap() { assert.equal(centers.length, 1); },
    isHeroMapFocused: () => false, setHeroLeafletInteraction() {}, syncHeroVehicleOverlay() {} };
  vm.runInNewContext(body('ensureHeroLeafletMap'), context);
  context.ensureHeroLeafletMap();
  assert.equal(maps, 0);
  context.latestVehicleLocation = { lat: 37.5665, lon: 126.978 };
  const first = context.ensureHeroLeafletMap();
  assert.deepEqual(centers, [{ lat: 37.5665, lon: 126.978 }]);
  assert.equal(context.ensureHeroLeafletMap(), first);
  assert.equal(maps, 1);
});
