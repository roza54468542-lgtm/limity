// Офлайн-кэш «Лимитов» + приём квитанций через «Поделиться» (Android).
var CACHE = 'limity-v42';
var SHELL = ['./', './index.html', './config.js', './manifest.webmanifest',
  './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png'];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(SHELL); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== CACHE && k !== 'share-inbox'; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});
function put(req, res) {
  if (res && (res.ok || res.type === 'opaque')) { var copy = res.clone(); caches.open(CACHE).then(function (c) { c.put(req, copy); }); }
  return res;
}
self.addEventListener('fetch', function (e) {
  var req = e.request, url = new URL(req.url);

  // Квитанция пришла через «Поделиться»: сохраняем и открываем приложение
  if (req.method === 'POST' && url.origin === self.location.origin && /\/share\/?$/.test(url.pathname)) {
    e.respondWith(req.formData().then(function (fd) {
      var files = fd.getAll('receipt').filter(function (f) { return f && f.size; });
      return caches.open('share-inbox').then(function (c) {
        return Promise.all(files.map(function (f, i) {
          return c.put(new Request('./shared/' + Date.now() + '-' + i), new Response(f, { headers: { 'content-type': f.type || 'image/png', 'x-name': encodeURIComponent(f.name || '') } }));
        }));
      });
    }).then(function () { return Response.redirect('./?shared=1', 303); })
      .catch(function () { return Response.redirect('./', 303); }));
    return;
  }
  if (req.method !== 'GET') return;
  if (url.origin === self.location.origin) {
    e.respondWith(fetch(req).then(function (res) { return put(req, res); }).catch(function () {
      return caches.match(req).then(function (m) { return m || caches.match('./index.html'); });
    }));
    return;
  }
  if (url.hostname === 'www.gstatic.com' || url.hostname === 'fonts.gstatic.com' || url.hostname === 'fonts.googleapis.com' || url.hostname === 'cdn.jsdelivr.net' || url.hostname === 'cdnjs.cloudflare.com') {
    e.respondWith(caches.match(req).then(function (m) { return m || fetch(req).then(function (res) { return put(req, res); }); }));
  }
});
