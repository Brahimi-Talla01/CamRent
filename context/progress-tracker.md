# Progress Tracker

Mettre à jour ce fichier dès que la phase courante, la fonctionnalité active ou l'état d'implémentation change.

## Current Phase

- **Phase 0 — Validation du problème** (en cours)

## Current Goal

- Produire l'échantillon exploratoire et les rapports de qualité qui valident la faisabilité du problème ML (livrables attendus par le Plan Technique §77).

## Completed

- **Documents de conception (amont)** : les trois documents de référence sont rédigés et servent d'entrée au projet.
  - `assets/CamRent_Conception_Produit_et_Probleme_Data.md` — conception produit et définition du problème Data.
  - `assets/CamRent_Plan_Technique_Implementation_Architecture_Data_ML.md` — architecture Data/ML/applicative et roadmap.
  - `assets/Data_Discovery_Report.md` — Data Discovery Report (sources, volumes, qualité, contraintes, faisabilité).

## In Progress

- **Phase 0 — Validation du problème** : le Data Discovery Report est rédigé. Restent à produire :
  - `data/samples/` — échantillons bruts par source (`geloka_sample.csv`, `koutchoumi_sample.csv`, `jumia_sample.csv` si dispo) ;
  - `profiling/` — `missing_values_report.md`, `duplicates_report.md`, distributions ;
  - `quality_report/` — score qualité + recommandations ;
  - `eda/` — première analyse (univariée, bivariée, insights).

## Next Up

- Phase 1 — Data ingestion (scripts de collecte, stockage Raw, métadonnées, premières validations).

## Open Questions

- **Tension de stack à trancher** : le Data Discovery Report (§5.3) propose de figer MongoDB + Airflow + dbt + AWS/GCP, tandis que le Plan Technique (§71-74) demande de ne **rien figer avant l'EDA**. Décision retenue à ce stade : suivre le Plan Technique (ne rien figer), conformément à `architecture-context.md`.
- Quelle méthode d'intervalle de prédiction retenir (quantiles, bootstrapping, quantile regression…) ? À décider après expérimentation (Phases 5-6).
- Séparation train / validation / test : aléatoire ou chronologique ? À décider selon la disponibilité de la date de publication.
- Comment traiter la **surface manquante** (< 10 % de disponibilité) : imputation, exclusion, ou modèle sans surface ?
- Périmètre géographique exact du MVP (liste des quartiers de Yaoundé et Douala retenus).

## Architecture Decisions

- Suivre l'architecture **progressive** du Plan Technique : ne pas introduire Airflow / MongoDB / Data Warehouse / streaming avant besoin réel.
- **ELT** comme philosophie principale, avec ETL ciblé dans l'ingestion.
- **PostgreSQL** joue le rôle de base opérationnelle **et** analytique au MVP.
- **Bronze / Silver / Gold** comme organisation des données.
- **Baseline avant modèle** : aucun modèle ML complexe tant qu'une baseline mesurée n'est pas battue.
- Cible = `rent_price` (prix demandé dans les annonces), à ne pas confondre avec le prix réellement payé.

## Session Notes

- Dépôt au stade planification : `assets/` (documents de conception), `docs/` (vide), `inspire/` (exemples de référence).
- Ce dossier `context/` est le point d'entrée de tout agent IA travaillant sur CamRent.
- Les `feature-specs/` sont numérotées par phase (`00` → `12`), conformément au Plan Technique §59-69.
