# Code Standards

## Général

- Modules courts et à responsabilité unique.
- Corriger la cause racine, pas empiler des contournements.
- Ne jamais mélanger plusieurs responsabilités dans un même module ou script.
- Respecter les frontières définies dans `architecture-context.md`.

## Python

- Python typé (annotations de type) et formaté de façon cohérente sur tout le projet (`ruff` / `black` une fois l'outillage figé).
- Éviter les objets non typés ; valider les données externes aux frontières (Pydantic / Pandera).
- Les scripts d'ingestion et de transformation sont **idempotents** : rejouables sans effet de bord.
- Aucun chemin ni secret en dur : configuration via variables d'environnement.
- Une fonction = une responsabilité ; pas de script monolithique « tout-en-un ».

## SQL / transformations

- Privilégier SQL pour les transformations structurées.
- Nommage explicite : `stg_*` (staging), `int_*` (intermediate), `fct_*` (faits), `dim_*` (dimensions), `mart_*` (marts).
- Aucune transformation destructive sur les tables brutes.
- Les agrégats exposés doivent toujours inclure le **nombre d'observations**.

## Data Quality

- La qualité est une **fonctionnalité**, pas une tâche ponctuelle.
- Chaque étape critique a des tests : présence, volume, format, fraîcheur, nulls, types, ranges, unicité, cohérence.
- Seuils adaptés au contexte métier, jamais choisis arbitrairement.
- Ne pas supprimer automatiquement les valeurs extrêmes : les isoler et les analyser (quarantine).
- Distinguer doublon technique / même logement republié / logements réellement différents.

## ML

- Toujours commencer par une **baseline** (moyenne globale, médiane par ville, médiane par quartier+type).
- Un modèle n'est retenu que s'il **bat la baseline** de façon vérifiable.
- Mesurer les performances globalement **et par segment** (ville, quartier, type, chambres, niveau de prix).
- Séparation train / validation / test explicite ; privilégier une séparation chronologique si les données le permettent.
- Zéro data leakage : une feature ne doit dépendre que d'informations disponibles au moment de la prédiction.
- Ne pas utiliser `rent_per_m2` comme feature (dépend directement de la cible).
- Toute expérience est tracée (MLflow) : dataset/version, features, hyperparamètres, métriques, version du code, date.
- Le Deep Learning n'est pas une priorité du MVP.

## API

- Valider et parser l'entrée **avant** toute logique.
- Retourner des formes de réponse cohérentes et prévisibles.
- Les handlers restent fins : la complexité va dans des modules partagés.
- L'API retourne une fourchette, pas seulement une valeur ponctuelle.

## Frontend

- Next.js + TypeScript. Par défaut : composants serveur ; `"use client"` uniquement si nécessaire.
- L'interface met l'accent sur la **compréhension des données**, pas sur des dashboards surchargés.
- Toujours afficher le contexte : nombre d'observations, fourchette, limites de l'estimation.
- Ne jamais afficher un niveau de confiance non justifié statistiquement.

## Organisation des fichiers

- `ingestion/` — scripts de collecte et parsing.
- `pipelines/` — orchestration et enchaînement des étapes.
- `dbt/` — modèles SQL versionnés.
- `ml/` — notebooks, code d'entraînement, modèles, évaluation.
- `backend/` — API, services, repositories, schémas.
- `frontend/` — application Next.js.
- `tests/` — tests unitaires, d'intégration, de données, e2e.
- Nommer les fichiers d'après la responsabilité qu'ils portent, pas d'après la technologie.

## Nommage

- Unité monétaire : FCFA (XAF). La cible s'appelle `rent_price`.
- Quartiers : toujours normaliser (casse, accents, « Quartier - Ville ») avant comparaison.
- Colonnes en `snake_case`, en anglais pour le dataset ML (`city`, `neighborhood`, `property_type`, `bedrooms`, `bathrooms`, `area_m2`, `furnished`, `parking`, `gated`, `rent_price`).
