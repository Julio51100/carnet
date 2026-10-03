#!/usr/bin/env python3
"""Construit le site installable de Nutrisport à partir de la page de l’appli (la même que dans Claude).

    python3 build_site.py SOURCE.html DOSSIER_SORTIE [--assets] [--media DOSSIER_PHOTOS] [--fonts DOSSIER_POLICES]

- SOURCE.html : la page de l’appli, telle que publiée dans Claude (sans <html>/<head>).
- DOSSIER_SORTIE : le site prêt à publier (GitHub Pages, Netlify…).
- --assets : refait les icônes (depuis src/logo.png) et les écrans de lancement (Pillow et Playwright requis).
- --media : dossier des photos d’exercices (ex/*.webp) à copier.
- --fonts : dossier contenant les fichiers instrument-sans-latin(-ext)-standard-normal.woff2 et OFL.txt.
"""
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
LOGO = os.path.join(HERE, 'logo.png')  # logo rond, transparent autour de l’anneau doré

BG = '#0f1210'
NAME = 'Nutrisport'
DESCRIPTION = 'Ton carnet de nutrition et de musculation : repas et macros, séances, poids et objectifs. Fonctionne sans réseau.'

# Écrans de lancement de l’iPhone (largeur et hauteur en points, densité) — portrait
SPLASH = [
    (440, 956, 3), (402, 874, 3), (420, 912, 3), (430, 932, 3), (393, 852, 3), (390, 844, 3),
    (428, 926, 3), (375, 812, 3), (414, 896, 3), (414, 896, 2), (375, 667, 2), (414, 736, 3),
]


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(s)


def page(body, w, h, extra_css=''):
    return ('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;width:%dpx;height:%dpx;overflow:hidden;background:transparent}%s</style></head><body>%s</body></html>'
            % (w, h, extra_css, body))


def render_assets(out):
    from PIL import Image, ImageDraw
    emblem = Image.open(LOGO).convert('RGBA')
    icons = os.path.join(out, 'icons')
    os.makedirs(icons, exist_ok=True)

    def on_canvas(size, frac, bg=None):
        """Le logo centré, à frac de la largeur, sur fond transparent ou uni."""
        canvas = Image.new('RGBA', (size, size), bg or (0, 0, 0, 0))
        d = round(size * frac)
        canvas.alpha_composite(emblem.resize((d, d), Image.LANCZOS), ((size - d) // 2, (size - d) // 2))
        return canvas
    black = (0, 0, 0, 255)
    on_canvas(192, .96).save(os.path.join(icons, 'icon-192.png'), optimize=True)
    on_canvas(512, .96).save(os.path.join(icons, 'icon-512.png'), optimize=True)
    # Android découpe l’icône « maskable » (cercle, goutte…) : le logo reste dans la zone sûre de 80 %
    on_canvas(192, .78, black).convert('RGB').save(os.path.join(icons, 'icon-maskable-192.png'), optimize=True)
    on_canvas(512, .78, black).convert('RGB').save(os.path.join(icons, 'icon-maskable-512.png'), optimize=True)
    # iPhone : pas de transparence, coins arrondis ajoutés par iOS
    on_canvas(180, .88, black).convert('RGB').save(os.path.join(icons, 'apple-touch-icon.png'), optimize=True)
    on_canvas(32, 1).save(os.path.join(icons, 'favicon-32.png'), optimize=True)
    # Raccourci « Ajouter un aliment » : un + doré sur fond noir
    S = 384
    sc = Image.new('RGBA', (S, S), black)
    g = ImageDraw.Draw(sc)
    gold, w, L = (200, 152, 72, 255), 40, 104
    g.rounded_rectangle((S / 2 - w / 2, S / 2 - L, S / 2 + w / 2, S / 2 + L), w / 2, fill=gold)
    g.rounded_rectangle((S / 2 - L, S / 2 - w / 2, S / 2 + L, S / 2 + w / 2), w / 2, fill=gold)
    sc.resize((96, 96), Image.LANCZOS).convert('RGB').save(os.path.join(icons, 'shortcut-add.png'), optimize=True)
    old_svg = os.path.join(icons, 'favicon.svg')
    if os.path.exists(old_svg):
        os.remove(old_svg)
    # Écrans de lancement de l’iPhone : le logo et le nom, rendus par Playwright avec la police de l’appli
    jobs = []
    font = os.path.abspath(os.path.join(out, 'fonts', 'instrument-sans-latin.woff2'))
    css = ('@font-face{font-family:"IS";src:url("file://%s") format("woff2");font-weight:400 700;font-stretch:75%% 100%%}'
           'body{background:%s!important;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6vw}'
           '.g{width:46vw;height:46vw;margin-top:-8vh}.t{font:600 7.2vw/1 "IS",sans-serif;letter-spacing:-.01em;color:#e8ebe7}' % (font, BG))
    for w, h, d in SPLASH:
        jobs.append({'out': os.path.join(out, 'splash/splash-%dx%d.png' % (w * d, h * d)), 'width': w, 'height': h, 'scale': d,
                     'html': page('<img class="g" src="file://%s" alt=""><div class="t">%s</div>' % (os.path.abspath(LOGO), NAME), w, h, css)})
    jp = os.path.join(out, '_jobs.json')
    write(jp, json.dumps(jobs))
    subprocess.run(['node', os.path.join(HERE, 'render_assets.js'), jp], check=True)
    os.remove(jp)


def splash_links():
    links = []
    for w, h, d in SPLASH:
        media = '(device-width: %dpx) and (device-height: %dpx) and (-webkit-device-pixel-ratio: %d) and (orientation: portrait)' % (w, h, d)
        links.append('<link rel="apple-touch-startup-image" media="%s" href="splash/splash-%dx%d.png">' % (media, w * d, h * d))
    return '\n'.join(links)


def file_hash(paths):
    h = hashlib.sha256()
    for p in sorted(paths):
        with open(p, 'rb') as f:
            h.update(os.path.basename(p).encode())
            h.update(f.read())
    return h.hexdigest()


def build(src, out, assets, media_dir, fonts_dir):
    source = read(src)
    os.makedirs(out, exist_ok=True)

    # Photos d’exercices et polices
    if media_dir:
        dst = os.path.join(out, 'ex')
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(media_dir, dst)
    if fonts_dir:
        os.makedirs(os.path.join(out, 'fonts'), exist_ok=True)
        for sub in ('latin', 'latin-ext'):
            shutil.copy(os.path.join(fonts_dir, 'instrument-sans-%s-standard-normal.woff2' % sub), os.path.join(out, 'fonts', 'instrument-sans-%s.woff2' % sub))
        lic = os.path.join(fonts_dir, 'OFL.txt')
        if os.path.exists(lic):
            shutil.copy(lic, os.path.join(out, 'fonts', 'OFL.txt'))
    if assets:
        render_assets(out)

    # Page de l’appli : en-tête de site installable + la page publiée dans Claude
    m = re.search(r'<script>try \{ if \(localStorage\.getItem\("cpm\.theme"\).*?</script>\n', source)
    if not m:
        sys.exit('Repère du script de thème introuvable dans la source')
    head_src, body_src = source[:m.end()], source[m.end():]
    head_src = re.sub(r'<title>.*?</title>\n', '', head_src)
    head_src = re.sub(r'<link rel="preconnect"[^>]*>\n', '', head_src)
    head_src = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>\n', '', head_src)
    if 'fonts.googleapis.com' in head_src:
        sys.exit('Lien Google Fonts non retiré')

    today = datetime.date.today().isoformat()
    digest = hashlib.sha256(source.encode()).hexdigest()[:6]
    version = '%s.%s' % (today, digest)
    font_css = (
        '@font-face { font-family: "Instrument Sans"; font-style: normal; font-weight: 400 700; font-stretch: 75% 100%; font-display: swap;'
        ' src: url(fonts/instrument-sans-latin-ext.woff2) format("woff2");'
        ' unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF; }\n'
        '@font-face { font-family: "Instrument Sans"; font-style: normal; font-weight: 400 700; font-stretch: 75% 100%; font-display: swap;'
        ' src: url(fonts/instrument-sans-latin.woff2) format("woff2");'
        ' unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD; }')
    head = '\n'.join([
        '<!doctype html>',
        '<html lang="fr">',
        '<head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
        '<title>%s</title>' % NAME,
        '<meta name="description" content="%s">' % DESCRIPTION,
        '<meta name="theme-color" content="%s">' % BG,
        '<meta name="color-scheme" content="dark light">',
        '<link rel="manifest" href="manifest.webmanifest">',
        '<link rel="icon" href="icons/favicon-32.png" sizes="32x32" type="image/png">',
        '<link rel="icon" href="icons/icon-192.png" sizes="192x192" type="image/png">',
        '<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">',
        '<meta name="mobile-web-app-capable" content="yes">',
        '<meta name="apple-mobile-web-app-capable" content="yes">',
        '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">',
        '<meta name="apple-mobile-web-app-title" content="%s">' % NAME,
        splash_links(),
        '<link rel="preload" href="fonts/instrument-sans-latin.woff2" as="font" type="font/woff2" crossorigin>',
        '<style>\n%s\n</style>' % font_css,
        '<script>window.CARNET_VERSION = "%s";</script>' % version,
    ])
    html = head + '\n' + head_src + '</head>\n<body>\n' + body_src.rstrip() + '\n</body>\n</html>\n'
    write(os.path.join(out, 'index.html'), html)

    # Manifeste
    manifest = {
        'id': './',
        'name': '%s · nutrition et muscu' % NAME,
        'short_name': NAME,
        'description': DESCRIPTION,
        'lang': 'fr',
        'dir': 'ltr',
        'start_url': './',
        'scope': './',
        'display': 'standalone',
        'background_color': BG,
        'theme_color': BG,
        'categories': ['health', 'fitness', 'food'],
        'icons': [
            {'src': 'icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
            {'src': 'icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
            {'src': 'icons/icon-maskable-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'maskable'},
            {'src': 'icons/icon-maskable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
        ],
        'shortcuts': [
            {'name': 'Ajouter un aliment', 'short_name': 'Ajouter', 'url': './?ajouter', 'icons': [{'src': 'icons/shortcut-add.png', 'sizes': '96x96', 'type': 'image/png'}]},
            {'name': 'Séances', 'url': './#seances', 'icons': [{'src': 'icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png'}]},
        ],
    }
    shots = sorted(f for f in os.listdir(os.path.join(out, 'screens'))) if os.path.isdir(os.path.join(out, 'screens')) else []
    if shots:
        manifest['screenshots'] = [{'src': 'screens/' + f, 'sizes': '1170x2532', 'type': 'image/webp', 'form_factor': 'narrow', 'label': lbl}
                                   for f, lbl in zip(shots, ['Le journal du jour', 'Les séances', 'Le suivi du poids'])]
    write(os.path.join(out, 'manifest.webmanifest'), json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

    # Service worker
    ex = [os.path.join(out, 'ex', f) for f in os.listdir(os.path.join(out, 'ex'))] if os.path.isdir(os.path.join(out, 'ex')) else []
    media_version = file_hash(ex)[:8] if ex else 'v1'
    # Planche de vignettes : gardée sur le téléphone dès l’installation (son nom contient son empreinte)
    atlas = sorted('ex/' + os.path.basename(p) for p in ex if os.path.basename(p).startswith('vignettes'))
    if ex and 'url("%s")' % atlas[-1] not in source:
        sys.exit('La source ne pointe pas vers %s : lance d’abord src/build_media.py' % atlas[-1])
    core = ['./', 'manifest.webmanifest', 'fonts/instrument-sans-latin.woff2', 'fonts/instrument-sans-latin-ext.woff2',
            'icons/icon-192.png', 'icons/favicon-32.png']
    sw = read(os.path.join(HERE, 'sw.template.js'))
    sw = (sw.replace('__VERSION__', version).replace('__MEDIA__', media_version)
            .replace('__CORE_FILES__', json.dumps(core)).replace('__MEDIA_FILES__', json.dumps(atlas)))
    write(os.path.join(out, 'sw.js'), sw)
    write(os.path.join(out, '.nojekyll'), '')
    print('site construit :', out, '| version', version, '| photos', media_version, '| page', len(html) // 1024, 'Ko')
    return version


if __name__ == '__main__':
    args = sys.argv[1:]
    def opt(name):
        if name in args:
            i = args.index(name)
            v = args[i + 1]
            del args[i:i + 2]
            return v
        return None
    media = opt('--media')
    fonts = opt('--fonts')
    assets = '--assets' in args
    if assets:
        args.remove('--assets')
    if len(args) != 2:
        sys.exit(__doc__)
    build(args[0], args[1], assets, media, fonts)
