// Service worker: offline app shell + Android "Share to Interpreter" target.
// It never sees your API key and never talks to any server except this site.

const VERSION = "v3";
const SHELL = `shell-${VERSION}`;
const ASSETS = [
  "./", "index.html", "styles.css", "js/app.js", "js/sarvam.js", "js/audio.js",
  "manifest.webmanifest", "icons/icon.svg", "icons/icon-192.png", "icons/icon-512.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(SHELL).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k.startsWith("shell-") && k !== SHELL) await caches.delete(k);
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return; // Sarvam API calls go straight to the network

  if (e.request.method === "POST" && url.pathname.endsWith("/share-target")) {
    e.respondWith(receiveShare(e.request));
    return;
  }
  if (e.request.method !== "GET") return;

  // Network first (so updates land), cache fallback (so it opens offline).
  e.respondWith((async () => {
    try {
      const res = await fetch(e.request);
      if (res.ok) (await caches.open(SHELL)).put(e.request, res.clone());
      return res;
    } catch {
      return (await caches.match(e.request, { ignoreSearch: true })) || caches.match("index.html");
    }
  })());
});

async function receiveShare(request) {
  const base = new URL("./", self.registration.scope);
  try {
    const form = await request.formData();
    const file = form.getAll("audio").find((f) => f && typeof f !== "string");
    if (!file) return Response.redirect(`${base}?shared=none`, 303);
    const cache = await caches.open("share-target");
    await cache.put("shared-audio", new Response(file, {
      headers: { "content-type": file.type || "audio/ogg", "x-filename": encodeURIComponent(file.name || "voice-note.opus") },
    }));
    return Response.redirect(`${base}?shared=1`, 303);
  } catch {
    return Response.redirect(`${base}?shared=none`, 303);
  }
}
