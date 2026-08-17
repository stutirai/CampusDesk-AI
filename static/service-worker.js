const CACHE_NAME = "campusdesk-ai-v1";
const urlsToCache = [
  "/",
  "/static/style.css",
  "/static/script.js",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener("fetch", (event) => {
  // Network-first for /chat and /upload (always need fresh answers),
  // cache-first for static shell files.
  if (event.request.url.includes("/chat") || event.request.url.includes("/upload")) {
    return;
  }
  event.respondWith(
    caches.match(event.request).then((response) => response || fetch(event.request))
  );
});
