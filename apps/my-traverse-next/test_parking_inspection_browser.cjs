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
        const clueCard = page.locator('#parking-inspection-card');
        assert.equal(await clueCard.getAttribute('aria-expanded'), 'false', 'clues start folded behind the rail card');
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
