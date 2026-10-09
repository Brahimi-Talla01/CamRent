# Progress Tracker

Mettre à jour ce fichier dès que la phase courante, la fonctionnalité active ou l'état d'implémentation change.

## Current Phase

- **Phase 1 — Data ingestion** (mergée dans `develop` via la PR #16, issue #2 close)

## Current Goal

- Démarrer la Phase 2 — Data cleaning (issue #3) : déduplication, conversion des types, référentiel géographique.

## Completed

- **Documents de conception (amont)** : les trois documents de référence sont rédigés et servent d'entrée.
  - `assets/CamRent_Conception_Produit_et_Probleme_Data.md`
  - `assets/CamRent_Plan_Technique_Implementation_Architecture_Data_ML.md`
  - `assets/Data_Discovery_Report.md`

- **Dépôt et outillage** : dépôt relié à GitHub (`Brahimi-Talla01/CamRent`), branches `main` (production) et `develop` (défaut), CI/CD (`.github/workflows/`), protection par ruleset (PR obligatoire, `CI` requis, pas de force-push).
- **Contexte IA** : `context/` (6 fichiers + `feature-specs/` par phase) et `AGENTS.md`.
- **Phase 0 — Validation du problème** (mergée dans `develop`, issue #1 close) dans `docs/phase-0/` :
  - `data-discovery-report.md`, `legal-assessment.md`, `feasibility.md`,
    `profiling/`, `quality_report/`, `eda/`, `scripts/profile_sample.py`.
  - Échantillon (non versionné, source tierce sans licence) : `data/samples/`.

- **Phase 1 — Data ingestion** (mergée dans `develop`, issue #2 close) dans `ingestion/` + `docs/phase-1/` :
  - package `ingestion/` : `config.py`, `models.py`, `http_client.py` (`requests` + `robots.txt` + débit + retries), `storage.py` (JSONL daté immuable + métadonnées de lot), `bronze.py`, `__main__.py` (CLI), `sources/` (`geloka`, `koutchoumi`, `reference_local`, `raw_document`).
  - porte légale : toute source non `verified`/`local` refuse de tourner sans `--confirm-legal`.
  - layout `data/raw/` conforme à la spec (`listings/`, `reference_data/`, `user_submissions/`, `metadata/`).
  - validations Bronze (présence, format, volume, clés, métadonnées, fraîcheur) — **16/16**.
  - tests `tests/unit/test_ingestion_*.py` (**18** tests, verts) ; `ruff` sans erreur.
  - revue légale : `docs/phase-1/legal-review.md` ; vérifications résumées dans `docs/phase-0/legal-assessment.md`.
  - minimisation : aucune donnée personnelle stockée (texte brut Koutchoumi non conservé).

## In Progress

- Aucun.

## Next Up

- Phase 2 — Data cleaning (issue #3) : déduplication, conversion des types, référentiel géographique, traitement des prix censurés.

## Open Questions

- **Prix censurés** (Koutchoumi `"> X"`) : exclure ou modéliser comme bornes (`rent_price >= X`) ? → Phase 2.
- **Surface** (absente) : la collecter, ou concevoir le MVP sans elle ? → Phase 2.
- **Référentiel géographique** : liste canonique des quartiers de Yaoundé / Douala → Phase 2.
- **Endpoints MINFI / INS** : documents stockés bruts, endpoints et formats à valider.
- **Dataset tiers `deegeorgie`** : usage strictement local (sans licence), non redistribué.
- Méthode d'intervalle de prédiction (quantiles, bootstrap, quantile regression) — Phases 5-6.
- Séparation train/validation/test : aléatoire ou chronologique ?
- Périmètre géographique exact du MVP (liste des quartiers).

## Architecture Decisions

- Stack **Niveau 1 (prototype Data)** retenue : Python, CSV/Parquet, PostgreSQL, Pandas, scikit-learn.
- **Couche HTTP d'ingestion** : `requests` (Phase 1), avec `robots.txt`, débit limité et User-Agent transparent.
- **ELT** comme philosophie principale, avec ETL ciblé dans l'ingestion ; **pas de normalisation** en Phase 1.
- **PostgreSQL** joue le rôle de base opérationnelle **et** analytique au MVP.
- **Bronze / Silver / Gold** comme organisation des données.
- **Baseline avant modèle** : aucun modèle complexe tant qu'une baseline mesurée n'est pas battue.
- Cible = `rent_price` (prix **demandé** dans les annonces).

## Session Notes

- Échantillon Phase 0 : 3 065 lignes brutes → **≈ 1 226 lignes uniques** (71,7 % de doublons Koutchoumi).
- `robots.txt` : Geloka `Allow: /` ; Koutchoumi directives commentées (aucune règle active).
- **Geloka** : CGU restrictives (usage personnel non commercial, pas de copie/redistribution) → baromètre utilisé comme repère agrégé avec citation.
- **Koutchoumi** : aucune CGU/ToS publiée ; structure observée = catégories `/<type>-to-rent-at-<city>-cameroon.html` (`?page=N`) + détails `/en/<id>/<slug>` (le slug encode ville/quartier/pièces/prix).
- Le dataset `deegeorgie` **ne déclare aucune licence** → non versionné, usage local seulement.
