# Composants tiers

AllNightLong est distribué sous licence Apache 2.0 (voir `LICENSE`).
Il intègre les composants suivants, soumis à leur propre licence.

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

## Leaflet

- Rôle : carte utilisée pour créer les lieux d'observation
- Version : 1.9.4 (paquet npm `leaflet`)
- Auteurs : Volodymyr Agafonkin, CloudMade et contributeurs
- Code source : https://github.com/Leaflet/Leaflet
- Licence : BSD 2-Clause (voir `licenses/Leaflet-BSD-2-Clause.txt`)

## Données cartographiques

Les fonds de carte, les adresses et les recherches de lieux viennent d'OpenStreetMap
(© contributeurs OpenStreetMap, données sous licence ODbL : https://www.openstreetmap.org/copyright),
via les serveurs de tuiles et le service Nominatim de la fondation OpenStreetMap.
L'altitude d'un lieu est fournie par Open-Meteo (https://open-meteo.com).
Ces données sont consultées en ligne et ne sont pas incluses dans l'application.
