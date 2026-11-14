// MANTOTA Service Worker — minimal pour activer l'installation PWA
// v3 — ne cache jamais les réponses 4xx/5xx + purge automatique au déploiement
const CACHE_NAME = 'mantota-v4';

// Au déclenchement du SW — mise en cache des ressources statiques essentielles
self.addEventListener('install', (event) => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) =>
            cache.addAll([
                '/manifest.json',
                '/favicon.ico',
                '/apk-logo.png',
            ]).catch(() => {})
        )
    );
});

// Activation — nettoie les anciens caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
            )
        ).then(() => self.clients.claim())
    );
});

// Stratégie Network First : réseau d'abord, cache en fallback
self.addEventListener('fetch', (event) => {
    // Ne pas intercepter les requêtes non-GET, API/Inertia, admin, backup
    const url = event.request.url;
    if (
        event.request.method !== 'GET' ||
        event.request.headers.get('X-Inertia') ||
        url.includes('/api/') ||
        url.includes('/admin/') ||
        url.includes('fonts.bunny.net')
    ) {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Ne cacher QUE les réponses 200 OK des assets statiques
                if (
                    response.ok &&
                    response.status === 200 &&
                    event.request.url.includes('/build/')
                ) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                }
                return response;
            })
            .catch(() =>
                caches.match(event.request).then(
                    (cached) => cached || new Response('Offline', { status: 503, statusText: 'Service Unavailable' })
                )
            )
    );
});
