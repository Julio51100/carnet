# Nutrisport

Nutrisport (anciennement Carnet) : carnet de nutrition et de musculation, avec repas et macros, séances, poids et objectifs.
Une appli web à installer sur l’écran d’accueil du téléphone, qui fonctionne aussi sans réseau.

## Installer l’appli

- **iPhone** : ouvrir le lien dans Safari, toucher Partager, puis « Sur l’écran d’accueil ». Ouvrir ensuite Nutrisport depuis son icône.
- **Android** : ouvrir le lien dans Chrome, puis toucher « Installer » dans l’appli (ou menu ⋮, « Installer l’application »).

## Les données

Le carnet de chaque personne reste sur son téléphone (IndexedDB) : rien n’est envoyé sur un serveur et personne d’autre ne le voit.
Exporter une sauvegarde de temps en temps depuis l’onglet Objectifs : elle permet de tout retrouver sur un autre téléphone.
Sur iPhone, supprimer l’icône efface aussi le carnet.

## Mettre à jour

La page de l’appli est `src/carnet.html`, la même que la version publiée dans Claude. Après une modification :

```sh
python3 src/build_site.py src/carnet.html . --fonts src/fonts
```

Ajouter `--assets` pour refaire les icônes et les écrans de lancement à partir du logo `src/logo.png` (Pillow et Playwright requis), puis publier les fichiers.
Les applis déjà installées récupèrent la nouvelle version à la prochaine ouverture avec du réseau.

## Crédits

- Photos d’exercices : [Free Exercise DB](https://github.com/yuhonas/free-exercise-db), domaine public (Unlicense). Pour en changer : `src/build_media.py`.
- Vidéos d’exercices : liens vers des démonstrations publiées sur YouTube par leurs auteurs (chaîne citée dans chaque fiche) ; elles ne sont pas copiées dans le dépôt.
- Police : [Instrument Sans](https://github.com/Instrument/instrument-sans), SIL Open Font License (voir `fonts/OFL.txt`).
