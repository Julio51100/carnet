# Carnet : consignes pour les mises à jour

Appli web installable (GitHub Pages) de Jules : nutrition, séances de musculation, suivi du poids. Interface en français, thème sombre par défaut.

## Où modifier

- `src/carnet.html` est la seule source de l’appli (CSS, HTML et script dans un fichier). La même page est aussi publiée comme artifact Claude : le code détecte `window.claude` et utilise alors la base de l’artifact au lieu de l’appareil. Ne casse pas ce mode.
- `index.html`, `sw.js` et `manifest.webmanifest` sont générés : ne les modifie pas à la main.

## Après chaque modification

```sh
python3 src/build_site.py src/carnet.html . --fonts src/fonts
```

Le numéro de version (date + empreinte de la source) change tout seul : les applis installées affichent « Une nouvelle version de Carnet est prête » à la prochaine ouverture. Ajoute `--assets` seulement pour redessiner l’icône ou les écrans de lancement (Playwright requis).

## Règles

- Les données de chacun restent sur son téléphone (IndexedDB, base `carnet:<chemin de l’appli>`, documents rangés par chemin : `days/AAAA-MM-JJ`, `products/<id>`, `workouts/<id>`, `programs/<id>`, `meals/<id>`, `exercises/<id>`, `settings/goals|profile|generator|ui`). Une mise à jour ne doit jamais effacer ni renommer ces chemins sans migration.
- Le format de sauvegarde (`{ app: 'carnet', version: 1, exportedAt, data }`) doit rester lisible par les anciennes versions et inversement.
- Aucune donnée personnelle dans le dépôt : il est public.
- Teste sur une largeur de téléphone (390 px) en thème sombre et clair, hors ligne compris, avant de publier.
