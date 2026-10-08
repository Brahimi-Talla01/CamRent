# Architecture Context

## Principes directeurs

1. **Data before model** — la priorité est : qualité des données → pipeline fiable → analyse → modèle → produit. Le modèle ML n'est pas le cœur unique du projet.
2. **Raw data immuable** — les données brutes ne sont jamais écrasées. Flux : `RAW → CLEAN → TRANSFORMED → ANALYTICAL`. Cela permet de rejouer les traitements si une erreur est découverte.
3. **Reproductibilité** — mêmes données + même version du code → mêmes transformations, et autant que possible mêmes modèles.
4. **Séparation des responsabilités** — ingestion, stockage, qualité, transformation, analyse, entraînement ML, serving, application sont séparés.
5. **Observabilité** — on doit pouvoir savoir si les pipelines fonctionnent, si les données arrivent, si leur qualité se dégrade, si les volumes changent brutalement, si le modèle devient moins performant.
6. **Pas de sur-engineering** — on ajoute une technologie uniquement quand elle répond à un besoin réel (§72-74).

## Stack cible

| Couche              | Technologie                         | Rôle                                                                 |
| ------------------- | ----------------------------------- | -------------------------------------------------------------------- |
| Ingestion           | Python                              | Collecte des sources (web, fichiers, API, contributions)             |
| Raw storage         | Parquet / JSON + Object Storage     | Conservation des données brutes (filesystem local → S3/R2/MinIO)     |
| Base relationnelle  | PostgreSQL                          | Base opérationnelle + analytique principale                          |
| Géospatial          | PostGIS                             | Latitude/longitude, points, zones, distances                         |
| Transformation      | SQL + Python, puis dbt              | Staging → intermediate → marts                                       |
| Orchestration       | Python/cron au début, puis Airflow  | Planification, dépendances, retries, logs                            |
| Data quality        | dbt tests + Pandera ou Great Expectations | Validations Bronze/Silver, dérive, fraîcheur                   |
| ML                  | scikit-learn, puis XGBoost/LightGBM | Régression supervisée de `rent_price`                                |
| Experiment tracking | MLflow                              | Expériences, hyperparamètres, métriques, modèles, versions           |
| API                 | FastAPI                             | Serving des prédictions et données de marché                         |
| Frontend            | Next.js + TypeScript                | Application utilisateur                                              |
| Conteneurisation    | Docker                              | Environnement local standardisé                                      |
| CI/CD               | GitHub Actions / GitLab CI          | Lint → tests → data tests → build → deploy                           |
| Streaming           | Non nécessaire au MVP               | (Kafka/Redpanda plus tard, si réellement justifié)                   |

## System boundaries / structure cible

Voir Plan Technique §55 :

```
camrent/
│
├── docs/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── samples/
│
├── ingestion/
│
├── pipelines/
│
├── dbt/
│
├── ml/
│   ├── notebooks/
│   ├── src/
│   ├── models/
│   └── evaluation/
│
├── backend/
│
├── frontend/
│
├── tests/
│
├── infrastructure/
│
├── .github/
│
├── docker-compose.yml
└── README.md
```

- `ingestion/` — collecte des sources brutes (web, fichiers, API, contributions). Vérifie les CGU / robots.txt avant toute collecte automatisée.
- `data/` — données brutes immuables, données traitées, échantillons. Ne jamais écraser `raw/`.
- `pipelines/` — orchestration et enchaînement des étapes du pipeline.
- `dbt/` — transformations SQL versionnées (staging / intermediate / marts).
- `ml/` — notebooks EDA, code d'entraînement/évaluation, modèles, évaluation par segment.
- `backend/` — API Python (FastAPI), services, repositories, schémas.
- `frontend/` — application Next.js + TypeScript.
- `tests/` — tests unitaires, d'intégration, de données, end-to-end.
- `infrastructure/` — Docker, configuration de déploiement.

## Architecture des données (Bronze / Silver / Gold)

- **Bronze** — données brutes telles que collectées, peu ou pas transformées. Ex : `price = "180 000 FCFA"`, `location = "Bonamoussadi"`.
- **Silver** — données nettoyées et standardisées : types corrigés, valeurs normalisées, doublons traités, valeurs manquantes identifiées, unités harmonisées. Ex : `price = 180000`, `city = Douala`, `neighborhood = Bonamoussadi`, `property_type = apartment`.
- **Gold** — données prêtes pour l'analyse, les dashboards, le ML et l'API. Ex : `ml_rent_dataset` avec les features finales.

## Pipeline de données

```
Extract → Ingest → Raw Storage → Validate → Clean → Standardize → Deduplicate
→ Enrich → Transform → Quality Checks → Analytical Tables → ML Dataset
```

Le mode d'exécution du MVP est **batch** (ex. tous les jours). Le streaming n'est pas requis au MVP.

## Modèle de stockage

- **Raw** : Object Storage / Parquet / JSON, organisé par date (`raw/listings/2026-10-01/`, `raw/user_submissions/`, `raw/reference_data/`).
- **PostgreSQL** : données normalisées (`properties`, `locations`, `neighborhoods`, `cities`, `amenities`, `listings`), données de marché (`rent_observations`, `market_statistics`), données applicatives (`users`, `prediction_requests`, `predictions`, `feedback`).
- Pour le MVP, PostgreSQL joue à la fois le rôle de base opérationnelle et analytique. Un Data Warehouse ne sera introduit que si les volumes/workloads le justifient.
- **MongoDB** : non obligatoire pour le MVP. À n'ajouter que si les données semi-structurées deviennent un vrai besoin.

## Flux ELT / ETL

- Philosophie principale : **ELT** (Extract → Load → Transform) pour conserver les données originales et permettre le retraitement.
- **ETL ciblé** dans l'ingestion lorsque nécessaire (parsing, extraction, conversion de format, élimination de données manifestement invalides).

## Modèle de serving

- **API de prédiction** : `POST /api/v1/predictions` → `estimated_rent`, `lower_bound`, `upper_bound`, `currency`, `model_version`.
- **API de marché** : `GET /api/v1/market/cities`, `/market/neighborhoods`, `/market/prices`.
- **API de comparaison** : `POST /api/v1/comparisons`.
- Le backend ne fait pas de travail ML long : il appelle le modèle et/ou les tables Gold.

## Décisions techniques provisoires

| Domaine               | Choix initial                    | Évolution possible                        |
| --------------------- | -------------------------------- | ----------------------------------------- |
| Raw storage           | Parquet + Object Storage         | S3 / R2 / MinIO                           |
| Document store        | MongoDB si nécessaire            | MongoDB cluster                           |
| Base relationnelle    | PostgreSQL                       | Data Warehouse                            |
| Géospatial            | PostGIS                          | Infrastructure géospatiale avancée        |
| Transformation        | SQL + Python                     | dbt                                       |
| Orchestration         | Python/cron au début             | Airflow                                   |
| Data quality          | dbt tests + Pandera/GE           | Soda / GE avancé                          |
| ML                    | scikit-learn                     | XGBoost / LightGBM                        |
| Experiment tracking   | MLflow                           | Plateforme ML                             |
| API                   | FastAPI                          | Architecture distribuée si nécessaire     |
| Frontend              | Next.js + TypeScript             | —                                         |
| Conteneurisation      | Docker                           | Kubernetes si réellement nécessaire       |
| CI/CD                 | GitHub Actions / GitLab CI       | —                                         |
| Streaming             | Non nécessaire au MVP            | Kafka / Redpanda                          |
| Cache                 | Non nécessaire initialement      | Redis                                     |

## Invariants

1. Les données brutes (`raw/`) ne sont **jamais** modifiées après collecte.
2. Les étapes de transformation sont reproductibles et versionnées.
3. Chaque étape critique du pipeline possède des contrôles qualité.
4. Un échec de pipeline ne doit pas remplacer un dataset Gold valide par un dataset vide ou invalide.
5. Les données invalides vont en **quarantine**, elles ne sont pas supprimées silencieusement.
6. Aucune feature ne doit introduire de **data leakage** (informations non disponibles au moment réel de la prédiction).
7. Aucune collecte automatisée sans vérification préalable des CGU / robots.txt / droits sur les données.
8. Aucune valeur affichée sans son **nombre d'observations** lorsque c'est une statistique de marché.
9. Une estimation n'est jamais présentée comme une valeur officielle du bien.
