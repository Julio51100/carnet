# Nutrisport (anciennement Carnet) : consignes pour les mises à jour

Appli web installable (GitHub Pages) de Jules, appelée Nutrisport : nutrition, séances de musculation, suivi du poids. Interface en français, thème sombre par défaut.

## Où modifier

- `src/carnet.html` est la seule source de l’appli (CSS, HTML et script dans un fichier). La même page est aussi publiée comme artifact Claude : le code détecte `window.claude` et utilise alors la base de l’artifact au lieu de l’appareil. Ne casse pas ce mode.
- `index.html`, `sw.js` et `manifest.webmanifest` sont générés : ne les modifie pas à la main.
- Photos des exercices : `EX_MEDIA_FILES` et `EX_MEDIA` dans la source, fichiers `ex/*.webp` (départ | arrivée) et planche de vignettes `ex/vignettes-<empreinte>.webp`. Après un changement de photo, lance `python3 src/build_media.py src/carnet.html . --fedb <copie de github.com/yuhonas/free-exercise-db>` : il crée les photos manquantes, refait la planche (nouveau nom) et supprime les fichiers inutiles.
- Vidéos des exercices : `EX_VIDEO` (vidéo YouTube choisie) et `EX_VQ` (recherche YouTube précise) dans la source.
- Catalogue d’aliments : `FOOD_CATALOG_ROWS` (valeurs moyennes, rayon, rôle dans les propositions, portion habituelle, portions proposées facultatives), `FOOD_CATS` et `FOOD_KEYWORDS` (mots de recherche) dans la source.

## Après chaque modification

```sh
python3 src/build_site.py src/carnet.html . --fonts src/fonts
```

Le numéro de version (date + empreinte de la source) change tout seul : les applis installées affichent « Une nouvelle version de Nutrisport est prête » à la prochaine ouverture. Ajoute `--assets` seulement pour refaire les icônes et les écrans de lancement à partir du logo `src/logo.png` (Pillow et Playwright requis). Le logo sert d’icône sur l’écran d’accueil du téléphone (et d’écran de lancement) : Jules ne le veut pas dans l’en-tête de l’appli.

## Interface

Style « Épuré » choisi par Jules : fond graphite, Instrument Sans (étroite pour les gros chiffres), couleurs réservées aux macros (protéines bleu, glucides orange, lipides vert) et au vert des réussites. Cartes sans bordure en sombre, filet léger en clair.

- En-tête : un bonjour avec le pseudo sur Jour, le nom de l’onglet ailleurs, la photo de profil à droite. Le thème clair ou sombre se change dans le profil. L’état d’enregistrement ne s’affiche qu’en cas de problème.
- Jour : ce qu’il reste à manger en grand, les macros, la routine en quatre cases (créatine, eau, cardio, poids), la séance du jour, puis les repas, avec en tête l’assistant « Prépare ta journée ».
- Assistant (hors ligne, sans IA en ligne : rien ne quitte le téléphone) : Jules écrit ses consignes (« 3000 kcal, sans pomme, max 20 g d’amandes, du saumon ce soir, en 4 repas, j’ai foot ce soir »). `consParse` (dans la source) les découpe en éléments affichés en pastilles « Compris », chacune supprimable ; ce qui n’est pas compris est signalé, jamais deviné. La fenêtre « Prépare ta journée » complète les repas encore vides (objectif moins ce qui est noté) ou refait toute la journée. Les consignes valent pour le jour choisi seulement (gardées sur l’appareil, clé `cpm.consignes`) et ne changent ni les produits ni les réglages ; seul le cardio du jour est coché ou décoché quand elles le disent. Tests de l’analyseur : extraire le bloc « Assistant : consignes du jour » et le lancer dans Node.
- Séances : compteurs de la semaine et du mois, séance du jour, Mes séances, la semaine en cases, l’historique. Pendant une séance : barre de progression des séries, dernière fois en clair, badge de record.
- Ordre des exercices (séance du jour et séance type) : appui long (400 ms) sur le nom ou la photo d’un exercice, la liste se replie autour du doigt, l’exercice suit le doigt et se pose à sa nouvelle place, avec « Annuler » dans le message. « Monter » et « Descendre » restent dans le menu de l’exercice (clavier, lecteur d’écran). Code : bloc « Séances : changer l’ordre des exercices au doigt » ; l’écouteur `touchmove` non passif sur `#wEditor` doit rester posé d’avance (sinon iOS fait défiler la page pendant le glisser).
- Produits : deux vues, « Mes produits » (ta base) et « Catalogue » (par rayon, recherche, filtre « Cochés »). Chaque ligne a une case : coché = l’appli peut le proposer dans les repas (proposer une journée et idées pour compléter). Le maximum par jour se règle dans la fenêtre du produit, la fiche de l’aliment ou « Aliments utilisés ».

## Règles

- Les données de chacun restent sur son téléphone (IndexedDB, base `carnet:<chemin de l’appli>`, documents rangés par chemin : `days/AAAA-MM-JJ`, `products/<id>`, `workouts/<id>`, `programs/<id>`, `meals/<id>`, `exercises/<id>`, `settings/goals|profile|generator|foods|ui|me`). `settings/me` est le profil (pseudo et photo en data URL JPEG 320 px). Une mise à jour ne doit jamais effacer ni renommer ces chemins sans migration.
- Séances : l’onglet met en avant « Mes séances », les séances types que Jules crée. Une séance type (`programs/<id>`) garde ses exercices et les dernières charges de chacun (`items[].sets`). Une séance d’un jour (`workouts/<id>`) en est une copie et garde ses propres charges : charges prévues dans `sets[].pk/pr`, ce qui a été fait dans `kg/reps/done`. Seule une séance prévue ni commencée ni modifiée (`edited: false`) suit les changements de sa séance type ; une séance faite n’est jamais réécrite (celles d’avant ce modèle, sans champ `edited`, comptent comme modifiées). Une séance compte comme faite si sa date est passée ou aujourd’hui et qu’au moins une série a des répétitions. Après chaque enregistrement, la séance ouverte est relue depuis la base (nouvel objet) : un « Annuler » la retrouve par son identifiant, jamais par l’objet gardé avant.
- Produits de Jules : sa base (`products/<id>`) ne change que quand il modifie un produit lui-même ; une mise à jour n’y ajoute ni n’y réécrit rien (un produit enregistré sans changement n’est pas réécrit). Ses produits sont proposés sauf ceux décochés (`settings/generator`, `excluded`). Les aliments du catalogue ne sont jamais écrits dans `products/` : ils sont proposés seulement s’ils sont cochés (`settings/foods`, `on`). Le maximum par jour de n’importe quel aliment est dans `settings/foods` (`max`, par identifiant) et vaut pour toute la journée proposée et pour les idées (moins ce qui est déjà noté). Les identifiants `cat-…` du catalogue ne changent jamais (ils sont dans `settings/foods` et les journées) ; un aliment du catalogue qui porte le nom d’un produit de Jules (ou d’un produit courant `c-…`) est remplacé par ce produit, marqué « dans tes produits », et n’est jamais proposé en double.
- Le format de sauvegarde (`{ app: 'carnet', version: 1, exportedAt, data }`) doit rester lisible par les anciennes versions et inversement.
- Aucune donnée personnelle dans le dépôt : il est public.
- Le nom affiché est « Nutrisport » (titre, nom sous l’icône, écran de lancement, textes de l’appli). Les identifiants internes gardent « carnet » : dépôt et adresse `/carnet/`, fichier `src/carnet.html`, base IndexedDB `carnet:<chemin>`, caches du service worker, clés `cpm.*` et champ `app: 'carnet'` des sauvegardes. Ne les renomme pas : les données et les applis déjà installées en dépendent.
- Photo d’un exercice : seulement si elle montre le bon matériel (machine guidée, machine à disques, poulie, Smith, barre, haltères…) et le bon mouvement. Pour une variante proche (prise, un bras, barre EZ au lieu de droite…), ajoute une légende qui dit ce qui change. Sinon pas de photo : la fiche montre la vidéo en premier.
- Vidéo d’un exercice : uniquement un identifiant relevé dans un vrai résultat et vérifié avec `https://www.youtube.com/oembed?url=https://youtu.be/<id>&format=json` (titre et chaîne recopiés tels quels) ; elle doit montrer cet exercice sur ce matériel. Ajoute une précision (5ᵉ valeur) quand elle montre une variante proche. Dans le doute, pas de vidéo : la recherche `EX_VQ` prend le relais.
- Teste sur une largeur de téléphone (390 px) en thème sombre et clair, hors ligne compris, avant de publier.
