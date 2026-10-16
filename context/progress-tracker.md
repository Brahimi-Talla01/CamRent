# Progress Tracker

Mettre à jour ce fichier dès que la phase courante, la fonctionnalité active ou l'état d'implémentation change.

## Current Phase

- **Phase 7 — Model registry** terminée et **mergée** (PR #29, squash `daacdc0`, issue #8 close) ; Phase 6 mergée (PR #27, squash `99969c6`, issue #7 close), Phase 5 mergée (PR #26, squash `38ad713`, issue #6 close), Phase 4 mergée (PR #23 + conformité PR #25, issue #5 close), Phase 3 mergée (PR #19, issue #4) et durcissement du référentiel mergé (PR #22, issue #20 close).
- **Audit et plan de réalignement** (2026-10-15) : audit en lecture seule des phases 00-07 et plan validé dans `context/plans/camrent-audit-and-realignment-plan.md` (branche `chore/audit-realignement`). Les 10 décisions d'arbitrage ont été validées par le porteur du projet ; elles sont consignées dans la section « Recadrage produit — décisions validées » ci-dessous ; le suivi d'exécution par lot vit au §14 du plan.
- **Lots A1 et A2 terminés et vérifiés (2026-10-15)** — détails en « Completed » ci-dessous. A1 = décisions actées dans la documentation ; A2 = registre de modèles gouverné (promotion approuvée explicitement, version servie épinglée dans `ml/models/champion.json`, hash de dataset complet, emplacement d'artefacts épinglé). Vérifications : `ruff` 0 erreur, `pytest` **161 réussis / 1 ignoré**, refus de promotion sans approbation (exit 1, registre inchangé) puis promotion `rent-model-v3` avec approbation. Specs de cadrage 13/14/15 créées (reste du lot 0). Ces lots sont portés par la **PR #33** (branche `chore/audit-realignement` → `develop`).
- **Lot B — qualité et contrat de données terminé et vérifié (2026-10-16)** — détails en « Completed » ci-dessous. Périmètre : provenance d'ingestion (version de connecteur, empreinte de contenu, statut de validation), quarantaine et métadonnées de lot interrogeables en base, `mart_data_quality` et `mart_ingestion_lots`, colonne `rent_semantics`, contrôle des bornes de pièces. Vérifications : `ruff` 0 erreur ; `pytest` **175 réussis / 1 ignoré** ; `dbt build` **137/137** (16 modèles, 121 tests dont 6 singuliers) ; contrôles `psql` sur les volumes et l'invariant de publication.
- **Prochaine étape : lot C — CI de données** (service PostgreSQL et `dbt build` en CI, backend de build figé, `.env.example` aligné sur le port 5433, schémas dbt `dev`/`prod` séparés). **La Phase 8 n'est pas encore démarrée** : elle suivra en deux temps (**08a API publique** puis **08b API interne** — ordre aligné sur le plan §10/lot 4), puis la Phase 9 (09a estimation publique / 09b administration), les specs 13/14 du back-office venant **après** 08 et 09 (décision 7).

## Current Goal

- **Lot C — CI de données** : exécuter `dbt build` (16 modèles, 121 tests) sur un service PostgreSQL en intégration continue, figer le backend de build, aligner `.env.example` (5433) et séparer les schémas dbt `dev`/`prod` — pour que les invariants de données (N ≥ 30, bornes, motifs de rejet, sémantique de cible) soient protégés automatiquement, et non par des exécutions locales.

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

- **Phase 4 — Data marts** (mergée dans `develop` via la PR #23 — squash `75775b9` ; issue #5 close) :
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
  - tests dbt : **83 tests** (not_null, unique, relationships faits→dims, accepted_values,
    bornes inclusives `within_range`, 2 tests singuliers) — `dbt build` : **95/95 PASS**.
  - conformité revue après coup (spec §5 « ranges » et §6 Data Catalog) : test générique
    `within_range` (prix ≥ 1, chambres 0-10, N ≥ 1, année/mois/jour, cible ≥ 1), relations
    complètes faits → dims (type et date en `relationships`, paire ville/quartier par test
    singulier), invariant de publication des médianes gardé par
    `assert_median_published_only_at_or_above_threshold` ; champ **Fréquence** ajouté aux 8
    datasets du catalogue qui l'omettaient et nommage des schémas réels documenté
    (`analytics_staging` / `analytics_intermediate` / `analytics_marts`).
  - invariants embarqués dans les modèles : `n_observations` sur tout agrégat de marché ;
    médiane par quartier non publiée sous N<30 (var `min_publish_n`, défaut 30 — décision
    Phase 3) mais N/moyenne visibles ; républications / prix bornés / quartiers non
    reconnus conservés + quantifiés (`pct_price_bound`, drapeaux) ; **pas de**
    `rent_per_m2` dans `mart_ml_dataset` (cible = `target_rent_price`).
  - Data Catalog : `docs/phase-4/data-catalog.md` (grain, source, fréquence, owner,
    sensibilité, qualité + lineage) ; `dbt/README.md` ; `docs/phase-4/README.md`
    (résultats réels du rejeu du 2026-10-13).
  - vérifications : ruff OK ; pytest **44 passed, 1 skipped** (5 tests du chargeur dans
    `tests/unit/test_pipelines_db.py`) ; cohérence EDA ↔ marts contrôlée en SQL
    (médianes 100 000/150 000, 253 groupes, seuil 30 respecté, 101 non reconnus).
  - correction de revue : le chargement utilisait `if_exists="replace"` (DROP +
    recréation), ce qui cassait les vues dbt dépendantes et rendait `dbt build`
    inutilisable juste après un `load` — remplacé par vidage (`TRUNCATE`) puis
    insertion ; validé par un rejeu réel (2 992 lignes après deux `load`, puis
    `dbt build` 95/95).

- **Phase 5 — Baseline ML** (mergée dans `develop` via la PR #26, squash `38ad713`) :
  - `ml/src/` : `config`, `data` (mart `analytics_marts.mart_ml_dataset`, scénarios), `split`
    (70/15/15, graine `20261009`), `baselines` (`baseline_global`, `baseline_city`,
    `baseline_neighborhood` + chaîne de repli explicite), `evaluation` (MAE/RMSE/R²/MedAE,
    segments, IC bootstrap), `report` (rendu dérivé), CLI `python -m ml.src baselines`.
  - résultats (2 992 obs → 2 094/449/449) : MAE validation **190 141** (globale) /
    **147 296** (ville) / **97 079** (quartier+type) ; test 275 818 / 234 258 / 185 261 ;
    R² validation −0,001 / −0,169 / **0,426**.
  - **seuil à battre** : MAE validation < **79 773 FCFA** (borne basse IC 95 % bootstrap,
    2 000 tirages) = **17,83 %** de mieux que la meilleure baseline ; scénarios de
    sensibilité : hors républications (N=991) → 115 721 ; prix exacts sans aberration
    (N=422) → 120 069.
  - constat méthodologique : la MAE est instable (97 079 validation → 185 261 test,
    +90,8 %) alors que la MedAE ne varie que de ~12 % → le gain devra être confirmé sur
    la MedAE et plusieurs graines en Phase 6.
  - aucune exclusion silencieuse : toutes les observations évaluées dans le scénario
    principal ; segments sous 30 observations **signalés** (`*`), jamais masqués ;
    quartiles de prix calculés sur l'entraînement seulement.
  - tests : `tests/unit/test_ml_{data,split,baselines,evaluation}.py` (**37 tests**) ;
    `ruff` sans erreur ; métriques JSON déterministes (md5 identique au rejeu).

- **Phase 6 — Modèles ML** (mergée dans `develop` via la PR #27, squash `99969c6` ; issue #7 close) :
  - `ml/src/` : `features` (imputation et profondeur de marché ajustées sur
    l'entraînement), `models` (6 familles × cible brute/`log1p` = 12 candidats),
    `training` (comparaison sur la même séparation, sélection multi-graines),
    `uncertainty` (split-conformal vs régression quantile), `interpretability`,
    `persistence`, `model_report`, CLI `python -m ml.src models`.
  - **modèle retenu : `random_forest_log1p`** — MAE validation **75 425 FCFA**
    contre 97 079 pour `baseline_neighborhood` (**−22,31 %**, sous le seuil de
    79 773 FCFA) ; MedAE 20 710 contre 40 000 (−48 %).
  - sélection **en deux temps** : présélection sur la graine de référence, puis
    choix du **gain médian** face à la baseline recalculée sur chaque graine
    (3 graines) — la baseline est battue sur 3/3 (gain médian 12,35 %, minimal
    11,99 %), le seuil IC n'étant franchi que sur 1/3.
  - fourchette : régression quantile retenue (couverture 90,7 % en validation
    comme en test, visée 90 % ; largeur médiane 135 995 FCFA en test).
  - explicabilité : quartier (+33 756 FCFA d'erreur médiane si permuté), chambres
    (+14 190), salles de bain (+10 182) ; dépendance partielle monotone ; exemple
    local expliqué dans le rapport.
  - tests : `tests/unit/test_ml_{features,models,training,uncertainty,interpretability}.py`
    (**59 tests**) ; suite complète 140 passed / 1 skipped ; `ruff` sans erreur ;
    CI : `lightgbm` ajouté à l'installation (le zoo doit pouvoir être testé).
  - deux bugs corrigés en cours de route : sélection qui ne consultait qu'une
    graine (contre la règle documentée) et accès non défendu au bloc de robustesse
    d'un candidat hors présélection — les deux couverts par des tests de régression.
  - vérification finale (2026-10-14) : `ruff` 0, `pytest` **140 passed / 1 skipped**,
    `python -m ml.src models` exit 0 (métriques identiques au rejeu) ; rapport sans
    chemin absolu ; issues #6 et #7 rattachées à leur fusion (commentaire) et closes.

- **Phase 7 — Model registry** (mergée dans `develop` via la PR #29, squash `daacdc0` ; issue #8 close) :
  - `ml/src/` : `tracking` (1 run MLflow par candidat), `registry` (version +
    règle de promotion), `run_registry`, `registry_report`, CLI
    `python -m ml.src registry`.
  - **expérience `rent_prediction`** : 12 runs — hyperparamètres, MAE/RMSE/R² (+
    MedAE, P90, prix moyen observé) sur les 3 ensembles, **métriques par segment**
    (artefact `segments_validation.json`, 5 dimensions), version du dataset (hash
    du contenu : `mart_ml_dataset@21774b224bdb`, 2 992 obs), SHA Git + versions
    logicielles, date.
  - **registre** : `rent-model-v1`, alias `champion` (promu — baseline battue 3/3,
    seuil Phase 5 franchi, 3 séparations) ; rechargé depuis
    `models:/rent-model@champion` et servant une prévision.
  - **règle de promotion** écrite et applicable (`bat_la_baseline`,
    `seuil_phase_5`, `reproductible`) ; promotion explicite, aucun déploiement
    automatique, aucun modèle non enregistré déployable.
  - **backend** : base PostgreSQL dédiée `mlflow` dérivée de `DATABASE_URL` (SQLite
    pour les tests, file store refusé pour le registre) ; `mlflow-skinny` (+
    `alembic`, `skops`) au lieu de `mlflow` complet — pas de serveur ni de 50 Mo
    de `pyarrow`.
  - tests : `tests/unit/test_ml_{tracking,registry}.py` (**14 tests**) ; suite
    complète **154 passed / 1 skipped** ; `ruff` sans erreur ; CI vertes (PR #29,
    correctif PR #30).
  - deux bugs corrigés et couverts par des tests : `str(URL)` SQLAlchemy masquait
    le mot de passe en `***` (impossible de s'authentifier) et une expérience
    MLflow supprimée doit être restaurée avant réutilisation ; le rapport
    versionné masque l'URI (aucun secret dans un fichier suivi).

- **Issue #20 — Enrichissement du référentiel géographique** (`pipelines/geo.py`) :
  - 26 quartiers réels ajoutés au seed (15 à Douala, 11 à Yaoundé), vérifiés sur les palettes Wikipédia « Quartiers de Douala » et « Quartiers de Yaoundé ».
  - alias tracés : sous-quartiers d'Akwa (`Akwa I`/`Akwa II` → `Akwa`), variante `Cite Ubo Palmiers` → `Cité des Palmiers` (confirmée par les annonces Koutchoumi), `Mbangue` → `Bangue`, et descriptions d'annonces nommant explicitement un quartier canonique.
  - résultats : quartiers non reconnus **582 → 101 lignes** (19,5 % → 3,4 %), 138 → 78 libellés distincts ; quartiers canoniques utilisés 34 → 61 ; 0 conflit ville/quartier maintenu ; quarantine inchangée (78).
  - conséquences mesurées : republications 1 970 → 2 001 (dédup technique affinée par la fusion des alias) ; rapports Phase 2 (`docs/phase-2/cleaning-report.md`) et EDA rejoués sans nouvelle valeur en dur.
  - libellés volontairement laissés non reconnus (ambigus ou non vérifiables) : `Elig`, `DENVER`, `COAF`, `a`, noms de villes, descriptions libres.
  - tests : `tests/unit/test_pipelines_geo.py` étendu (39 `passed`, 1 `skipped`) ; `ruff` sans erreur ; `python -m pipelines silver` puis EDA rejoués.

- **Lot A1 — décisions actées (documentation seule, 2026-10-15)** :
  - `context/plans/camrent-audit-and-realignment-plan.md` : plan de réalignement validé, 10 décisions intégrées (§9), ordre des lots (§10), suivi d'exécution (§14).
  - `context/progress-tracker.md` : phase courante, objectif, section « Recadrage produit — décisions validées (2026-10-15) », questions ouvertes mises à jour.
  - `context/project-overview.md` : extensions retenues (back-office à fondations d'abord, marketplace conditionnée, Conakry séparé) et décisions de périmètre (sémantique de cible, prix censurés, registre gouverné, CI de données).
  - `context/architecture-context.md` : frontières des sous-systèmes A-E (sans microservices) et section « Gouvernance du registre de modèles ».
  - `context/feature-specs/07-model-registry.md` : promotion nominative approuvée, épinglage de version, hash de dataset complet, artefacts épinglés.
  - Aucune modification de code par ce lot.

- **Lot A2 — registre de modèles gouverné (2026-10-15)** (équivalent du « Lot 1 » du plan) :
  - `ml/src/tracking.py` : `dataset_version` hashe **tout le contenu** du mart (schéma + valeurs, `pd.isna` géré explicitement) et expose `n_colonnes`/`colonnes` — sensible à tout changement de feature (P5).
  - `ml/src/registry.py` + `run_registry.py` + `__main__.py` : `require_promotion_approval()` ; une promotion non approuvée est refusée **avant toute écriture** ; tags `approuve_par` / `approuve_le` ; options `--confirm-promotion` / `--approved-by` (P2).
  - `ml/src/registry.py::write_champion_pin` : version servie épinglée dans le fichier **versionné** `ml/models/champion.json` (seul artefact de modèle non ignoré — vérifié par `git check-ignore`, exit 1) (P2).
  - `ml/src/config.py` : `CHAMPION_PIN_PATH` ; `MODEL_ARTIFACT_NAME` requalifié (artefact de phase 6, pas une version) ; `MLFLOW_ARTIFACT_LOCATION` épinglé à `ml/artifacts/mlflow` (indépendant du répertoire d'exécution) ; `.env.example` et `.gitignore` (`!ml/models/champion.json`) alignés (P2).
  - `ml/src/registry_report.py` : lignes d'approbation et version épinglée, chemins affichés relatifs (jamais d'absolu dans un rapport versionné).
  - tests : `tests/unit/test_ml_{tracking,registry}.py` étendus (**7 nouveaux tests**) + `tests/unit/conftest.py` (artefacts de test isolés) ; suite complète **161 réussis, 1 ignoré** (le skip `pyarrow` préexistant) ; `ruff` 0 erreur ; vérifié en CLI : refus exit 1 sans approbation (2 versions inchangées, aucun pin créé), puis promotion `rent-model-v3` (alias `champion` → v3, tags d'approbation, `champion.json` écrit).
  - **Reste ouvert (P2 partiel, plan §7.5)** : politique de rétention des runs — l'expérience `rent_prediction` compte 84 runs sans politique d'hygiène.

- **Lot B — qualité et contrat de données (2026-10-16)** (plan §10 « Lot 2 », écarts P4 et P3/mesure) :
  - **B1 — provenance d'ingestion** : `ingestion/config.py::CONNECTOR_VERSION` (version du code de
    collecte/parsing) ; `ingestion/storage.py` consigne par lot `connector_version`,
    `content_sha256` / `content_bytes` (empreinte du fichier brut, calculée en flux) et
    `lot_validation_status` / `lot_validation_failures` ; `ingestion/bronze.py::check_lot` valide
    **un** lot (utilisé par le CLI à la collecte, avant l'écriture des métadonnées, pour consigner
    un statut réel) et `run_validations` réutilise ces contrôles.
  - **B2 — qualité en base** : `pipelines/db.py` charge trois tables d'atterrissage (Silver,
    quarantaine, métadonnées de lot) avec la même stratégie idempotente (vidage puis insertion,
    jamais de `DROP`) ; dbt expose `stg_quarantine`, `stg_ingestion_runs`, `mart_data_quality`
    (motifs de rejet agrégés par source, avec le total de la source) et `mart_ingestion_lots`
    (un lot par ligne, provenance lisible, `has_provenance` pour signaler les lots antérieurs).
  - **B3 — sémantique de cible** (décision 9) : `mart_ml_dataset.rent_semantics`
    (`asking_rent` / `unknown`), cible non renommée.
  - **B4 — bornes de pièces** : le contrôle demandé par la spec 02 §12 **existait déjà** en
    Phase 2 (`pipelines/silver.py::_outlier_flags` signale `bathrooms > 10` en `bathrooms_outlier`) ;
    ce lot ajoute ce qui manquait — un test dbt qui **vérifie le signalement**
    (`assert_implausible_rooms_are_signalled`, contrôle négatif probant : avec la borne forcée à 0,
    le test remonte 2 987 lignes et échoue) — et corrige l'affirmation inverse portée par le suivi.
    Aucune donnée n'a été modifiée : les 3 observations à `bathrooms = 80` restent conservées et signalées.
  - **Vérifications** : `ruff` 0 erreur ; `pytest` **175 réussis / 1 ignoré** (+14 tests :
    7 ingestion, 7 chargeur) ; `dbt build` **137/137** (16 modèles, 121 tests dont 6 singuliers,
    contre 95/95 et 83 tests) ; en base : `landing.quarantine_listings` 78 lignes,
    `landing.ingestion_runs` 3 lots, `mart_data_quality` 4 lignes (52/18/7/1 = 78 rejets réconciliés),
    `mart_ingestion_lots` 3 lots avec `has_provenance = false`, `rent_semantics = asking_rent` sur
    2 992 lignes, volumes et invariant de publication inchangés (234 médianes non publiées sur 253,
    plus petit N publié = 31).
  - **Contrôle de bout en bout** : un lot rejoué via le CLI (`reference_local`, `--limit 20`, racine
    temporaire) écrit `connector_version`, `content_sha256` et `lot_validation_status: "ok"` ;
    l'empreinte recalculée indépendamment (`sha256sum`) est identique.
  - **Reste ouvert** : aucune observation à sémantique non établie aujourd'hui — `rent_semantics`
    vaudra `unknown` pour une future source sans prix interprétable ; les lots antérieurs au 2026-10-16
    n'ont pas de provenance (absence signalée, jamais comblée).

- **Harmonisation documentaire face au plan (2026-10-15)** — revue de cohérence de tous les documents de suivi (`context/`, `docs/`, READMEs) contre le plan validé, corrections validées par le porteur du projet :
  - specs `06`/`08`/`09` alignées sur les features réellement disponibles (payload API et formulaire sans `area_m2`/`parking`/`gated`) et le découpage 08a/08b puis 09a/09b ;
  - `project-overview.md` : variables MVP séparées (disponibles aujourd'hui / hors périmètre tant que non collectées) ;
  - compléments demandés par le plan sur les specs `00` (reproduction partielle), `01` (provenance : empreinte de contenu, version de connecteur), `02` (rejets en base, `rent_semantics`, bornes `bathrooms`, drapeaux à trois états), `04` (sémantique de cible, table de qualité), `11` (qualité en continu, jobs ML, audit), `12` (sauvegardes, retour arrière du modèle, runbooks, schémas dev/prod) ;
  - `ui-context.md` (séparation public / administration) et `code-standards.md` (`rent_semantics`) ;
  - note de décision 4 (« adapter la cible et l'intervalle », lot E) ajoutée dans `docs/phase-2/README.md`, `docs/phase-5/README.md`, `docs/phase-6/README.md` et `pipelines/README.md`.

## In Progress

- **Aucun lot en cours.** Le lot B est terminé et vérifié (2026-10-16) ; ses changements sont **non commités**, sur la branche dédiée `lot-b-qualite-donnees` (aucun commit ni push sans demande explicite, AGENTS.md §8).

## Next Up

- **Lot C — CI de données** (plan §10 « Lot 3 ») : service PostgreSQL et `dbt build` en CI, backend de build figé,
  `.env.example` aligné sur le port 5433, schémas dbt `dev`/`prod` séparés. Inclut le critère de la §8.1 du plan :
  **0 test ignoré** dans l'environnement de référence (installer `pyarrow`, absent du venv local — c'est le seul test
  encore ignoré de la suite).
- **Lot D — Phase 8 en deux temps** (plan §10 « Lot 4 ») : **08a API publique** (prédiction, marché, comparaison — modèle
  **épinglé**) puis **08b API interne** (permissions, jobs, accès administrateur).
- **Lot E — prix censurés** : adapter la cible et l'intervalle, par une expérience **mesurée**, après
  stabilisation du registre.
- **Puis** : Phase 9 (09a estimation publique / 09b administration, `ui-context.md` figé avant code),
  specs 13/14 du back-office (décision 7 : implémentation **après** 08 et 09 ; specs de cadrage créées
  le 2026-10-15), spec 15 marketplace (phase de décision — spec de cadrage créée, aucun code engagé),
  Phases 10/11/12 selon besoin mesuré, Conakry (chantier séparé, décision 10).
- Hygiène du registre (rétention des runs) à traiter dans un lot ultérieur (P2 partiel).
- Tâche ouverte : pondération/explicitation des prix bornés et des républications dans
  l'entraînement (rejoint le lot E).

## Recadrage produit — décisions validées (2026-10-15)

Décisions prises par le porteur du projet après l'audit (détail dans
`context/plans/camrent-audit-and-realignment-plan.md` §9) :

1. **Marketplace** : conservée dans le périmètre du produit, mais **structurée** — à cadrer par une
   spec de découverte avant toute implémentation. Elle n'est pas retirée, elle n'est pas non plus
   engagée.
2. **Priorité** : le **back-office d'abord**, entendu comme ses **fondations** (capacités gouvernées
   et interrogeables), l'interface venant après les phases 08 et 09.
3. **Registre** : **MLflow conservé** ; la promotion d'un modèle est **approuvée par un
   administrateur** (rôle `admin`).
4. **Prix censurés** : **adapter la cible et l'intervalle** (expérience mesurée, lot E), au lieu
   d'exclure ou de pondérer à l'aveugle.
5. **Périmètre géographique** : **Yaoundé et Douala** ; **Conakry est un chantier séparé**
   (devise, référentiel et sources locales), sans données ni modèle dans l'immédiat.
6. **Collecte** : **on finalise le MVP d'abord** — aucune nouvelle collecte engagée maintenant.
7. **Back-office** : les specs **13/14 viennent après 08 et 09** ; rôles internes à préciser
   (l'administrateur est le premier rôle identifié).
8. **CI** : renforcée **oui** — tests de données (`dbt build`) sur PostgreSQL en CI.
9. **Sémantique de cible** : **ajouter** une colonne `rent_semantics` (`asking_rent` / `unknown`),
   sans renommer la cible existante.
10. **Conakry** : décision à instruire **séparément** (données, code, produit, commercialisation).

Matérialisation technique retenue : artefacts de modèles stockés **localement, non versionnés**, dans
un chemin **épinglé et documenté** (`ml/artifacts/mlflow`), la version servie étant épinglée dans le
fichier versionné `ml/models/champion.json`.

## Open Questions

- **Hygiène du registre (P2 partiel)** : la politique de rétention des runs n'est pas implémentée — l'expérience `rent_prediction` compte **84 runs** (cumul des exécutions). À traiter dans un lot ultérieur (plan §7.5) ; aucune suppression de version n'est automatique.
- **Emplacement d'artefacts historique** : l'expérience `rent_prediction` conserve l'emplacement enregistré à sa création (`mlruns/3`) car MLflow n'expose pas de modification ; l'emplacement épinglé (`ml/artifacts/mlflow`) s'appliquera aux nouvelles expériences (documenté dans `docs/phase-7/README.md`).
- **Prix censurés** : conservés avec `price_is_bound` (borne inférieure, 2 564 lignes sur 2 992) ; le seuil de la Phase 5 et la sélection de la Phase 6 sont mesurés sur toutes les observations. Décision prise (2026-10-15) : **adapter la cible et l'intervalle** — mise en œuvre dans le lot E, mesures à produire (lot E non commencé).
- **Gain ML à démontrer** : **démontré** en Phase 6 — `random_forest_log1p` à 75 425 FCFA de MAE de validation (seuil 79 773), MedAE divisée par près de deux, gain confirmé sur 3 séparations (médian 12,35 %). Le seuil IC n'est franchi que sur 1 graine sur 3 : les arbitrages produit ne doivent pas reposer sur un écart inférieur à cette marge.
- **Surface** (absente) : décision du 2026-10-15 — **on finalise le MVP d'abord**, sans nouvelle collecte ; la surface reste hors du périmètre des features.
- **Référentiel géographique** : seed enrichi (issue #20) ; 101 lignes (78 libellés distincts) restent non reconnues — descriptions d'annonces, libellés ambigus (`Elig`) ou non vérifiables (`DENVER`, `COAF`) conservés et signalés, sans mapping inventé.
- **Republications** : 2 001 lignes marquées `is_republication` ; décider si conservées/pondérées pour l'entraînement (le drapeau est exposé dans `mart_ml_dataset` pour une décision explicite en Phase 5-6).
- **Endpoints MINFI / INS** : documents stockés bruts, endpoints et formats à valider.
- **Dataset tiers `deegeorgie`** : usage strictement local (sans licence), non redistribué.
- Méthode d'intervalle de prédiction du produit : **résolu en Phase 6** — régression quantile (gradient boosting aux quantiles 5 % / 95 %), retenue sur le split-conformal car elle couvre le niveau visé (90,7 % en validation et en test) avec une fourchette médiane deux fois plus étroite ; la calibration n'utilise que la validation, la couverture de test sert de vérification.
- Séparation train/validation/test : **aléatoire** retenue (70/15/15, graine fixe) — `posted_at` vide et `collected_at` sur une seule journée, donc séparation chronologique impossible (Phase 5). À revoir si une collecte étalée dans le temps devient disponible.
- Périmètre géographique du MVP : **Yaoundé et Douala** (décision du 2026-10-15) ; la liste exacte des quartiers reste à arrêter. **Conakry** est un chantier **séparé**, à instruire avant toute donnée ou modèle.

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
- Phase 5 : baselines mesurées — MAE validation 97 079 FCFA (quartier+type) contre 190 141 (moyenne globale) ; seuil à battre 79 773 FCFA (−17,83 %) ; MAE instable (test 185 261) alors que la MedAE reste à 40 000/35 000 → gain ML à confirmer sur plusieurs graines.
- Phase 4 (conformité) : vérification complète de la phase (chaîne rejouée, base interrogée, manifeste dbt, catalogue) — 0 orphelin sur les 4 clés, 0 violation du seuil N<30, drapeaux alignés sur le Silver (2 001 / 2 564 / 17 / 101) ; écarts corrigés : tests de bornes et relations manquants, invariant N<30 gardé par un test, champ Fréquence du catalogue, nommage des schémas, commentaire CI obsolète. Piste annoncée alors comme « non traitée » (`bathrooms` atteint 80) : **vérifiée le 2026-10-16** — la valeur est bien signalée (`outlier_flags = bathrooms_outlier` sur 3 observations) ; ce qui manquait était le test dbt de ce signalement, ajouté par le lot B.
- Phase 4 (suite) : PR #23 mergée en squash (`75775b9`, issue #5 close) ; chargement rejouable (vidage `TRUNCATE` + réinsertion, table jamais droppée) et CI qui installe désormais `sqlalchemy` afin d'exécuter réellement les tests du chargeur.
- Phase 4 : PostgreSQL docker-compose sur **5433** (5432 occupé par le PostgreSQL système local, mot de passe `camrent` inconnu) ; dbt installé dans `.venv` (dbt-core 1.12.5, dbt-postgres 1.11.0, compatible Python 3.14) ; connexion dbt via variables `DBT_*` (profiles.yml) ; `pipelines load` via `DATABASE_URL`.
- **Phase 6** : exécution réelle sur `mart_ml_dataset` (2 992 obs) — 12 candidats comparés ; les trois ensembles d'arbres sur `log1p` sont au coude-à-coude (75 161 / 75 281 / 75 425 FCFA), très loin devant les linéaires (82 032 à 151 066) ; la transformation `log1p` vaut 4 000 à 10 000 FCFA par famille. LightGBM non retenu (dépendance et temps d'entraînement sans gain démontré), mais comparé et documenté. Le rang de la graine de référence ne suffit pas : `random_forest_log1p` 3ᵉ sur la graine de référence, 1ᵉʳ sur les 2 autres.
- **Phase 6** : conteneur `camrent-postgres` en écoute sur le **port 5433** alors que `.env` porte `POSTGRES_PORT=5432` — l'URL réelle est `postgresql://camrent:change-me@localhost:5433/camrent` (écrit dans `ml/README.md`).
- Phase 4 : `dbt build` 95/95 (12 modèles + 83 tests) ; volumes vérifiés en base : 2 992 lignes traversant toutes les couches ; mart_city_prices : Douala N=2 811 méd. 100 000, Yaoundé N=181 méd. 150 000 (conforme EDA) ; 253 groupes quartier×type×chambres ; médiane null strictement sous N=30 ; 101 non reconnus / 2 001 républications / 2 564 prix bornés / 17 aberrations conservés avec drapeaux.
- **Lot B (2026-10-16)** : après le lot, `python -m pipelines load` charge trois tables
  (`landing.silver_listings` 2 992 · `landing.quarantine_listings` 78 · `landing.ingestion_runs` 3 lots) ;
  `dbt build` = 137/137 (16 modèles, 121 tests dont 6 singuliers) ; le mart `mart_ml_dataset` gagne
  `rent_semantics` (rappel : le hash de dataset MLflow couvre **tout** le contenu du mart depuis le
  lot A2, une nouvelle colonne change donc la version de dataset — les métriques publiées des
  phases 5-6 n'ont pas été recalculées par ce lot).
- **Phase 7** : `mlflow-skinny` 3.17.1 (Python 3.14) — `alembic` et `skops` sont nécessaires en plus du `mlflow-skinny` ; base de registre `mlflow` créée une fois dans le conteneur (`createdb -U camrent mlflow`) ; l'URI de suivi est **dérivée de `DATABASE_URL`** — jamais via `str(URL)` (SQLAlchemy masquerait le mot de passe en `***`) ; la création des tables MLflow est très lente sur SQLite (~100 s) alors qu'elle est immédiate sur PostgreSQL.
- **Lot A2 (2026-10-15)** : promotion non approuvée refusée **avant toute écriture** (vérifié en CLI : 2 versions inchangées, aucun fichier épinglé créé, exit 1) ; avec `--confirm-promotion --approved-by` : création de `rent-model-v3`, alias `champion` → v3, tags `approuve_par`/`approuve_le`, écriture de `ml/models/champion.json` ; registre à **3 versions** (v1 rejeu du 2026-10-14, v2, v3). Le fichier `ml/models/champion.json` est le **seul** artefact de modèle versionné (`git check-ignore` exit 1) ; `ml/artifacts/mlflow` est ignoré. `stash@{0}` conserve les anciens rapports régénérés (phases 6-7) ; aucun commit ni push.
