# Progress Tracker

Mettre à jour ce fichier dès que la phase courante, la fonctionnalité active ou l'état d'implémentation change.

## Current Phase

- **Phase 4 — Data marts** en cours (branche `phase/4-data-marts`) ; Phase 3 mergée (PR #19, issue #4) et durcissement du référentiel mergé (PR #22, issue #20 close).

## Current Goal

- Terminer et vérifier la Phase 4 : Silver chargé dans PostgreSQL (2 992 lignes) + marts dbt construits (74/74 tests dbt OK) ; reste PR → revue → merge.

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

- **Phase 2 — Data cleaning** (mergée dans `develop`, issue #3 close) dans `pipelines/` + `docs/phase-2/` (volumes d'origine, avant l'enrichissement #20) :
  - package `pipelines/` : `geo.py` (référentiel seed + résolution), `parsing.py`, `adapters.py` (par source), `silver.py` (resolution, validation, dédup, quarantine, écriture), `report.py`, `__main__.py`.
  - sorties : `data/processed/silver_listings.parquet`, `quarantine_listings.parquet`, `docs/phase-2/cleaning-report.md`.
  - règles : types, villes/quartiers canoniques, catégories, valeurs bornées (`price_is_bound`), dédup (technique vs republication), aberrations signalées (jamais supprimées), invalides en quarantine.
  - construction réelle : Raw 3 078 → **2 992 lignes Silver**, **78 en quarantine** (cohérent avec ≈ 1 226 uniques : 1 970 republications).
  - tests `tests/unit/test_pipelines_*.py` (**19** tests) ; `ruff` sans erreur.

- **Phase 3 — Analyse exploratoire (EDA)** (mergée dans `develop`, PR #19, issue #4 close — chiffres ci-dessous **avant** l'enrichissement #20) :
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

- **Phase 4 — Data marts** (branche `phase/4-data-marts`, en revue) :
  - `pipelines/db.py` + CLI `python -m pipelines load` : charge le Silver Parquet dans
    `landing.silver_listings` (idempotent : vidage `TRUNCATE` puis réinsertion par lot,
    la table n'est jamais droppée ; DATABASE_URL requis) — 2 992 lignes.
  - projet dbt (`dbt/`) : `stg_listings` → `int_clean_listings` → 4 dims (`dim_city`,
    `dim_neighborhood`, `dim_property_type`, `dim_date` — dates observées, pas de
    calendrier artificiel), 2 faits (`fct_rent_observations`, `fct_listings`),
    4 marts (`mart_neighborhood_prices`, `mart_city_prices`, `mart_property_prices`,
    `mart_ml_dataset`).
  - connexion dbt via variables d'environnement (`profiles.yml`, aucun secret en dur) ;
    PostgreSQL 16 via docker-compose (port 5433 : le Postgres système de la machine
    occupe déjà 5432) ; dbt-core 1.12.5 + dbt-postgres 1.11.0 (Python 3.14).
  - tests dbt : **62 tests** (not_null, unique, relationships faits→dims, accepted_values)
    — `dbt build` : **74/74 PASS**.
  - invariants embarqués dans les modèles : `n_observations` sur tout agrégat de marché ;
    médiane par quartier non publiée sous N<30 (var `min_publish_n`, défaut 30 — décision
    Phase 3) mais N/moyenne visibles ; républications / prix bornés / quartiers non
    reconnus conservés + quantifiés (`pct_price_bound`, drapeaux) ; **pas de**
    `rent_per_m2` dans `mart_ml_dataset` (cible = `target_rent_price`).
  - Data Catalog : `docs/phase-4/data-catalog.md` (grain, source, fréquence, owner,
    sensibilité, qualité + lineage) ; `dbt/README.md` ; `docs/phase-4/README.md`
    (résultats réels du rejeu du 2026-10-12).
  - vérifications : ruff OK ; pytest **44 passed, 1 skipped** (5 tests du chargeur dans
    `tests/unit/test_pipelines_db.py`) ; cohérence EDA ↔ marts contrôlée en SQL
    (médianes 100 000/150 000, 253 groupes, seuil 30 respecté, 101 non reconnus).
  - correction de revue : le chargement utilisait `if_exists="replace"` (DROP +
    recréation), ce qui cassait les vues dbt dépendantes et rendait `dbt build`
    inutilisable juste après un `load` — remplacé par vidage (`TRUNCATE`) puis
    insertion ; validé par un rejeu réel (2 992 lignes après deux `load`, puis
    `dbt build` 74/74).

- **Issue #20 — Enrichissement du référentiel géographique** (`pipelines/geo.py`) :
  - 26 quartiers réels ajoutés au seed (15 à Douala, 11 à Yaoundé), vérifiés sur les palettes Wikipédia « Quartiers de Douala » et « Quartiers de Yaoundé ».
  - alias tracés : sous-quartiers d'Akwa (`Akwa I`/`Akwa II` → `Akwa`), variante `Cite Ubo Palmiers` → `Cité des Palmiers` (confirmée par les annonces Koutchoumi), `Mbangue` → `Bangue`, et descriptions d'annonces nommant explicitement un quartier canonique.
  - résultats : quartiers non reconnus **582 → 101 lignes** (19,5 % → 3,4 %), 138 → 78 libellés distincts ; quartiers canoniques utilisés 34 → 61 ; 0 conflit ville/quartier maintenu ; quarantine inchangée (78).
  - conséquences mesurées : republications 1 970 → 2 001 (dédup technique affinée par la fusion des alias) ; rapports Phase 2 (`docs/phase-2/cleaning-report.md`) et EDA rejoués sans nouvelle valeur en dur.
  - libellés volontairement laissés non reconnus (ambigus ou non vérifiables) : `Elig`, `DENVER`, `COAF`, `a`, noms de villes, descriptions libres.
  - tests : `tests/unit/test_pipelines_geo.py` étendu (39 `passed`, 1 `skipped`) ; `ruff` sans erreur ; `python -m pipelines silver` puis EDA rejoués.

## In Progress

- Phase 4 — Data marts : code + docs terminés sur `phase/4-data-marts`, PR #23
  ouverte vers `develop`, en attente de CI / revue / merge.

## Next Up

- Fusion de la Phase 4 (PR → revue → merge squash dans `develop`), puis Phase 5 —
  Baseline ML (les marts et `mart_ml_dataset` sont prêts).

## Open Questions

- **Prix censurés** : conservés avec `price_is_bound` (borne inférieure) ; stratégie de pondération/exclusion à figer en Phases 5-6.
- **Surface** (absente) : la collecter, ou concevoir le MVP sans elle ?
- **Référentiel géographique** : seed enrichi (issue #20) ; 101 lignes (78 libellés distincts) restent non reconnues — descriptions d'annonces, libellés ambigus (`Elig`) ou non vérifiables (`DENVER`, `COAF`) conservés et signalés, sans mapping inventé.
- **Republications** : 2 001 lignes marquées `is_republication` ; décider si conservées/pondérées pour l'entraînement (le drapeau est exposé dans `mart_ml_dataset` pour une décision explicite en Phase 5-6).
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
- Référentiel (issue #20) : 26 quartiers ajoutés et alias tracés ; non reconnus 582 → 101 (19,5 % → 3,4 %) ; quartiers canoniques utilisés 34 → 61 ; republications 1 970 → 2 001 ; 0 conflit ville/quartier.
- Phase 4 : PostgreSQL docker-compose sur **5433** (5432 occupé par le PostgreSQL système local, mot de passe `camrent` inconnu) ; dbt installé dans `.venv` (dbt-core 1.12.5, dbt-postgres 1.11.0, compatible Python 3.14) ; connexion dbt via variables `DBT_*` (profiles.yml) ; `pipelines load` via `DATABASE_URL`.
- Phase 4 : `dbt build` 74/74 (12 modèles + 62 tests) ; volumes vérifiés en base : 2 992 lignes traversant toutes les couches ; mart_city_prices : Douala N=2 811 méd. 100 000, Yaoundé N=181 méd. 150 000 (conforme EDA) ; 253 groupes quartier×type×chambres ; médiane null strictement sous N=30 ; 101 non reconnus / 2 001 républications / 2 564 prix bornés / 17 aberrations conservés avec drapeaux.
