const CACHE_NAME = "kessler-research-english-2026-08-06-v12";
const APP_ASSETS = [
  "./",
  "./index.html",
  "./styles.css?v=2026-08-04-7",
  "./app.js?v=2026-08-04-7",
  "./interview.js?v=2026-08-04-7",
  "./manifest.webmanifest",
  "./data/learning_items.json",
  "./audio/interview/manifest.json",
  "./audio/interview/preview.mp3",
  "./audio/interview/introduction.mp3",
  "./audio/interview/lactylome-objective.mp3",
  "./audio/interview/lactylome-methods.mp3",
  "./audio/interview/lactylome-findings.mp3",
  "./audio/interview/mass-spec-experience.mp3",
  "./audio/interview/technical-problem.mp3",
  "./audio/interview/motivation.mp3",
  "./audio/interview/visit-project.mp3",
  "./audio/interview/contribution.mp3",
  "./audio/interview/funding.mp3",
  "./audio/interview/availability.mp3",
  "./audio/interview/questions.mp3",
  "./audio/interview/introduction-follow-up.mp3",
  "./audio/interview/lactylome-objective-follow-up.mp3",
  "./audio/interview/lactylome-methods-follow-up.mp3",
  "./audio/interview/lactylome-findings-follow-up.mp3",
  "./audio/interview/mass-spec-experience-follow-up.mp3",
  "./audio/interview/motivation-follow-up.mp3",
  "./audio/interview/visit-project-follow-up.mp3",
  "./audio/interview/funding-follow-up.mp3",
  "./audio/interview/availability-follow-up.mp3",
  "./audio/interview/practice-introduction.mp3",
  "./audio/interview/practice-lactylome-objective.mp3",
  "./audio/interview/practice-lactylome-methods.mp3",
  "./audio/interview/practice-lactylome-findings.mp3",
  "./audio/interview/practice-mass-spec.mp3",
  "./audio/interview/practice-motivation.mp3",
  "./audio/interview/practice-visit-project.mp3",
  "./audio/interview/practice-funding.mp3",
  "./audio/interview/practice-availability.mp3",
  "./audio/interview/practice-questions.mp3",
  "./self-introduction/",
  "./self-introduction/index.html",
  "./self-introduction/self-introduction.mp3",
  "./self-introduction/self-introduction.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)));
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const destination = event.request.destination;
  const networkFirst = event.request.mode === "navigate"
    || ["document", "script", "style", "manifest"].includes(destination);

  if (networkFirst) {
    event.respondWith((async () => {
      try {
        const response = await fetch(event.request, { cache: "no-store" });
        if (response.ok && new URL(event.request.url).origin === self.location.origin) {
          const cache = await caches.open(CACHE_NAME);
          await cache.put(event.request, response.clone());
        }
        return response;
      } catch {
        return (await caches.match(event.request, { ignoreSearch: true }))
          || (await caches.match("./index.html"));
      }
    })());
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      const network = fetch(event.request)
        .then((response) => {
          if (response.ok && new URL(event.request.url).origin === self.location.origin) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return response;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
