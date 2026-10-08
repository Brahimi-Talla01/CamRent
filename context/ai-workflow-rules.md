# Development Workflow

## Approche

Construire CamRent de façon incrémentale selon un **workflow piloté par la spécification**. Les fichiers de `context/` définissent quoi construire, comment le construire, et l'état d'avancement. Toujours implémenter en s'appuyant sur ces specs — ne pas inférer ni inventer de comportement.

> **Principe directeur :** ne pas commencer par coder l'interface. Commencer par prouver que le problème Data est correctement défini et que les données permettent réellement de construire une estimation utile.

## Ordre des phases

Respecter l'ordre des phases (voir `feature-specs/`) :

```
Phase 0  Validation du problème
Phase 1  Data ingestion
Phase 2  Data cleaning
Phase 3  EDA
Phase 4  Data warehouse / marts
Phase 5  Baseline ML
Phase 6  Modèles ML
Phase 7  Model registry
Phase 8  API
Phase 9  Frontend
Phase 10 Orchestration
Phase 11 Observabilité
Phase 12 Production
```

## Règles de périmètre

- Travailler sur **une phase à la fois**.
- Préférer de petits incréments vérifiables à de grands changements spéculatifs.
- Ne pas mélanger plusieurs frontières de responsabilité dans une même étape (ex. pipeline + API, ou frontend + training).

## Quand découper le travail

Découper une étape si elle combine :

- des changements UI et des changements de pipeline ;
- du traitement Data et de la persistance en base ;
- plusieurs routes API non liées ;
- un comportement qui n'est pas clair dans les fichiers de contexte.

Si un changement ne peut pas être vérifié de bout en bout rapidement, son périmètre est trop large.

## Contraintes propres au projet

- **Légal d'abord** : aucune collecte automatisée sans vérifier CGU, `robots.txt`, droits sur les données et règles de stockage.
- **Raw immuable** : ne jamais modifier les données de `data/raw/` après collecte.
- **Reproductibilité** : toute transformation doit pouvoir être rejouée à l'identique.
- **Baseline d'abord** : aucun modèle complexe avant d'avoir une baseline mesurée qui batte la naïve.
- **Pas de sur-engineering** : ne pas introduire Airflow, MongoDB, Kafka, Spark, un Data Warehouse… sans besoin réel démontré (voir `architecture-context.md` §Décisions provisoires et Plan Technique §72-74).
- **Honnêteté des résultats** : ne jamais présenter une estimation comme une valeur officielle, ni une statistique sans son nombre d'observations.

## Gestion des exigences manquantes

- Ne pas inventer de comportement produit non défini dans les fichiers de contexte.
- Si une exigence est ambiguë, la résoudre dans le fichier de contexte concerné **avant** d'implémenter.
- Si une exigence est absente, l'ajouter comme **point ouvert** dans `progress-tracker.md` avant de continuer.
- En cas de tension entre deux documents, la signaler et trancher explicitement, puis mettre à jour le contexte.

## Composants de fondation protégés

Ne pas modifier les composants tiers générés/utilisés (bibliothèques, code généré, migrations appliquées) sans instruction explicite. La logique propre au projet se place dans les modules applicatifs.

## Garder la documentation à jour

Mettre à jour le fichier de contexte concerné dès qu'un changement affecte :

- l'architecture ou les frontières du système ;
- le modèle de stockage ;
- les conventions de code ;
- le périmètre des fonctionnalités.

L'état d'avancement (`progress-tracker.md`) doit refléter l'état **réel** de l'implémentation, pas l'état souhaité.

## Avant de passer à la phase suivante

1. La phase courante fonctionne de bout en bout dans son périmètre défini.
2. Aucun invariant de `architecture-context.md` n'a été violé.
3. Les livrables de la phase sont produits et vérifiés.
4. `progress-tracker.md` reflète le travail terminé.
