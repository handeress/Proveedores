// Guarda la app en el celular para que abra sin señal.
const CACHE = 'proveedores-v5';
const ARCHIVOS = ['./', './index.html', './manifest.json', './icon-192.png', './icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ARCHIVOS)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});

// Primero lo guardado (abre rápido aunque la señal sea mala); si hay internet, actualiza para la próxima vez.
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return;
  // Buzón y datos iniciales: siempre de la red, nunca de lo guardado.
  if (url.pathname.includes('/buzon/') || url.pathname.endsWith('carga.bin')) return;
  e.respondWith(
    caches.open(CACHE).then(async c => {
      const guardado = await c.match(e.request, { ignoreSearch: true });
      const red = fetch(e.request).then(r => { if (r.ok) c.put(e.request, r.clone()); return r; }).catch(() => null);
      if (guardado) { e.waitUntil(red); return guardado; }
      return (await red) || (await c.match('./index.html'));
    })
  );
});
