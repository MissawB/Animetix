const CACHE_NAME = 'animetix-v7';
const STATIC_ASSETS = [
    '/',
    '/static/animetix/img/logo/logo.png',
    '/static/animetix/data/offline_catalog.db',
    '/static/animetix/js/offline_engine.js',
    '/static/animetix/audio/click.mp3',
    '/static/animetix/audio/win.mp3',
    '/static/animetix/audio/loss.mp3',
    '/static/animetix/audio/unlock.mp3',
    'https://unpkg.com/htmx.org@1.9.12',
    'https://cdn.tailwindcss.com',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/howler/2.2.4/howler.min.js'
];

self.addEventListener('install', event => {
    event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS)));
});

self.addEventListener('activate', event => {
    event.waitUntil(caches.keys().then(keys => Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
    )));
});

self.addEventListener('fetch', event => {
    if (event.request.mode === 'navigate') {
        event.respondWith(fetch(event.request).catch(() => caches.match('/')));
        return;
    }
    event.respondWith(caches.match(event.request).then(response => response || fetch(event.request)));
});

// PUSH NOTIFICATIONS (Daily Streak Reminders)
self.addEventListener('push', (event) => {
    const data = event.data ? event.data.json() : { title: 'Animetix', body: 'Votre série de victoires est en danger !' };
    const options = {
        body: data.body,
        icon: '/static/animetix/img/logo/logo.png',
        badge: '/static/animetix/img/logo/logo.png',
        vibrate: [100, 50, 100],
        data: { url: data.url || '/' }
    };
    event.waitUntil(self.registration.showNotification(data.title, options));
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(clients.openWindow(event.notification.data.url));
});

// BACKGROUND SYNC API
self.addEventListener('sync', event => {
    if (event.tag === 'sync-offline-scores') {
        event.waitUntil(syncOfflineData());
    }
});

async function syncOfflineData() {
    // In a real app we would use IndexedDB. We will mock a localforage equivalent or assume clients handles IndexedDB
    // To simplify for this SW without extra libs, we will ask clients to push data
    const clientsList = await self.clients.matchAll();
    for (const client of clientsList) {
        client.postMessage({ type: 'REQUEST_OFFLINE_DATA_SYNC' });
    }
}
