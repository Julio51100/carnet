#!/usr/bin/env python3
"""Photos des exercices de Carnet : fichiers ex/*.webp et planche de vignettes.

Usage :
    python3 src/build_media.py src/carnet.html . [--fedb CHEMIN]

- Lit EX_MEDIA_FILES dans la source : la liste des photos utilisées, dans l’ordre de la planche.
- Crée les photos manquantes ex/<nom>.webp (départ | arrivée côte à côte) à partir d’une copie locale
  de Free Exercise DB (github.com/yuhonas/free-exercise-db, domaine public), donnée par --fedb.
- Refait la planche de vignettes ex/vignettes-<empreinte>.webp : son nom change avec son contenu,
  pour que les téléphones ne gardent pas une ancienne planche en cache.
- Met à jour la source (adresse de la planche, nombre de rangées) et supprime les photos qui ne servent plus.
Ensuite, reconstruire le site : python3 src/build_site.py src/carnet.html . --fonts src/fonts
"""
import hashlib
import io
import json
import os
import re
import sys

from PIL import Image

W, H = 640, 427          # une image d’exécution
TW, TH, COLS = 108, 72, 12  # une vignette, colonnes de la planche


def slug(name):
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', name.lower())).strip('-')


def main(src_path, out, fedb):
    src = open(src_path, encoding='utf-8').read()
    files = json.loads(re.search(r'const EX_MEDIA_FILES = (\[.*?\]);', src).group(1))
    ex_dir = os.path.join(out, 'ex')
    os.makedirs(ex_dir, exist_ok=True)

    # Photos manquantes, depuis Free Exercise DB
    fedb_dirs = {}
    if fedb:
        base = os.path.join(fedb, 'exercises')
        fedb_dirs = {slug(d): os.path.join(base, d) for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))}
    for name in files:
        path = os.path.join(ex_dir, name + '.webp')
        if os.path.exists(path):
            continue
        if name not in fedb_dirs:
            sys.exit('Photo absente : %s (indique la copie de Free Exercise DB avec --fedb)' % name)
        sheet = Image.new('RGB', (2 * W, H))
        for i in range(2):
            frame = Image.open(os.path.join(fedb_dirs[name], '%d.jpg' % i)).convert('RGB').resize((W, H), Image.LANCZOS)
            sheet.paste(frame, (i * W, 0))
        sheet.save(path, 'WEBP', quality=70, method=6)
        print('photo ajoutée :', name)

    # Planche de vignettes (première image de chaque photo)
    rows = (len(files) + COLS - 1) // COLS
    atlas = Image.new('RGB', (COLS * TW, rows * TH), (128, 128, 128))
    for i, name in enumerate(files):
        im = Image.open(os.path.join(ex_dir, name + '.webp')).convert('RGB')
        first = im.crop((0, 0, im.width // 2, im.height)).resize((TW, TH), Image.LANCZOS)
        atlas.paste(first, ((i % COLS) * TW, (i // COLS) * TH))
    buf = io.BytesIO()
    atlas.save(buf, 'WEBP', quality=64, method=6)
    data = buf.getvalue()
    atlas_name = 'vignettes-%s.webp' % hashlib.sha256(data).hexdigest()[:8]
    with open(os.path.join(ex_dir, atlas_name), 'wb') as f:
        f.write(data)

    # Fichiers qui ne servent plus
    keep = {n + '.webp' for n in files} | {atlas_name}
    gone = sorted(f for f in os.listdir(ex_dir) if f not in keep)
    for f in gone:
        os.remove(os.path.join(ex_dir, f))

    # Source : adresse de la planche et nombre de rangées
    new = re.sub(r'url\("ex/vignettes[^"]*\.webp"\)', 'url("ex/%s")' % atlas_name, src)
    new = re.sub(r'const EX_MEDIA_COLS = \d+, EX_MEDIA_ROWS = \d+;', 'const EX_MEDIA_COLS = %d, EX_MEDIA_ROWS = %d;' % (COLS, rows), new)
    if 'url("ex/%s")' % atlas_name not in new:
        sys.exit('Adresse de la planche introuvable dans la source')
    if new != src:
        with open(src_path, 'w', encoding='utf-8') as f:
            f.write(new)
    print('photos : %d | planche : %s (%d Ko, %d rangées) | supprimés : %s'
          % (len(files), atlas_name, len(data) // 1024, rows, ', '.join(gone) or 'aucun'))


if __name__ == '__main__':
    args = sys.argv[1:]
    fedb = None
    if '--fedb' in args:
        i = args.index('--fedb')
        fedb = args[i + 1]
        del args[i:i + 2]
    if len(args) != 2:
        sys.exit(__doc__)
    main(args[0], args[1], fedb)
