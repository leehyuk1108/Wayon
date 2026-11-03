// Isolated mobile rendering: local assets, synthetic telemetry, and no mutation requests.
import assert from 'node:assert/strict';
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {createServer} from 'node:http';
import {resolve, extname} from 'node:path';
import {fileURLToPath} from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const output = resolve(root, 'output/playwright/iphone');
await mkdir(output, {recursive: true});
const modulePath = process.env.TRAVERSE_PLAYWRIGHT_MODULE;
assert.ok(modulePath, 'Set TRAVERSE_PLAYWRIGHT_MODULE to the installed Playwright module.');
const {webkit, chromium} = await import(modulePath);
const types = {'.html':'text/html', '.css':'text/css', '.js':'text/javascript', '.json':'application/json',
  '.png':'image/png', '.otf':'font/otf', '.woff2':'font/woff2', '.webp':'image/webp', '.svg':'image/svg+xml'};
const server = createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const file = resolve(root, 'public', '.' + (url.pathname === '/' ? '/index.html' : decodeURIComponent(url.pathname)));
  if (req.method !== 'GET' || !file.startsWith(resolve(root, 'public') + '/')) {
    res.writeHead(403).end(); return;
  }
  try { res.writeHead(200, {'content-type': types[extname(file)] || 'application/octet-stream'}).end(await readFile(file)); }
  catch { res.writeHead(404).end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const now = new Date().toISOString();
const session = {authenticated:true, csrfToken:'layout-only-fixture', capabilities:{commands:false, live:false, ambient:false}, account:{loggedIn:false}};
const feed = {vehicleStatus:{ok:true, source:'gmone', updatedAt:now, stale:false, data:{
  range:'450', battery:'12.5', battery_level:'80', mileage:'12345', fuel:'50', oil:'90', last_update:now,
  tire_pressure:'240 kPa', tire_pressure_all:'FL: 240 kPa, FR: 240 kPa, RL: 240 kPa, RR: 240 kPa',
  gmone_details:{rawStatus:{fCap:80, fLvl:62}, vehicleState:{engineRunning:false}},
}}, state:{updated_at:now, onroad:0, ignition:0, enabled:0, speed_mps:0,
  latitude:37.5665, longitude:126.978, voltage_v:'12.5', raw_json:JSON.stringify({gps:{updatedAt:now, fresh:true}, openpilot:{active:false}})},
  vehicleLock:{locked:true, occurredAt:now}, trips:[], snapshots:[]};
const sizes = [
  ['small',320,568,0,0,0], ['se',375,667,0,0,0], ['iphone',390,844,47,34,0],
  ['pro',393,852,59,34,0], ['max',430,932,59,34,0], ['max-large',440,956,62,34,0],
  ['standalone',402,874,62,34,0],
  ['landscape',844,390,0,21,47], ['se-landscape',667,375,0,0,0], ['desktop',1280,900,0,0,0],
];
const reports = [], failures = [];
let mutationRequests = 0, browser;
try {
  for (const engine of ['webkit', 'chromium']) {
    browser = await (engine === 'webkit' ? webkit : chromium).launch({headless:true,
      ...(engine === 'chromium' && process.env.TRAVERSE_BROWSER_EXECUTABLE ? {executablePath:process.env.TRAVERSE_BROWSER_EXECUTABLE} : {})});
    for (const [name,width,height,top,bottom,side] of sizes) {
      if (process.env.LAYOUT_CASE && process.env.LAYOUT_CASE !== name) continue;
      const context = await browser.newContext({viewport:{width,height}, isMobile:width < 1000, hasTouch:true, deviceScaleFactor:1, serviceWorkers:'block'});
      await context.route('**/*', async route => {
        const request = route.request(), url = new URL(request.url());
        if (request.method() !== 'GET') { mutationRequests++; await route.abort(); return; }
        if (url.origin === origin && url.pathname === '/pwa.css') {
          let css = await readFile(resolve(root,'public/pwa.css'),'utf8');
          if (name === 'standalone') {
            // Exercise the real standalone rule with WebKit's reported short-dvh defect.
            // This fixture is not an iPhone shell; physical mirroring is verified separately.
            assert.ok(css.includes('@media (display-mode: standalone)'));
            css = css.replace('@media (display-mode: standalone)', '@media all')
              .replaceAll('100dvh', `calc(100vh - ${top}px)`);
          }
          await route.fulfill({contentType:'text/css',body:css + `\n:root { --pwa-safe-top:${top}px; --pwa-safe-bottom:${bottom}px; --pwa-safe-left:${side}px; --pwa-safe-right:${side}px; }`});
          return;
        }
        if (url.origin === origin && url.pathname.startsWith('/api/')) {
          const body = url.pathname === '/api/session' ? session : url.pathname === '/api/wayon/json' ? feed : {ok:true, trips:[], snapshots:[]};
          await route.fulfill({status:200, contentType:'application/json', body:JSON.stringify(body)}); return;
        }
        if (url.origin === origin || ['tiles.openfreemap.org','server.arcgisonline.com'].includes(url.hostname)) {
          await route.continue(); return;
        }
        await route.abort();
      });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      try {
        await page.goto(origin);
        await page.waitForSelector('body[data-pwa="ready"]');
        await page.evaluate(async () => { await document.fonts.ready; });
        await page.waitForTimeout(500);
        const metrics = await page.evaluate(() => {
          const rect = s => { const r=document.querySelector(s).getBoundingClientRect(); return {x:r.x,y:r.y,w:r.width,h:r.height,b:r.bottom,r:r.right}; };
          const panel = document.querySelector('#tab-control');
          return {viewport:[innerWidth,innerHeight], overflow:document.documentElement.scrollWidth-innerWidth,
            nav:rect('.footer-nav'), map:rect('.home-map-hero'), rail:rect('.home-feature-rail'),
            main:rect('.main-content'), spacer:rect('.status-bar-padding'), panel:{h:panel.clientHeight,scroll:panel.scrollHeight},
            bodyPadding:getComputedStyle(document.body).paddingTop};
        });
        assert.equal(metrics.overflow, 0, 'horizontal page overflow');
        assert.ok(Math.abs(metrics.nav.b-height) < 1, 'nav reaches viewport bottom');
        assert.equal(metrics.nav.h,45+Math.max(8,bottom),'compact navigation retains the full home-gesture inset');
        const lastNav=await page.locator('.footer-nav .nav-item').first().boundingBox();
        assert.ok(height-lastNav.y-lastNav.height>=bottom,'navigation targets stay above the home indicator');
        assert.equal(metrics.spacer.h, top, 'one top inset');
        assert.equal(metrics.bodyPadding, '0px');
        const compact = await page.evaluate(() => {
          const el=s=>document.querySelector(s);
          return {title:parseFloat(getComputedStyle(el('.home-status-title')).fontSize),
            command:el('.home-command-bar').getBoundingClientRect().height,
            card:el('.home-feature-card').getBoundingClientRect().width};
        });
        assert.equal(compact.title,42,'compact title does not scale with viewport width');
        assert.equal(compact.command,60,'compact dock keeps usable touch targets');
        assert.equal(compact.card,160,'compact service cards');
        assert.ok(metrics.map.h >= 220, 'usable minimum map');
        assert.ok(metrics.main.x >= side && metrics.main.r <= width-side, 'landscape safe margins');
        const alignment = await page.evaluate(() => {
          const left=s=>document.querySelector(s).getBoundingClientRect().left;
          const settings=document.querySelector('#btnSecretSettings').getBoundingClientRect();
          const hero=document.querySelector('.home-map-hero').getBoundingClientRect();
          const status=document.querySelector('.home-status-button').getBoundingClientRect();
          const badge=document.querySelector('.home-status-kicker').getBoundingClientRect();
          return {fuel:left('.home-fuel-track'), command:left('.home-command-bar'), heading:left('.home-feature-heading strong'),
            settingsRight:hero.right-settings.right, settingsTop:settings.top-hero.top, statusTop:status.top-hero.top,
            headerGap:settings.left-status.right, headerCenters:Math.abs(badge.top+badge.height/2-settings.top-settings.height/2)};
        });
        assert.ok(Math.abs(alignment.fuel-alignment.command)<1 && Math.abs(alignment.heading-alignment.command)<1, 'consistent section margins');
        assert.ok(Math.abs(alignment.settingsRight-8)<1, 'settings inset is applied once');
        assert.equal(alignment.settingsTop,20,'settings moved down without duplicating safe top');
        assert.equal(alignment.statusTop,30,'status badge and title moved down together');
        assert.ok(alignment.headerGap>=0 && alignment.headerCenters<2,'badge and settings align without overlap');
        for (const selector of ['body','.tab-panel','.home-feature-rail','#pwa-login']) {
          assert.equal(await page.locator(selector).first().evaluate(el=>getComputedStyle(el).touchAction),'manipulation','disable browser double-tap on '+selector);
        }
        const viewport=await page.locator('meta[name="viewport"]').getAttribute('content');
        assert.doesNotMatch(viewport,/user-scalable\s*=\s*no|maximum-scale\s*=/i,'keep pinch zoom available');
        assert.equal(await page.locator('.snapshot-viewer-stage').evaluate(el=>getComputedStyle(el).touchAction),'none','preserve the photo viewer custom gestures');
        const fuelLabel=await page.locator('.home-fuel-label').boundingBox();
        await page.touchscreen.tap(fuelLabel.x+fuelLabel.width/2,fuelLabel.y+fuelLabel.height/2);
        await page.touchscreen.tap(fuelLabel.x+fuelLabel.width/2,fuelLabel.y+fuelLabel.height/2);
        assert.equal(await page.evaluate(()=>visualViewport.scale),1,'two fixture taps do not zoom the page');
        if (metrics.panel.scroll <= metrics.panel.h+1) {
          assert.ok(metrics.nav.y-metrics.rail.b <= 14, 'no dead space before navigation');
          assert.ok(metrics.nav.y >= metrics.rail.b, 'rail does not overlap navigation');
        }
        await page.locator('#tab-control').evaluate(el => {el.scrollTop=el.scrollHeight;});
        const bottomRail = await page.locator('.home-feature-rail').boundingBox();
        assert.ok(bottomRail.y+bottomRail.height <= metrics.nav.y+1, 'cards reachable by scrolling');
        await page.locator('#tab-control').evaluate(el => {el.scrollTop=0;});
        if (['iphone','max','small','landscape','standalone'].includes(name)) {
          await page.waitForSelector('.hero-map.map-surface-ready', {timeout:15000});
          await page.screenshot({path:resolve(output,`${engine}-${name}.png`)});
        }
        for (const selector of ['.nav-item','.home-quick-action:not([hidden])','.home-sunroof-actions .action-button-grouped:not([hidden])']) {
          const targets = await page.locator(selector).evaluateAll(es => es.filter(e => e.getClientRects().length).map(e => {const r=e.getBoundingClientRect();return {id:e.id,w:r.width,h:r.height};}));
          assert.ok(targets.every(r=>r.w>=44 && r.h>=44), 'touch targets '+JSON.stringify(targets));
        }
        // Actual existing tab handlers and finder close/open, not replacement navigation.
        await page.locator('.nav-item[data-target="tab-info"]').press('Enter');
        await page.waitForSelector('#tab-info.active');
        assert.equal(await page.locator('.nav-item[data-target="tab-info"]').getAttribute('aria-current'), 'page');
        await page.locator('.nav-item[data-target="tab-extras"]').click();
        await page.waitForSelector('#tab-extras.active');
        await page.locator('.nav-item[data-target="tab-control"]').click();
        await page.locator('#home-card-finder').click();
        await page.waitForSelector('#tab-control.finder-open');
        await page.waitForFunction(() => {
          const style=getComputedStyle(document.querySelector('#btnCloseVehicleFinder'));
          return style.opacity==='1' && new DOMMatrixReadOnly(style.transform).m42===0;
        });
        const finder=await page.locator('.home-map-hero').boundingBox();
        assert.equal(finder.width,width); assert.equal(finder.height,height);
        await page.locator('#btnCloseVehicleFinder').click({trial:true});
        const finderClose=await page.locator('#btnCloseVehicleFinder').boundingBox();
        const finderParents=await page.locator('#btnCloseVehicleFinder').evaluate(el=>{
          const result=[];
          for(let e=el;e;e=e.parentElement) {const r=e.getBoundingClientRect(),s=getComputedStyle(e);result.push({tag:e.id||e.className||e.tagName,x:r.x,y:r.y,scroll:[e.scrollLeft,e.scrollTop],transform:s.transform,position:s.position});}
          return result;
        });
        assert.ok(finderClose.x>=side+17.9 && finderClose.y>=top+55.9,'finder close avoids notch '+JSON.stringify(finderParents));
        const finderControls=await page.locator('.finder-map-controls').boundingBox();
        assert.ok(finderControls.x+finderControls.width<=width-side-17.9,'finder controls avoid right notch');
        const mapScroll=await page.locator('#hero-location-map').evaluate(el=>[el.scrollLeft,el.scrollTop]);
        assert.deepEqual(mapScroll,[0,0],'outer map surface must not scroll controls');
        await page.locator('#btnCloseVehicleFinder').click();
        await page.waitForSelector('#tab-control:not(.finder-open)');
        await page.locator('#btnSecretSettings').click();
        await page.waitForSelector('#tab-settings.active');
        // Native settings remain scrollable; focus does not force tiny-font Safari zoom.
        const textInputs=await page.locator('#tab-settings input:not([type="range"]):not([type="checkbox"])').evaluateAll(es=>es.filter(e=>e.getClientRects().length).map(e=>parseFloat(getComputedStyle(e).fontSize)));
        assert.ok(textInputs.every(s=>s>=16));
        await page.locator('.nav-item[data-target="tab-control"]').click();
        await page.evaluate(() => {
          document.documentElement.style.fontSize='32px';
          document.querySelector('#home-vehicle-updated').textContent='2026. 11. 2. 오후 11:59:59 (3분 전)';
          document.querySelector('#home-card-address').textContent='서울특별시 중구 세종대로 서울시청 지하 주차장';
          document.querySelector('#home-fuel-level').textContent='~82.1 L';
          document.querySelector('#home-range-value').textContent='1,024 km';
        });
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth),0,'large text overflow');
        const clipped = await page.locator('.home-updated-row, .home-updated-row strong, .home-feature-copy, .home-feature-copy strong, .home-feature-copy span, .home-fuel-value').evaluateAll(es =>
          es.filter(e=>e.getClientRects().length && e.scrollWidth>e.clientWidth+1).map(e=>e.className || e.id || e.tagName));
        assert.deepEqual(clipped,[], 'large text must not be hidden by overflow');
        const fuelAlignment=await page.evaluate(()=>document.querySelector('.home-fuel-value').getBoundingClientRect().right-document.querySelector('.home-fuel-track').getBoundingClientRect().right);
        assert.ok(Math.abs(fuelAlignment)<1,'long fuel value stays right aligned');
        await page.locator('#tab-control').evaluate(el=>{el.scrollTop=el.scrollHeight;});
        const largeRail = await page.locator('.home-feature-rail').boundingBox();
        assert.ok(largeRail.y+largeRail.height<=metrics.nav.y+1,'large text remains reachable');
        if (name === 'iphone') {
          // Approximate the reduced viewport while typing; not an actual iOS keyboard test.
          await page.evaluate(() => {
            document.documentElement.style.fontSize='';
            window.dispatchEvent(new CustomEvent('traverseweb:sessionlost'));
          });
          await page.setViewportSize({width:390,height:320});
          await page.locator('#pwa-password').fill('synthetic-not-submitted');
          await page.locator('#pwa-login button').scrollIntoViewIfNeeded();
          const loginButton=await page.locator('#pwa-login button').boundingBox();
          assert.ok(loginButton.y>=0 && loginButton.y+loginButton.height<=320, 'login button reachable with short viewport');
          await page.screenshot({path:resolve(output,`${engine}-login-short.png`)});
        }
        assert.deepEqual(errors,[], 'uncaught JS exceptions');
        reports.push({engine,name,...metrics});
      } catch (error) { failures.push({engine,name,message:error.message}); await page.screenshot({path:resolve(output,`${engine}-${name}-failure.png`)}).catch(()=>{}); }
      await context.close();
    }
    await browser.close(); browser=null;
  }
  assert.equal(mutationRequests,0,'no mutation request even to local fixture');
} finally { await browser?.close(); await new Promise(resolve=>server.close(resolve)); }
await writeFile(resolve(output,'report.json'),JSON.stringify({reports,failures,mutationRequests},null,2));
console.log(JSON.stringify({passed:reports.length,failures,mutationRequests,output},null,2));
assert.equal(failures.length,0,'layout scenarios failed');
