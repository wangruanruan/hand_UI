const CACHE_NAME = 'chaos-magic-v1';
const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './manifest.json',
  './assets/loop1.wav',
  './assets/loop2.wav',
  './assets/charge.wav',
  './assets/boom.wav',
  'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',
  'https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js',
  'https://cdn.jsdelivr.net/npm/@mediapipe/control_utils/control_utils.js',
  'https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => Promise.all(keyList.map((key) => {
      if (key !== CACHE_NAME) return caches.delete(key);
    })))
  );
  return self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => response || fetch(event.request))
  );
});