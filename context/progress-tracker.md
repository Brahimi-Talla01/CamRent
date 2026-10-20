# Progress Tracker

Mettre à jour ce fichier dès que la phase courante, la fonctionnalité active ou l'état d'implémentation change.

## Current Phase

- **Phase 7 — Model registry** terminée et **mergée** (PR #29, squash `daacdc0`, issue #8 close) ; Phase 6 mergée (PR #27, squash `99969c6`, issue #7 close), Phase 5 mergée (PR #26, squash `38ad713`, issue #6 close), Phase 4 mergée (PR #23 + conformité PR #25, issue #5 close), Phase 3 mergée (PR #19, issue #4) et durcissement du référentiel mergé (PR #22, issue #20 close).
- **Audit et plan de réalignement** (2026-10-15) : audit en lecture seule des phases 00-07 et plan validé dans `context/plans/camrent-audit-and-realignment-plan.md` (branche `chore/audit-realignement`). Les 10 décisions d'arbitrage ont été validées par le porteur du projet ; elles sont consignées dans la section « Recadrage produit — décisions validées » ci-dessous ; le suivi d'exécution par lot vit au §14 du plan.
- **Lots A1 et A2 terminés et vérifiés (2026-10-15)** — détails en « Completed » ci-dessous. A1 = décisions actées dans la documentation ; A2 = registre de modèles gouverné (promotion approuvée explicitement, version servie épinglée dans `ml/models/champion.json`, hash de dataset complet, emplacement d'artefacts épinglé). Vérifications : `ruff` 0 erreur, `pytest` **161 réussis / 1 ignoré**, refus de promotion sans approbation (exit 1, registre inchangé) puis promotion `rent-model-v3` avec approbation. Specs de cadrage 13/14/15 créées (reste du lot 0). Ces lots sont portés par la **PR #33** (branche `chore/audit-realignement` → `develop`).
- **Lot B — qualité et contrat de données terminé, vérifié et mergé (2026-10-16, PR #35)** — détails en « Completed » ci-dessous. Périmètre : provenance d'ingestion (version de connecteur, empreinte de contenu, statut de validation), quarantaine et métadonnées de lot interrogeables en base, `mart_data_quality` et `mart_ingestion_lots`, colonne `rent_semantics`, contrôle des bornes de pièces. Vérifications : `ruff` 0 erreur ; `pytest` **175 réussis / 1 ignoré** en local (le test Parquet reste ignoré sans `pyarrow`) et **176 réussis / 0 ignoré** en CI ; `dbt build` **137/137** (16 modèles, 121 tests dont 6 singuliers) ; contrôles `psql` sur les volumes et l'invariant de publication.
- **Lot C — CI de données terminé, vérifié et mergé (2026-10-16, PR #37)** — détails en « Completed » ci-dessous. Périmètre : tests de données (`dbt build`) en CI sur un service PostgreSQL avec jeu synthétique déterministe, backend de build figé (`pyproject.toml`), profils dbt `dev`/`prod` séparés, `.env.example` complété. Vérifications : `ruff` 0 erreur ; `pytest` **182 réussis / 0 ignoré** (local **et CI**) ; pipeline de la PR : chargement 360/48/3 puis `dbt build` **137/137 en CI** ; paquet installé et importable hors dépôt.
- **Phase 8 terminée (2026-10-20)** : **08a API publique** complète (tickets #50 à #54, PR #75 à #84) et **08b API interne** ouverte par son socle (#61, PR #86). **Prochaine étape : Phase 9 (lot 5 du plan)** — 09a frontend public (tickets #55 à #58) puis 09b administration, les modules 13.1 à 13.5 du back-office venant **après** 08 et 09 (décision 7).
- **Suivi des tickets réorganisé par sous-système (2026-10-17, PR #70)** : les milestones de phase sont remplacés par les milestones de **sous-système** (`architecture-context.md` §Sous-systèmes fonctionnels) — **Data Platform**, **Estimation**, **Back-office**, **Marketplace** — et chaque phase est découpée en **tickets de module** (3 à 5 par phase), la phase restant portée par le préfixe du titre (`08a.2`, `13.4`). Les **29 tickets de module** sont #43 à #69, #72 et #73 — ces deux derniers complètent la phase 12 (déploiement et sécurité, vérification du retour arrière du modèle), non couverte par 12.1 à 12.4. Les tickets de phase #9 à #13 sont **fermés** avec un commentaire listant leurs tickets de remplacement, et les milestones de phase 08 à 12 sont fermés (les milestones 00 à 07 restent comme historique des issues fermées). Aucune issue ouverte n'est sans milestone. Décision : « pas de ticket trop lourd — un ticket par module ».
- **08a.1 — socle de l'API publique terminé, vérifié et mergé (2026-10-17, PR #75)** — détails en « Completed » ci-dessous. Premier des cinq tickets de module de 08a : `backend/` n'était qu'un `.gitkeep` avant cet incrément.
- **08a.2 — endpoint de prédiction terminé et vérifié (2026-10-18, PR #77)** — détails en « Completed » ci-dessous. Le modèle épinglé est désormais **servi** : `POST /api/v1/predictions` renvoie la fourchette calibrée de la Phase 6 et la version réellement chargée.
- **08a.3 — provenance du modèle verrouillée (2026-10-18, ticket #52, PR #78)** — détails en « Completed » ci-dessous.
- **08a.3+ — serving durci (2026-10-18, PR #80)** — détails en « Completed » ci-dessous. Arbitrage du porteur du projet : **re-promotion gouvernée** sur le mart courant (`rent-model-v4`, approbation nominative), plutôt qu'une simple mention documentaire de l'écart.
- **08a.4 — endpoints de marché terminés, vérifiés et mergés (2026-10-19, PR #82, squash `01a1081`)** — détails en « Completed » ci-dessous. Villes, quartiers et prix sont servis depuis les marts, avec N obligatoire, seuil de publication et biais visibles ; issue #53 close.
- **08a.5 — comparaison terminée, vérifiée et mergée (2026-10-20, PR #84, squash `d7285a4`)** — issue #54 close. `POST /api/v1/comparisons` réutilise strictement prédiction et marché, avec groupe explicite, écarts signés et médiane jamais publiée sous le seuil.
- **08b.1 — socle de l'API interne terminé, vérifié et mergé (2026-10-20, PR #86, squash `0b185af`, issue #61 close)** — détails en « In Progress » ci-dessous.
- **09a.1 — socle du frontend public implémenté et vérifié (2026-10-20, ticket #55)** — livraison à ouvrir. Thème figé dans `context/ui-context.md`, Next.js + TypeScript dans `frontend/`, client d'API paramétré par variable d'environnement, accueil et navigation ; les écrans métier (09a.2 à 09a.4) annoncent explicitement leur ticket. Application **Django distincte** de l'API publique : comptes internes, rôle `admin`, autorisation par action (échec fermé), journal d'audit consultable, frontière public/interne vérifiée par test et sur serveur réel.

## Current Goal

- **Phase 9a — frontend public** (plan §10, lot 5) : **#55 implémenté et vérifié localement** (thème figé, socle Next.js, client API, accueil et navigation) ; écrans métier **#56 à #58** ensuite. Le socle 08b.1 reste la base des modules back-office 13.x, après 09.
- **Lot D — Phase 8 en deux temps** (plan §10 « Lot 4 », tickets de module) : **08a API publique** — **#50 livré** (socle, schémas stricts, erreurs au format unique), **#51 livré** (prédiction servie depuis le modèle épinglé), **#52 livré** (provenance verrouillée, `rent-model-v4`), **#53 livré** (endpoints de marché, PR #82), **#54 implémenté et vérifié localement** (comparaison, branche `feat/08a.5-comparisons`, livraison à ouvrir) — puis **08b API interne** — **#61 livré et mergé** (08b.1 : authentification par jeton, rôle `admin`, autorisation par action, journal d'audit, application Django séparée — PR #86). Le payload reste strictement limité aux champs réellement collectés ; les invariants de données sont protégés en CI par le lot C.

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

- **Lot C — CI de données (2026-10-16)** (plan §10 « Lot 3 », décision 8, écarts P7/P8) :
  - **CI de données** : `.github/workflows/ci.yml` gagne un service PostgreSQL 16 (base
    `camrent_ci`, mot de passe de service éphémère — aucun secret dans le dépôt) et trois
    étapes après `ruff`/`pytest` : génération du jeu synthétique, `pipelines load`, puis
    `dbt build` dans le schéma jetable `analytics_ci` (exercice du levier `DBT_SCHEMA_DEV`).
    Le commentaire « `dbt build` hors CI » est retiré (devenu faux) ; les étapes suivantes
    (integration tests, build front, déploiement) restent explicitement reportées aux phases 8/9/12.
  - **Jeu synthétique CI** : `tests/data/make_synthetic_dataset.py` — déterministe (graine
    fixe), reproduit une collecte locale **sans réseau ni donnée tierce** (le jeu réel est un
    dépôt sans licence : redistribution interdite) et refuse d'écrire sous `data/` réel ;
    6 tests (`tests/unit/test_ci_dataset.py`) verrouillent le contrat Phase 4 (colonnes,
    bornes, accepted values, unicité, déterminisme).
  - **Backend de build figé** : `pyproject.toml` gagne `[build-system]` (setuptools) et la
    déclaration explicite des paquets du layout plat — critère §8.2 « le paquet s'installe » :
    installable et importable hors dépôt (vérifié dans un venv isolé).
  - **Schémas dbt `dev`/`prod`** (P8) : `profiles.yml` sépare `dev` → `analytics`
    (fallback `DBT_SCHEMA`) et `prod` → `analytics_prod` (`DBT_SCHEMA_PROD`) ; les deux
    cibles n'écrivent plus jamais dans le même schéma, **sans migration** : le schéma
    `analytics` local est intact (le premier `dbt build --target prod` créera `analytics_prod`).
  - `.env.example` : `DBT_TARGET` et `DBT_SCHEMA_DEV`/`DBT_SCHEMA_PROD` documentés
    (port 5433 déjà conforme au critère §8.2).
  - **Vérifications** : `ruff` 0 erreur ; `pytest` **182 réussis / 0 ignoré** en local
    (`pyarrow`, dépendance cœur, installé dans le venv — critère §8.1) ; YAML du workflow et
    TOML validés ; chaîne complète rejouée en base/schéma jetables `camrent_ci`/`analytics_ci` :
    360 lignes silver + 48 quarantaine + 3 lots → `pipelines load` OK → `dbt build`
    **137/137** ; paquet installé et importable hors dépôt.

- **Harmonisation documentaire face au plan (2026-10-15)** — revue de cohérence de tous les documents de suivi (`context/`, `docs/`, READMEs) contre le plan validé, corrections validées par le porteur du projet :
  - specs `06`/`08`/`09` alignées sur les features réellement disponibles (payload API et formulaire sans `area_m2`/`parking`/`gated`) et le découpage 08a/08b puis 09a/09b ;
  - `project-overview.md` : variables MVP séparées (disponibles aujourd'hui / hors périmètre tant que non collectées) ;
  - compléments demandés par le plan sur les specs `00` (reproduction partielle), `01` (provenance : empreinte de contenu, version de connecteur), `02` (rejets en base, `rent_semantics`, bornes `bathrooms`, drapeaux à trois états), `04` (sémantique de cible, table de qualité), `11` (qualité en continu, jobs ML, audit), `12` (sauvegardes, retour arrière du modèle, runbooks, schémas dev/prod) ;
  - `ui-context.md` (séparation public / administration) et `code-standards.md` (`rent_semantics`) ;
  - note de décision 4 (« adapter la cible et l'intervalle », lot E) ajoutée dans `docs/phase-2/README.md`, `docs/phase-5/README.md`, `docs/phase-6/README.md` et `pipelines/README.md`.

- **08a.1 — socle de l'API publique (ticket #50, 2026-10-17, PR #75 `feat/08a-api-socle`)** :
  - `backend/` créé avec le découpage de la spec 08 §1 : `api/` (application ASGI, route de santé,
    gestion d'erreurs), `domain/` (vocabulaire réel des données), `infrastructure/`
    (configuration, accès PostgreSQL), `schemas/` (contrat strict), et `services/`,
    `repositories/`, `ml/` posés pour les tickets #51/#53/#54.
  - **Contrat versionné** : `GET /api/v1/health` → `{"status": "ok", "api_version": "0.1.0",
    "api_prefix": "/api/v1"}` ; la route n'existe pas hors `/api/v1` (vérifié : `/health` → 404).
  - **Schéma strict** : cinq champs acceptés (`city`, `neighborhood`, `property_type`, `bedrooms`,
    `bathrooms`) ; `area_m2`, `parking`, `gated` et `furnished` sont **refusés** (422), pas ignorés.
    Vocabulaire fermé sur les valeurs réellement présentes (Douala 2 811 / Yaoundé 181 ;
    `apartment`/`studio`/`room`/`house`) et bornes de pièces 0-10 identiques à celles de la
    plateforme data.
  - **Erreurs au format unique** : `validation_error`, `bad_request`, `method_not_allowed`,
    `not_found`, `internal_error`. Les gestionnaires sont branchés sur les classes **Starlette** :
    une route inconnue (404) et une méthode non autorisée (405) sont levées en amont de FastAPI —
    le premier essai sur la classe FastAPI laissait ces deux cas hors format, constaté par test
    avant correction.
  - **Aucune fuite technique** : un échec interne renvoie un message générique ; seules la classe de
    l'exception et le chemin sont journalisés (test dédié avec un message d'exception piégé).
  - **Configuration sans secret** : `DATABASE_URL` est lue à l'appel, avec une erreur explicite qui
    nomme la variable manquante ; l'application démarre et répond sur `/health` sans base.
  - **Outillage** : l'extra `api` (fastapi, uvicorn) est ajouté à l'installation CI
    (`.[dev,transform,ml,api]`) — sans lui les tests de l'API n'auraient pas tourné — et `httpx`
    rejoint l'extra `dev` pour `fastapi.testclient` ; les sous-paquets `backend*` sont déclarés dans
    `pyproject.toml`.
  - **Vérifications** : `ruff` 0 erreur ; `pytest` **220 réussis en local et en CI** (182 avant
    l'incrément, +38 ; l'extra `api` permet aux tests de l'API de tourner réellement en CI) ;
    `dbt build` **137/137 en CI** (inchangé) ; serveur réel `uvicorn` — santé 200, route inconnue 404
    au format unique, `/health` hors préfixe 404, contrat OpenAPI limité à `['/api/v1/health']`.
  - **Reste pour 08a** : #52 (provenance du pin), #53 (marché), #54 (comparaison).

- **08a.2 — endpoint de prédiction (ticket #51, 2026-10-17, PR #77 `feat/08a-predictions`)** :
  - **Modèle servi** : `backend/ml/loader.py` résout le champion du registre épinglé
    (`ml/models/champion.json`) et charge le pipeline **et** l'intervalle calibré ; un artefact
    absent ou illisible lève une erreur explicite, jamais une prédiction inventée.
  - **Service d'estimation** : features construites par le `FeatureBuilder` d'entraînement (aucune
    recomposition hors entraînement), quantiles 5 %/95 % de la Phase 6 appliqués, ordre
    `lower_bound <= estimated_rent <= upper_bound` garanti et plancher à 1 FCFA.
  - **Contrat** : `POST /api/v1/predictions` renvoie `estimated_rent`, `lower_bound`, `upper_bound`,
    `currency`, `model_version` ; quartier inconnu → **404** `not_found`, champ non collecté →
    **422** `validation_error` avec détail par champ, échec de serving → **500** générique.
  - **Tests** : `test_backend_ml.py` (chargement, reproductibilité, invariant d'ordre) et
    `test_api_predictions.py` (200/404/422, format d'erreur) — **20 nouveaux tests**.
  - **Vérifications** : `ruff` 0 erreur ; `pytest` **240 réussis** ; E2E réel sous `uvicorn` avec le
    modèle v3 épinglé — **200** `{"estimated_rent":109990,"currency":"XAF","lower_bound":80000,"upper_bound":150002,"model_version":"rent-model-v3"}`,
    deux appels identiques → réponses identiques.
  - **Reste pour 08a** : #53 (marché), #54 (comparaison).

- **08a.3 — provenance du modèle épinglé (ticket #52, 2026-10-18, PR #78 `feat/08a.3-provenance-pin`, squash `e9eb0dc`)** :
  - **Arbitrage** : le pin v3 décrivait `mart_ml_dataset@5050042e720e` (schéma d'avant le lot B)
    alors que le mart vivant est `mart_ml_dataset@d3c11c225f48`. Décision du porteur du projet :
    **re-promotion gouvernée** sur le mart courant, avec approbation nominative « Ibrahim Talla » —
    pas une mention documentaire de l'écart.
  - **Mise en œuvre** : `python -m ml.src registry --confirm-promotion --approved-by "Ibrahim Talla"`
    → **`rent-model-v4`** (alias `champion` → 4), pin réécrit avec le dataset courant
    (`d3c11c225f48`, 2 992 observations), rapport Phase 7 régénéré. `champion.json` n'a pas été
    édité à la main.
  - **Contrôles** : `backend/ml/loader.py::verify_pinned_version` exige que l'alias `champion`
    pointe la **même version et la même URI** que le pin (alias déplacé → erreur explicite) ; le
    pin doit porter sa provenance (`dataset.version`, `dataset.hash_md5`) ; `ml.src.registry.read_champion_pin`
    refuse désormais un pin illisible ou incomplet (au lieu de rendre un contenu ambigu).
  - **Contrôle avant serving** : nouvelle commande `python -m ml.src pin` — exit 0 avec la version et
    le dataset épinglés, **exit 1** si le pin est absent, illisible ou incomplet (aucun déploiement
    sur une provenance invérifiable).
  - **Tests** : **9 nouveaux** (`test_backend_ml.py` : pin sans provenance, alias conforme, alias
    déplacé, alias absent ; `test_ml_registry.py` : pin illisible, incomplet, sans provenance de
    dataset, commande `pin` sur fichier absent et sur pin sain) ; fixture de serving isolée enrichie
    d'un pin complet.
  - **Vérifications** : `ruff` 0 erreur ; `pytest` **249 réussis en local et en CI** ; `dbt build`
    **137/137 en CI** ; re-promotion réelle en CLI ;
    E2E `uvicorn` — **200** `{"estimated_rent":109990,"currency":"XAF","lower_bound":80000,"upper_bound":150002,"model_version":"rent-model-v4"}`,
    valeurs identiques à la v3, deux appels identiques → réponses identiques ; pin divergent refusé.

- **08a.3+ — serving durci, limites du ticket #52 fermées (2026-10-18, PR #80 `feat/08a.3b-serving-durci`, squash `ebb6530`)** :
  - **Intervalle servi depuis le registre** : `backend/ml/loader.py::load_interval` relit l'intervalle
    calibré dans les **artefacts du run épinglé** (`pin.run_id`), au lieu du fichier local
    `ml/models/rent_model_v1_intervalle.joblib` — plus d'artefact non versionné dont la
    correspondance avec le modèle serait à vérifier à la main.
  - **Chemin de production testé en CI** : `tests/unit/test_serving_registry.py` monte un registre
    MLflow **SQLite** et des artefacts temporaires, journalise modèle + intervalle, écrit un pin
    comme la CLI le ferait, puis charge via `PinnedModelProvider` ; vérifie aussi le refus d'un pin
    périmé et l'absence d'artefact d'intervalle.
  - **Préflight pin ↔ mart** : `python -m ml.src pin --check-dataset` compare le hash du pin au mart
    vivant (base requise) et sort en **erreur 1** en cas de dérive ou de base injoignable ; le
    serving ne relit toujours pas la base à chaque requête.
  - **Tests** : **7 nouveaux** (3 d'intégration registre, 4 sur le préflight) ; suite **256 réussis**
    en local **et en CI** (les tests d'intégration registre s'exécutent réellement, aucun skip).
  - **Vérifications** : `ruff` 0 erreur ; préflight réel — exit 0 sur le pin courant, exit 1 sur un
    pin périmé ; E2E `uvicorn` **sans** le fichier d'intervalle local — **200** avec les mêmes bornes
    (`rent-model-v4`) ; `dbt build` 137/137 en CI.

- **08a.4 — endpoints de marché (ticket #53, 2026-10-19, PR #82 `feat/08a.4-market-endpoints`, squash `01a1081`)** :
  - **Marts enrichis** : `n_republication`/`pct_republication` sur les trois marts de prix,
    quartiers non reconnus au niveau ville, p10/p90 et qualité sur le mart type × ville ;
    tests dbt de non-nullité et de bornes (parts 0–100), catalogue et docs phase 4 à jour.
  - **Endpoints** : `GET /api/v1/market/cities`, `/neighborhoods` (ville obligatoire) et `/prices`,
    lus **exclusivement** dans les marts (aucun recalcul de statistique). Le grain de réponse suit
    exactement les filtres : ville → `mart_city_prices`, type seul → `mart_property_prices`,
    quartier ou chambres → `mart_neighborhood_prices`.
  - **Invariants** : `n_observations` obligatoire dans le schéma (aucune valeur par défaut) ;
    médiane réappliquée sous `min_publish_n` côté service, `median_published` explicite ; aucune
    médiane ni centile agrégés au niveau quartier (effectif, moyenne pondérée, min/max seulement).
  - **Période et erreurs** : `period=YYYY-MM` accepté pour l'unique mois observé, autre mois →
    **200 vide explicite** ; marts multi-mois → **400** ; `neighborhood` sans `city` → **400** ;
    ville/type hors vocabulaire, chambres hors 0–10, mois mal formé → **422** ; sans résultat →
    **200** avec `n_observations: 0` et groupes vides.
  - **Tests** : **16 unitaires** (`test_api_market.py`, dépôt simulé : contrat, seuil, période,
    filtres, schéma sans N) + **7 d'intégration** (`tests/integration/test_market_api.py`,
    comparaison valeur par valeur aux marts PostgreSQL). La CI exécute l'intégration après
    `dbt build` (`DBT_MARTS_SCHEMA=analytics_ci_marts`) ; l'étape unitaire ignore ce dossier pour
    éviter un « skip » trompeur.
  - **Vérifications** : `ruff` 0 ; **272 unitaires + 7 d'intégration** en CI ; `dbt build`
    **169/169** (16 modèles, 153 tests) ; serveur `uvicorn` réel — villes N=2 811/181, 88 quartiers
    pour Douala, Makepe×appartement×2 ch. N=632 médiane 90 000, Bonapriso×appartement×1 ch. N=25
    **médiane nulle** (`median_published=false`).

## In Progress

- **09a.1 — socle du frontend public (ticket #55) : implémenté et vérifié, livraison en attente.** Aucun commit ni PR à ce stade (`AGENTS.md` §8). Périmètre : `context/ui-context.md` **figé** (palette, typographie système, échelle d'espacement, arrondis, breakpoints 480/768/1024/1280, style des graphiques, contrastes AA) ; projet **Next.js 16 + React 19 + TypeScript strict** dans `frontend/` (App Router, composants serveur, aucun `"use client"`) ; thème centralisé dans `app/globals.css` (tokens uniquement, aucune couleur littérale dans les composants) ; mise en page (lien d'évitement, en-tête, navigation du parcours, pied de page rappelant les limites) ; accueil exposant le parcours et « ce que l'outil fait / ne fait pas » ; pages `/estimer`, `/explorer`, `/comparer` explicitement « Écran à venir » (ticket 09a.2/09a.3/09a.4), sans donnée simulée ; 404 au thème ; client `lib/api.ts` avec base `NEXT_PUBLIC_API_BASE_URL`, erreurs typées (`config`, `network`, `timeout` 8 s, `http`, `invalid`) reprenant l'enveloppe d'erreur de l'API. Vérifications : `npm run lint` 0 erreur ; `npm run typecheck` 0 erreur ; `npm test` **11 réussis** ; `npm run build` **succès** (5 routes prérendues) ; serveur réel `next start` — `/` 200 (16,7 Ko), `/estimer` 200, `/explorer` 200, `/comparer` 200, `/inconnu` 404 ; CSS servi contenant les tokens et les media queries ; captures Chrome headless 1280×1600 et 390×1600. CI : job **Frontend** ajouté (Node 22, `npm ci`, lint, typecheck, tests, build), **pas encore exécuté sur GitHub**. Prochaine action : ouvrir la PR, puis #56.
- **08b.1 — socle de l'API interne (ticket #61) : terminé, vérifié et mergé le 2026-10-20.** PR **#86** (branche `feat/08b.1-api-interne` → `develop`, squash `0b185af`), CI **verte** (2 min 21 s : `ruff`, 357 tests unitaires, migrations PostgreSQL, `dbt build`, 11 tests d'intégration), issue #61 close, branche supprimée. Périmètre : application **Django** séparée dans `backend/internal/` (`settings`, `urls`, `wsgi`/`asgi`, `manage.py`), modèle de compte dédié (`InternalUser`, e-mail unique + rôle), rôle `admin` seul ouvert, authentification par jeton `Authorization: Bearer` (empreinte SHA-256 en base, pas de session donc pas de CSRF), autorisation déclarée **par action** (table action → rôles, échec fermé), route de santé publique, journal d'audit (`internal_audit_entries` : auteur, action, cible, date, résultat ; clés sensibles filtrées), route `GET /audit` paginée et filtrable, commande de bootstrap `create_internal_user` journalisée, erreurs au format unique de l'API (`unauthenticated` 401, `forbidden` 403, `invalid_credentials` 401, `conflict` 409). Vérifications : `ruff` 0 ; **357 tests unitaires** (+71) sur SQLite en mémoire ; migrations `accounts.0001_initial` + `audit.0001_initial` appliquées sur PostgreSQL local ; `makemigrations --check` sans changement ; serveur réel Django ASGI (port 8001) — santé 200, login 200, `/me` 200 avec jeton et 401 sans, mot de passe faux 401 indistinguable d'un compte inconnu, rôle non déclaré 403 et refus journalisé, création 201 / doublon 409, logout 204 puis 401, routes publiques absentes de l'interne et inversement, `/api/v1/health` public toujours 200 sans authentification. CI mise à jour (extra `internal`, étape `makemigrations --check` + `migrate` sur PostgreSQL), **exécutée et verte** sur la PR #86. Prochaine action : #62 à #66, appuyés sur ce socle.
- **08a.5 — endpoint de comparaison (ticket #54) : implémenté et vérifié, livraison en attente.** Branche locale `feat/08a.5-comparisons` ; aucune PR ouverte à ce stade. Périmètre : `POST /api/v1/comparisons` (1 à 10 logements), réutilisant **strictement** `EstimationService.estimate` (08a.2) et `MarketService.prices` (08a.4) — aucun second calcul d'estimation ou de statistique ; groupe de comparaison explicite au grain du mart `(ville, quartier, type, chambres)`, les salles de bain ne servant qu'à l'estimation ; écarts signés `asking_rent - référence` (absolu et relatif à une décimale) vers l'estimation, la moyenne et la médiane ; médiane sous 30 → `null`, `median_published=false`, `to_market_median=null` ; groupe de marché absent → `market=null` sans élargir la référence ; quartier inconnu → 404 ; liste vide, plus de 10 logements, prix demandé < 1, champ non collecté ou chambres hors 0–10 → 422. Vérifications : `ruff` 0 ; **286 tests unitaires** (+14) et **11 tests d'intégration** (+4) ; `dbt build` 169/169 inchangé ; HTTP réel — Makepe×appartement×2 ch. à 150 000 → estimation 109 990, marché N=632 (moyenne 98 498, médiane 90 000), écarts +40 010/+36,4 %, +51 502/+52,3 %, +60 000/+66,7 % ; Bonapriso×appartement×1 ch. → N=25, médiane nulle, écart médian nul ; comparaison multiple vérifiée ; simulation CI sur base synthétique — 169/169 puis 11 intégrations. Prochaine action : ouvrir la PR (demande explicite requise par `AGENTS.md` §8), puis #55 à #58.
- **Aucun autre lot en cours.** L'incrément **08a.4 (endpoints de marché, ticket #53)** est **terminé, vérifié et mergé** : PR **#82** (branche `feat/08a.4-market-endpoints` → `develop`, squash `01a1081`), 2026-10-19 ; CI verte (`ruff` 0, **272 tests unitaires** + **7 tests d'intégration** exécutés réellement après `dbt build`, **169/169** en CI), issue #53 close, branche supprimée. Détails et chiffres réels en « Completed » ci-dessous.
- L'incrément **08a.3+ (serving durci)** est **terminé, vérifié et mergé** : PR **#80** (branche `feat/08a.3b-serving-durci` → `develop`, squash `ebb6530`), 2026-10-18 ; CI verte (`ruff` 0, **256 tests réussis** dont les 3 tests d'intégration registre, `dbt build` 137/137), intervalle servi depuis le registre, préflight `pin --check-dataset` ; branche supprimée après fusion. Le ticket de module **#52** (provenance verrouillée, 08a.3) est **terminé, vérifié et mergé** : PR **#78** (branche `feat/08a.3-provenance-pin` → `develop`, squash `e9eb0dc`), 2026-10-18 ; CI verte (`ruff` 0, **249 tests réussis**, `dbt build` 137/137), re-promotion gouvernée `rent-model-v4` sur le mart courant, E2E réel sous `uvicorn` ; branche supprimée après fusion, issue #52 close. Le ticket de module **#51** (prédiction, 08a.2) est **terminé et vérifié** : PR **#77** (branche `feat/08a-predictions` → `develop`), 2026-10-18 ; CI verte (`ruff` 0, **240 tests réussis**, `dbt build` inchangé), E2E réel sous `uvicorn` avec le modèle v3 épinglé. Le ticket de module **#50** (socle de l'API publique, 08a.1) est **terminé, vérifié et mergé** : PR **#75** (branche `feat/08a-api-socle` → `develop`), 2026-10-17 ; CI verte (`ruff` 0, **220 tests réussis** dont les 38 nouveaux, `dbt build` 137/137). Le lot C est **terminé, vérifié et mergé** : PR **#37** (branche `chore/ci-data-tests-on-postgres` → `develop`), fusionné le 2026-10-16 ; pipeline de la PR **verte** — `ruff` 0 erreur, `pytest` **182 réussis / 0 ignoré** en CI, chargement 360/48/3, `dbt build` **137/137 en CI** (le premier run avait échoué avant démarrage : `${{ runner.temp }}` n'est pas lisible au niveau env de job — corrigé par `GITHUB_ENV`). Le lot B est **terminé, vérifié et mergé** : PR **#35** (branche `lot-b-qualite-donnees` → `develop`), squash `627784e`, fusionné le 2026-10-16 ; pipeline CI vertes après la PR et après le merge (`ruff` 0 erreur, **176 tests réussis, 0 ignoré** dans CI — `pyarrow` y est installé). Les branches ont été supprimées après fusion.

## Next Up

- **Estimation** : #56 à #58 (09a.2 à 09a.4, écrans du parcours) après le socle 09a.1 (#55, implémenté et vérifié localement) ; puis #59 (11.4 observabilité du modèle), #60 (12.4 tests d'intégration et bout en bout) et #73 (12.6 vérification du retour arrière du modèle).
- **Back-office** : #62 à #66 (13.1 sources, 13.2 datasets,
  13.3 qualité, 13.4 jobs, 13.5 registre), #67 (14.1 rapports et audit), #68/#69 (09b.1/09b.2
  interface d'administration — après les fondations 13), tous appuyés sur le socle 08b.1 (#61,
  mergé, PR #86).
- **Data Platform — lots ouverts** : #39 (lot E, prix censurés : adapter la cible et l'intervalle par
  une expérience mesurée), #40 (lot F, rétention des runs), #41 (reproductibilité de bout en bout).
- **Data Platform — phases conditionnelles** : #44/#45/#46 (11.1 à 11.3, observabilité des données),
  #43 (10, ordonnancement — condition d'entrée à vérifier), #47/#48/#49/#72 (12.1 à 12.3 et 12.5,
  production et déploiement).
- **Marketplace** : #38 (15, décision et cadrage — aucun code avant décision explicite).
- Conakry reste un chantier **séparé** (décision 10), sans ticket ouvert.

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
- **Provenance du modèle épinglé — résolu le 2026-10-18 (ticket #52)** : l'écart entre le pin v3 (`mart_ml_dataset@5050042e720e`, schéma d'avant le lot B) et le mart vivant (`mart_ml_dataset@d3c11c225f48`) est **clos** par une re-promotion gouvernée : `rent-model-v4`, approuvée le 2026-10-18 par « Ibrahim Talla », pin réécrit par la CLI. Le serving vérifie en plus que l'alias `champion` pointe bien la version et l'URI épinglées. Reste ouvert (hors ticket) : la cohérence pin ↔ mart n'est revérifiée qu'à la promotion, pas à chaque requête.
- **Emplacement d'artefacts historique** : l'expérience `rent_prediction` conserve l'emplacement enregistré à sa création (`mlruns/3`) car MLflow n'expose pas de modification ; l'emplacement épinglé (`ml/artifacts/mlflow`) s'appliquera aux nouvelles expériences (documenté dans `docs/phase-7/README.md`).
- **Prix censurés** : conservés avec `price_is_bound` (borne inférieure, 2 564 lignes sur 2 992) ; le seuil de la Phase 5 et la sélection de la Phase 6 sont mesurés sur toutes les observations. Décision prise (2026-10-15) : **adapter la cible et l'intervalle** — mise en œuvre dans le lot E, mesures à produire (lot E non commencé). Les marts de marché exposent désormais `n_price_bound`/`pct_price_bound` et `n_republication`/`pct_republication` (ticket #53), en plus des quartiers non reconnus au niveau ville.
- **Marché — période unique** : les marts de marché n'ont pas de dimension temporelle et les observations tiennent dans un seul jour de collecte (2026-10-09). Le filtre `period` est accepté pour ce mois et renvoie un vide explicite pour un autre ; il sera refusé (400) si une collecte étalée dans le temps rend les marts multi-mois sans dimension temporelle.
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
- **Lot C (2026-10-16)** : en base jetable `camrent_ci`, le jeu synthétique charge
  `landing.silver_listings` 360 · `landing.quarantine_listings` 48 · `landing.ingestion_runs` 3 lots,
  puis `dbt build` **137/137** dans le schéma `analytics_ci` — le schéma `analytics` réel est
  inchangé. `pyarrow` installé dans le venv local : la suite entière passe à **182 / 0 ignoré**
  (elle ne s'arrêtait plus qu'à cause d'une dépendance cœur manquante, pas d'un test défaillant).
- **Phase 7** : `mlflow-skinny` 3.17.1 (Python 3.14) — `alembic` et `skops` sont nécessaires en plus du `mlflow-skinny` ; base de registre `mlflow` créée une fois dans le conteneur (`createdb -U camrent mlflow`) ; l'URI de suivi est **dérivée de `DATABASE_URL`** — jamais via `str(URL)` (SQLAlchemy masquerait le mot de passe en `***`) ; la création des tables MLflow est très lente sur SQLite (~100 s) alors qu'elle est immédiate sur PostgreSQL.
- **Lot A2 (2026-10-15)** : promotion non approuvée refusée **avant toute écriture** (vérifié en CLI : 2 versions inchangées, aucun fichier épinglé créé, exit 1) ; avec `--confirm-promotion --approved-by` : création de `rent-model-v3`, alias `champion` → v3, tags `approuve_par`/`approuve_le`, écriture de `ml/models/champion.json` ; registre à **3 versions** (v1 rejeu du 2026-10-14, v2, v3). Le fichier `ml/models/champion.json` est le **seul** artefact de modèle versionné (`git check-ignore` exit 1) ; `ml/artifacts/mlflow` est ignoré. `stash@{0}` conserve les anciens rapports régénérés (phases 6-7) ; aucun commit ni push.
