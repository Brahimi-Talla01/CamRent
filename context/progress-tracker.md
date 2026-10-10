# Progress Tracker

Mettre à jour ce fichier dès que la phase courante, la fonctionnalité active ou l'état d'implémentation change.

## Current Phase

- **Phase 3 — EDA** (implémentée et vérifiée, livrable dans `eda/`, PR vers `develop` à préparer)

## Current Goal

- Livrer le rapport EDA (`eda/univariate_analysis.md`, `eda/bivariate_analysis.md`, `eda/insights.md`) via une PR vers `develop` (issue #4).

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

- **Phase 2 — Data cleaning** (mergée dans `develop`, issue #3 close) dans `pipelines/` + `docs/phase-2/` :
  - package `pipelines/` : `geo.py` (référentiel seed + résolution), `parsing.py`, `adapters.py` (par source), `silver.py` (resolution, validation, dédup, quarantine, écriture), `report.py`, `__main__.py`.
  - sorties : `data/processed/silver_listings.parquet`, `quarantine_listings.parquet`, `docs/phase-2/cleaning-report.md`.
  - règles : types, villes/quartiers canoniques, catégories, valeurs bornées (`price_is_bound`), dédup (technique vs republication), aberrations signalées (jamais supprimées), invalides en quarantine.
  - construction réelle : Raw 3 078 → **2 992 lignes Silver**, **78 en quarantine** (cohérent avec ≈ 1 226 uniques : 1 970 republications).
  - tests `tests/unit/test_pipelines_*.py` (**19** tests) ; `ruff` sans erreur.

- **Phase 3 — Analyse exploratoire (EDA)** (branche `phase/3-eda`, issue #4) :
  - calcul des stats : `eda/compute_statistics.py` (calcule toutes les statistiques du Silver, écrit `eda/statistics.json`, artefact régénérable et ignoré par git).
  - rendu des rapports : `eda/generate_reports.py` (rendu **purement dérivé** de `statistics.json` — aucun chiffre en dur — vers `eda/univariate_analysis.md`, `eda/bivariate_analysis.md`, `eda/insights.md`).
  - résultats clés :
    - 2 992 lignes Silver (Douala 2 811, Yaoundé 181).
    - Distribution très asymétrique (skewness ≈ 35, kurtosis ≈ 1 412) → transformation `log1p` fortement recommandée (skewness ≈ 0,11 après).
    - 2 564 prix bornés (85,7 %), 1 970 republications (65,8 %), 17 aberrations (lignes conservées).
    - Quartiers sous-représentés : 172 quartiers distincts, dont 103 avec une seule observation ; 152 avec ≤ 10 observations → médianes non publiées en dessous de 30 observations.
    - Biais de couverture : top-5 quartiers = 68,7 % des lignes, 582 observations sur des quartiers non reconnus.
    - Pas de surface (`area_m2` absent), pas de date (`posted_at` absent), pas de meublé/parking/barrière → ces features sont inutilisables pour le MVP.
    - `koutchoumi` ne contribue que 5 lignes → non représentatif ; `reference_local` 2 987 lignes.
  - correction de bugs de génération (revue senior) : filtre `outlier_flags` (chaîne vide ≠ `NaN`, retenait à tort les 2 992 lignes), désalignement des médianes du top-5 quartiers, colonne « N chambres » affichant les effectifs, part « appartement » figée à 100 %, en-tête listant les colonnes au lieu des villes, et suppression de toutes les valeurs en dur (dates, pourcentages, moyennes).
  - tests : `36 passed, 1 skipped` (toute la suite unitaire, avec `requests`, `SQLAlchemy`, `psycopg` installés) ; `ruff` sans erreur sur `eda/`.

## In Progress

- Aucun (en attente de la PR de Phase 3).

## Next Up

- Phase 4 — Data marts (construction des marts à partir du Silver + des décisions de Phase 3).

## Open Questions

- **Prix censurés** : conservés avec `price_is_bound` (borne inférieure) ; stratégie de pondération/exclusion à figer en Phases 5-6.
- **Surface** (absente) : la collecter, ou concevoir le MVP sans elle ?
- **Référentiel géographique** : seed en place ; 582 quartiers Silver non reconnus à enrichir (Phase 3 ou 4).
- **Republications** : 1 970 lignes marquées `is_republication` ; décider si conservées/pondérées pour l'entraînement.
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
- **Silver** : Raw immuable → normalisation + validation + dédup ; aberrations **signalées** (`outlier_flags`), invalides en **quarantine** (jamais supprimées) ; aucune imputation permissive.
- **Périmètre Silver** : `koutchoumi` (live) + `reference_local` (jeux locaux `jumia.csv` / `koutchoumi1.csv`) ; Geloka exclu (médianes agrégées).

## Session Notes

- Échantillon Phase 0 : 3 065 lignes brutes → **≈ 1 226 lignes uniques** (71,7 % de doublons Koutchoumi).
- `robots.txt` : Geloka `Allow: /` ; Koutchoumi directives commentées (aucune règle active).
- **Geloka** : CGU restrictives (usage personnel non commercial, pas de copie/redistribution) → baromètre utilisé comme repère agrégé avec citation.
- **Koutchoumi** : aucune CGU/ToS publiée ; structure observée = catégories `/<type>-to-rent-at-<city>-cameroon.html` (`?page=N`) + détails `/en/<id>/<slug>` (le slug encode ville/quartier/pièces/prix).
- Le dataset `deegeorgie` **ne déclare aucune licence** → non versionné, usage local seulement.
- Silver (Phase 2) : 3 078 bruts → 2 992 Silver / 78 quarantine ; `price_is_bound` 2 564 ; aberrations 17 ; quartiers non reconnus 582.
- EDA (Phase 3) : 2 992 lignes → distribution asymétrique, 2 564 prix bornés, 1 970 republications, 17 aberrations, 582 quartiers non reconnus, pas de surface/date/meublé.
