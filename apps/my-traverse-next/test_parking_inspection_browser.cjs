const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

test('offline Chromium: native disclosure, separate timestamps, candidate labels and layout at four widths', {
    skip: !process.env.PARKING_PLAYWRIGHT_MODULE,
}, async () => {
    const {chromium} = require(process.env.PARKING_PLAYWRIGHT_MODULE);
    const browser = await chromium.launch({headless: true, executablePath: process.env.PARKING_BROWSER_EXECUTABLE,
        args: ['--disable-background-networking', '--disable-component-update', '--disable-sync', '--no-first-run']});
    try {
        const context = await browser.newContext({offline: true, serviceWorkers: 'block'});
        await context.route('**/*', route => route.abort());
        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        const assets = path.join(__dirname, 'app/src/main/assets');
        const source = fs.readFileSync(path.join(assets, 'main.html'), 'utf8');
        const html = source.replace(/<script\b[^>]*>[^]*?<\/script>/g, '').replace(/<link\b[^>]*>/g, '');
        await page.setContent(html);
        await page.addScriptTag({content: fs.readFileSync(path.join(assets, 'parking-inspection.js'), 'utf8')});
        await page.addScriptTag({content: fs.readFileSync(path.join(assets, 'vendor/lucide.min.js'), 'utf8')});
        await page.evaluate(() => {
            document.querySelectorAll('.tab-panel').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-extras').classList.add('active');
            const evidence = [{frameIndex: 0, box: [0, 0, 0.2, 0.2]}, {frameIndex: 1, box: [0, 0, 0.2, 0.2]}];
            const reading = {kind: 'pillar', text: 'W'.repeat(32), status: 'readable', alternatives: [], evidence};
            const inspection = {version: 1, status: 'completed', readings: [
                ...['baseline', 'corroborated', 'additional'].map(confidence => ({...reading, confidence})),
                ...Array.from({length: 29}, (_, index) => ({...reading, status: 'ambiguous', text: null,
                    confidence: index % 2 ? 'uncertain' : 'conflict', alternatives: ['W'.repeat(32), '<script>alert(1)</script>']}))],
                surroundings: [{type: 'vent', label: '<img src=x onerror=alert(1)>' + 'W'.repeat(70), color: 'gray', evidence}],
                coverage: {overviewViews: 12, overviewExpected: 12, targetsRequested: 24, targetsInspected: 12, completeSceneGuaranteed: false}};
            window.parkingTestNow = Date.parse('2026-11-04T05:00:00Z');
            window.parkingTestPayload = {ok: true, generatedAt: '2026-11-04T04:58:00Z',
                observation: {parkedAt: '2026-11-02T01:00:00Z', status: 'completed',
                    result: {analysis: {readings: []}, frames: [{camera: 'wide', phase: 'approach'}, {camera: 'wide', phase: 'parked'}], inspection}}};
            const model = ParkingInspection.viewModel(window.parkingTestPayload, window.parkingTestNow);
            ParkingInspection.render(document.getElementById('parking-inspection-content'), model);
            lucide.createIcons();
        });
        const content = page.locator('#parking-inspection-content');
        const details = content.locator('details');
        const summary = details.locator('summary');
        const cardHandler = source.match(/wayonSnapshotCard\?\.addEventListener\('click',[\s\S]*?\n        \}\);/);
        assert.ok(cardHandler, 'exercise the actual gallery card click handler');
        const clueCardHandler = source.match(/const parkingInspectionCard = [\s\S]*?\n        \}\);/);
        assert.ok(clueCardHandler, 'exercise the actual clue card toggle');
        await page.addScriptTag({content: `
            const wayonSnapshotCard = document.getElementById('wayon-snapshot-card');
            window.parkingSnapshotOpenCount = 0;
            window.parkingRefreshCount = 0;
            function openSnapshotViewerLatest() { window.parkingSnapshotOpenCount++; }
            ${cardHandler[0]}
            ${clueCardHandler[0]}
            document.getElementById('parking-inspection-refresh').addEventListener('click', () => window.parkingRefreshCount++);
        `});
        // The extras tab folds the clues into one row; the row shows a one-line brief.
        const briefSource = source.match(/function parkingInspectionBrief\(model\) \{[\s\S]*?\n        \}/);
        assert.ok(briefSource, 'exercise the actual folded-row brief');
        assert.equal(await page.evaluate(src => new Function(`${src}; return parkingInspectionBrief;`)()(
            ParkingInspection.viewModel(window.parkingTestPayload, window.parkingTestNow)), briefSource[0]),
            `기둥 ${'W'.repeat(32)} · 외 2개 · 확인 필요 29건`);
        // The parked photo's caption carries the clues: spot as the title, note underneath.
        const noteSource = source.match(/function parkingInspectionNote\(model\) \{[\s\S]*?\n        \}/);
        const captionSource = source.match(/function renderParkingInspectionCaption\(model\) \{[\s\S]*?\n        \}/);
        assert.ok(noteSource && captionSource, 'exercise the actual photo caption');
        const clueCard = page.locator('#parking-inspection-card');
        await clueCard.click();
        assert.equal(await page.evaluate(() => window.parkingSnapshotOpenCount), 1, 'without clues the caption opens the photo');
        assert.equal(await clueCard.getAttribute('aria-expanded'), 'false');
        await page.evaluate(src => new Function(`${src}; return renderParkingInspectionCaption;`)()(
            ParkingInspection.viewModel(window.parkingTestPayload, window.parkingTestNow)),
            [briefSource[0], noteSource[0], captionSource[0]].join('\n'));
        assert.equal(await page.locator('#wayon-snapshot-card.has-ai').count(), 1);
        assert.equal(await page.locator('#parking-inspection-spot').textContent(), `기둥 ${'W'.repeat(32)} 부근`);
        assert.equal(await page.locator('#parking-inspection-brief').textContent(), 'AI 추정 · 외 2개 · 확인 필요 29건');
        await page.evaluate(() => { window.parkingSnapshotOpenCount = 0; });
        assert.equal(await clueCard.getAttribute('aria-expanded'), 'false', 'clues start folded under the photo caption');
        assert.equal(await content.isVisible(), false);
        await clueCard.click();
        assert.equal(await clueCard.getAttribute('aria-expanded'), 'true');
        assert.equal(await content.isVisible(), true);
        assert.equal(await page.evaluate(() => window.parkingSnapshotOpenCount), 0, 'opening the clue card must not open a photo');
        await summary.click();
        assert.notEqual(await details.getAttribute('open'), null);
        assert.equal(await page.evaluate(() => window.parkingSnapshotOpenCount), 0, 'disclosure must not open a photo');
        await summary.click();
        await page.locator('#parking-inspection-refresh').click();
        assert.equal(await page.evaluate(() => window.parkingRefreshCount), 1);
        assert.equal(await page.evaluate(() => window.parkingSnapshotOpenCount), 0, 'refresh must not open a photo');
        await page.locator('#wayon-snapshot-card .snapshot-card-title h4').click();
        assert.equal(await page.evaluate(() => window.parkingSnapshotOpenCount), 1, 'existing card photo opening remains');
        assert.equal(await summary.textContent(), '\ud655\uc778 \ud544\uc694 29\uac74');
        assert.equal(await details.locator('li').count(), 29);
        assert.deepEqual(await content.locator(':scope > h6').allTextContents(),
            ['\uc77d\uc740 \ud45c\uc9c0', '\uc8fc\ubcc0 \ud658\uacbd \ud6c4\ubcf4']);
        const timestamps = await content.locator(':scope > p').allTextContents();
        assert.match(timestamps[0], /^\uad00\uce21 .*2026.*11.*02.*2\uc77c \uc804$/);
        assert.match(timestamps[1], /^\uacb0\uacfc \uac31\uc2e0 .*2026.*11.*04.*2\ubd84 \uc804$/);
        assert.match(await content.locator('.parking-inspection-disclaimer').textContent(), /AI.*\uc0ac\ub78c \ud655\uc778 \uc804/);
        // No sign read: the AI-judged place titles the photo; with nothing at all the old prompt stays.
        const captionSources = [briefSource[0], noteSource[0], captionSource[0]].join('\n');
        await page.evaluate(src => new Function(`${src}; return renderParkingInspectionCaption;`)()(
            {phase: 'ready', known: [], uncertain: [], surroundings: [], placeLabel: '\uc9c0\ud558 \uc8fc\ucc28\uc7a5'}), captionSources);
        assert.equal(await page.locator('#parking-inspection-spot').textContent(), '\uc9c0\ud558 \uc8fc\ucc28\uc7a5');
        assert.equal(await page.locator('#wayon-snapshot-card.has-ai').count(), 1);
        assert.equal(await page.locator('#parking-inspection-brief').textContent(), 'AI \ucd94\uc815');
        await page.evaluate(src => new Function(`${src}; return renderParkingInspectionCaption;`)()(
            {phase: 'ready', known: [], uncertain: [], surroundings: [], placeLabel: ''}), captionSources);
        assert.equal(await page.locator('#parking-inspection-spot').textContent(), '\uc8fc\ucc28 \ud45c\uc9c0 \ud655\uc778 \ud544\uc694');
        assert.equal(await page.locator('#wayon-snapshot-card.has-ai').count(), 0);
        await page.evaluate(src => new Function(`${src}; return renderParkingInspectionCaption;`)()(
            ParkingInspection.viewModel(window.parkingTestPayload, window.parkingTestNow)), captionSources);
        await clueCard.click();
        assert.equal(await clueCard.getAttribute('aria-expanded'), 'true');

        async function checkLayout(width, state) {
            await page.locator('.parking-inspection').scrollIntoViewIfNeeded();
            const dimensions = await page.locator('.parking-inspection').evaluate(section => {
                const bounds = element => { const r = element.getBoundingClientRect(); return {left: r.left, right: r.right, top: r.top, bottom: r.bottom, width: r.width, height: r.height}; };
                const parent = bounds(section);
                const visible = [...section.querySelectorAll('*')].filter(el => el.checkVisibility());
                const overflow = visible.filter(el => {
                    const r = bounds(el);
                    return r.width && (r.left < parent.left - 1 || r.right > parent.right + 1 || el.scrollWidth > el.clientWidth + 1);
                }).map(el => el.className?.baseVal ?? el.className);
                const rows = visible.filter(el => el.classList.contains('parking-inspection-item')).map(bounds);
                return {parent, overflow, rows, title: bounds(section.querySelector('h5')),
                    button: bounds(section.querySelector('button')),
                    next: bounds(section.nextElementSibling || section.parentElement.nextElementSibling),
                    summary: bounds(section.querySelector('summary')),
                    unsafe: section.querySelectorAll('#parking-inspection-content img, #parking-inspection-content script').length,
                    icon: section.querySelectorAll('button svg').length};
            });
            assert.ok(dimensions.parent.width > 100, JSON.stringify({width, dimensions}));
            assert.deepEqual(dimensions.overflow, [], `overflow at ${width}`);
            assert.ok(dimensions.title.right <= dimensions.button.left, `header overlap at ${width}`);
            assert.ok(dimensions.parent.bottom <= dimensions.next.top + 1, `next section overlap at ${width}`);
            for (let i = 1; i < dimensions.rows.length; i++) assert.ok(dimensions.rows[i - 1].bottom <= dimensions.rows[i].top + 1);
            assert.equal(dimensions.rows.length, state === 'collapsed' ? 4 : 33);
            assert.ok(dimensions.summary.height >= 44, `summary touch target at ${width}`);
            assert.equal(dimensions.unsafe, 0);
            assert.equal(dimensions.icon, 1);
            const screenshot = await page.locator('.parking-inspection').screenshot();
            assert.ok(screenshot.length > 1500, `nonempty screenshot at ${width}`);
            if (process.env.PARKING_SCREENSHOT_DIR) {
                fs.mkdirSync(process.env.PARKING_SCREENSHOT_DIR, {recursive: true});
                fs.writeFileSync(path.join(process.env.PARKING_SCREENSHOT_DIR, `parking-${width}-${state}.png`), screenshot);
            }
        }
        for (const width of [320, 390, 768, 1280]) {
            await page.setViewportSize({width, height: 900});
            assert.equal(await details.getAttribute('open'), null);
            assert.equal(await details.locator('li').first().isVisible(), false);
            assert.equal(await content.locator(':scope > ul > li').count(), 4);
            await checkLayout(width, 'collapsed');
            await summary.focus();
            await summary.press('Enter');
            assert.notEqual(await details.getAttribute('open'), null);
            assert.equal(await details.locator('li').last().isVisible(), true);
            await checkLayout(width, 'expanded');
            await summary.press('Space');
            assert.equal(await details.getAttribute('open'), null);
            await summary.click();
            assert.notEqual(await details.getAttribute('open'), null);
            await summary.click();
            assert.equal(await details.getAttribute('open'), null);
        }
        await page.evaluate(() => {
            const value = structuredClone(window.parkingTestPayload);
            const item = value.observation.result.inspection.readings.find(row => row.status === 'ambiguous');
            value.observation.result.inspection.readings = Array.from({length: 32}, () => structuredClone(item));
            ParkingInspection.render(document.getElementById('parking-inspection-content'), ParkingInspection.viewModel(value, window.parkingTestNow));
        });
        assert.equal(await summary.textContent(), '\ud655\uc778 \ud544\uc694 32\uac74');
        assert.equal(await details.locator('li').count(), 32);
        assert.equal(await details.locator('li').last().isVisible(), false);
        await summary.click();
        assert.equal(await details.locator('li').last().isVisible(), true);
        for (const generatedAt of [null, 'invalid', '2026-02-30T00:00:00Z']) {
            await page.evaluate(generatedAt => {
                const value = structuredClone(window.parkingTestPayload);
                value.generatedAt = generatedAt;
                value.observation.result.inspection.readings = [];
                ParkingInspection.render(document.getElementById('parking-inspection-content'), ParkingInspection.viewModel(value, window.parkingTestNow));
            }, generatedAt);
            assert.equal(await details.count(), 0);
            assert.match(await content.locator(':scope > p').first().textContent(), /^\uad00\uce21 /);
            assert.doesNotMatch(await content.textContent(), /\uacb0\uacfc \uac31\uc2e0/);
        }
        assert.deepEqual(errors, []);
        await context.close();
    } finally { await browser.close(); }
});

test('offline Chromium: the AI-read photo sits in the opened clues, never over the latest hero photo', {
    skip: !process.env.PARKING_PLAYWRIGHT_MODULE,
}, async () => {
    const {chromium} = require(process.env.PARKING_PLAYWRIGHT_MODULE);
    const browser = await chromium.launch({headless: true, executablePath: process.env.PARKING_BROWSER_EXECUTABLE,
        args: ['--disable-background-networking', '--disable-component-update', '--disable-sync', '--no-first-run']});
    try {
        const context = await browser.newContext({offline: true, serviceWorkers: 'block'});
        await context.route('**/*', route => route.abort());
        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        const assets = path.join(__dirname, 'app/src/main/assets');
        const source = fs.readFileSync(path.join(assets, 'main.html'), 'utf8');
        await page.setContent(source.replace(/<script\b[^>]*>[^]*?<\/script>/g, '').replace(/<link\b[^>]*>/g, ''));
        const pick = pattern => { const match = source.match(pattern); assert.ok(match, `actual source for ${pattern}`); return match[0]; };
        const functions = [
            pick(/function findParkingFocusSnapshot\(focus\) \{[\s\S]*?\n        \}/),
            pick(/function placeParkingFocusBox\(rect\) \{[\s\S]*?\n        \}/),
            pick(/function updateParkingFocus\(\) \{[\s\S]*?\n        \}/),
            pick(/document\.getElementById\('parking-focus-open'\)\?\.addEventListener\('click',[\s\S]*?\n        \}\);/),
        ];
        // The real 16:31 case: the sign was read at the top right, where the cabin picture-in-picture sits on the hero.
        await page.addScriptTag({content: `
            var parkingInspectionModel = null, parkingFocusRequestedAll = false, wayonSnapshotsLoadedAll = true;
            var wayonCloudSnapshots = [
                {camera: 'wide', kvKey: 'latest', capturedAt: '2026-11-10T07:31:00Z', capturedAtDisplay: '16:31'},
                {camera: 'wide', kvKey: 'parked', capturedAt: '2026-11-10T05:31:02.400Z', capturedAtDisplay: '14:31'},
            ];
            window.focusOpenCount = 0;
            const canvas = Object.assign(document.createElement('canvas'), {width: 1280, height: 960});
            const draw = canvas.getContext('2d');
            draw.fillStyle = '#556'; draw.fillRect(0, 0, 1280, 960);
            draw.fillStyle = '#fc0'; draw.fillRect(0.72 * 1280, 0.04 * 960, 0.12 * 1280, 0.08 * 960);
            window.focusImageUrl = canvas.toDataURL('image/png');
            function hasWayonCloudKey() { return true; }
            function loadAllWayonSnapshots() { window.loadAllCount = (window.loadAllCount || 0) + 1; }
            function snapshotCameraLabel(snapshot) { return snapshot.camera === 'wide' ? '전방' : snapshot.camera; }
            function loadWayonSnapshotImage(img) { img.src = window.focusImageUrl; }
            function openParkingFocusSnapshot() { window.focusOpenCount++; }
            ${functions.join('\n')}
        `});
        await page.evaluate(() => {
            document.querySelectorAll('.tab-panel').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-extras').classList.add('active');
            document.getElementById('parking-inspection-panel').hidden = false;
            parkingInspectionModel = {phase: 'ready', focus: {label: "표지 AMBER'S ENGLISH", capturedAt: '2026-11-10T05:31:02Z',
                camera: 'wide', phase: 'parked', box: [0.72, 0.04, 0.84, 0.12]}};
            updateParkingFocus();
        });
        const figure = page.locator('#parking-focus');
        await figure.waitFor({state: 'visible'});
        assert.equal(await page.locator('#wayon-snapshot-card #parking-focus, #wayon-snapshot-card img[alt*="AI"]').count(), 0,
            'the hero keeps the latest photo; nothing from the AI photo is layered on it');
        assert.equal(await page.locator('#parking-inspection-panel > #parking-focus').count(), 1);
        assert.equal(await page.locator('#parking-focus-caption').textContent(), 'AI가 읽은 사진 · 14:31 전방');
        assert.equal(await page.evaluate(() => window.loadAllCount || 0), 0);
        for (const width of [320, 390, 768]) {
            await page.setViewportSize({width, height: 900});
            const geometry = await page.evaluate(() => {
                const r = id => document.getElementById(id).getBoundingClientRect();
                const label = document.getElementById('parking-focus-label').getBoundingClientRect();
                return {img: r('parking-focus-img'), frame: r('parking-focus-open'), box: r('parking-focus-box'), label};
            });
            const {img, frame, box, label} = geometry;
            const near = (actual, expected, what) => assert.ok(Math.abs(actual - expected) <= 1.5, `${what} at ${width}: ${actual} vs ${expected}`);
            near(img.height, img.width * 0.75, 'photo keeps its own aspect ratio');
            near(box.left, img.left + 0.72 * img.width - 4, 'box left');
            near(box.top, img.top + 0.04 * img.height - 4, 'box top');
            near(box.width, 0.12 * img.width + 8, 'box width');
            near(box.height, 0.08 * img.height + 8, 'box height');
            for (const [name, rect] of [['box', box], ['label', label]]) {
                assert.ok(rect.left >= frame.left - 0.5 && rect.right <= frame.right + 0.5
                    && rect.top >= frame.top - 0.5 && rect.bottom <= frame.bottom + 0.5, `${name} inside the photo at ${width}`);
            }
        }
        await page.locator('#parking-focus-open').click();
        assert.equal(await page.evaluate(() => window.focusOpenCount), 1, 'tapping the AI photo opens that photo');
        await page.evaluate(() => { parkingInspectionModel = {phase: 'ready', focus: null}; updateParkingFocus(); });
        assert.equal(await figure.isVisible(), false, 'no AI focus, no photo');
        assert.deepEqual(errors, []);
        await context.close();
    } finally { await browser.close(); }
});
