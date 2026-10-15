# Phase 14 — Back-office : rapports et observabilité

Lire `context/architecture-context.md` (§Principes directeurs, §Sous-systèmes
fonctionnels) et `context/product/camrent-product-realignment.md` (§3.2) avant de
commencer.

Objectif : donner à l'équipe une vue d'ensemble et des rapports internes sur la santé
de la plateforme — qualité des données, exécutions, jobs ML, modèle actif, incidents —
en réutilisant les données déjà produites plutôt qu'en ajoutant des outils.

> **Statut (2026-10-15)** : spec de cadrage créée d'après le recadrage ;
> implémentation après la Phase 13 et, pour la dérive, après la Phase 11.

## Implementation

1. **Vue d'ensemble** — état des collectes, qualité, exécutions dbt, jobs ML, modèle
   actif épinglé et incidents récents.
2. **Rapports internes** — qualité (rejets et motifs, couverture par ville, quartier
   et type) et marché (marts, avec `n_observations` toujours affiché) ; rapports
   **publics** seulement après validation de leur méthodologie.
3. **Observabilité** — consommer les métriques de la Phase 11 (fraîcheur, volumes,
   qualité, dérive) : une seule source par métrique, aucun outil parallèle.
4. **Alertes** — fraîcheur, volume, qualité, dérive, échec de job ; seuils justifiés,
   pas de bruit.
5. **Audit** — journal des actions sensibles consultable (qui a promu, lancé ou
   désactivé quoi, et quand).

## Dependencies

- Phase 13 (fondations du back-office), Phase 11 (observabilité), Phase 4 (marts) et
  Phase 7 (registre de modèles).

## Scope Limits

- Pas de plateforme d'observabilité managée sans besoin mesuré.
- Pas de rapports publics dont la méthodologie n'a pas été validée.
- Pas de duplication des métriques : chaque métrique a une seule source.

## Check When Done

- La vue d'ensemble reflète l'état réel (collectes, qualité, jobs, modèle actif) sans
  calcul divergent de celui des rapports de phase.
- Chaque statistique affichée porte son nombre d'observations.
- Les alertes existent avec des seuils documentés et ne génèrent pas de bruit.
- Le journal d'audit est consultable et couvre les actions sensibles.
