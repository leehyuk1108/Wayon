(function (root, factory) {
    const api = factory();
    if (typeof module === 'object' && module.exports) module.exports = api;
    else root.ParkingInspection = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
    'use strict';

    const CONFIDENCE = Object.freeze({
        baseline: '\uae30\ubcf8 \ud310\ub3c5', corroborated: '\uc7ac\ud655\uc778', additional: '\ucd94\uac00 \ud310\ub3c5',
        conflict: '\ud310\ub3c5 \ubd88\uc77c\uce58', uncertain: '\ud655\uc778 \ud544\uc694',
    });
    const KINDS = Object.freeze({ floor: '\uce35', zone: '\uad6c\uc5ed', pillar: '\uae30\ub465', bay: '\uc8fc\ucc28\uba74 \ud45c\uc9c0', unknown: '\ud45c\uc9c0' });
    const FEATURES = Object.freeze({ door: '\ubb38', shutter: '\uc154\ud130', vent: '\ud658\uae30\uad6c', fence: '\uc6b8\ud0c0\ub9ac',
        stairs: '\uacc4\ub2e8', pipe: '\ubc30\uad00', parking_line: '\uc8fc\ucc28\uc120' });
    const INSPECTION_STATUS = Object.freeze({ pending: '\ucd94\uac00 \ud655\uc778 \uc911', failed: '\ucd94\uac00 \ud655\uc778 \uc2e4\ud328', skipped: '\ucd94\uac00 \ud655\uc778 \uc0dd\ub7b5' });
    const own = (object, key) => typeof key === 'string' && Object.prototype.hasOwnProperty.call(object, key);
    const record = value => value !== null && typeof value === 'object' && !Array.isArray(value);
    const list = (value, max) => Array.isArray(value) ? value.slice(0, max) : [];
    const text = (value, max) => typeof value === 'string'
        ? Array.from(value.replace(/[\u0000-\u001f\u007f-\u009f\u200b-\u200f\u202a-\u202e\u2060-\u206f]/g, '').trim()).slice(0, max).join('') : '';

    function evidenceLabel(evidence, frames) {
        const phases = new Set();
        const items = list(evidence, 12);
        for (const item of items) {
            const frame = record(item) && Number.isInteger(item.frameIndex) && item.frameIndex >= 0 && item.frameIndex < 12
                ? frames[item.frameIndex] : null;
            const box = item?.box;
            if (!record(frame) || !['road', 'wide'].includes(frame.camera) || !['approach', 'parked'].includes(frame.phase)
                || !Array.isArray(box) || box.length !== 4 || !box.every(n => typeof n === 'number' && Number.isFinite(n) && n >= 0 && n <= 1)
                || box[0] >= box[2] || box[1] >= box[3]) return '\ucd2c\uc601 \uc2dc\uc810 \ud655\uc778 \ud544\uc694';
            phases.add(frame.phase);
        }
        if (phases.size === 2) return '\uc811\uadfc \uc911\u00b7\uc8fc\ucc28 \uc2dc \uc0ac\uc9c4';
        if (phases.has('approach')) return '\uc811\uadfc \uc911 \uc0ac\uc9c4';
        if (phases.has('parked')) return '\uc8fc\ucc28 \uc2dc \uc0ac\uc9c4';
        return '\ucd2c\uc601 \uc2dc\uc810 \ud655\uc778 \ud544\uc694';
    }

    function observationTime(value, now, label = '\uad00\uce21', invalid = '\uad00\uce21 \uc2dc\uac01 \ud655\uc778 \ud544\uc694') {
        if (typeof value !== 'string' || value.length > 40 || !/T.*(?:Z|[+-]\d{2}:\d{2})$/.test(value)) return invalid;
        const time = Date.parse(value);
        if (!Number.isFinite(time) || time > now + 120000) return invalid;
        const date = new Intl.DateTimeFormat('ko-KR', {
            timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
        }).format(new Date(time));
        const minutes = Math.max(0, Math.floor((now - time) / 60000));
        const age = minutes < 1 ? '1\ubd84 \ubbf8\ub9cc \uc804' : minutes < 60 ? `${minutes}\ubd84 \uc804`
            : minutes < 1440 ? `${Math.floor(minutes / 60)}\uc2dc\uac04 \uc804` : `${Math.floor(minutes / 1440)}\uc77c \uc804`;
        return `${label} ${date} KST \u00b7 ${age}`;
    }

    function resultUpdateTime(value, now) {
        if (typeof value !== 'string' || value.length > 40
            || !/^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$/.test(value)) return '';
        const calendar = Date.parse(value.slice(0, 10) + 'T00:00:00Z');
        if (!Number.isFinite(calendar) || new Date(calendar).toISOString().slice(0, 10) !== value.slice(0, 10)) return '';
        return observationTime(value, now, '\uacb0\uacfc \uac31\uc2e0', '');
    }

    // The first reliable sign's best evidence: a parked-phase exterior frame (latest first) and its normalized box,
    // so the app can show that exact photo with the sign outlined. Null when no frame/box passes validation.
    function focusFor(reading, frames, label) {
        let best = null;
        for (const evidence of list(reading.evidence, 12)) {
            if (!record(evidence) || !Number.isInteger(evidence.frameIndex) || !Array.isArray(evidence.box) || evidence.box.length !== 4) continue;
            const frame = frames[evidence.frameIndex];
            const box = evidence.box;
            if (!record(frame) || !['wide', 'road'].includes(frame.camera)) continue;
            if (!box.every(v => typeof v === 'number' && Number.isFinite(v) && v >= 0 && v <= 1) || !(box[0] < box[2] && box[1] < box[3])) continue;
            const captured = Date.parse(frame.capturedAt || '');
            if (!Number.isFinite(captured)) continue;
            const rank = [frame.phase === 'parked' ? 1 : 0, captured];
            if (best && (best.rank[0] > rank[0] || (best.rank[0] === rank[0] && best.rank[1] >= rank[1]))) continue;
            best = { rank, focus: { label, capturedAt: new Date(captured).toISOString(), camera: frame.camera,
                phase: frame.phase === 'parked' || frame.phase === 'approach' ? frame.phase : '', box: box.slice() } };
        }
        return best ? best.focus : null;
    }

    // 서버가 사진 전체를 두 번 따로 보고 같은 답을 낸 칸만 온다(나머지는 unknown).
    const PLACE = Object.freeze({
        setting: { indoor: '실내', outdoor: '야외' },
        level: { underground: '지하', ground: '지상', upper: '위층' },
        area: { parking_structure: '주차장', parking_lot: '주차장', street: '길가' },
    });

    // 예: 지하 주차장, 야외 주차장, 지상 실내 주차장, 길가 주차, 실내 주차. 모두 모르면 빈 문자열.
    function describePlace(place) {
        if (!record(place)) return '';
        const pick = key => own(PLACE[key], place[key]) ? place[key] : '';
        const setting = pick('setting'), level = pick('level'), area = pick('area');
        if (area === 'street') return '길가 주차';
        const parts = [];
        if (level && !(level === 'ground' && setting === 'outdoor')) parts.push(PLACE.level[level]);
        if (setting && level !== 'underground') parts.push(PLACE.setting[setting]);
        if (area) parts.push(PLACE.area[area]);
        else if (parts.length) parts.push('주차');
        return parts.join(' ');
    }

    function viewModel(payload, now = Date.now()) {
        if (!record(payload) || payload.ok !== true || !Object.prototype.hasOwnProperty.call(payload, 'observation')) throw new Error('invalid_response');
        if (payload.observation === null) return { phase: 'empty', message: '\uc800\uc7a5\ub41c \uc8fc\ucc28 \uc0ac\uc9c4 \ub2e8\uc11c\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.' };
        const observation = payload.observation;
        if (!record(observation)) throw new Error('invalid_observation');
        const result = record(observation.result) ? observation.result : {};
        const frames = list(result.frames, 12);
        const inspection = record(result.inspection) && result.inspection.version === 1 ? result.inspection : null;
        // A completed inspection already contains the fused baseline and new readings.
        const completed = inspection?.status === 'completed' && Array.isArray(inspection.readings);
        const readings = list(completed ? inspection.readings : result.analysis?.readings, completed ? 32 : 16);
        const known = [], uncertain = [], knownReadings = [];
        for (const reading of readings) {
            if (!record(reading) || !own(KINDS, reading.kind) || !['readable', 'ambiguous'].includes(reading.status)) continue;
            const value = text(reading.text, 32);
            const confidence = completed && own(CONFIDENCE, reading.confidence) ? reading.confidence
                : !completed && reading.status === 'readable' ? 'baseline' : 'uncertain';
            const reliable = reading.status === 'readable' && value && !['conflict', 'uncertain'].includes(confidence);
            const alternatives = list(reading.alternatives, 4).map(value => text(value, 32)).filter(Boolean);
            // 글자도 후보도 없는 '판독 불명'은 위치를 알려 주지 못하므로 목록에서 뺀다(길가 간판마다 하나씩 생긴다).
            if (!value && !alternatives.length) continue;
            const item = { label: KINDS[reading.kind], value: value || '\ud310\ub3c5 \ubd88\uba85',
                confidence, badge: CONFIDENCE[confidence], evidence: evidenceLabel(reading.evidence, frames),
                alternatives: alternatives.length ? `\ud6c4\ubcf4: ${alternatives.join(' / ')}` : '' };
            if (reliable) knownReadings.push({ item, reading });
            else uncertain.push(item);
        }
        // 제목과 사진 상자는 첫 표지를 쓴다. 용도 모를 숫자만 있는 글자(간판 전화번호 등)는 위치를 말해 주지
        // 못하므로 글자가 있는 표지 뒤로 보낸다(안정 정렬이라 나머지 순서는 그대로).
        const digitsOnly = ({ item }) => item.label === KINDS.unknown && !/\p{L}/u.test(item.value);
        knownReadings.sort((a, b) => digitsOnly(a) - digitsOnly(b));
        known.push(...knownReadings.map(entry => entry.item));
        const top = knownReadings[0];
        const focus = top ? focusFor(top.reading, frames, `${top.item.label} ${top.item.value}`) : null;
        const placeLabel = completed ? describePlace(inspection.place) : '';
        const surroundings = completed ? list(inspection.surroundings, 3).filter(item => record(item) && own(FEATURES, item.type))
            .map(item => ({ value: text(item.label, 96) || FEATURES[item.type], evidence: evidenceLabel(item.evidence, frames) })) : [];
        const coverage = completed && record(inspection.coverage) ? inspection.coverage : {};
        const count = value => Number.isInteger(value) && value >= 0 && value <= 10000;
        const coverageParts = [];
        if (count(coverage.overviewViews) && count(coverage.overviewExpected)) coverageParts.push(`\uc804\uccb4 \uc0ac\uc9c4 \uac80\ud1a0 ${coverage.overviewViews}/${coverage.overviewExpected}`);
        if (count(coverage.targetsInspected) && count(coverage.targetsRequested)) coverageParts.push(`\ud45c\uc9c0 \uac80\ud1a0 ${coverage.targetsInspected}/${coverage.targetsRequested}`);
        const status = own(INSPECTION_STATUS, inspection?.status) ? INSPECTION_STATUS[inspection.status]
            : ['queued', 'running', 'pending'].includes(observation.status) ? '\uc0ac\uc9c4 \ud310\ub3c5 \uc911'
                : observation.status === 'failed' ? '\uc0ac\uc9c4 \ud310\ub3c5 \uc2e4\ud328' : '';
        return { phase: 'ready', time: observationTime(observation.parkedAt, now), updatedTime: resultUpdateTime(payload.generatedAt, now), status,
            known, uncertain, surroundings, focus, placeLabel, coverage: coverageParts.join(' \u00b7 '),
            disclaimer: 'AI \uc0ac\uc9c4 \ub2e8\uc11c \u00b7 \uc0ac\ub78c \ud655\uc778 \uc804 \u00b7 \uc815\ud655\ud55c \uc8fc\ucc28\uba74\uc740 \ud655\uc778\ub418\uc9c0 \uc54a\uc558\uc2b5\ub2c8\ub2e4.' };
    }

    function render(target, model) {
        if (!target) return;
        const document = target.ownerDocument;
        const fragment = document.createDocumentFragment();
        function append(parent, tag, className, value) {
            const element = document.createElement(tag);
            element.className = className;
            element.textContent = value;
            parent.appendChild(element);
            return element;
        }
        if (model.phase !== 'ready') {
            append(fragment, 'p', 'parking-inspection-meta', model.message || '\uc8fc\ucc28 \uc0ac\uc9c4 \ub2e8\uc11c \ub300\uae30 \uc911');
        } else {
            append(fragment, 'p', 'parking-inspection-meta', model.time);
            if (model.updatedTime) append(fragment, 'p', 'parking-inspection-meta', model.updatedTime);
            if (model.status) append(fragment, 'p', 'parking-inspection-meta', model.status);
            if (model.placeLabel) {
                append(fragment, 'h6', 'parking-inspection-heading', '주차 환경');
                const place = append(append(fragment, 'ul', 'parking-inspection-list', ''), 'li', 'parking-inspection-item', '');
                append(append(place, 'div', 'parking-inspection-line', ''), 'span', 'parking-inspection-value', model.placeLabel);
                append(place, 'span', 'parking-inspection-meta', 'AI 추정 · 사진 전체 판단 두 번 일치');
            }
            for (const [heading, items, collapsed] of [['\uc77d\uc740 \ud45c\uc9c0', model.known],
                ['\uc8fc\ubcc0 \ud658\uacbd \ud6c4\ubcf4', model.surroundings], ['\ud655\uc778 \ud544\uc694', model.uncertain, true]]) {
                if (!items.length) continue;
                const parent = collapsed ? append(fragment, 'details', 'parking-inspection-uncertain', '') : fragment;
                append(parent, collapsed ? 'summary' : 'h6', collapsed ? 'parking-inspection-summary' : 'parking-inspection-heading',
                    collapsed ? `${heading} ${items.length}\uac74` : heading);
                const list = append(parent, 'ul', 'parking-inspection-list', '');
                for (const item of items) {
                    const row = append(list, 'li', 'parking-inspection-item', '');
                    const line = append(row, 'div', 'parking-inspection-line', '');
                    append(line, 'span', 'parking-inspection-value', item.label ? `${item.label} ${item.value}` : item.value);
                    if (item.badge) append(line, 'span', `parking-inspection-badge ${item.confidence}`, item.badge);
                    if (item.alternatives) append(row, 'span', 'parking-inspection-meta', item.alternatives);
                    append(row, 'span', 'parking-inspection-meta', item.evidence);
                }
            }
            if (!model.known.length && !model.uncertain.length && !model.surroundings.length && !model.placeLabel) append(fragment, 'p', 'parking-inspection-meta', '\ud655\uc778\ub41c \uc0ac\uc9c4 \ub2e8\uc11c\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.');
            if (model.coverage) append(fragment, 'p', 'parking-inspection-meta', model.coverage + ' \u00b7 \uc804\uccb4 \uc7a5\uba74 \ud655\uc778 \ubcf4\uc7a5 \uc5c6\uc74c');
            append(fragment, 'p', 'parking-inspection-meta parking-inspection-disclaimer', model.disclaimer);
        }
        target.replaceChildren(fragment);
    }

    function createController(options) {
        let generation = 0, token = '', account = null, opened = false, active = null;
        const schedule = options.setTimeout || setTimeout;
        const cancelTimer = options.clearTimeout || clearTimeout;
        const emit = options.onChange;
        function clear() {
            generation++;
            opened = false;
            const previous = active;
            active = null;
            previous?.controller.abort();
            previous?.cancel();
            emit({ phase: 'idle', message: '\uc8fc\ucc28 \uc0ac\uc9c4 \ub2e8\uc11c \ub300\uae30 \uc911' });
        }
        function setToken(value) {
            const next = typeof value === 'string' ? value.trim() : '';
            if (next !== token) { token = next; clear(); }
        }
        function setAccount(loggedIn, email) {
            const next = JSON.stringify([!!loggedIn, typeof email === 'string' ? email.trim().toLowerCase() : '']);
            if (next !== account) { account = next; clear(); }
        }
        function load(manual) {
            setToken(options.getToken());
            if (!token) { emit({ phase: 'idle', message: '\ud074\ub77c\uc6b0\ub4dc \uc5f0\uacb0 \ud544\uc694' }); return Promise.resolve(false); }
            if (active) return active.promise;
            if (opened && !manual) return Promise.resolve(false);
            opened = true;
            const id = generation, requestToken = token;
            const controller = new AbortController();
            const ticket = { controller };
            active = ticket;
            const cancelled = new Promise((_, reject) => { ticket.cancel = () => reject(new Error('cancelled')); });
            const deadline = new Promise((_, reject) => {
                ticket.timer = schedule(() => { controller.abort(); reject(new Error('timeout')); }, 12000);
            });
            emit({ phase: 'loading', message: '\uc0ac\uc9c4 \ub2e8\uc11c \ubd88\ub7ec\uc624\ub294 \uc911' });
            const read = async () => {
                const response = await options.request(options.endpoint, {
                    method: 'GET', headers: { Authorization: `Bearer ${requestToken}` }, cache: 'no-store', redirect: 'error',
                    signal: controller.signal,
                });
                if (!response.ok) throw new Error('request_failed');
                return viewModel(await response.json(), (options.now || Date.now)());
            };
            ticket.promise = Promise.race([read(), cancelled, deadline]).then(model => {
                if (generation !== id) return false;
                if (String(options.getToken() || '').trim() !== requestToken) { setToken(options.getToken()); return false; }
                emit(model);
                return true;
            }).catch(() => {
                if (generation === id && String(options.getToken() || '').trim() !== requestToken) { setToken(options.getToken()); return false; }
                if (generation === id) emit({ phase: 'error', message: '\uc0ac\uc9c4 \ub2e8\uc11c\ub97c \ubd88\ub7ec\uc624\uc9c0 \ubabb\ud588\uc2b5\ub2c8\ub2e4.' });
                return false;
            }).finally(() => {
                cancelTimer(ticket.timer);
                if (active === ticket) active = null;
            });
            return ticket.promise;
        }
        emit({ phase: 'idle', message: '\uc8fc\ucc28 \uc0ac\uc9c4 \ub2e8\uc11c \ub300\uae30 \uc911' });
        return { open: () => load(false), refresh: () => load(true), clear, setToken, setAccount };
    }

    return { viewModel, render, createController };
});
