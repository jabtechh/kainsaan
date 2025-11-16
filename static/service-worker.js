// Service Worker for Kain Saan PWA
// Provides offline support and caches static assets

const CACHE_NAME = 'kainsaan-v1';
const OFFLINE_URL = '/offline/';

// Assets to cache on install
const STATIC_ASSETS = [
    '/',
    '/static/manifest.json',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[Service Worker] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME) {
                            console.log('[Service Worker] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch event - network first, then cache, then offline page
self.addEventListener('fetch', (event) => {
    const { request } = event;
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip chrome extensions and other protocols
    if (!request.url.startsWith('http')) {
        return;
    }
    
    // Network-first strategy for API calls
    if (request.url.includes('/api/')) {
        event.respondWith(
            fetch(request)
                .catch(() => {
                    return new Response(
                        JSON.stringify({ error: 'You are offline. Please check your connection.' }),
                        {
                            headers: { 'Content-Type': 'application/json' },
                            status: 503
                        }
                    );
                })
        );
        return;
    }
    
    // Cache-first strategy for static assets
    if (
        request.url.includes('/static/') ||
        request.url.includes('tailwindcss.com') ||
        request.url.includes('maps.googleapis.com')
    ) {
        event.respondWith(
            caches.match(request)
                .then((cached) => {
                    if (cached) {
                        return cached;
                    }
                    return fetch(request).then((response) => {
                        // Cache the fetched resource
                        if (response.status === 200) {
                            const responseClone = response.clone();
                            caches.open(CACHE_NAME).then((cache) => {
                                cache.put(request, responseClone);
                            });
                        }
                        return response;
                    });
                })
        );
        return;
    }
    
    // Network-first with cache fallback for pages
    event.respondWith(
        fetch(request)
            .then((response) => {
                // Cache successful responses
                if (response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, responseClone);
                    });
                }
                return response;
            })
            .catch(() => {
                // Try to return cached version
                return caches.match(request)
                    .then((cached) => {
                        if (cached) {
                            return cached;
                        }
                        // Return offline page as last resort
                        return caches.match(OFFLINE_URL);
                    });
            })
    );
});
