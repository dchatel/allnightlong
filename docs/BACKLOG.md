# Backlog

Idées et améliorations notées pour plus tard, pas encore planifiées dans un lot.

## Rapport d'observation

- [ ] Placer le cadre de notes global de l'observation **au-dessus** de la liste des cibles (actuellement en dessous).
- [x] Poses bon / passable / mauvais au niveau de l'observation (le champ), plus par cible : tout le stack est traité de la même façon pour chaque objet du champ. La cible garde sa hauteur et ses notes. Migration : remonter les comptes ; s'ils diffèrent entre cibles, prendre la première et signaler dans « Données à vérifier ».
- [x] Image favorite par cible : ouvrir une observation depuis une cible montre sa favorite à elle, et la galerie du rapport s'ouvre filtrée sur cette cible.
  - Base : `observations.favorite_image_id` (champ entier, remplace `is_favorite`) et `observation_targets.favorite_image_id` (une favorite par cible), remis à vide si l'image est supprimée.
  - Éditeur d'image : les coches deviennent des chips « Champ entier », « objet A », « objet B »… ; choix multiple pour les objets, « Champ entier » exclusive. Chaque chip cochée porte une étoile = favorite de cet objet (remplace l'ancienne favorite de l'objet).
  - Décocher une chip retire à l'image la favorite de cet objet seulement ; passer du champ entier aux objets (ou l'inverse) retire la favorite de l'ancien choix.
  - Liste des images : plus de bouton étoile, seulement la croix ; à sa gauche, alignés à droite : objets, puis type. L'étoile se place devant chaque objet dont l'image est la favorite, en gras (ex. « M 42 + ⭐ **NGC 1977** · Traitée »).
  - Liste principale : favorite du champ ; depuis une cible : favorite de la cible, sinon sa première image, sinon celle du champ.

## Général

- [ ] Renommer le titre « AwakeTonight » en « AllNightLong » (barre de titre `TitleBar.svelte`, écran de chargement `+layout.svelte`).
- [ ] Réglage de la taille des polices dans les paramètres : un facteur appliqué à la taille par défaut (ex. 90 %, 100 %, 115 %, 130 %).
