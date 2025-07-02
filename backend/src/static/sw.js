// Biped Service Worker - PWA Functionality
const CACHE_NAME = 'biped-v1.0.0';
const STATIC_CACHE = 'biped-static-v1.0.0';
const DYNAMIC_CACHE = 'biped-dynamic-v1.0.0';

// Files to cache for offline functionality
const STATIC_FILES = [
  '/',
  '/mobile.html',
  '/index.html',
  '/manifest.json',
  '/biped-logo.png',
  '/biped-logo-horizontal.png',
  '/biped-hero-bg.png',
  // Add other critical assets
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
  /\/api\/analytics\/platform-health/,
  /\/api\/analytics\/metrics\/current/,
  /\/api\/ai\/analyze-job/,
  /\/api\/vision\/analyze-image/
];

// Install event - cache static files
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('Service Worker: Caching static files');
        return cache.addAll(STATIC_FILES);
      })
      .then(() => {
        console.log('Service Worker: Static files cached');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Service Worker: Error caching static files', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Handle different types of requests
  if (request.method === 'GET') {
    // Static files - cache first strategy
    if (STATIC_FILES.some(file => url.pathname.endsWith(file))) {
      event.respondWith(cacheFirstStrategy(request));
    }
    // API requests - network first with cache fallback
    else if (url.pathname.startsWith('/api/')) {
      event.respondWith(networkFirstStrategy(request));
    }
    // Images and assets - cache first strategy
    else if (request.destination === 'image' || 
             request.url.includes('.png') || 
             request.url.includes('.jpg') || 
             request.url.includes('.jpeg') || 
             request.url.includes('.svg')) {
      event.respondWith(cacheFirstStrategy(request));
    }
    // Other requests - network first
    else {
      event.respondWith(networkFirstStrategy(request));
    }
  }
});

// Cache first strategy - for static assets
async function cacheFirstStrategy(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.error('Cache first strategy failed:', error);
    return new Response('Offline - Content not available', {
      status: 503,
      statusText: 'Service Unavailable'
    });
  }
}

// Network first strategy - for dynamic content and APIs
async function networkFirstStrategy(request) {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache successful API responses
      if (request.url.includes('/api/')) {
        const cache = await caches.open(DYNAMIC_CACHE);
        cache.put(request, networkResponse.clone());
      }
    }
    
    return networkResponse;
  } catch (error) {
    console.log('Network failed, trying cache:', error);
    
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      const offlineResponse = await caches.match('/mobile.html');
      if (offlineResponse) {
        return offlineResponse;
      }
    }
    
    return new Response(JSON.stringify({
      error: 'Offline - Network unavailable',
      offline: true,
      timestamp: new Date().toISOString()
    }), {
      status: 503,
      statusText: 'Service Unavailable',
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('Service Worker: Background sync triggered', event.tag);
  
  if (event.tag === 'background-sync-jobs') {
    event.waitUntil(syncOfflineJobs());
  } else if (event.tag === 'background-sync-messages') {
    event.waitUntil(syncOfflineMessages());
  }
});

// Sync offline job postings
async function syncOfflineJobs() {
  try {
    const offlineJobs = await getOfflineData('pending-jobs');
    
    for (const job of offlineJobs) {
      try {
        const response = await fetch('/api/jobs', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(job)
        });
        
        if (response.ok) {
          await removeOfflineData('pending-jobs', job.id);
          console.log('Synced offline job:', job.id);
        }
      } catch (error) {
        console.error('Failed to sync job:', job.id, error);
      }
    }
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// Sync offline messages
async function syncOfflineMessages() {
  try {
    const offlineMessages = await getOfflineData('pending-messages');
    
    for (const message of offlineMessages) {
      try {
        const response = await fetch('/api/messages', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(message)
        });
        
        if (response.ok) {
          await removeOfflineData('pending-messages', message.id);
          console.log('Synced offline message:', message.id);
        }
      } catch (error) {
        console.error('Failed to sync message:', message.id, error);
      }
    }
  } catch (error) {
    console.error('Message sync failed:', error);
  }
}

// Push notifications
self.addEventListener('push', (event) => {
  console.log('Service Worker: Push notification received');
  
  let notificationData = {
    title: 'Biped',
    body: 'You have a new notification',
    icon: '/biped-logo.png',
    badge: '/biped-logo.png',
    tag: 'biped-notification',
    requireInteraction: false,
    actions: [
      {
        action: 'view',
        title: 'View',
        icon: '/biped-logo.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss'
      }
    ]
  };
  
  if (event.data) {
    try {
      const data = event.data.json();
      notificationData = { ...notificationData, ...data };
    } catch (error) {
      console.error('Error parsing push data:', error);
    }
  }
  
  event.waitUntil(
    self.registration.showNotification(notificationData.title, notificationData)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  console.log('Service Worker: Notification clicked', event);
  
  event.notification.close();
  
  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/mobile.html')
    );
  } else if (event.action === 'dismiss') {
    // Just close the notification
    return;
  } else {
    // Default action - open app
    event.waitUntil(
      clients.matchAll({ type: 'window' })
        .then((clientList) => {
          for (const client of clientList) {
            if (client.url.includes('/mobile.html') && 'focus' in client) {
              return client.focus();
            }
          }
          if (clients.openWindow) {
            return clients.openWindow('/mobile.html');
          }
        })
    );
  }
});

// Message handling from main thread
self.addEventListener('message', (event) => {
  console.log('Service Worker: Message received', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  } else if (event.data && event.data.type === 'CACHE_URLS') {
    event.waitUntil(
      caches.open(DYNAMIC_CACHE)
        .then((cache) => {
          return cache.addAll(event.data.urls);
        })
    );
  }
});

// Utility functions for offline data management
async function getOfflineData(storeName) {
  try {
    const cache = await caches.open(DYNAMIC_CACHE);
    const response = await cache.match(`/offline-data/${storeName}`);
    
    if (response) {
      return await response.json();
    }
    return [];
  } catch (error) {
    console.error('Error getting offline data:', error);
    return [];
  }
}

async function removeOfflineData(storeName, itemId) {
  try {
    const data = await getOfflineData(storeName);
    const filteredData = data.filter(item => item.id !== itemId);
    
    const cache = await caches.open(DYNAMIC_CACHE);
    await cache.put(`/offline-data/${storeName}`, new Response(JSON.stringify(filteredData)));
  } catch (error) {
    console.error('Error removing offline data:', error);
  }
}

// Periodic background sync (if supported)
self.addEventListener('periodicsync', (event) => {
  console.log('Service Worker: Periodic sync triggered', event.tag);
  
  if (event.tag === 'content-sync') {
    event.waitUntil(syncContent());
  }
});

async function syncContent() {
  try {
    // Sync critical content in background
    const response = await fetch('/api/analytics/platform-health');
    if (response.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put('/api/analytics/platform-health', response.clone());
    }
  } catch (error) {
    console.error('Periodic sync failed:', error);
  }
}

console.log('Service Worker: Loaded and ready');

