const CACHE_NAME = 'c2-panel-v1';
const ASSETS = [
    '/',
    '/index.html',
    '/styles.css',
    '/app.js',
    '/manifest.json'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS);
        })
    );
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});

self.addEventListener('push', (event) => {
    const data = event.data.json();
    const title = 'System Update Alert';
    const options = {
        body: data.message,
        icon: '/icons/icon-192.png'
    };
    event.waitUntil(self.registration.showNotification(title, options));
});