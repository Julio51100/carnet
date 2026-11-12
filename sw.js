/* Nutrisport : fonctionnement hors ligne et mises à jour.
   - La page de l’appli s’ouvre tout de suite depuis la copie gardée sur le téléphone ; la dernière version est
     récupérée en arrière-plan et proposée (« Recharger ») dès qu’elle est prête.
   - Polices, icônes, photos d’exercices et lecteur de codes-barres sont servis depuis le téléphone une fois téléchargés.
   Fichier généré par src/build_site.py : ne pas modifier à la main. */
const VERSION = '2026-11-12.befae8';
/* Caches propres à l’adresse de l’appli : une autre appli du même site n’y touche pas */
const PREFIX = 'carnet:' + new URL(self.registration.scope).pathname + ':';
const CORE = PREFIX + 'core-' + VERSION;
const MEDIA = PREFIX + 'media-58f611e5';
/* Lecteur de codes-barres (vendor/) : téléchargé au premier scan, gardé tant qu’il ne change pas */
const LIBS = PREFIX + 'libs-v1';
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
    await Promise.all(keys.filter(k => k.startsWith(PREFIX) && k !== CORE && k !== MEDIA && k !== LIBS).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

/* Version de la page récupérée en arrière-plan, quand elle est plus récente que celle qui vient d’être affichée */
let newerPage = null;
const pageVersion = text => { const m = /CARNET_VERSION = "([^"]+)"/.exec(text); return m ? m[1] : null; };
const pageTag = res => res.headers.get('etag') || res.headers.get('last-modified') || '';

self.addEventListener('message', event => {
  const type = event.data && event.data.type;
  if (!event.source) return;
  /* Un nouveau service worker vient de prendre la main : la page demande sa version */
  if (type === 'version?') event.source.postMessage({ type: 'version', version: VERSION });
  /* Au démarrage de la page : une version plus récente a-t-elle été récupérée pendant son ouverture ? */
  else if (type === 'page?' && newerPage) event.source.postMessage({ type: 'version', version: newerPage });
});

async function cachedPage() {
  const core = await caches.open(CORE);
  return (await core.match(APP_PAGE)) || (await caches.match(APP_PAGE)) || null;
}
/* La page récupérée remplace la copie du téléphone ; si c’est une autre version que celle affichée, les fenêtres ouvertes sont prévenues */
async function refreshPage(res, shown) {
  const core = await caches.open(CORE);
  const copy = res.clone();
  await core.put(APP_PAGE, res.clone());
  if (!shown) return;
  const a = pageTag(shown), b = pageTag(copy);
  if (a && b && a === b) return;
  const [was, now] = await Promise.all([shown.clone().text(), copy.text()]);
  const v0 = pageVersion(was), v1 = pageVersion(now);
  if (!v1 || v0 === v1) return;
  newerPage = v1;
  const wins = await self.clients.matchAll({ type: 'window' });
  wins.forEach(w => w.postMessage({ type: 'version', version: v1 }));
}

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  const scope = new URL(self.registration.scope);
  if (!url.pathname.startsWith(scope.pathname)) return;
  const rel = url.pathname.slice(scope.pathname.length);

  /* La page de l’appli : la copie du téléphone d’abord (ouverture immédiate, même avec un mauvais réseau),
     le réseau en arrière-plan pour la prochaine fois */
  if (req.mode === 'navigate') {
    if (rel !== '' && rel !== 'index.html') return;
    event.respondWith((async () => {
      const shown = await cachedPage();
      const network = fetch(req).then(async res => {
        if (res.ok) await refreshPage(res, shown).catch(() => null);
        return res;
      });
      event.waitUntil(network.then(() => null, () => null));
      if (shown) return shown.clone();
      /* Rien sur le téléphone (premier passage) : le réseau */
      return network;
    })());
    return;
  }

  /* Photos d’exercices et lecteur de codes-barres : gardés tant qu’ils ne changent pas */
  if (rel.startsWith('ex/') || rel.startsWith('vendor/')) {
    const name = rel.startsWith('ex/') ? MEDIA : LIBS;
    event.respondWith((async () => {
      const cache = await caches.open(name);
      const hit = await cache.match(req, { ignoreSearch: true });
      if (hit) return hit;
      const res = await fetch(req);
      if (res.ok) cache.put(req, res.clone());
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
