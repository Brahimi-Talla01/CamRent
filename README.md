# CamRent

**Analyse et estimation des loyers au Cameroun - périmètre initial : Yaoundé et Douala.**

CamRent est une plateforme Data/ML qui exploite des données immobilières (principalement des annonces)
pour estimer le prix d'un logement, fournir une fourchette d'estimation, explorer les prix par zone et
comparer des logements. Le modèle ML est un composant central, pas le produit entier.

## Documentation de référence

| Emplacement                                          | Contenu                                                 |
| ---------------------------------------------------- | ------------------------------------------------------- |
| [`context/`](./context/)                             | Contexte produit et technique utilisé par les agents IA |
| [`context/feature-specs/`](./context/feature-specs/) | Une spec par phase (00 → 12)                            |
| [`assets/`](./assets/)                               | Documents de conception amont                           |

Fichiers de contexte clés :

- `context/project-overview.md` — vision, utilisateurs, MVP, hors périmètre
- `context/architecture-context.md` — stack, frontières système, invariants
- `context/code-standards.md` — conventions de code
- `context/ai-workflow-rules.md` — workflow de développement par phases
- `context/progress-tracker.md` — état d'avancement

## Structure du dépôt

```
.
├── data/
│   ├── raw/            données brutes immuables (non versionnées)
│   ├── processed/      données nettoyées / Silver (non versionnées)
│   └── samples/        échantillons exploratoires (Phase 0)
├── ingestion/          scripts de collecte (Phase 1)
├── pipelines/          orchestration des étapes de pipeline
├── dbt/                transformations SQL versionnées (Phase 4)
├── ml/
│   ├── notebooks/      analyse exploratoire (Phase 3)
│   ├── src/            features & entraînement (Phases 5-6)
│   ├── models/         artefacts de modèles (non versionnés)
│   └── evaluation/     métriques par segment
├── backend/            API FastAPI (Phase 8)
├── frontend/           application Next.js + TypeScript (Phase 9)
├── tests/
│   ├── unit/           parsing, normalisation, features, services
│   ├── integration/    API ↔ DB, API ↔ Model, Pipeline ↔ DB
│   ├── data/           nulls, types, ranges, unicité, fraîcheur
│   └── e2e/            parcours complet
├── infrastructure/     Docker / déploiement
├── .github/workflows/  CI (Phase 12)
├── context/            contexte produit et technique
├── assets/             documents de conception
├── docker-compose.yml  services locaux (PostgreSQL, MVP)
├── pyproject.toml      dépendances et outillage Python
└── .env.example        variables d'environnement attendues
```

Cette structure suit le Plan Technique §55. Les dossiers `backend/`, `frontend/`, `dbt/` restent
vides jusqu'à leur phase respective.

## Démarrage (Phase 0-1)

```bash
cp .env.example .env          # renseigner les valeurs
docker compose up -d postgres  # base locale
```

Installation des dépendances Python selon l'outillage retenu (pip / uv), par exemple :

```bash
pip install pandas pyarrow SQLAlchemy "psycopg[binary]"
pip install -e ".[ml,api,quality,dev]"   # quand le backend de build sera ajouté
```

## Roadmap

Le projet suit 13 phases (Plan Technique §59-69), une spec par phase dans `context/feature-specs/` :

```
00 Validation du problème   →  05 Baseline ML        →  10 Orchestration
01 Data ingestion           →  06 Modèles ML         →  11 Observabilité
02 Data cleaning            →  07 Model registry     →  12 Production
03 EDA                      →  08 API
04 Data marts               →  09 Frontend
```

> **Principe directeur :** ne pas commencer par coder l'interface. Prouver d'abord que le problème
> Data est correctement défini et que les données permettent une estimation utile.
