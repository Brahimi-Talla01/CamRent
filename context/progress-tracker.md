# Progress Tracker

Mettre à jour ce fichier dès que la phase courante, la fonctionnalité active ou l'état d'implémentation change.

## Current Phase

- **Phase 0 — Validation du problème** (livrables produits, en PR)

## Current Goal

- Clôturer l'issue #1 une fois la PR de Phase 0 mergée dans `develop`.

## Completed

- **Documents de conception (amont)** : les trois documents de référence sont rédigés et servent d'entrée.
  - `assets/CamRent_Conception_Produit_et_Probleme_Data.md`
  - `assets/CamRent_Plan_Technique_Implementation_Architecture_Data_ML.md`
  - `assets/Data_Discovery_Report.md`

- **Dépôt et outillage** : dépôt relié à GitHub (`Brahimi-Talla01/CamRent`), branches `main` (production) et `develop` (défaut), CI/CD (`.github/workflows/`), protection par ruleset (PR obligatoire, `CI` requis, pas de force-push).
- **Contexte IA** : `context/` (6 fichiers + `feature-specs/` par phase) et `AGENTS.md`.
- **Phase 0 — livrables** dans `docs/phase-0/` :
  - `data-discovery-report.md` (10 points du Plan Technique §76)
  - `legal-assessment.md` (CGU / `robots.txt` / licence par source)
  - `feasibility.md` (verdict + décision de stack)
  - `profiling/missing_values_report.md`, `profiling/duplicates_report.md`
  - `quality_report/data_quality_score.md`, `quality_report/recommendations.md`
  - `eda/univariate_analysis.md`, `eda/bivariate_analysis.md`, `eda/insights.md`
  - `scripts/profile_sample.py` (reproductible, bibliothèque standard uniquement)
  - Échantillon (non versionné, source tierce sans licence) : `data/samples/`

## In Progress

- Aucun.

## Next Up

- Phase 1 — Data ingestion (issue #2), **après vérification des CGU** de Koutchoumi et Geloka.

## Open Questions

- **Collecte** : quelles sources retenir, et les CGU de Koutchoumi / Geloka autorisent-elles la collecte ?
- **Prix censurés** (Koutchoumi `"> X"`) : exclure ou modéliser comme bornes (`rent_price >= X`) ?
- **Surface** (absente) : la collecter, ou concevoir le MVP sans elle ?
- **Dataset tiers `deegeorgie`** : à garder strictement local (sans licence), non redistribué.
- Méthode d'intervalle de prédiction (quantiles, bootstrap, quantile regression) — à décider Phases 5-6.
- Séparation train/validation/test : aléatoire ou chronologique (dépend de la date de collecte).
- Périmètre géographique exact du MVP (liste des quartiers).

## Architecture Decisions

- Stack **Niveau 1 (prototype Data)** retenue : Python, CSV/Parquet, PostgreSQL, Pandas, scikit-learn.
  Non introduits : MongoDB, Airflow, dbt, AWS/GCP, Data Warehouse, streaming.
- **ELT** comme philosophie principale, avec ETL ciblé dans l'ingestion.
- **PostgreSQL** joue le rôle de base opérationnelle **et** analytique au MVP.
- **Bronze / Silver / Gold** comme organisation des données.
- **Baseline avant modèle** : aucun modèle complexe tant qu'une baseline mesurée n'est pas battue.
- Cible = `rent_price` (prix **demandé** dans les annonces).

## Session Notes

- Échantillon Phase 0 : 3 065 lignes brutes → **≈ 1 226 lignes uniques** (71,7 % de doublons Koutchoumi).
- `koutchoumi1.csv` : prix en **bornes** (`"> X FCFA"`), 98 % Douala.
- `jumia.csv` : 11 % d'annonces sans prix (« Contactez le vendeur »).
- Surface et date **absentes** des deux fichiers.
- `robots.txt` vérifiés le 2026-10-08 : Geloka `Allow: /` ; Koutchoumi directives **commentées**.
- Le dataset `deegeorgie` **ne déclare aucune licence** → non versionné, usage local seulement.
