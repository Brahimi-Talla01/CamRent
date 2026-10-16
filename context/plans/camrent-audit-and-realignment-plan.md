# CamRent — Audit du projet et plan de réalignement

**Statut :** **validé** par le porteur du projet le 2026-10-15 (10 décisions, §9) ; lots A1 (documentation), A2 (registre gouverné) et B (qualité et contrat de données) exécutés et vérifiés — suivi au **§14**
**Date :** 2026-10-15 (mis à jour le 2026-10-16 après exécution du lot B)
**Branche de travail :** `chore/audit-realignement` (tirée de `develop`, commit `051bf26`)
**Périmètre de cette étape :** lecture seule — aucun code, aucune migration, aucune spécification
existante n'a été modifié
**Référence produit :** `context/product/camrent-product-realignment.md` (v1.0, 2026-10-14)

Ce document est le livrable des **étapes 0 et 1** du recadrage (§8 : audit en lecture seule, puis
plan de réalignement). Les 10 décisions du §9 ont été rendues le 2026-10-15 ; les lots A1 (équivalent
du « Lot 0 » documentaire, partiellement couvert) et A2 (équivalent du « Lot 1 » registre) ont été
exécutés et vérifiés (**§14**). Les lots restants (B à E) restent soumis à leur condition d'entrée
(§10). Les constats des §1 à §13 décrivent **l'état au moment de l'audit** et sont conservés tels
quels, photographie de référence.

---

## 0. Contexte, méthode et règles appliquées

### 0.1 Règles de dépôt respectées

Les fichiers suivants ont été lus et appliqués avant toute intervention :

- `AGENTS.md` (checklist §1, périmètre §2, interdits §3, règles Data §5, Git §8) ;
- `context/ai-workflow-rules.md` ;
- `context/project-overview.md`, `context/architecture-context.md` ;
- `context/code-standards.md`, `context/ui-context.md` ;
- `context/progress-tracker.md` ;
- `context/feature-specs/00` à `12` ;
- `assets/` (Conception produit, Plan technique, Data Discovery Report) ;
- le code, les tests, les configurations, les migrations dbt et l'historique Git.

**Contradiction de règles signalée :** `AGENTS.md` §8 interdit tout trailer de génération et tout
co-auteur (`Co-Authored-By:`, `Generated with …`, `🤖`). Cette règle est contraire au modèle de commit
par défaut de l'outil utilisé ; **la règle du dépôt prévaut** et aucun commit ne portera de mention
d'outil ou d'agent.

**Aucun conflit bloquant** n'a été relevé entre `AGENTS.md`, `ai-workflow-rules.md` et
`architecture-context.md`. Les tensions documentaires non bloquantes sont listées au §4 (P9).

### 0.2 Préparation Git

- Le travail a démarré sur un HEAD détaché (`chore/suivi-phase-7`, `e8e6dba`) portant deux fichiers
  modifiés non commités : `docs/phase-6/model-report.md` et `docs/phase-7/registry-report.md`
  (rapports régénérés localement), ainsi que `context/product/` non suivi.
- Ces deux modifications ont été mises de côté dans `stash@{0}`
  (« artefacts de rapports ML régénérés localement (phases 6-7) »). Rien n'a été supprimé :
  `git stash pop` les restaure.
- `develop` a été mis à jour par avance rapide sur `origin/develop` (`051bf26`), puis la branche
  `chore/audit-realignement` a été créée.
- Aucune opération destructive, aucun `push`, aucune réécriture d'historique n'a été effectué.

### 0.3 Ce qui a réellement été exécuté

| Vérification                   | Commande                                  | Résultat                                                                                                                                                                                                                  |
| ------------------------------ | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Suite unitaire complète        | `.venv/bin/python -m pytest tests -q`     | **154 réussis, 1 ignoré** (132 s)                                                                                                                                                                                         |
| Identification du test ignoré  | `pytest -q -rs`                           | `tests/unit/test_pipelines_silver.py:121` — `could not import 'pyarrow'` (absent du venv local ; **installé en CI**)                                                                                                      |
| Lint                           | `.venv/bin/ruff check .`                  | `All checks passed!`                                                                                                                                                                                                      |
| Projet dbt (analyse seule)     | `dbt parse`, `dbt ls` (depuis `dbt/`)     | `Found 12 models, 83 data tests, 1 source` ; 2 tests singuliers `assert_*`                                                                                                                                                |
| Base `camrent`, lecture seule  | `psql` via `docker exec camrent-postgres` | `landing.silver_listings` = **2 992** ; `analytics_marts.mart_ml_dataset` = **2 992**                                                                                                                                     |
| Schémas créés                  | idem                                      | `analytics_staging` (1 vue), `analytics_intermediate` (1 vue), `analytics_marts` (10 tables), `landing` (1 table)                                                                                                         |
| Marts de marché                | idem                                      | `mart_city_prices` : Douala N=2 811, médiane 100 000, 89 % de prix bornés ; Yaoundé N=181, médiane 150 000, 31 %                                                                                                          |
| Invariant de publication       | idem                                      | `mart_neighborhood_prices` : 253 lignes, **234 médianes NULL**, plus petit N publié = **31** (seuil N≥30 respecté)                                                                                                        |
| Registre MLflow, lecture seule | `psql` sur la base `mlflow`               | `rent-model` versions **1** (run `c04e80d7`) et **2** (run `ab97ec18`) ; alias `champion` → **version 2** ; 72 runs ; expériences `Default`, `debug_exp` (supprimée), `debug_spy` (supprimée), `rent_prediction` (active) |
| Conteneur local                | `docker ps`                               | `camrent-postgres` up (healthy), exposé sur **5433**                                                                                                                                                                      |

### 0.4 Ce qui n'a pas pu être exécuté (et n'est donc pas affirmé comme vérifié)

- **`dbt build` non rejoué** : la commande matérialise des tables, ce qui sort du périmètre lecture
  seule. Les chiffres « 95/95 » proviennent des rapports versionnés, pas d'une mesure de cette
  session.
- **Aucun CLI de pipeline ou de ML relancé** (`python -m pipelines …`, `python -m ml.src …`) : les
  résultats ML rappelés viennent des rapports versionnés et du tracker.
- **Aucun accès réseau** : CGU des sources, `robots.txt`, issues GitHub et services externes non
  vérifiés ; les analyses juridiques reposent sur `docs/phase-0/legal-assessment.md` et
  `docs/phase-1/legal-review.md`.
- Les bases locales contiennent un état **antérieur à cette mission** (versions 2, alias déplacé,
  72 runs) : il est rapporté comme fait constaté, sans l'attribuer au code fusionné dans `develop`.

---

## 1. Résumé de l'état réel du projet

**En une phrase :** les phases 0 à 7 sont réellement implémentées, testées et documentées avec une
discipline d'invariants remarquable ; le projet s'est arrêté après la Phase 7, et l'écart principal
avec le recadrage ne porte pas sur le travail réalisé mais sur trois points — la **reproductibilité
de bout en bout**, la **gouvernance du registre de modèles** et le **périmètre produit** (API, front,
back-office, observabilité, production absents).

### 1.1 Ce qui est solide et à préserver

- **Chaîne de données réelle** : `data/raw/` (JSONL datés + métadonnées de lot) → Silver
  (`data/processed/silver_listings.parquet`, 2 992 lignes) → PostgreSQL (`landing.silver_listings`)
  → dbt (12 modèles, 83 tests) → `analytics_marts` (4 dimensions, 2 faits, 4 marts).
- **Qualité mesurée, jamais silencieuse** : quarantaine avec motif (`pipelines/silver.py`,
  `quarantine_listings.parquet`), drapeaux conservés (`price_is_bound`, `is_republication`,
  `outlier_flags`, `neighborhood_recognized`), aucune suppression automatique.
- **Invariant de publication tenu en base** : médiane de quartier non publiée sous 30 observations
  (vérifié : 234 médianes NULL sur 253, plus petit N publié = 31), nombre d'observations toujours
  exposé.
- **ML honnête** : baseline mesurée avant tout modèle (`ml/src/baselines.py`), seuil de référence en
  intervalle de confiance bootstrap (`ml/src/run_baselines.py::_reference_threshold`), sélection
  multi-graines, fourchette calibrée et validée par sa couverture (`ml/src/uncertainty.py`),
  explicabilité disponible (`ml/src/interpretability.py`), aucune feature dépendante de la cible
  (`features.py` : `rent_per_m2` exclu).
- **Hygiène** : secrets hors dépôt (`.env` ignoré, `.env.example` versionné), URI masquée dans les
  rapports (`tracking.py::mask_tracking_uri`), lint propre, 154 tests verts.
- **Documentation structurée par phase** : `docs/phase-0` à `docs/phase-7`, `dbt/README.md`,
  `ml/README.md`, `ingestion/README.md`, `pipelines/README.md`, catalogue de données
  (`docs/phase-4/data-catalog.md`).

### 1.2 Ce qui manque ou diverge

1. **Reproductibilité** : un clone ne permet pas de rejouer `Raw → Silver → marts → modèle`, car
   `data/raw/*`, `data/processed/*`, `ml/models/*` et `mlruns/` sont ignorés et `data/samples` n'est
   pas versionné (licence tierce). Voir P1.
2. **Registre de modèles** : l'état « quel modèle sert » vit dans une base PostgreSQL locale, non
   versionnée, dont l'emplacement d'artefacts dépend du répertoire d'exécution ; il a déjà divergé du
   rapport versionné. Voir P2.
3. **Données** : la cible est très majoritairement censurée (bornes « à partir de »), la couverture
   est déséquilibrée (Douala 2 811 / Yaoundé 181), surface et date absentes. Voir P3.
4. **Traçabilité** : ni version de connecteur, ni empreinte de contenu, ni historique de prix ; la
   quarantaine et les métadonnées ne sont pas en base. Voir P4.
5. **Capacités produit** : `backend/`, `frontend/`, `infrastructure/`, `tests/integration/` ne
   contiennent qu'un `.gitkeep` ; la CI ne couvre ni les tests de données ni le build. Voir P7, P10.
6. **Documentation** : redondances entre `assets/` et `context/`, absence de `docs/phase-3/`,
   compteurs de tests périmés, `progress-tracker.md` portant des chiffres d'avant l'issue #20. Voir
   P9.

### 1.3 Où en est officiellement le projet

`context/progress-tracker.md` : « Phase 7 — Model registry terminée et mergée », **aucune phase en
cours**, prochaine étape annoncée « Phase 8 — API » (issue #9) servie depuis
`models:/rent-model@champion`. Cette annonce est cohérente avec l'historique Git
(`daacdc0` Phase 7 mergée, `051bf26` miroir des variables d'environnement) **mais** elle suppose
résolu le problème de gouvernance du registre décrit en P2.

---

## 2. Inventaire des fonctionnalités par état

Cinq états sont distingués, conformément à la demande d'audit :
**implémentée et vérifiée** / **partiellement implémentée** / **documentée uniquement** /
**absente** / **présente mais non vérifiée**.

> **Note de mise à jour (2026-10-15) :** ce tableau photographie l'état **avant** l'exécution des
> lots. Le lot A2 a depuis traité les écarts **P2 et P5** (promotion approuvée explicitement,
> épinglage de la version servie, hash de dataset complet, emplacement d'artefacts épinglé) —
> les lignes « Registre de modèles + règle de promotion » et « Versionnement de dataset »
> relèvent désormais de l'état **implémentée et vérifiée**, sous réserve de l'hygiène des runs
> (rétention) restée ouverte. Voir §14.

| Fonctionnalité                                                                                 | État                                                     | Preuves (chemins, fonctions, vérifications)                                                                                                                                                                                              |
| ---------------------------------------------------------------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Registre des sources et métadonnées de collecte                                                | Implémentée et vérifiée                                  | `ingestion/config.py` (`SOURCES`, `SourceSpec`, droits _verified_ / _uncertain_ / \*local`), `ingestion/storage.py::write_metadata`                                                                                                      |
| Porte légale avant collecte automatisée                                                        | Implémentée et vérifiée                                  | `ingestion/http_client.py` (robots.txt, débit, UA), `sources/base.py`, tests `tests/unit/test_ingestion_guard.py` (5)                                                                                                                    |
| Raw immuable daté + validations Bronze                                                         | Implémentée et vérifiée                                  | `ingestion/storage.py`, `ingestion/bronze.py` ; `data/raw/{listings,reference_data,metadata}/2026-10-09/` (local, non versionné)                                                                                                         |
| Silver dataset reproductible + quarantaine                                                     | Implémentée et vérifiée                                  | `pipelines/silver.py`, `pipelines/parsing.py`, `pipelines/adapters.py`, `pipelines/geo.py` ; `data/processed/silver_listings.parquet`, `quarantine_listings.parquet` (`quarantine_reason`)                                               |
| Référentiel géographique enrichi                                                               | Implémentée et vérifiée                                  | `pipelines/geo.py` (seed + alias) ; non reconnus 582 → 101 (tracker, issue #20) ; 8 tests dédiés                                                                                                                                         |
| EDA reproductible (statistiques dérivées)                                                      | Implémentée et vérifiée                                  | `eda/compute_statistics.py` → `eda/statistics.json` (ignoré), `eda/generate_reports.py` → `eda/{univariate,bivariate,insights}.md`                                                                                                       |
| Chargement Silver → PostgreSQL idempotent                                                      | Implémentée et vérifiée                                  | `pipelines/db.py` (vidage `TRUNCATE` + insertion, jamais de `DROP`) ; 2 992 lignes constatées en base                                                                                                                                    |
| Modèles dbt (dims, faits, marts)                                                               | Implémentée et vérifiée                                  | `dbt/models/**` ; `dbt ls` = 12 modèles ; 10 tables dans `analytics_marts`                                                                                                                                                               |
| Tests dbt (not_null, unique, relations, bornes, invariants)                                    | Implémentée et vérifiée (non rejouée dans cette session) | 83 tests déclarés (`dbt ls`), dont `within_range` et 2 tests singuliers ; conformité confirmée en base sur N≥30 et les volumes                                                                                                           |
| Data Catalog                                                                                   | Implémentée et vérifiée                                  | `docs/phase-4/data-catalog.md` (8 datasets : grain, source, fréquence, owner, sensibilité, qualité, lineage)                                                                                                                             |
| Baselines ML + seuil de référence                                                              | Implémentée et vérifiée                                  | `ml/src/baselines.py`, `run_baselines.py`, `evaluation.py` ; 37 tests ; `docs/phase-5/baseline-report.md` ; seuil 79 773 FCFA                                                                                                            |
| Comparaison de familles de modèles                                                             | Implémentée et vérifiée                                  | `ml/src/models.py`, `training.py` ; 59 tests ; `docs/phase-6/model-report.md` ; modèle retenu `random_forest_log1p`                                                                                                                      |
| Fourchette de prédiction validée                                                               | Implémentée et vérifiée                                  | `ml/src/uncertainty.py` (split-conformal comparé à la régression quantile ; couverture 90,7 % en validation et en test)                                                                                                                  |
| Explicabilité                                                                                  | Implémentée et vérifiée                                  | `ml/src/interpretability.py` (importance par permutation, dépendance partielle, explication locale) ; 13 tests                                                                                                                           |
| Suivi d'expériences MLflow                                                                     | Implémentée et vérifiée                                  | `ml/src/tracking.py` ; `rent_prediction` active dans la base `mlflow` ; 8 tests                                                                                                                                                          |
| Registre de modèles + règle de promotion                                                       | **Partiellement implémentée**                            | `ml/src/registry.py` (règle `bat_la_baseline` / `seuil_phase_5` / `reproductible`) ; 6 tests ; **mais** promotion automatique (alias déplacé sans approbation tracée), version locale divergente du rapport, artefacts non épinglés (P2) |
| Versionnement de dataset                                                                       | **Partiellement implémentée**                            | `tracking.py::dataset_version` (hash MD5) — mais le hash ne couvre que `listing_key` + cible : insensible à un changement de features (P5)                                                                                               |
| Traçabilité de la provenance (empreinte de contenu, version de connecteur, historique de prix) | **Absente**                                              | `ingestion/storage.py::write_metadata` n'enregistre que source, URL, date, méthode, volume, format ; `stg_listings.sql` : `listing_key = md5(source_file\|source_listing_id)`                                                            |
| Qualité interrogeable en base (rejets, motifs, exécutions)                                     | **Absente**                                              | `pipelines/db.py` ne charge que le Silver ; la quarantaine reste en Parquet, les métadonnées en JSON                                                                                                                                     |
| Sémantique de cible explicite (`asking_rent` / `actual_rent` / `unknown`)                      | **Documentée uniquement**                                | recadrage §5.1 ; `mart_ml_dataset.sql` n'expose aucune colonne de sémantique                                                                                                                                                             |
| API de prédiction / marché / comparaison                                                       | **Absente**                                              | `backend/.gitkeep` ; spec `context/feature-specs/08-api.md`                                                                                                                                                                              |
| Frontend d'estimation                                                                          | **Absente**                                              | `frontend/.gitkeep` ; `context/ui-context.md` provisoire ; spec `09-frontend.md`                                                                                                                                                         |
| Back-office (sources, datasets, qualité, jobs, modèles, audit)                                 | **Absente** (non spécifiée)                              | recadrage §3.2 ; specs 13/14 proposées                                                                                                                                                                                                   |
| Marketplace (recherche, comptes annonceurs, contacts)                                          | **Absente**, décision non prise                          | recadrage §3.4 ; spec 15 proposée (phase de décision)                                                                                                                                                                                    |
| Orchestration planifiée                                                                        | **Absente**                                              | spec `10-orchestration.md` ; aucun DAG ni cron versionné                                                                                                                                                                                 |
| Observabilité (fraîcheur, volumes, rejets, dérive, alertes)                                    | **Absente** (prémices de logs)                           | `logging` présent dans `ingestion/__main__.py`, `sources/base.py`, `http_client.py`, `pipelines/__main__.py`, `ml/src/__main__.py` ; aucune métrique ni alerte                                                                           |
| Tâches asynchrones et jobs (entraînement hors requête HTTP)                                    | **Absente**                                              | recadrage §6 ; aucun worker, aucune file de tâches                                                                                                                                                                                       |
| Authentification, rôles, permissions, audit des actions                                        | **Absente**                                              | recadrage §3.5 ; spec `12-production.md` §6                                                                                                                                                                                              |
| Autorisation et licences des sources                                                           | Implémentée et vérifiée (documentaire)                   | `docs/phase-0/legal-assessment.md`, `docs/phase-1/legal-review.md`, `data/samples/README.md` ; piste `chore/remove-inspire-from-repo` sur le dépôt distant                                                                               |
| CI (lint + tests unitaires)                                                                    | Implémentée et vérifiée                                  | `.github/workflows/ci.yml` ; 154 tests verts et `ruff` propre reproduits localement                                                                                                                                                      |
| CI des tests de données, d'intégration et build                                                | **Absente**                                              | commentaire explicite dans `ci.yml` ; `cd.yml` = placeholder `workflow_dispatch`                                                                                                                                                         |

---

## 3. Tableau comparatif : spécifications vs code existant

| Spécification               | Exigence                                                                                                                 | Réalité du code                                                                                                                                                                                                 | Écart                                                         |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `00-validation-probleme.md` | échantillon dans `data/samples/`, profiling, rapport de qualité, verdict de faisabilité, décision de stack               | `docs/phase-0/` complet ; `data/samples/` **non versionné** (licence tierce) ; `scripts/profile_sample.py` versionné                                                                                            | Faible : reproduction partielle hors du dépôt                 |
| `01-data-ingestion.md`      | scripts par source, raw daté, métadonnées de lot, validations Bronze, idempotence                                        | `ingestion/` conforme ; `SOURCES` documenté ; 17 tests collectés (le README en annonce 18)                                                                                                                      | Faible : compteur documentaire (P9)                           |
| `02-data-cleaning.md`       | types, devises, quartiers, catégories, déduplication, quarantine, rapport                                                | `pipelines/` conforme ; `price_is_bound` (2 564), `is_republication` (2 001), aberrations signalées, quarantine avec motif                                                                                      | Moyen : motifs de rejet non persistés en base (P4)            |
| `03-eda.md`                 | rapports univarié, bivarié, insights + nombre d'observations systématique                                                | `eda/` conforme et **entièrement dérivé** de `statistics.json`                                                                                                                                                  | Faible : pas de `docs/phase-3/` (P9)                          |
| `04-data-marts.md`          | PostgreSQL, dims/faits, 4 marts, dbt, tests, grain, Data Catalog, lineage                                                | 12 modèles, 83 tests, 10 tables `analytics_marts`, catalogue complet                                                                                                                                            | Aucun sur le fond ; **tests non exécutés en CI** (P7)         |
| `05-baseline-ml.md`         | 3 baselines, séparation 70/15/15 ou chronologique, MAE/RMSE/R², segments, seuil                                          | `ml/src/` conforme ; séparation aléatoire justifiée (`posted_at` vide, une seule journée de collecte)                                                                                                           | Aucun                                                         |
| `06-modeles-ml.md`          | ordre d'exploration, features directes/géo/dérivées, comparaison, intervalle, explicabilité                              | modèles, intervalles et explicabilité conformes ; **features demandées indisponibles** (`area_m2`, `furnished`, `parking`, `gated`, `latitude`, `longitude`, `property_age`) → `features.py::EXCLUDED_FEATURES` | **Spec à corriger** (P6)                                      |
| `07-model-registry.md`      | MLflow, `rent_prediction`, traçabilité par run, versions `rent-model-vN`, règle de promotion, versionnement des datasets | tout existe, **mais** promotion automatique, artefacts non épinglés, version de dataset partielle, état local divergent                                                                                         | **Point de reprise prioritaire** (P2, P5)                     |
| `08-api.md`                 | payload avec `area_m2`, `parking`, `gated` ; endpoints marché/comparaison ; `model_version`                              | aucun backend ; les champs du payload sont vides dans les données ; les marts marché sont prêts                                                                                                                 | **Spec à réviser avant implémentation** (P6)                  |
| `09-frontend.md`            | Next.js, flux estimation → exploration → comparaison, `ui-context.md` figé avant de coder                                | `frontend/` vide ; `ui-context.md` explicitement provisoire                                                                                                                                                     | Cohérent : phase non commencée                                |
| `10-orchestration.md`       | DAG quotidien, retries, reprise, rejouabilité, exécution manuelle                                                        | rien ; condition d'entrée (plusieurs pipelines stabilisés) **non atteinte**                                                                                                                                     | Cohérent : ne pas démarrer                                    |
| `11-observabilite.md`       | santé pipeline, fraîcheur, volumes, qualité, logs structurés, dérive, alertes                                            | rien, mais les matières premières existent (métadonnées de lot, motifs de rejet, `stats`)                                                                                                                       | **À compléter, en s'appuyant sur les données déjà produites** |
| `12-production.md`          | 3 environnements, docker-compose, CI complète, 4 niveaux de tests, secrets, sauvegardes                                  | `infrastructure/` vide ; `profiles.yml` : `dev` et `prod` **identiques** ; CI partielle ; `.env.example` annonce 5432 alors que le conteneur expose 5433                                                        | **À compléter** (P7, P8)                                      |

---

## 4. Incohérences et risques prioritaires

### P1 — Reproductibilité de bout en bout non garantie (risque élevé)

- **Faits :** `.gitignore` exclut `data/raw/*`, `data/processed/*`, `ml/models/*`, `mlruns/` ;
  `data/samples` n'est pas versionné (licence absente, `data/samples/README.md`) ; `data/raw/`
  local ne contient qu'une journée de collecte (`2026-10-09`) ; `pyproject.toml` n'a **pas** de
  `build-system` (commentaire explicite), donc le paquet n'est pas installable en l'état.
- **Conséquence :** aucun tiers, aucune CI et aucun futur environnement ne peut recalculer les
  chiffres publiés (2 992 lignes, MAE 75 425, 95/95). C'est le blocage principal avant l'API et la
  production.
- **Recommandations :** documenter la procédure de reconstitution (sources, empreintes attendues,
  commandes) ; à terme, un jeu de test figé et versionnable (extrait anonymisé autorisé) ; figer le
  backend de build.

### P2 — Gouvernance du registre de modèles (risque élevé, prioritaire)

- **Faits :** base `mlflow` → `rent-model` **v1** (run `c04e80d7`) **et v2** (run `ab97ec18`), alias
  `champion` pointant sur **v2** ; 72 runs dans `rent_prediction` ; expériences `debug_exp` et
  `debug_spy` supprimées ; `docs/phase-7/registry-report.md` (versionné) documente 12 runs et
  `rent-model-v1` ; `mlruns/` (41 Mo) non suivi ; `MLFLOW_ARTIFACT_LOCATION` absent de
  `.env.example` (l'emplacement des artefacts dépend donc du répertoire d'exécution) ;
  `ml/src/config.py::MODEL_ARTIFACT_NAME = "rent_model_v1"` figé alors que le registre numérote en
  `vN` ; `ml/src/registry.py` déplace l'alias **sans trace d'approbation**.
- **Conséquence :** « quel modèle sert aujourd'hui ? » n'est pas vérifiable depuis le dépôt, et
  chaque exécution de `python -m ml.src registry` crée une version et déplace le champion. Cela
  contredit le back-office §3.2 (module 6 : approbation, déploiement, retrait) et la promesse
  « aucun modèle non enregistré déployable ».
- **Recommandations :** promotion explicite (`--confirm-promotion`, tags `approuve_par`,
  `approuve_le`) ; fichier versionné `ml/models/champion.json` (version + `run_id` + empreinte) ;
  emplacement d'artefacts documenté et épinglé ; politique de rétention des runs ; garde-fou
  empêchant les tests d'écrire dans la base de développement.

### P3 — Cible censurée et couverture déséquilibrée (risque élevé, produit)

- **Faits :** `mart_city_prices` → Douala 2 811 observations avec **89 % de prix bornés**, Yaoundé
  181 observations avec 31 % ; Silver : 2 001 républications, 101 quartiers non reconnus (78
  libellés), top-5 quartiers ≈ 68,7 % des lignes ; surface, date, meublé, parking et barrière
  **indisponibles** ; rapport Phase 6 : MAE validation 75 425 contre MAE test 159 130.
- **Conséquence :** l'estimation porte largement sur des prix minorants ; toute promesse de
  précision fine serait trompeuse. La question des prix censurés, ouverte depuis la Phase 0, est
  bloquante pour l'affichage produit (« fourchette » sur une cible censurée).
- **Recommandations :** trancher explicitement la stratégie (exclure / traiter comme borne `≥` /
  pondérer / adapter la cible et l'intervalle) ; exposer la part de prix bornés et la couverture par
  zone dans l'interface ; documenter le périmètre géographique réellement fiable.

### P4 — Traçabilité des données incomplète au regard du recadrage §5.2 (risque moyen à élevé)

- **Faits :** `ingestion/storage.py::write_metadata` (source, URL, date, méthode, volume, format ;
  **pas** de version de connecteur, **pas** d'empreinte de contenu, **pas** de statut de
  validation) ; `stg_listings.sql` : `listing_key = md5(source_file|source_listing_id)` ; aucune
  table d'exécutions ni de rejets en base (`pipelines/db.py` ne charge que le Silver) ;
  `mart_ml_dataset.sql` n'expose ni sémantique de cible ni URL.
- **Conséquence :** impossible de détecter un changement de prix d'une même annonce entre deux
  collectes, ni d'alimenter le module « Qualité » du back-office autrement qu'en relisant des
  fichiers locaux.
- **Recommandations :** ajouter version de parseur et empreinte de contenu au lot ; charger
  quarantaine et métadonnées en `landing`, puis exposer une table de qualité (motif, source,
  nombre de rejets) ; ajouter la sémantique de cible (`rent_semantics`).

### P5 — Version de dataset insensible aux features (risque moyen)

- **Fait :** `ml/src/tracking.py::dataset_version` hashe uniquement `listing_key` et
  `target_rent_price` ; version constatée `mart_ml_dataset@21774b224bdb`.
- **Conséquence :** une modification de `bedrooms` ou `neighborhood` conserve **la même** version,
  ce qui donne une fausse garantie de reproductibilité aux runs et au registre.
- **Recommandation :** hasher toutes les colonnes du mart (clés, features, cible) et couvrir le
  changement par un test de régression.

### P6 — Contrats de spécification inapplicables (risque moyen)

- **Faits :** `06-modeles-ml.md` §2 exige `area_m2`, `latitude`, `longitude`, `distance_to_center`,
  `property_age`, `furnished`, `parking`, `gated` ; `08-api.md` §2 met `area_m2`, `parking` et
  `gated` dans le payload ; `ml/src/features.py::EXCLUDED_FEATURES` documente leur indisponibilité.
- **Conséquence :** une API implémentée telle quelle accepterait des champs silencieusement ignorés.
- **Recommandation :** réviser les specs 06 et 08 avant toute implémentation (voir §6).

### P7 — Aucune barrière automatique sur les invariants de données (risque moyen)

- **Faits :** `.github/workflows/ci.yml` = `ruff check .` + `pytest -q` sur Python 3.12, avec un
  commentaire listant ce qui n'est pas encore activé (dbt, intégration, build front) ; `cd.yml` =
  `echo` de placeholder ; `tests/integration/` ne contient qu'un `.gitkeep`.
- **Conséquence :** les invariants (N≥30, relations faits→dims, bornes, volumes) ne sont protégés
  que par des exécutions locales.
- **Recommandation :** service PostgreSQL en CI et `dbt build` (tests de données) ; le projet compile
  déjà (`dbt parse` réussi) et 83 tests sont prêts à tourner.

### P8 — Pas de séparation d'environnements, port incohérent (risque moyen)

- **Faits :** `dbt/profiles.yml` définit `dev` et `prod` avec la même base et le même schéma ;
  `.env.example` annonce `POSTGRES_PORT=5432` alors que le conteneur expose **5433** (contournement
  documenté seulement dans `ml/README.md` et les notes de session).
- **Conséquence :** risque d'exécuter une charge étiquetée « prod » sur la base de développement.
- **Recommandation :** schémas distincts par environnement (`DBT_SCHEMA`), corriger `.env.example`.

### P9 — Documentation : redondances, emplacements et compteurs périmés (risque faible à moyen)

- **Faits :** `assets/Data_Discovery_Report.md` (183 lignes) face à
  `docs/phase-0/data-discovery-report.md` (69 lignes) ; `assets/CamRent_Conception_Produit_et_Probleme_Data.md`
  (963 lignes) face à `context/project-overview.md` (113 lignes) ; pas de `docs/phase-3/` (les
  rapports sont dans `eda/`) ; `docs/phase-1/README.md` annonce 18 tests (17 collectés) ;
  `docs/phase-2/README.md` ligne 40 et `context/progress-tracker.md` lignes 224-226 portent
  1 970 républications et 582 quartiers non reconnus (état d'avant l'issue #20 ; état courant
  2 001 et 101, correctement rapporté ailleurs) ; `context/product/` n'est référencé par aucun
  fichier de contexte.
- **Conséquence :** risque de travailler sur une version obsolète d'un document et de citer des
  chiffres périmés.
- **Recommandation :** désigner une source de vérité par document (voir §6) et dater les compteurs.

### P10 — Capacités produit absentes mais déjà présupposées (risque moyen)

- **Faits :** `backend/`, `frontend/`, `infrastructure/`, `tests/integration/` ne contiennent qu'un
  `.gitkeep` ; les specs 08 à 12 les supposent.
- **Conséquence :** les dépendances réelles de l'API (registre épinglé, tables de qualité, rôles,
  jobs) ne sont pas prêtes ; implémenter l'API d'abord reviendrait à construire sur un socle
  instable.
- **Recommandation :** traiter d'abord les lots 1 à 3 (§10), puis l'API (08a/08b) et le front
  (09a/09b).

---

## 5. Décisions proposées sur les phases existantes

| Phase                            | Décision proposée                                                                                                                                                                     | Justification                                                                                                                                                |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `00-validation-probleme.md`      | **Conserver**, compléter par une note « reproduction partielle : échantillon non versionné »                                                                                          | Le travail est fait et vérifié ; seule la reproduction hors dépôt est limitée (P1)                                                                           |
| `01-data-ingestion.md`           | **Conserver et compléter** (version de connecteur, empreinte de contenu, statut de validation, exécutions)                                                                            | Exigences du recadrage §5.2 non couvertes (P4)                                                                                                               |
| `02-data-cleaning.md`            | **Conserver et compléter** (règles versionnées, motifs de rejet en base, distinction `false`/`true`/`unknown`, contrôle des bornes `bathrooms` — valeur 80 constatée et non signalée) | Exigences du recadrage §5.3 ; point ouvert déjà consigné dans le tracker                                                                                     |
| `03-eda.md`                      | **Conserver**, corriger l'emplacement documentaire (ajouter `docs/phase-3/README.md` pointant vers `eda/`, sans déplacer les artefacts)                                               | Convention `docs/phase-N/` rompue sans raison de fond (P9)                                                                                                   |
| `04-data-marts.md`               | **Conserver et compléter** (sémantique de cible, table de qualité/rejets, tests de données en CI)                                                                                     | Les modèles et tests sont conformes ; il manque les supports du back-office (P4, P7)                                                                         |
| `05-baseline-ml.md`              | **Conserver** (aucune correction de fond)                                                                                                                                             | Baselines, seuil et scénarios de sensibilité vérifiables et documentés                                                                                       |
| `06-modeles-ml.md`               | **Corriger** (features réellement disponibles ; scénario « prix censurés » explicite)                                                                                                 | Spec contredisant le code et les données (P3, P6)                                                                                                            |
| `07-model-registry.md`           | **Point de reprise prioritaire** : corriger la gouvernance (approbation, épinglage, artefact store, hygiène des runs, version de dataset)                                             | La phase est marquée terminée alors que l'état servi n'est pas vérifiable depuis le dépôt (P2, P5)                                                           |
| `08-api.md`                      | **Réviser puis découper** : `08a` API publique (prédiction, marché, comparaison), `08b` API interne/admin (permissions, jobs)                                                         | Payload inapplicable (P6) ; les responsabilités publiques et internes ne doivent pas être mélangées                                                          |
| `09-frontend.md`                 | **Réviser et découper** : `09a` estimation publique, `09b` administration                                                                                                             | Le recadrage sépare le produit public du back-office ; `ui-context.md` doit être figé avant de coder                                                         |
| `10-orchestration.md`            | **Conserver et proportionner** (condition d'entrée inchangée : pas d'Airflow avant stabilisation)                                                                                     | Aucun besoin mesuré aujourd'hui ; éviter la sur-ingénierie                                                                                                   |
| `11-observabilite.md`            | **Compléter** (qualité, jobs, erreurs, fraîcheur, audit, alertes) en réutilisant les données déjà produites                                                                           | Aucune observabilité, alors que la matière première existe (P4, P10)                                                                                         |
| `12-production.md`               | **Compléter** (secrets, sauvegardes, tests de données en CI, retour arrière, runbooks, environnements séparés)                                                                        | Phase la plus éloignée de l'état réel (P7, P8)                                                                                                               |
| Nouvelles specs `13`, `14`, `15` | **Créer uniquement sur validation** : `13-backoffice-foundations`, `14-backoffice-reporting-observability`, `15-marketplace-discovery-and-scope`                                      | Le back-office est transversal et doit être planifié au moment où les fonctions qu'il pilote existent ; la marketplace doit rester une phase de **décision** |

**Hors MVP, à laisser dehors :** marketplace complète, Conakry et multi-pays, paiements et
facturation, streaming (Kafka), microservices, éditeur graphique de pipelines, exécution de scripts
arbitraires, entraînement synchrone dans une requête HTTP, score de confiance non calibré,
suppression automatique de valeurs atypiques.

---

## 6. Changements documentaires proposés (fichier par fichier, aucun exécuté)

| Fichier                                               | Changement proposé                                                                                                                                   | Raison                                                                          |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `AGENTS.md`                                           | §1 et §10 : ajouter `context/product/camrent-product-realignment.md` et `context/plans/` aux lectures obligatoires                                   | Le recadrage est aujourd'hui invisible dans les règles de travail (P9)          |
| `context/ai-workflow-rules.md`                        | ajouter l'enchaînement « audit → plan validé → lot vérifié » et la liste des sous-systèmes (Data Platform, Back-office, Estimation, Marketplace)     | Aligner le workflow sur le recadrage §8                                         |
| `context/project-overview.md`                         | aligner sur la vision §2 du recadrage : loyers **demandés**, marketplace **conditionnelle**, back-office, limites de communication                   | Éviter deux visions concurrentes (P9)                                           |
| `context/architecture-context.md`                     | ajouter la frontière des quatre sous-systèmes, la politique des artefacts ML et du registre, la décision « un seul déploiement modulaire + workers » | Le document ne couvre ni le back-office ni la gouvernance des modèles (P2, P10) |
| `context/progress-tracker.md`                         | corriger les chiffres périmés (§Session Notes), marquer les points ouverts (registre, qualité, prix censurés), **sans inventer de progrès**          | Le tracker doit refléter l'état réel (AGENTS.md §7)                             |
| `context/feature-specs/00` à `05`                     | ajouter une note de statut datée (« vérifié le 2026-10-15 ») et les écarts constatés                                                                 | Tracer l'audit sans réécrire les décisions                                      |
| `context/feature-specs/06-modeles-ml.md`              | retirer/marquer comme indisponibles les features non collectées ; documenter la stratégie prix censurés                                              | Contredit `features.py` (P6)                                                    |
| `context/feature-specs/07-model-registry.md`          | préciser la promotion **explicite** (approbation), l'épinglage de version, l'emplacement d'artefacts, la version de dataset complète                 | Le code ne satisfait pas la règle telle qu'elle est lue (P2, P5)                |
| `context/feature-specs/08-api.md`                     | réviser le payload (champs réellement disponibles), découper 08a/08b, préciser les erreurs et le `model_version`                                     | Payload inapplicable (P6)                                                       |
| `context/feature-specs/09-frontend.md`                | découper 09a (public) et 09b (administration) ; rappeler que `ui-context.md` doit être figé avant                                                    | Séparation public/admin du recadrage                                            |
| `context/feature-specs/10-orchestration.md`           | conserver, préciser la condition d'entrée                                                                                                            | Éviter l'introduction prématurée d'Airflow                                      |
| `context/feature-specs/11-observabilite.md`           | compléter : qualité, jobs, erreurs, fraîcheur, audit, alertes, seuils justifiés                                                                      | Phase la plus utile après le lot 2                                              |
| `context/feature-specs/12-production.md`              | compléter : secrets, sauvegardes, tests de données en CI, retour arrière, runbooks, environnements séparés                                           | Écarts P7 et P8                                                                 |
| `context/ui-context.md`                               | séparer les principes public / administration ; indiquer que le thème reste à figer                                                                  | Prérequis de la Phase 9                                                         |
| `docs/phase-1/README.md`                              | corriger le compteur de tests (17 collectés) et dater la vérification                                                                                | P9                                                                              |
| `docs/phase-2/README.md`                              | dater explicitement les chiffres 1 970 / 582 comme « avant l'issue #20 »                                                                             | P9                                                                              |
| `docs/phase-3/README.md` (nouveau)                    | pointer vers `eda/` et rappeler la commande de régénération                                                                                          | Convention documentaire (P9)                                                    |
| `docs/phase-7/README.md`                              | préciser que le registre est un **état local mutable** et que le livrable reproductible reste le rapport + le code                                   | Éviter la lecture erronée actuelle (P2)                                         |
| `context/plans/camrent-audit-and-realignment-plan.md` | **le présent document**                                                                                                                              | Livrable des étapes 0 et 1                                                      |
| `assets/` (Conception produit, Data Discovery Report) | décider d'une source de vérité (renvoi depuis `context/`, sans supprimer)                                                                            | Redondances P9                                                                  |

---

## 7. Modifications techniques envisagées (aucune exécutée)

Présentées par ordre de dépendance, avec le besoin concret qu'elles servent.

1. **Version de dataset complète** — `ml/src/tracking.py::dataset_version` : hasher toutes les
   colonnes du mart (clés, features, cible). _Besoin :_ P5, la traçabilité des runs.
2. **Promotion explicite** — `ml/src/registry.py` + `ml/src/run_registry.py` + CLI : option
   `--confirm-promotion`, tags `approuve_par` / `approuve_le`, refus de déplacer l'alias sans
   confirmation. _Besoin :_ P2, gouvernance du registre et futur module d'approbation.
3. **Épinglage de version** — écrire un fichier versionné (`ml/models/champion.json`) contenant
   version, `run_id`, empreinte du dataset, SHA Git ; `config.MODEL_ARTIFACT_NAME` ne doit plus être
   figé. _Besoin :_ P2, rendre « quel modèle sert » vérifiable depuis le dépôt.
4. **Emplacement des artefacts** — documenter et épingler `MLFLOW_TRACKING_URI` et
   `MLFLOW_ARTIFACT_LOCATION` dans `.env.example` (sans secret), avec un chemin indépendant du
   répertoire d'exécution. _Besoin :_ P2, éviter les artefacts « perdus » dans `mlruns/`.
5. **Hygiène du registre** — politique de rétention des runs, suppression contrôlée des versions non
   promues, garde-fou empêchant les tests d'écrire dans la base `mlflow` de développement.
   _Besoin :_ P2 (72 runs, expériences `debug_*`).
6. **Qualité et rejets en base** — `pipelines/db.py` et dbt : charger `quarantine_listings` et les
   métadonnées de lots dans `landing`, puis exposer une table de qualité (motif, source, nombre de
   rejets). _Besoin :_ P4, module « Qualité » du back-office et Phase 11.
7. **Provenance renforcée** — `ingestion` : version du parseur, empreinte de contenu par lot, statut
   de validation, éventuellement table d'exécutions. _Besoin :_ P4, historique des prix.
8. **Sémantique de cible** — `dbt/models/marts/mart_ml_dataset.sql` : colonne `rent_semantics`
   (`asking_rent` / `unknown`) et exposition de l'URL source si les droits le permettent.
   _Besoin :_ recadrage §5.1.
9. **Bornes de données** — contrôles sur `bathrooms` (valeur 80 constatée) et sur les prix extrêmes.
   _Besoin :_ P3, qualité mesurée.
10. **CI de données** — service PostgreSQL + `dbt build` (12 modèles, 83 tests) ; installation du
    paquet avec un backend de build figé ; correction du port dans `.env.example` (5432 → 5433).
    _Besoin :_ P7, P8.
11. **Séparation d'environnements dbt** — `DBT_SCHEMA` distinct en `dev` et `prod` (opération non
    destructive, à confirmer). _Besoin :_ P8.
12. **Base de l'API** (lot ultérieur) : schémas Pydantic stricts, chargement du modèle **épinglé**,
    aucune logique d'entraînement dans les handlers, fourchette issue de l'intervalle calibré
    sauvegardé (`rent_model_v1_intervalle.joblib`). _Besoin :_ phases 08a/08b.

Aucune de ces modifications n'est engagée : elles nécessitent les décisions du §9.

---

## 8. Tests et critères d'acceptation des prochains lots

### 8.1 Vérifications de référence (à reproduire à chaque lot)

| Contrôle                 | Commande                                              | Critère                                                                             |
| ------------------------ | ----------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Lint                     | `.venv/bin/ruff check .`                              | 0 erreur                                                                            |
| Tests unitaires          | `.venv/bin/python -m pytest tests -q`                 | 0 échec ; **0 test ignoré** dans l'environnement de référence (installer `pyarrow`) |
| Projet dbt               | `cd dbt && dbt parse && dbt ls`                       | 12 modèles, 83 tests (au minimum : pas de régression)                               |
| Tests de données         | `python -m pipelines load` puis `cd dbt && dbt build` | 12 modèles + 83 tests en succès                                                     |
| Volumes et grain         | requêtes `psql` de contrôle                           | `count(*) = 2992` de `landing.silver_listings` à `analytics_marts.mart_ml_dataset`  |
| Invariant de publication | `psql` sur `mart_neighborhood_prices`                 | 0 médiane publiée sous N=30 ; plus petit N publié ≥ 30                              |
| Déterminisme ML          | `python -m ml.src models` (artefacts JSON)            | métriques identiques au rejeu (md5 inchangé)                                        |

### 8.2 Critères d'acceptation par lot

- **Lot 0 (documentaire)** : les écarts du §6 sont corrigés ; aucun chiffre non vérifié n'est
  ajouté ; le diff est lisible et réversible ; `progress-tracker.md` reste fidèle à l'état réel.
- **Lot 1 (registre)** : promotion refusée sans confirmation explicite (test unitaire dédié) ;
  version de dataset qui change quand une feature change (test de régression sur P5) ; l'alias
  `champion` et la version servie sont lisibles depuis un fichier versionné ; `python -m ml.src
registry` est idempotent **ou** exige la confirmation ; le rapport régénéré correspond à l'état
  réellement constaté en base.
- **Lot 2 (qualité/observabilité)** : la quarantaine et les métadonnées de lots sont interrogeables
  en base ; les motifs de rejet sont agrégés ; la version de parseur et l'empreinte de contenu
  existent par lot ; les bornes `bathrooms` sont contrôlées ; tests unitaires ajoutés.
- **Lot 3 (CI de données)** : `dbt build` s'exécute en CI sur un service PostgreSQL ; le paquet
  s'installe ; `.env.example` est cohérent avec le conteneur ; `dev` et `prod` sont séparés
  (schémas distincts) sans migration destructive.
- **Lot 4 (08a/08b)** : `POST /api/v1/predictions` retourne `estimated_rent`, `lower_bound`,
  `upper_bound`, `currency`, `model_version` ; les statistiques de marché incluent toujours
  `n_observations` ; entrées invalides → 400/404/422 prévisibles ; aucune logique d'entraînement
  dans les routes ; test d'intégration API → base → modèle ; le modèle chargé est la version
  épinglée.
- **Lot 5 (09a/09b)** : `ui-context.md` figé avant le code ; l'interface affiche fourchette,
  nombre d'observations et limites de la donnée ; aucun pourcentage de confiance non justifié ;
  parcours estimation → exploration → comparaison fonctionnel sur les données réelles.

---

## 9. Décisions nécessitant votre approbation

1. **Marketplace** : à documenter comme piste (`15-marketplace-discovery-and-scope`) ou à écarter
   explicitement du périmètre ?
   Réponse: On conserve la Marketplace dans le MVP mais de façon structuré
2. **Priorité après la pause** : (a) fiabiliser registre et qualité puis API et front minimal, ou
   (b) commencer par le back-office ?
   Réponse: b)
3. **Registre** : MLflow est-il conservé ? Quel emplacement d'artefacts (local versionné,
   MinIO/S3) et **qui** approuve une promotion ?
   Réponse: Oui il est conservé, l'admin
4. **Prix censurés** : exclure, traiter comme borne (`≥`), pondérer, ou adapter la cible et
   l'intervalle ?
   R: adapter la cible et
   l'intervalle
5. **Périmètre géographique du MVP** : liste des quartiers retenus, et que fait-on de Yaoundé
   (181 observations) ?
   Réponse: Yaoundé, Douala et Conakry
6. **Collecte supplémentaire** : autorisation d'étendre la collecte (surface, dates, nouvelles
   sources) et conditions légales associées ?
   Réponse : On finalise d'abord avant de recollecter les données
7. **Back-office** : créer les specs 13 et 14 maintenant ou après 08 et 09 ? Quels rôles internes
   au départ ?
   R: après 08 et 09
8. **CI renforcée** : introduire PostgreSQL et `dbt build` en CI (coût en temps d'exécution) ?
   R: oui
9. **Sémantique de cible** : renommer en `asking_rent` / `monthly_rent_xaf` (migration de schéma) ou
   ajouter une colonne `rent_semantics` ?
   R: ajouté rent_semantics
10. **Conakry** : décision séparée (données, code, produit ou commercialisation ?).
    R: Oui il faut séparer

---

## 10. Ordre de travail progressif proposé

| Lot               | Contenu                                                                                                                                                                     | Écarts traités                | Condition d'entrée |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- | ------------------ |
| **Lot 0**         | Documentation seule, aucun code : rattacher le recadrage, corriger les compteurs périmés, créer `docs/phase-3/README.md`, créer les specs approuvées (13/14/15 si retenues) | P9, P6 (partie documentaire)  | Décisions 1, 2, 7  |
| **Lot 1**         | Registre fiable : promotion explicite, épinglage de version, emplacement d'artefacts, hash de dataset complet, hygiène des runs, tests                                      | P2, P5                        | Décision 3         |
| **Lot 2**         | Qualité et observabilité des données : quarantaine et métadonnées en base, version de parseur, empreinte de contenu, contrôle des bornes, tests                             | P4, P3 (mesure)               | Décision 6         |
| **Lot 3**         | CI de données : PostgreSQL + `dbt build`, backend de build figé, `.env.example` corrigé, `dev`/`prod` séparés                                                               | P7, P8, P1 (partie outillage) | Décision 8         |
| **Lot 4**         | Phase 8 API en deux temps : 08a public (prédiction, marché, comparaison), 08b interne (permissions, jobs)                                                                   | P6, P10                       | Décisions 3, 4, 5  |
| **Lot 5**         | Phase 9 : 09a estimation publique, puis 09b administration (`ui-context.md` figé avant)                                                                                     | P10                           | Lot 4              |
| **Lots suivants** | 10 orchestration (si besoin mesuré), 11 observabilité continue, 12 production (environnements, sauvegardes, runbooks), 13/14/15 si approuvées                               | —                             | Lots précédents    |

Principe : **un lot = un changement cohérent, vérifiable et réversible**, avec mise à jour du
tracker après vérification, conformément à `AGENTS.md` §2 et §6.

---

## 11. Séparation : faits constatés, hypothèses, recommandations

### 11.1 Faits constatés (reproductibles, avec leur preuve)

> **Rectificatif (2026-10-16).** Le fait ci-dessous, repris de l'audit et de P3, est **inexact** :
> `bathrooms = 80` est bien **signalé** (`outlier_flags = bathrooms_outlier`, 3 observations),
> depuis la Phase 2 (`pipelines/silver.py::_outlier_flags`). Ce qui manquait réellement était le
> test du signalement — ajouté par le lot B (`assert_implausible_rooms_are_signalled`).
> Le constat d'audit est conservé tel quel ci-dessous, comme photographie datée.

| Fait                                                                                                                           | Preuve                                                       |
| ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| 154 tests réussis, 1 ignoré (`pyarrow` absent du venv local)                                                                   | `pytest tests -q`, `pytest -q -rs`                           |
| Lint sans erreur                                                                                                               | `ruff check .`                                               |
| 12 modèles dbt, 83 tests, 2 tests singuliers                                                                                   | `dbt ls`                                                     |
| 2 992 lignes de `landing.silver_listings` jusqu'à `analytics_marts.mart_ml_dataset`                                            | requêtes `psql`                                              |
| `mart_city_prices` : Douala N=2 811 (89 % bornés), Yaoundé N=181 (31 %)                                                        | requête `psql`                                               |
| 234 médianes NULL sur 253, plus petit N publié = 31                                                                            | requête `psql`                                               |
| Registre : `rent-model` v1 (`c04e80d7`) et v2 (`ab97ec18`), alias `champion` → v2, 72 runs, `debug_exp`/`debug_spy` supprimées | requêtes `psql` sur `mlflow`                                 |
| `mlruns/` = 41 Mo non suivis ; `MLFLOW_ARTIFACT_LOCATION` absent de `.env.example`                                             | `du -sh mlruns`, `.env.example`                              |
| `dataset_version` ne hashe que `listing_key` + cible                                                                           | `ml/src/tracking.py`                                         |
| `MODEL_ARTIFACT_NAME` figé sur `rent_model_v1`                                                                                 | `ml/src/config.py`                                           |
| Alias déplacé sans approbation                                                                                                 | `ml/src/registry.py`                                         |
| Features exigées par la spec 06 toutes exclues                                                                                 | `ml/src/features.py::EXCLUDED_FEATURES`                      |
| Payload de la spec 08 contenant des champs vides dans les données                                                              | `context/feature-specs/08-api.md` §2, `mart_ml_dataset.sql`  |
| Quarantaine et métadonnées absentes de la base                                                                                 | `pipelines/db.py`, `ingestion/storage.py`                    |
| `backend/`, `frontend/`, `infrastructure/`, `tests/integration/` = `.gitkeep`                                                  | `git ls-files`                                               |
| CI = lint + tests unitaires ; `cd.yml` = placeholder                                                                           | `.github/workflows/{ci,cd}.yml`                              |
| `dev` et `prod` dbt identiques ; `.env.example` annonce 5432, conteneur sur 5433                                               | `dbt/profiles.yml`, `.env.example`, `docker ps`              |
| Absence de `docs/phase-3/` ; compteurs 18/19 tests et chiffres d'avant #20                                                     | `ls docs`, `pytest --collect-only`, `docs/phase-2/README.md` |

### 11.2 Hypothèses (à confirmer, non affirmées comme vraies)

1. La divergence v1/v2 du registre provient d'une exécution locale de `python -m ml.src registry`
   après la fusion de la Phase 7 (le rapport versionné correspond à la v1 constatée en base).
2. Les expériences `debug_exp` / `debug_spy` (supprimées) résultent de tests ou de manipulations
   antérieures utilisant la base de développement plutôt qu'un backend SQLite.
3. Les 101 quartiers non reconnus et le déséquilibre Douala/Yaoundé pèsent directement sur l'erreur
   du modèle pour Yaoundé, sans que cela ait été mesuré par ville dans cette session.
4. Le port 5433 est le bon port local (5432 étant occupé par un PostgreSQL système) ; `.env.example`
   n'a pas été mis à jour après ce changement.
5. L'échantillon local `data/samples/` (non versionné) est bien celui décrit dans
   `data/samples/README.md` (dépôt tiers sans licence).

### 11.3 Recommandations (à décider, non exécutées)

1. Traiter **P2 et P5 en premier** (lot 1) : sans registre épinglé et sans approbation tracée, la
   Phase 8 ne peut pas être développée sur une base vérifiable.
2. Traiter **P4 (lot 2)** avant toute promesse de back-office « Qualité » : les données existent mais
   ne sont pas interrogeables.
3. Réviser **06 et 08 avant toute implémentation** : sinon l'API exposerait des champs que le modèle
   ignore.
4. Trancher la **stratégie prix censurés** (décision 4) : elle conditionne le libellé du produit et
   la valeur de la fourchette.
5. Introduire les **tests de données en CI** (lot 3) : c'est la barrière la moins coûteuse contre les
   régressions d'invariants.
6. Ne **pas** démarrer la marketplace ni Conakry dans ce cycle ; les traiter comme des décisions
   séparées (spec 15 en phase de décision le cas échéant).
7. Conserver les décisions techniques déjà prises (PostgreSQL unique, dbt, MLflow, pas d'Airflow,
   pas de MongoDB) tant qu'aucun besoin mesuré ne les remet en cause.

---

## 12. Limites de cet audit

- Audit **en lecture seule** : `dbt build` et les CLI de pipeline/ML n'ont pas été relancés ; les
  chiffres ML (MAE, couverture, 95/95) proviennent des rapports versionnés et du tracker.
- **Aucun accès réseau** : CGU, `robots.txt`, issues GitHub et services externes non vérifiés.
- Les bases `camrent` et `mlflow` locales contiennent un état **antérieur à cette mission** (version
  2, alias déplacé, 72 runs) ; il est rapporté comme constaté, sans l'attribuer au code de `develop`.
- Aucune mesure de la représentativité réelle du marché : les constats P3 reposent sur le Silver et
  les marts actuels (2 992 lignes, une seule journée de collecte).
- Le présent document est une **proposition** : il ne remplace aucune décision existante et attend
  validation avant toute modification du dépôt.

---

## 13. Annexes

### 13.1 Commandes exécutées dans le cadre de l'audit

```bash
# Git
git log --oneline -n 15
git branch -avv
git status --short
git stash push -m "audit: artefacts de rapports ML régénérés localement (phases 6-7)" \
  -- docs/phase-6/model-report.md docs/phase-7/registry-report.md
git checkout develop && git merge --ff-only origin/develop
git checkout -b chore/audit-realignement

# Vérifications de code
.venv/bin/python -m pytest tests -q
.venv/bin/python -m pytest tests -q -rs
.venv/bin/ruff check .

# dbt (analyse seule, aucune matérialisation)
cd dbt && ../.venv/bin/dbt parse --no-version-check
cd dbt && ../.venv/bin/dbt ls --resource-type model --output name --no-version-check

# Base applicative (lecture seule)
docker exec camrent-postgres psql -U camrent -d camrent -tAc "select count(*) from landing.silver_listings"
docker exec camrent-postgres psql -U camrent -d camrent -tAc "select count(*) from analytics_marts.mart_ml_dataset"
docker exec camrent-postgres psql -U camrent -d camrent -tAc \
  "select city, n_observations, median_rent_price, pct_price_bound from analytics_marts.mart_city_prices order by n_observations desc"
docker exec camrent-postgres psql -U camrent -d camrent -tAc \
  "select count(*) filter (where median_rent_price is null), count(*), min(n_observations) filter (where median_rent_price is not null) from analytics_marts.mart_neighborhood_prices"

# Base du registre (lecture seule)
docker exec camrent-postgres psql -U camrent -d mlflow -tAc "select name, version, current_stage, status from model_versions order by version"
docker exec camrent-postgres psql -U camrent -d mlflow -tAc "select * from registered_model_aliases"
docker exec camrent-postgres psql -U camrent -d mlflow -tAc "select count(*) from runs"
docker exec camrent-postgres psql -U camrent -d mlflow -tAc "select name, lifecycle_stage from experiments"
```

### 13.2 Documents de référence lus

`AGENTS.md` · `context/ai-workflow-rules.md` · `context/project-overview.md` ·
`context/architecture-context.md` · `context/code-standards.md` · `context/ui-context.md` ·
`context/progress-tracker.md` · `context/product/camrent-product-realignment.md` ·
`context/feature-specs/00` à `12` · `assets/*` · `docs/phase-0` à `docs/phase-7` ·
`dbt/README.md`, `dbt/dbt_project.yml`, `dbt/profiles.yml` · `ml/README.md` ·
`ingestion/README.md`, `pipelines/README.md` · `.github/workflows/ci.yml`, `cd.yml` ·
`pyproject.toml`, `.env.example`, `.gitignore`, `docker-compose.yml`.

### 13.3 Prochaine action attendue

**État (2026-10-16) :** le plan a été examiné et **validé** (10 décisions, §9) ; les lots A1, A2 et
**B** sont exécutés et vérifiés (§14). La suite attendue :

1. exécution du **lot C** (CI de données), puis des lots D, E selon l'ordre du §10 et leurs
   conditions d'entrée ;
2. mise à jour de `context/progress-tracker.md` après chaque lot vérifié.

---

## 14. Suivi d'exécution (mis à jour le 2026-10-15)

Section ajoutée après validation des décisions du §9 ; les §§1-13 restent la photographie de
l'audit. Détail des changements et vérifications dans `context/progress-tracker.md`.

| Lot (§10) | État | Contenu |
| --- | --- | --- |
| **Lot 0 → A1** | **Terminé et vérifié (2026-10-15)** | Documentation seule : décisions actées dans `context/progress-tracker.md` (section « Recadrage produit — décisions validées »), `context/project-overview.md` (extensions retenues, décisions de périmètre), `context/architecture-context.md` (sous-systèmes A-E, gouvernance du registre), `context/feature-specs/07-model-registry.md` (promotion nominative, épinglage, hash complet). Reste du lot 0 : `docs/phase-3/README.md` et les specs de cadrage **13/14/15**, tous créés le 2026-10-15 (l'implémentation des specs 13/14 reste conditionnée à 08 et 09 — décision 7). |
| **Lot 1 → A2** | **Terminé et vérifié (2026-10-15)** | Registre gouverné : promotion refusée sans approbation **avant toute écriture** (§7.2), version servie épinglée dans `ml/models/champion.json` versionné (§7.3), hash de dataset couvrant tout le mart (§7.1), emplacement d'artefacts épinglé `ml/artifacts/mlflow` (§7.4), tags `approuve_par`/`approuve_le`. **Ouvert (§7.5)** : hygiène/rétention des runs (84 runs dans `rent_prediction`). Vérifications : `ruff` 0 erreur ; `pytest` **161 réussis, 1 ignoré** ; refus CLI exit 1 avec registre inchangé ; promotion `rent-model-v3` avec approbation ; pin non ignoré par git. |
| **Lot 2 → B** | **Terminé et vérifié (2026-10-16)** | Qualité et contrat de données (§7.6, §7.7, §7.8, §7.9), exécuté en quatre incréments vérifiés : **B1** provenance d'ingestion (`connector_version`, `content_sha256`, `lot_validation_status` par lot, validation d'un lot avant écriture des métadonnées) ; **B2** quarantaine et métadonnées de lot chargées dans `landing`, marts `mart_data_quality` (motifs agrégés + total par source) et `mart_ingestion_lots` ; **B3** `rent_semantics` (`asking_rent` / `unknown`) dans `mart_ml_dataset` ; **B4** contrôle des bornes de pièces par un test dbt qui **vérifie le signalement** (le signalement existait déjà en Phase 2 — l'affirmation inverse du §1.2/§4 P3 est corrigée). **Vérifications** : `ruff` 0 erreur ; `pytest` **175 réussis / 1 ignoré** ; `dbt build` **137/137** (16 modèles, 121 tests dont 6 singuliers) ; en base : 78 rejets réconciliés par motif, 3 lots, `rent_semantics` sans valeur nulle, volumes et invariant N ≥ 30 inchangés. **Fusionné via la PR #35** (squash `627784e`, 2026-10-16) — pipeline CI vertes avant et après le merge (176 tests réussis, 0 ignoré en CI). |
| **Lot 3 → C** | **Prochain lot** | CI de données (§7.10, §7.11) : PostgreSQL + `dbt build` en CI, backend de build figé, `.env.example` (5433), schémas `dev`/`prod`. Condition d'entrée : satisfaite (décision 8). Inclut le critère §8.1 « 0 test ignoré » (installer `pyarrow`). |
| **Lot 4 → D** | À faire | Phase 8 en deux temps : **08a** API publique (prédiction, marché, comparaison — modèle épinglé, §7.12) puis **08b** API interne (permissions, jobs). Conditions d'entrée : décisions 3, 4, 5 (prises) + lots B et C livrés. |
| **Lot 5** | À faire | Phase 9 : 09a estimation publique, 09b administration, `ui-context.md` figé avant code. Condition d'entrée : lot 4. |
| **Lot E** | À faire | Prix censurés : adapter la cible et l'intervalle par une expérience **mesurée** (décision 4). |
| **Lots suivants** | À planifier | Implémentation des specs 13/14 (back-office, décision 7 : après 08 et 09 — specs de cadrage créées le 2026-10-15), cadrage puis décision sur la 15 (marketplace), Phases 10/11/12 selon besoin mesuré, Conakry (décision 10 : séparé). |

Les lots A1, A2 et le reste du lot 0 ont été fusionnés via la PR #33 (squash `a168bef`,
2026-10-15). Le même jour, une **passe d'harmonisation documentaire** (validée par le porteur du
projet) a aligné les specs 00-12, `project-overview.md`, `ui-context.md`, `code-standards.md` et
les rapports de phases sur les décisions du §9 — payload API et formulaire sur les champs
réellement disponibles, découpages 08a/08b et 09a/09b, compléments demandés par le §5 (specs 00,
01, 02, 04, 11, 12), notes de la décision 4 dans les suites ouvertes des phases 2, 5 et 6 ; détail
dans `context/progress-tracker.md`.
