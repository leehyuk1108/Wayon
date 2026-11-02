const SHELL = 'traverse-shell-v2';
const STATIC = new Set(['/app-icon-v2-180.png','/app-icon-v2-192.png','/app-icon-v2-512.png']);
self.addEventListener('install', event => event.waitUntil(self.skipWaiting()));
self.addEventListener('activate', event => event.waitUntil((async () => {
  for (const name of await caches.keys()) if (name.startsWith('traverse-') && name !== SHELL) await caches.delete(name);
  await self.clients.claim();
})()));
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== self.location.origin || !STATIC.has(url.pathname)) return;
  event.respondWith((async () => {
    const cache = await caches.open(SHELL);
    const saved = await cache.match(event.request);
    if (saved) return saved;
    const response = await fetch(event.request);
    if (response.ok) await cache.put(event.request, response.clone());
    return response;
  })());
});
self.addEventListener('push', event => event.waitUntil((async () => {
  let payload;
  try { payload = event.data.json(); } catch { payload = {}; }
  const valid = typeof payload.title === 'string' && typeof payload.body === 'string' &&
    Number.isFinite(payload.expiresAt) && payload.expiresAt > Date.now();
  await self.registration.showNotification(valid ? payload.title.slice(0,100) : 'My Traverse', {
    body: valid ? payload.body.slice(0,500) : '앱에서 최신 차량 정보를 확인해 주세요.',
    tag: typeof payload.id === 'string' ? payload.id.slice(0,180) : 'traverse-update',
    icon: '/app-icon-v2-192.png', badge: '/app-icon-v2-192.png',
    data: {url: '/', eventId: valid ? payload.id : ''},
  });
})()));
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil((async () => {
    const clients = await self.clients.matchAll({type:'window',includeUncontrolled:true});
    const current = clients.find(client => new URL(client.url).origin === self.location.origin);
    if (current) { await current.focus(); current.postMessage({type:'refresh'}); }
    else await self.clients.openWindow('/');
  })());
});
