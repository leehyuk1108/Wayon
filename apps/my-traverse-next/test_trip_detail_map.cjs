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
