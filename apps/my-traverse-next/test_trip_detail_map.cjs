const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, 'app/src/main/assets/main.html'), 'utf8');
const pick = name => {
    const match = html.match(new RegExp(`\\n        (?:async )?function ${name}\\([^)]*\\) \\{[\\s\\S]*?\\n        \\}\\n`));
    assert.ok(match, `actual source of ${name}`);
    return match[0];
};

// The actual renderTripDetail with its map helpers, against a minimal Leaflet/DOM stand-in whose
// animation frames run only when flushed, as in the WebView.
function harness() {
    const frames = [];
    const layers = new Set();
    const element = () => ({ textContent: '', innerHTML: '', style: {}, scrollTop: 0,
        classList: { add() {}, toggle() {}, contains: () => true }, setAttribute() {} });
    const elements = {};
    const layer = kind => ({ kind, addTo() { layers.add(this); return this; }, remove() { layers.delete(this); } });
    const map = { invalidateSize() {}, setView() {} };
    const context = {
        console, Number, Math, Array, Object, String, Date, Set, Map,
        document: { getElementById: id => (elements[id] ??= element()) },
        tripDetailOverlay: element(), btnTripDetailRecenter: element(),
        requestAnimationFrame: callback => frames.push(callback),
        L: { polyline: () => layer('line'), marker: (latLng, options) => ({ ...layer(options.icon), latLng }),
            latLngBounds: coords => ({ coords }) },
        ensureTripDetailMap: () => map, tripDetailMarkerIcon: kind => kind,
        addTripMomentMarkers() {}, restoreTripDetailInitialView() {}, settleTripDetailMapView() {},
        renderDriveReport() {}, simplifyTripAddress: value => String(value || ''), escapeHtml: value => String(value),
        formatTripTimeRange: () => '', speedRouteColor: () => '#fff', segmentSpeedKmh: () => 10,
        hasWayonCloudKey: () => true,
    };
    vm.createContext(context);
    vm.runInContext(['let tripDetailRouteLayers = [], tripDetailStartMarker = null, tripDetailEndMarker = null;',
        'let tripDetailMomentMarkers = [], tripDetailInitialView = null, tripDetailRenderToken = 0;',
        ...['clearTripDetailMap', 'routePointCount', 'extractTripPoint', 'extractTripRoutePoint', 'tripRoutePoints',
            'speedRange', 'renderTripDetail'].map(pick),
        'this.renderTripDetail = renderTripDetail;'].join('\n'), context);
    return {
        render: item => context.renderTripDetail(item),
        flush: () => { while (frames.length) frames.shift()(); },
        lines: () => [...layers].filter(item => item.kind === 'line').length,
        markers: () => [...layers].filter(item => item.kind !== 'line').map(item => [item.kind, item.latLng.join(',')]),
    };
}

const point = (lat, lon) => ({ latitude: lat, longitude: lon, speedMps: 20 });
// 2026-11-08 19:09: the list item has only Gunsan/Incheon coordinates; the detail has the route.
const listItem = { id: 'trip-1f6', startLatitude: 36.02, startLongitude: 126.8, endLatitude: 37.54, endLongitude: 126.65,
    route: [], routePointCount: 720 };
const detailItem = { ...listItem, route: [point(36.02, 126.8), point(36.6, 126.5), point(37.54, 126.65)], reportDetailLoaded: true };

test('a cached detail drawn in the same frame leaves no straight start-to-end line or stray markers', () => {
    const h = harness();
    h.render({ id: 'trip-1f4', startLatitude: 35.16, startLongitude: 128.19, endLatitude: 36.01, endLongitude: 126.8,
        route: [point(35.16, 128.19), point(36.01, 126.8)], reportDetailLoaded: true });
    h.flush();
    h.render(listItem);
    h.render(detailItem);
    h.flush();
    assert.equal(h.lines(), 2, 'only the two route segments');
    assert.deepEqual(h.markers(), [['start', '36.02,126.8'], ['end', '37.54,126.65']], 'no marker of the earlier trip remains');
});

test('while the route is loading only the start and end markers are shown', () => {
    const h = harness();
    h.render(listItem);
    h.flush();
    assert.equal(h.lines(), 0);
    assert.equal(h.markers().length, 2);
    h.render(detailItem);
    h.flush();
    assert.equal(h.lines(), 2);
});

test('a trip with no cloud route to load still connects its start and end', () => {
    const h = harness();
    h.render({ startLatitude: 37.5, startLongitude: 126.7, endLatitude: 37.6, endLongitude: 126.8, route: [] });
    h.flush();
    assert.equal(h.lines(), 1);
});

test('the trip detail shows stored vehicle speeds before GPS-point speeds', async () => {
    const context = { Number, Math, Array, JSON, Map, console, tripDetailCache: new Map(),
        WAYON_CLOUD_TRIPS_URL: 'https://cloud.test/api/trips', hasWayonCloudKey: () => true, getWayonCloudViewToken: () => 'key',
        encodeURIComponent };
    let reply;
    context.fetch = async () => ({ ok: true, json: async () => reply });
    vm.createContext(context);
    vm.runInContext([...['normalizeTripRoute', 'routeMaxSpeedText', 'fetchWayonTripDetail'].map(pick),
        'this.fetchWayonTripDetail = fetchWayonTripDetail;'].join('\n'), context);
    const route = [{ latitude: 37.5, longitude: 126.6, speedMps: 31.2 }, { latitude: 37.6, longitude: 126.7, speedMps: 10 }];
    // 2026-11-10 23:11: route points stop in tunnels (112 km/h); the vehicle peaked near 149 km/h.
    reply = { id: 'new', route, vehicle_max_speed_mps: 41.28, vehicle_avg_speed_mps: 5120 / 915 };
    const fresh = await context.fetchWayonTripDetail({ id: 'new', topSpeed: '112 km/h', avgSpeed: '20 km/h' });
    assert.equal(fresh.topSpeed, '149 km/h');
    assert.equal(fresh.avgSpeed, '20 km/h');
    // Trips saved before the change carry no vehicle speeds and keep the route-based maximum.
    reply = { id: 'old', route };
    const old = await context.fetchWayonTripDetail({ id: 'old', topSpeed: '-- km/h', avgSpeed: '18 km/h' });
    assert.equal(old.topSpeed, '112 km/h');
    assert.equal(old.avgSpeed, '18 km/h');
});
