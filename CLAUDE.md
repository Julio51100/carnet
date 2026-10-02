# Carnet : consignes pour les mises à jour

Appli web installable (GitHub Pages) de Jules : nutrition, séances de musculation, suivi du poids. Interface en français, thème sombre par défaut.

## Où modifier

- `src/carnet.html` est la seule source de l’appli (CSS, HTML et script dans un fichier). La même page est aussi publiée comme artifact Claude : le code détecte `window.claude` et utilise alors la base de l’artifact au lieu de l’appareil. Ne casse pas ce mode.
- `index.html`, `sw.js` et `manifest.webmanifest` sont générés : ne les modifie pas à la main.
- Photos des exercices : `EX_MEDIA_FILES` et `EX_MEDIA` dans la source, fichiers `ex/*.webp` (départ | arrivée) et planche de vignettes `ex/vignettes-<empreinte>.webp`. Après un changement de photo, lance `python3 src/build_media.py src/carnet.html . --fedb <copie de github.com/yuhonas/free-exercise-db>` : il crée les photos manquantes, refait la planche (nouveau nom) et supprime les fichiers inutiles.
- Vidéos des exercices : `EX_VIDEO` (vidéo YouTube choisie) et `EX_VQ` (recherche YouTube précise) dans la source.

## Après chaque modification

```sh
python3 src/build_site.py src/carnet.html . --fonts src/fonts
```

Le numéro de version (date + empreinte de la source) change tout seul : les applis installées affichent « Une nouvelle version de Carnet est prête » à la prochaine ouverture. Ajoute `--assets` seulement pour refaire les icônes et les écrans de lancement à partir du logo `src/logo.png` (Pillow et Playwright requis). Le logo sert d’icône sur l’écran d’accueil du téléphone (et d’écran de lancement) : Jules ne le veut pas dans l’en-tête de l’appli.

## Règles

- Les données de chacun restent sur son téléphone (IndexedDB, base `carnet:<chemin de l’appli>`, documents rangés par chemin : `days/AAAA-MM-JJ`, `products/<id>`, `workouts/<id>`, `programs/<id>`, `meals/<id>`, `exercises/<id>`, `settings/goals|profile|generator|ui|me`). `settings/me` est le profil (pseudo et photo en data URL JPEG 320 px). Une mise à jour ne doit jamais effacer ni renommer ces chemins sans migration.
- Le format de sauvegarde (`{ app: 'carnet', version: 1, exportedAt, data }`) doit rester lisible par les anciennes versions et inversement.
- Aucune donnée personnelle dans le dépôt : il est public.
- Photo d’un exercice : seulement si elle montre le bon matériel (machine guidée, machine à disques, poulie, Smith, barre, haltères…) et le bon mouvement. Pour une variante proche (prise, un bras, barre EZ au lieu de droite…), ajoute une légende qui dit ce qui change. Sinon pas de photo : la fiche montre la vidéo en premier.
- Vidéo d’un exercice : uniquement un identifiant relevé dans un vrai résultat et vérifié avec `https://www.youtube.com/oembed?url=https://youtu.be/<id>&format=json` (titre et chaîne recopiés tels quels) ; elle doit montrer cet exercice sur ce matériel. Ajoute une précision (5ᵉ valeur) quand elle montre une variante proche. Dans le doute, pas de vidéo : la recherche `EX_VQ` prend le relais.
- Teste sur une largeur de téléphone (390 px) en thème sombre et clair, hors ligne compris, avant de publier.
