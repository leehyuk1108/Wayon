import {cp, mkdir, readFile, writeFile, unlink} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import sharp from 'sharp';

const root = fileURLToPath(new URL('../', import.meta.url));
const assets = root + '../my-traverse-next/app/src/main/assets/';
await mkdir(root + 'public', {recursive:true});
await cp(assets, root + 'public', {recursive:true});
let html = await readFile(assets + 'main.html', 'utf8');
const original = createHash('sha256').update(html).digest('hex');
html = html.replace('<head>', `<head>
    <link rel="manifest" href="/manifest.webmanifest">
    <link rel="icon" href="/app-icon-v2-192.png">
    <link rel="apple-touch-icon" href="/app-icon-v2-180.png">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="theme-color" content="#0b0b0b">
    <script src="/bridge.js"></script>
    <script src="/pwa.js" defer></script>`)
  .replaceAll('https://wayon-cloud.hyuklee.workers.dev/api/', '/api/wayon/');
// Web overrides must follow the native stylesheet, including its media queries.
html = html.replace('</head>', '    <link rel="stylesheet" href="/pwa.css">\n</head>')
  .replace('initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover',
    'initial-scale=1.0, viewport-fit=cover');
html = html.replace('<body', '<body data-pwa="checking"');
await writeFile(root + 'public/index.html', html);
await unlink(root + 'public/main.html');
for (const name of ['bridge.js','pwa.js','pwa.css','sw.js','manifest.webmanifest']) {
  await cp(root + 'client/' + name, root + 'public/' + name);
}
const live = (await readFile(assets + 'wayon_live.js','utf8'))
  .replaceAll('https://wayon-cloud.hyuklee.workers.dev/api/', '/api/wayon/')
  .replaceAll('Android System WebView', 'Safari / iOS')
  .replace('headers: { Authorization: `Bearer ${token}`, "Content-Type": "image/jpeg" },',
    'headers: { "X-CSRF-Token": window.TraverseWeb.csrfToken(), "Content-Type": "image/jpeg" },');
await writeFile(root + 'public/wayon_live.js', live);
for (const size of [180,192,512]) {
  await sharp(assets + '../res/mipmap-xxxhdpi/ic_launcher.webp').resize(size,size)
    .flatten({background:'#242424'}).png().toFile(root + `public/app-icon-v2-${size}.png`);
}
console.log(JSON.stringify({built:true,androidSourceSHA256:original,androidSourceUnmodified:true}));
