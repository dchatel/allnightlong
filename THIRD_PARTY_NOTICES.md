# Composants tiers

AllNightLong est distribué sous licence Apache 2.0 (voir `LICENSE`).
Il intègre le composant suivant, soumis à sa propre licence.

## Aladin Lite

- Rôle : affichage de la carte céleste
- Version : 3.8.2 (paquet npm `aladin-lite`)
- Auteur : Centre de Données astronomiques de Strasbourg (CDS)
- Code source : https://github.com/cds-astro/aladin-lite
- Licence : GNU LGPL 3.0 (voir `licenses/LGPL-3.0.txt` et `licenses/GPL-3.0.txt`)

Le fichier `LICENSE` du paquet 3.8.2 contient le texte de la LGPL 3.0, alors que son
`package.json` et son README indiquent GPL 3.0. Le dépôt officiel est sous LGPL 3.0.

Aladin Lite n'a pas été modifié. Pour utiliser une autre version, changez celle indiquée
dans `frontend/package.json`, puis recompilez l'application depuis le code source
d'AllNightLong : https://github.com/dchatel/allnightlong
