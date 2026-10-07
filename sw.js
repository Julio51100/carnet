/* Nutrisport : fonctionnement hors ligne et mises à jour.
   - La page de l’appli vient du réseau quand il répond vite (3,5 s), sinon de la copie gardée sur le téléphone.
   - Polices, icônes et photos d’exercices sont servies depuis le téléphone une fois téléchargées.
   Fichier généré par src/build_site.py : ne pas modifier à la main. */
const VERSION = '2026-10-07.d1610f';
/* Caches propres à l’adresse de l’appli : une autre appli du même site n’y touche pas */
const PREFIX = 'carnet:' + new URL(self.registration.scope).pathname + ':';
const CORE = PREFIX + 'core-' + VERSION;
const MEDIA = PREFIX + 'media-58f611e5';
const CORE_FILES = ["./", "manifest.webmanifest", "fonts/instrument-sans-latin.woff2", "fonts/instrument-sans-latin-ext.woff2", "icons/icon-192.png", "icons/favicon-32.png"];
const MEDIA_FILES = ["ex/vignettes-ab6a1fb5.webp"];
const APP_PAGE = new URL('./', self.registration.scope).href;

const fresh = url => new Request(url, { cache: 'reload' });

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const core = await caches.open(CORE);
    await core.addAll(CORE_FILES.map(fresh));
    const media = await caches.open(MEDIA);
    for (const f of MEDIA_FILES) {
      if (!(await media.match(f))) { try { await media.add(fresh(f)); } catch (e) { /* réessayé plus tard */ } }
    }
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k.startsWith(PREFIX) && k !== CORE && k !== MEDIA).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('message', event => {
  if (event.data && event.data.type === 'version?' && event.source) event.source.postMessage({ type: 'version', version: VERSION });
});

function withTimeout(promise, ms) {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error('timeout')), ms);
    promise.then(v => { clearTimeout(t); resolve(v); }, e => { clearTimeout(t); reject(e); });
  });
}

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  const scope = new URL(self.registration.scope);
  if (!url.pathname.startsWith(scope.pathname)) return;
  const rel = url.pathname.slice(scope.pathname.length);

  /* La page de l’appli */
  if (req.mode === 'navigate') {
    if (rel !== '' && rel !== 'index.html') return;
    const network = fetch(req).then(async res => {
      if (res.ok) { const c = await caches.open(CORE); await c.put(APP_PAGE, res.clone()); }
      return res;
    });
    event.waitUntil(network.then(() => null, () => null));
    const cachedPage = () => caches.open(CORE).then(c => c.match(APP_PAGE)).then(hit => hit || caches.match(APP_PAGE));
    event.respondWith(withTimeout(network, 3500)
      /* Page d’erreur du serveur (site en maintenance, adresse changée) : la copie sur le téléphone reste prioritaire */
      .then(res => (res.ok ? res : cachedPage().then(hit => hit || res)))
      .catch(async () => (await cachedPage()) || network));
    return;
  }

  /* Photos d’exercices : gardées tant qu’elles ne changent pas */
  if (rel.startsWith('ex/')) {
    event.respondWith((async () => {
      const media = await caches.open(MEDIA);
      const hit = await media.match(req, { ignoreSearch: true });
      if (hit) return hit;
      const res = await fetch(req);
      if (res.ok) media.put(req, res.clone());
      return res;
    })());
    return;
  }

  /* Le reste (polices, icônes, manifeste) : copie locale, rafraîchie en arrière-plan */
  if (rel.startsWith('src/')) return;
  event.respondWith((async () => {
    const core = await caches.open(CORE);
    const hit = await core.match(req, { ignoreSearch: true });
    const update = fetch(req).then(res => { if (res.ok) core.put(req, res.clone()); return res; });
    if (hit) { update.catch(() => null); return hit; }
    return update;
  })());
});
