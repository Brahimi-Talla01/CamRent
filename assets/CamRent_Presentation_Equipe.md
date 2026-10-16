# CamRent — Présentation du projet à l'équipe

**Support de présentation destiné aux nouveaux membres**

| | |
|---|---|
| **Version** | 1.0 |
| **Date** | 16 octobre 2026 |
| **Statut du dépôt au moment de la rédaction** | branche `develop`, dernier commit `2bcf81a` |
| **Sources** | `context/` (règles, vue produit, architecture, specs 00→15, plan de réalignement), `docs/phase-0` → `docs/phase-7`, `AGENTS.md` |
| **Nature** | document de présentation : **il ne fait pas référence normative** — le dépôt fait foi |

> **Règle de lecture appliquée tout au long du document**
> Chaque affirmation est rattachée à l'un de ces trois statuts :
> **[IMPLÉMENTÉ]** = le code existe, tourne et est testé ·
> **[EN COURS]** = en cours de refactorisation ou de réalisation, livré partiellement ·
> **[PRÉVU]** = prévu, spécifié, **non construit**.
> Toute information absente des sources est signalée comme **[À CONFIRMER]** plutôt que supposée.

---

## Sommaire

1. Vision et produit
2. Décisions de recadrage du 15 octobre 2026
3. Architecture fonctionnelle — cinq sous-systèmes
4. Architecture technique et choix technologiques
5. Le flux de données (RAW → CLEAN → TRANSFORMED → ANALYTICAL)
6. Le fonctionnement des phases 00 → 15
7. Ce qui a réellement été implémenté (phases 0 à 7)
8. Le pipeline ML en détail
9. Statuts : existant / en cours de refactorisation / prévu
   - 9.1 Existant · 9.2 En cours de refactorisation · 9.3 Prévu · 9.4 Ce qui n'existe pas du tout
10. La refactorisation en cours : le plan de réalignement par lots
11. Qualité, tests et intégration continue
12. Limites connues, points ouverts et informations incertaines
13. Glossaire
14. Sources de vérité et entretien du document
15. Annexes : commandes et arborescence

---

## 1. Vision et produit

### 1.1 Ce qu'est CamRent

CamRent est une **plateforme Data / ML d'analyse et d'estimation du marché locatif**
à Yaoundé et Douala. Ce n'est **pas** un formulaire branché sur un modèle : le modèle
ML est un composant central d'une plateforme d'analyse du marché.

**Proposition de valeur** (recadrage produit, §2.2) :

> Aider les utilisateurs à mieux comprendre les loyers demandés sur le marché
> immobilier, grâce à des données contrôlées, des estimations documentées et,
> si cette extension est validée, des annonces permettant de rechercher un
> logement et d'entrer en contact avec son annonceur.

### 1.2 Périmètre

| Élément | Décision |
|---|---|
| Villes | **Yaoundé et Douala** (périmètre MVP) |
| Devise | XAF (FCFA) |
| Cible du modèle | `rent_price` = **loyer demandé dans l'annonce**, pas le prix payé |
| Hors périmètre MVP | vente immobilière, locations journalières, bureaux/commerces, application mobile native, deep learning, chatbot, géolocalisation très fine |
| **Conakry** | **chantier séparé** (décision 10) : devise, référentiel géographique, sources et vérification légale locale à instruire — **aucune donnée ni modèle aujourd'hui** |
| **Marketplace** | conservée dans le périmètre mais **conditionnée** (décision 1) : cadrage d'abord (spec 15), **aucun code engagé** |
| **Nouvelle collecte** | **reportée** (décision 6) : on finalise le MVP d'abord |

### 1.3 Utilisateurs

- **Locataires** — savoir si un loyer est raisonnable, comparer, connaître les prix d'un quartier, trouver un quartier pour un budget.
- **Propriétaires / bailleurs** — estimer un loyer cohérent, se positionner par rapport au marché.
- **Analystes** — étudiants, chercheurs, journalistes, professionnels de l'immobilier, investisseurs.

### 1.4 Parcours utilisateur visé (MVP)

```
Accueil
   ↓
Estimer mon loyer      (ville, quartier, type, chambres, salles de bain)
   ↓
Résultat               loyer estimé + fourchette + statistiques de zone
                        + nombre d'observations + limites de la donnée
   ↓
Explorer le marché     prix par quartier / par type (toujours avec N)
   ↓
Comparer               2+ logements : écarts et explications
```

Ce parcours est **[PRÉVU]** : `frontend/` ne contient qu'un `.gitkeep`.

### 1.5 Limites de communication (obligations produit)

Ces règles ne sont pas des suggestions, ce sont des invariants du projet :

- **Jamais** de statistique de marché sans son **nombre d'observations**.
- **Jamais** de niveau de confiance non justifié statistiquement.
- **Jamais** présentée une estimation comme la valeur officielle du bien.
- Toujours rappeler que l'estimation repose sur **les prix observés dans les annonces**.

---

## 2. Décisions de recadrage du 15 octobre 2026

Un audit en lecture seule (octobre 2026) a produit un plan validé par le porteur du
projet. Ces 10 décisions **priment sur toute supposition** (détail :
`context/plans/camrent-audit-and-realignment-plan.md` §9).

| # | Décision | Conséquence concrète |
|---|---|---|
| 1 | Marketplace **conservée mais structurée** | spec 15 = phase de **décision**, aucun code |
| 2 | Priorité : **fondations du back-office d'abord** | l'interface (13/14) vient **après** 08 et 09 |
| 3 | **MLflow conservé**, promotion **approuvée par un administrateur** | alias `champion` déplacé uniquement avec approbation nominative |
| 4 | Prix censurés : **adapter la cible et l'intervalle** par une expérience mesurée | lot E, plutôt qu'exclure ou pondérer à l'aveugle |
| 5 | Périmètre : **Yaoundé et Douala**, Conakry séparée | pas de données Conakry |
| 6 | **Finaliser le MVP avant toute nouvelle collecte** | surface, dates, nouvelles sources : hors périmètre pour l'instant |
| 7 | Specs 13/14 du back-office **après 08 et 09** | rôle `admin` d'abord |
| 8 | CI renforcée : **oui** — `dbt build` sur PostgreSQL en CI | fait (lot C, 2026-10-16) |
| 9 | Ajouter **`rent_semantics`** (`asking_rent` / `unknown`), ne **pas** renommer la cible | fait (lot B) |
| 10 | Conakry : décision à instruire **séparément** | rien d'engagé |

**Matérialisation du registre** : artefacts de modèles stockés localement, non versionnés,
dans un chemin **épinglé** (`ml/artifacts/mlflow`) ; la version servie est épinglée dans le
fichier **versionné** `ml/models/champion.json`.

---

## 3. Architecture fonctionnelle — cinq sous-systèmes

Séparation **fonctionnelle** des responsabilités. Elle **n'impose pas des microservices** :
au MVP, une application modulaire avec des workers pour les tâches longues suffit.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       CamRent — écosystème modulaire                     │
├──────────────────────┬───────────────────────────────────────────────────┤
│ A — Data Platform    │ collecte, conservation, qualité, transformations, │
│                      │ datasets                                         │
│                      │ → ne publie pas d'estimation, pas d'interface     │
│                      │   publique                                       │
├──────────────────────┼───────────────────────────────────────────────────┤
│ B — Back-office      │ supervision interne : sources, datasets, qualité, │
│                      │ jobs ML, registre, audit                         │
│                      │ → accès réservé (`admin`) ; ne simule JAMAIS une  │
│                      │   capacité absente du backend                    │
├──────────────────────┼───────────────────────────────────────────────────┤
│ C — Estimation       │ estimation indicative du loyer mensuel demandé    │
│                      │ + données de marché                              │
│                      │ → ne s'entraîne pas en ligne ; sert uniquement    │
│                      │   une version enregistrée et approuvée           │
├──────────────────────┼───────────────────────────────────────────────────┤
│ D — Marketplace      │ mise en relation locataire / annonceur            │
│ (conditionnée)       │ → annonce publiée ≠ observation importée         │
├──────────────────────┼───────────────────────────────────────────────────┤
│ E — Services communs │ auth, rôles, audit, jobs asynchrones,             │
│                      │ observabilité, secrets                           │
│                      │ → API interne et API publique, autorisations      │
│                      │   distinctes                                     │
└──────────────────────┴───────────────────────────────────────────────────┘
```

**Règle d'ordonnancement** : les fondations du back-office (B) se construisent **avec les
fonctions qu'elles pilotent** ; son interface vient après les phases 08 et 09.

**Statut** : la frontière est documentée **[IMPLÉMENTÉ comme décision]** dans
`context/architecture-context.md` ; les sous-systèmes **B, C, D et E ne sont pas encore
construits** **[PRÉVU]**. Seule l'A — Data Platform existe en code.

---

## 4. Architecture technique et choix technologiques

### 4.1 Stack

| Couche | Technologie | Rôle |
|---|---|---|
| Ingestion | Python (`requests`, `urllib.robotparser`) | collecte contrôlée (robots.txt, débit, UA transparent) |
| Stockage brut | JSONL daté + Parquet (`data/raw/`, `data/processed/`) | données immuables, rejouables |
| Base relationnelle | **PostgreSQL 16** (docker-compose, port **5433**) | base opérationnelle **et** analytique du MVP |
| Transformation | **dbt** (staging → intermediate → marts) + Python | SQL versionné, testé, documenté |
| ML | **scikit-learn** (+ lightgbm comparé) | régression supervisée de `rent_price` |
| Suivi d'expériences | **MLflow** (`mlflow-skinny`, base dédiée `mlflow`) | runs, versions, registre |
| API | **FastAPI** — *prévu* | serving des prédictions et du marché |
| Frontend | **Next.js + TypeScript** — *prévu* | application utilisateur |
| CI/CD | **GitHub Actions** | lint + tests unitaires aujourd'hui (voir §11) |
| Orchestration | Python/cron d'abord, Airflow **seulement si besoin mesuré** | phase 10 |

### 4.2 Choix assumés (et refus assumés)

Le projet suit un principe de **pas de sur-engineering** : une technologie n'est introduite
que si un besoin réel est démontré.

**Choix retenus** — PostgreSQL unique au MVP (pas de Data Warehouse) · dbt pour les
transformations SQL · ELT (et ETL ciblé uniquement dans l'ingestion) · MLflow plutôt qu'un
registre maison · pas de DVC/lakeFS (volumes non justifiés) · `cloudpickle` pour le modèle
retenu (`TransformedTargetRegressor` porte des ufuncs numpy que `skops` refuse).

**Technologies explicitement non introduites** — Airflow, MongoDB, Redis, Kafka/streaming,
Kubernetes, Spark, Data Warehouse, microservices. Elles restent des *évolutions possibles*
documentées, **pas** des choix actuels.

**Architecture des données** : `Bronze` (brut collecté) → `Silver` (nettoyé, standardisé,
dédupliqué, signalé) → `Gold` (marts, dataset ML).

---

## 5. Le flux de données

```
  SOURCES                     DATA PLATFORM (sous-système A)              CONSOMMATEURS
 ┌────────────┐
 │ Koutchoumi │──┐
 │ (annonces) │  │      ┌───────────────────────────────────┐
 ├────────────┤  │      │ 1. INGESTION  (ingestion/)        │
 │ Jeux locaux│──┼─────▶│    collecte contrôlée (robots,     │
 │ jumia.csv  │  │      │    débit, porte légale)           │
 │ koutchoumi1│  │      └───────────────┬───────────────────┘
 ├────────────┤  │                      ▼
 │ Geloka     │──┘   ┌──────────────────────────────────────┐
 │ (agrégats, │      │ data/raw/<catégorie>/<date>/*.jsonl  │  ★ IMMUABLE
 │ hors ML)   │      │ data/raw/metadata/<date>/*.json      │  provenance :
 └────────────┘      │   connector_version · content_sha256 │  version, empreinte,
                     │   lot_validation_status              │  statut de validation
                     └───────────────┬──────────────────────┘   [lot B]
                                     ▼
                     ┌──────────────────────────────────────┐
                     │ 2. CLEANING  (pipelines/)            │
                     │    types · villes/quartiers · types   │
                     │    de logement · dédup · bornes       │
                     └──────┬──────────────────────┬────────┘
                            ▼                      ▼
             ┌──────────────────────────┐  ┌──────────────────────────┐
             │ data/processed/          │  │ data/processed/          │
             │ silver_listings.parquet  │  │ quarantine_listings      │
             │  2 992 observations      │  │   78 rejets + MOTIF      │
             └────────────┬─────────────┘  │ (jamais supprimés)       │
                          │                └────────────┬─────────────┘
                          ▼                             ▼
   ┌───────────────────────────────────────────────────────────────────┐
   │ 3. CHARGEMENT (pipelines/db.py → schéma landing)                  │
   │    silver_listings (2 992) · quarantine_listings (78)             │
   │    ingestion_runs (3 lots)          [TRUNCATE + insert, no DROP]  │
   └──────────────────────────┬────────────────────────────────────────┘
                              ▼
   ┌───────────────────────────────────────────────────────────────────┐
   │ 4. TRANSFORMATION dbt (dbt/models/)                               │
   │    staging: stg_listings · stg_quarantine · stg_ingestion_runs    │
   │    intermediate: int_clean_listings                               │
   │    dims : dim_city · dim_neighborhood ·                          │
   │           dim_property_type · dim_date                            │
   │    faits: fct_rent_observations · fct_listings                    │
   │    marts: mart_neighborhood_prices · mart_city_prices ·          │
   │           mart_property_prices · mart_ml_dataset ·                │
   │           mart_data_quality · mart_ingestion_lots                 │
   └──────────────────────────┬────────────────────────────────────────┘
                              ▼
       ┌──────────────────────┼──────────────────────┐
       ▼                      ▼                      ▼
  Analyse (EDA)         ML (Phases 5-7)         API / Front     [PRÉVU]
  eda/ → rapports       ml/src → modèle         backend/ vide
                        enregistré              frontend/ vide
```

### Invariants de données (à ne jamais enfreindre)

1. Les données **brutes ne sont jamais modifiées** après collecte.
2. Tout est **reproductible** : même code + même brut → même résultat.
3. Chaque étape critique a des **contrôles qualité**.
4. Un échec ne remplace **jamais** un dataset valide par un dataset vide.
5. Les données invalides vont en **quarantine**, jamais supprimées silencieusement.
6. **Zéro data leakage** : aucune feature dépendante de la cible (`rent_per_m2` est interdit).
7. Aucune collecte sans vérification **CGU / robots.txt / droits**.
8. Aucune statistique de marché **sans son nombre d'observations**.
9. Une estimation n'est **jamais** présentée comme la valeur officielle du bien.

---

## 6. Le fonctionnement des phases 00 → 15

### 6.1 Ordre des phases

```
00 Validation du problème      08 API (→ 08a publique, puis 08b interne)
01 Data ingestion              09 Frontend (→ 09a public, puis 09b administration)
02 Data cleaning               10 Orchestration   [condition d'entrée non atteinte]
03 EDA                         11 Observabilité
04 Data warehouse / marts      12 Production
05 Baseline ML                 13 Back-office : fondations   [après 08 et 09]
06 Modèles ML                  14 Back-office : rapports     [après 08 et 09]
07 Model registry              15 Marketplace : découverte   [phase de DÉCISION]
```

Une seule phase à la fois, petits incréments vérifiables, jamais deux responsabilités
mêlées dans une même étape (ni UI + pipeline, ni data + API).

### 6.2 Deux régimes de travail coexistent

**Pour les phases 00→07** : travail par **PR fusionnée**, le suivi étant tenu dans
`context/progress-tracker.md`.

**Pour le nouveau plan** : chaîne stricte

```
audit (lecture seule)  →  plan validé  →  un lot = un changement cohérent,
                                          vérifiable et réversible  →  vérification
                                          →  mise à jour du suivi
```

**Un lot n'est terminé que si** : ses critères d'acceptation sont satisfaits, les tests
passent (ou les échecs sont expliqués), les specs reflètent le comportement réel, le suivi
est à jour, les risques restants sont documentés, et l'utilisateur peut examiner les
changements.

### 6.3 Ordonnancement actuel des lots

| Lot | Contenu | État |
|---|---|---|
| **A1** | documentation : décisions actées, specs 13/14/15, `docs/phase-3/` | **[IMPLÉMENTÉ]** PR #33 |
| **A2** | registre gouverné : promotion approuvée, épinglage, hash complet | **[IMPLÉMENTÉ]** PR #33 |
| — | harmonisation documentaire des specs 00-12 | **[IMPLÉMENTÉ]** PR #34 |
| **B** | qualité et contrat de données | **[IMPLÉMENTÉ]** PR #35 |
| **C** | CI de données : PostgreSQL + `dbt build` en CI | **[TERMINÉ]** (2026-10-16) |
| **D** | Phase 8 en deux temps (08a, puis 08b) | **[PRÉVU]** — conditions : lots B **et** C livrés |
| **E** | prix censurés : adapter cible et intervalle, mesurée | **[PRÉVU]** |
| suivants | Phase 9 (09a/09b), specs 13/14, Phases 10/11/12, Conakry | **[PRÉVU]** |

---

## 7. Ce qui a réellement été implémenté (phases 0 à 7)

> Chiffres **datés** : ils viennent des rejeux locaux et des rapports versionnés
> (2026-10-09 → 2026-10-16). Un rejeu est nécessaire avant toute reprise de chiffres.

### 7.1 Vue d'ensemble

Détail des tests unitaires par domaine (collecte du 16/10/2026) : `ingestion` **24** ·
`pipelines` **34** · `ml` **117** · smoke **1** = **176 tests** — soit, en local,
**175 réussis / 1 ignoré** (`pyarrow` absent du venv local) et **176 / 0 en CI**.

| Phase | Statut | Preuves principales | Tests |
|---|---|---|---|
| **00 Validation du problème** | **[IMPLÉMENTÉ]** | `docs/phase-0/` : discovery, évaluation légale, faisabilité, profiling, score qualité, EDA | script `profile_sample.py` |
| **01 Data ingestion** | **[IMPLÉMENTÉ]** (+ provenance **[IMPLÉMENTÉ]**, lot B) | `ingestion/` : registre des sources, porte légale, raw daté, métadonnées, validations Bronze | **24 tests** d'ingestion |
| **02 Data cleaning** | **[IMPLÉMENTÉ]** (+ rejets en base **[IMPLÉMENTÉ]**, lot B) | `pipelines/` : 2 992 Silver / 78 quarantaine, drapeaux, référentiel geo | **34 tests** (`test_pipelines_*`) |
| **03 EDA** | **[IMPLÉMENTÉ]** | `eda/` : rapports **entièrement dérivés** de `statistics.json` | rendu sans valeur en dur |
| **04 Marts / dbt** | **[IMPLÉMENTÉ]** (+ qualité en base **[IMPLÉMENTÉ]**, lot B) | `dbt/` : 16 modèles, 121 tests, 6 tests singuliers | `dbt build` **137/137** |
| **05 Baseline ML** | **[IMPLÉMENTÉ]** | `ml/src/` : 3 baselines, seuil de référence 79 773 FCFA, IC bootstrap | 37 tests |
| **06 Modèles ML** | **[IMPLÉMENTÉ]** | modèle retenu `random_forest_log1p`, fourchette calibrée, explicabilité | 59 tests |
| **07 Model registry** | **[IMPLÉMENTÉ]** (+ gouvernance **[IMPLÉMENTÉ]**, lot A2) ; **rétention des runs [PRÉVU]** | MLflow, règle de promotion, approbation nominative, `champion.json` | **21 tests** (14 initiaux + 7 de gouvernance) |

### 7.2 Phase 0 — Validation du problème

- Rapports : sources, volumes, variables, contraintes, faisabilité (10 points du Plan Technique §76).
- **Évaluation légale par source** : Koutchoumi (aucune CGU publiée), Geloka (CGU restrictives,
  usage agrégé avec citation), jeu local `deegeorgie` (**aucune licence** → usage local, non
  redistribué).
- Échantillon : 3 065 lignes brutes → ≈ 1 226 uniques (71,7 % de doublons Koutchoumi).
- **Limite [À CONFIRMER]** : l'échantillon de Phase 0 n'est **pas versionné** (licence tierce) :
  la reproduction hors dépôt est **partielle** (point ouvert P1 du plan).

### 7.3 Phase 1 — Data ingestion

- Registre des sources (`ingestion/config.py`) : catégorie, droits (`verified` / `uncertain` /
  `local` / `restricted`), notice, URLs.
- **Porte légale** : une source non `verified`/`local` **refuse de tourner** sans
  `--confirm-legal` ; `robots.txt` vérifié, débit limité (2 s), User-Agent transparent,
  **aucune donnée personnelle** conservée.
- Raw daté et immuable : `data/raw/<catégorie>/<YYYY-MM-DD>/<source>_<HHMMSS>.jsonl`.
- Validations Bronze **16/16** : existence, format JSON, volume, clés requises,
  concordance métadonnées, fraîcheur.
- **Lot B** : chaque lot consigne `connector_version`, `content_sha256` (empreinte de contenu)
  et `lot_validation_status`, calculés **avant** l'écriture des métadonnées — qui ne sont
  jamais réécrites.

### 7.4 Phase 2 — Data cleaning (Silver)

- Construction réelle : **3 078 bruts → 2 992 lignes Silver** et **78 en quarantaine**.
- Quarantaine par motif (réel) : `prix_manquant` 52, `type_inconnu` 18, `city_inconnue` 7,
  `prix_invalide` 1.
- Drapeaux de qualité conservés : `price_is_bound` **2 564** (85,7 %), `is_republication`
  **2 001**, aberrations **17**, quartiers non reconnus **101** (après enrichissement du
  référentiel, issue #20 : 582 → 101).
- Bornes de pièces : `bathrooms = 80` (3 observations) est **conservé et signalé**
  (`bathrooms_outlier`). *À noter : l'audit initial a écrit « sans être signalé », affirmation
  corrigée le 16 octobre 2026 — le signalement existait, le test de ce signalement n'existait
  pas (ajouté par le lot B).*
- **Lot B** : quarantaine et métadonnées de lot sont désormais **interrogeables en base**.

### 7.5 Phase 3 — Analyse exploratoire

- Rapports `eda/univariate_analysis.md`, `bivariate_analysis.md`, `insights.md` —
  **purement dérivés** de `statistics.json` (aucune valeur en dur).
- Constats structurants : distribution **très asymétrique** (skewness ≈ 35, kurtosis ≈ 1 412)
  → transformation `log1p` recommandée (mesurée ensuite en Phase 6) ; couverture concentrée
  (Douala 2 811 / Yaoundé 181) ; features absentes du MVP (**surface, date de publication,
  meublé, parking, barrière**) ; **103 quartiers avec une seule observation** → décision de ne
  pas publier de médiane sous 30 observations.

### 7.6 Phase 4 — Data warehouse / marts

- `pipelines/db.py` charge le Silver dans `landing.silver_listings` — **vidage `TRUNCATE` puis
  insertion, jamais de `DROP`** (les vues dbt survivent au rejeu).
- Chaîne dbt : `stg_listings` → `int_clean_listings` → 4 dimensions, 2 faits, 6 marts.
- Invariants embarqués dans les modèles : `n_observations` partout ; médiane de quartier
  **null sous N < 30** ; drapeaux conservés et quantifiés ; **pas** de `rent_per_m2`.
- Data Catalog : `docs/phase-4/data-catalog.md` (grain, source, fréquence, propriétaire,
  sensibilité, qualité, lineage).
- **Lot B** : ajout de `stg_quarantine`, `stg_ingestion_runs`, `mart_data_quality` et
  `mart_ingestion_lots` ; colonne `rent_semantics` dans `mart_ml_dataset`.
- Vérification du 16/10 : `dbt build` **137/137** ; volumes 2 992 lignes de la landing à
  `mart_ml_dataset` ; invariant de publication intact (234 médianes non publiées sur 253
  groupes, plus petit N publié = 31).

### 7.7 Phase 5 — Baselines ML

- Trois baselines mesurées : moyenne globale, médiane par ville, médiane par
  ville + quartier + type (avec chaîne de repli explicite : quartier+type → ville+type →
  ville → moyenne globale).
- **Seuil à battre : MAE de validation < 79 773 FCFA** (borne basse d'un intervalle de
  confiance bootstrap à 95 %, 2 000 tirages) = 17,83 % de mieux que la meilleure baseline.
- Séparation aléatoire **70 / 15 / 15**, graine fixe `20261009` — la séparation
  chronologique est **impossible** : `posted_at` vide, une seule journée de collecte.
- Méthodologique : la MAE est **instable** (97 079 en validation → 185 261 en test, +90,8 %)
  alors que la MedAE ne varie que de ~12 % → le gain ML devait être confirmé sur la MedAE et
  plusieurs graines.

### 7.8 Phase 6 — Modèles ML

- 12 candidats (6 familles × cible brute / `log1p`), hyperparamètres **fixés** : la phase
  compare des familles, elle n'optimise pas.
- **Modèle retenu : `random_forest_log1p`** — MAE validation **75 425 FCFA** contre
  **97 079** pour la meilleure baseline (**−22,31 %**, sous le seuil 79 773) ; MedAE
  **20 710** contre 40 000 (**−48 %**).
- Sélection en **deux temps** : présélection sur la graine de référence, puis choix du
  **gain médian** sur 3 graines (baseline battue sur **3/3**, gain médian 12,35 %).
- Fourchette : **régression quantile** retenue — couverture **90,7 %** en validation comme en
  test (visée 90 %), largeur médiane 135 995 FCFA en test.
- Explicabilité : le **quartier** porte l'essentiel du signal (+33 756 FCFA d'erreur médiane
  si permuté), devant chambres (+14 190) et salles de bain (+10 182).
- **Features utilisées** : `city`, `neighborhood`, `property_type`, `bedrooms`, `bathrooms`
  + 2 dérivées sans leakage (`total_pieces`, `logements_dans_quartier`, comptées sur
  l'entraînement uniquement).

### 7.9 Phase 7 — Model registry (MLflow)

- Chaque run consigne : dataset et son hash, features, hyperparamètres, métriques (dont
  **par segment**), SHA Git, date.
- Backend : base PostgreSQL **dédiée** `mlflow` (dérivée de `DATABASE_URL`) ; SQLite pour les
  tests. Pas de serveur ni d'UI (inutiles au MVP).
- **Règle de promotion** : `bat_la_baseline` **et** `seuil_phase_5` **et** `reproductible`.
- **Promotion explicite** (lot A2) : l'alias `champion` n'est attribué qu'avec approbation
  nominative d'un administrateur (`--confirm-promotion --approved-by`) — **sans approbation,
  arrêt avant toute écriture** (vérifié : exit 1, registre inchangé).
- **Version servie épinglée** dans `ml/models/champion.json` (seul artefact de modèle
  versionné, aucun secret dedans).
- État local constaté le 15/10 : **3 versions** (`rent-model-v1`, `v2`, `v3`), alias
  `champion` → **v3**, expérience `rent_prediction` avec **84 runs**.
- **Ouvert** : aucune politique de rétention des runs.

---

## 8. Le pipeline ML en détail

```
                 mart_ml_dataset (2 992 obs, 70/15/15, graine 20261009)
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        ▼                               ▼                               ▼
  PHASE 5 — BASELINES            PHASE 6 — MODÈLES                PHASE 7 — REGISTRE
  ───────────────────            ─────────────────                ─────────────────
  moyenne globale                12 candidats :                    chaque run → MLflow :
  médiane par ville              linear/ridge/lasso/              dataset hash + features
  médiane par quartier           RF/GBM/LightGBM                  + hyperparams + métriques
  + type                         × (brute | log1p)                + par segment + SHA Git
        │                               │                                    │
        ▼                               ▼                                    ▼
  seuil à battre                modèle retenu                       règle de promotion
  MAE < 79 773 FCFA             random_forest_log1p                 bat_la_baseline
  (IC 95 % bootstrap)           MAE val 75 425 (−22,31 %)          ET seuil_phase_5
        │                       MedAE 20 710 (−48 %)               ET reproductible
        │                       battu sur 3/3 graines                       │
        │                               │                                    ▼
        └───────────────┬───────────────┘                     approbation ADMIN nominative
                        ▼                                     → alias `champion`
        ┌───────────────────────────────┐                      → épinglage `champion.json`
        │ FOURCHETTE (incertitude)      │                      → aucun déploiement auto
        │ régression quantile retenue   │
        │ couverture 90,7 % val ET test │                      SERVING (Phase 8a, prévue)
        │ (split-conformal en compar.)  │                      lit models:/rent-model@champion
        └───────────────────────────────┘                      + fourchette + N observations
                        │
                        ▼
        ┌───────────────────────────────┐
        │ EXPLICABILITÉ « pourquoi ? »  │
        │ importance par permutation    │
        │ dépendance partielle          │
        │ explication locale            │
        └───────────────────────────────┘
```

### Ce que dit le ML, et ce qu'il ne dit pas

- La prévision **typique** (MedAE) est deux fois juste qu'une médiane locale : c'est le chiffre
  le plus stable et le plus honnête à présenter.
- **53,9 %** des prévisions en test tombent à ±20 % du loyer observé.
- Le **R² de test global est 0,008** : la variance expliquée est quasi nulle mesurée en
  quadratique — **ne jamais communiquer ce chiffre seul**.
- Le modèle est en pratique **entraîné sur Douala** : Yaoundé n'a que 181 observations
  (25 en test, sous le seuil de 30, signalées `*`, jamais masquées).
- Le modèle est juste sur le marché courant, **imprécis sur le haut de gamme** (quartile Q4,
  Bonapriso).
- La cible est **approximative pour 2 564 observations sur 2 992** (prix bornés « à partir de »)
  : aucune méthode ne corrige cela. Décision 4 : **adapter la cible et l'intervalle** (lot E).

---

## 9. Statuts : existant / en cours de refactorisation / prévu

### 9.1 Existant — construit, testé, fusionné

| Élément | Emplacement | Preuve |
|---|---|---|
| Registre des sources + porte légale | `ingestion/` | 24 tests, Bronze 16/16 |
| Raw immuable daté + métadonnées + provenance | `data/raw/` (local), `ingestion/storage.py` | empreinte vérifiée par `sha256sum` |
| Silver + quarantaine motivée | `pipelines/` | 2 992 / 78 |
| Chargement en base (Silver, quarantaine, lots) | `pipelines/db.py` | 3 tables `landing`, idempotent |
| dbt : 16 modèles, 121 tests, 6 singuliers | `dbt/` | `dbt build` 137/137 |
| Marts de marché (N toujours exposé) | `analytics_marts` | invariant N ≥ 30 vérifié |
| Baselines, seuil bootstrap | `ml/src/baselines.py` | seuil 79 773 |
| Modèle retenu + fourchette + explicabilité | `ml/src/` | 75 425 MAE val |
| MLflow + promotion approuvée + épinglage | `ml/src/registry.py` | refus sans approbation vérifié |
| CI : lint + tests unitaires | `.github/workflows/ci.yml` | **176 tests, 0 ignoré** en CI |
| Documentation par phase | `docs/phase-0` → `phase-7` | rapports régénérables |
| Spécifications 00 → 15 | `context/feature-specs/` | 15 fichiers |

### 9.2 En cours de refactorisation — livré partiellement ou non commencé

| Sujet | Ce qui **change** | Statut détaillé |
|---|---|---|
| **Spécifications des phases 00-12** | corrigées après l'audit : payload API et formulaire réduits aux champs **réellement collectés** (06, 08, 09), découpages **08a/08b** et **09a/09b**, compléments apportés aux specs 00, 01, 02, 04, 11, 12 | **[IMPLÉMENTÉ]** PR #34 |
| **Phase 01 — provenance** | version de connecteur, empreinte de contenu, statut de validation par lot | **[IMPLÉMENTÉ]** lot B |
| **Phase 02 — rejets en base** | quarantaine et métadonnées interrogeables, `rent_semantics`, contrôle des bornes | **[IMPLÉMENTÉ]** lot B |
| **Phase 04 — qualité en base** | `mart_data_quality`, `mart_ingestion_lots`, `rent_semantics` dans le dataset ML | **[IMPLÉMENTÉ]** lot B |
| **Phase 07 — gouvernance** | promotion approuvée, épinglage, hash de dataset complet, emplacement d'artefacts épinglé | **[IMPLÉMENTÉ]** lot A2 |
| **Phase 07 — hygiène du registre** | politique de rétention des **84 runs** | **[PRÉVU]** — ouvert |
| **CI des données (affecte 04 et 12)** | `dbt build` + PostgreSQL en CI, backend de build figé, `.env.example` (5433), schémas `dev`/`prod` | **[TERMINÉ]** (2026-10-16) |
| **Cible censurée (affecte 02, 05, 06)** | adapter la cible et l'intervalle, par une expérience **mesurée** | **[PRÉVU]** — lot E |
| **Reproductibilité de bout en bout** | un clone ne rejoue pas `Raw → Silver → marts → modèle` (brut ignoré, échantillon non versionné, paquet non installable) | **[PRÉVU]** — point ouvert P1 |
| **Séparation d'environnements** | `dev` et `prod` dbt identiques aujourd'hui | **[PRÉVU]** — lot C |

### 9.3 Prévu — spécifié, non construit

| Phase | Contenu | État |
|---|---|---|
| **08a** API publique | `POST /api/v1/predictions`, `/market/*`, `/comparisons` | **[PRÉVU]** — `backend/` vide |
| **08b** API interne | permissions, jobs, administration | **[PRÉVU]** |
| **09a** Frontend public | estimation → exploration → comparaison | **[PRÉVU]** — `frontend/` vide, thème **non figé** |
| **09b** Administration | interface du back-office | **[PRÉVU]** |
| **10 Orchestration** | DAG planifié, retries, reprise | **[PRÉVU]** — **condition d'entrée non atteinte** (pas d'Airflow avant stabilisation) |
| **11 Observabilité** | fraîcheur, volumes, qualité, dérive, alertes | **[PRÉVU]** — la matière première existe en base |
| **12 Production** | docker-compose d'environnement, secrets, sauvegardes, runbooks, CI complète | **[PRÉVU]** — `infrastructure/` vide |
| **13 / 14 Back-office** | fondations puis rapports | **[PRÉVU]** — implémentation **après 08 et 09** |
| **15 Marketplace** | cadrage puis décision | **[PRÉVU]** — **aucun code** |
| **Conakry** | devise, référentiels, sources, droits locaux | **[PRÉVU]** — chantier séparé |

### 9.4 Ce qui n'existe pas du tout (contrôlé par `git ls-files`)

`backend/`, `frontend/`, `infrastructure/`, `tests/integration/` ne contiennent qu'un
`.gitkeep`. Aucune API, aucun écran, aucun DAG, aucune alerte, aucune authentification,
aucun rôles/permissions : **aucune de ces capacités n'est à présenter comme existante.**

---

## 10. La refactorisation en cours : le plan de réalignement par lots

### 10.1 Enchaînement validé

```
 phase 00-07 (terminées, mergées)
        │
        ▼
 audit en lecture seule ──▶ plan de réalignement VALIDÉ (15/10/2026, 10 décisions)
        │
        ├── A1 documentation ......................... ✅ PR #33
        ├── A2 registre gouverné ...................... ✅ PR #33
        ├── harmonisation des specs 00-12 ............ ✅ PR #34
        ├── B  qualité et contrat de données .......... ✅ PR #35   (16/10/2026)
        ├── C  CI de données ......................... ▶ PROCHAIN LOT
        ├── D  Phase 8 : 08a puis 08b ............... ▶ (exige B et C)
        ├── E  prix censurés, mesure à produire ....... ▶
        └── Phase 9 (09a/09b) puis 13/14 puis 10/11/12 ▶
```

### 10.2 Lot B — livré et fusionné le 16 octobre 2026 (PR #35)

**Ce qui a changé concrètement :**

1. **Provenance** : un lot de collecte porte sa version de code, l'empreinte SHA-256 de son
   contenu et le statut de ses validations — vérifié de bout en bout (l'empreinte du CLI
   correspond à `sha256sum`).
2. **Qualité en base** : `landing.quarantine_listings` (78 rejets) et
   `landing.ingestion_runs` (3 lots) sont chargés à chaque `python -m pipelines load`.
3. **Deux nouveaux marts** : `mart_data_quality` (motifs de rejet agrégés **avec** le total de
   la source — jamais un pourcentage seul) et `mart_ingestion_lots` (provenance lisible,
   `has_provenance` signale les lots antérieurs au lieu d'inventer une valeur).
4. **`rent_semantics`** : la sémantique de la cible devient une donnée **lue** (`asking_rent` /
   `unknown`) et non supposée.
5. **Contrôle des bornes** : un test dbt vérifie que toute valeur de pièces hors borne est
   **signalée** (contrôle négatif : borne forcée à 0 → 2 987 lignes, échec du test).

**Vérifications** : `ruff` 0 erreur · `pytest` **175 réussis / 1 ignoré** en local,
**176 / 0 en CI** · `dbt build` **137/137** · volumes et invariant N ≥ 30 inchangés.

### 10.3 Lot C — livré (2026-10-16)

Contenu livré (plan §8.2) : `dbt build` s'exécute **en CI** sur un service PostgreSQL —
le jeu synthétique déterministe (aucune donnée tierce, aucun réseau) traverse
`pipelines load` puis les 121 tests dbt dans un schéma jetable `analytics_ci` ; le paquet
s'installe (backend de build figé : `[build-system]` + paquets déclarés, installé par
`pip install -e '.[dev,transform,ml]'`) ; `.env.example` documente `DBT_TARGET` et les
schémas (port **5433**, critère déjà conforme) ; `dev` et `prod` sont séparés
(schémas `analytics` / `analytics_prod`) **sans migration destructive**.

> Vérifications : `ruff` 0 erreur · `pytest` **182 / 0 ignoré** en local (`pyarrow` installé
> dans le venv — critère §8.1) · chaîne complète en base jetable : 360/48/3 lignes chargées
> → `dbt build` **137/137** · schéma `analytics` réel inchangé · pipeline de la **PR #37**
> **verte en CI** : `pytest` **182 / 0 ignoré** et `dbt build` **137/137 exécutés en CI**.

### 10.4 Comment le statut est tenu

`context/progress-tracker.md` doit refléter l'**état réel**, jamais l'état souhaité. À chaque
lot vérifié : mise à jour du tracker et de la §14 du plan. La dernière synchronisation date
du 16/10/2026 (PR #37).

---

## 11. Qualité, tests et intégration continue

### 11.1 Échelles de vérification

| Niveau | Outil | État |
|---|---|---|
| Lint | `ruff check .` | **0 erreur** |
| Tests unitaires | `pytest tests -q` | **182 passent, 0 ignoré** (local et CI — `pyarrow` désormais installé partout) |
| Tests de données | `dbt build` | **137/137** — 16 modèles, 121 tests dont **6 tests singuliers** |
| Contrôles en base | requêtes `psql` | volumes, invariant de publication, réconciliation des motifs |
| Déterminisme ML | rejeu des artefacts JSON | md5 inchangé (durées seules variables) |
| CI (GitHub Actions) | `ruff` + `pytest` + tests de données (PostgreSQL + `dbt build`) | vertes sur PR **et** sur `develop` (dernier run : succès) |

### 11.2 Tests singuliers (les invariants les plus précieux)

- `assert_median_published_only_at_or_above_threshold` — aucune médiane de quartier publiée
  sous 30 observations, aucune absente au-dessus.
- `assert_neighborhood_key_exists_in_dim_neighborhood` — clé composite ville/quartier valide.
- `assert_data_quality_motifs_sum_to_quarantine_total` — la somme des motifs **égale** la
  quarantaine réelle (aucun rejet perdu).
- `assert_data_quality_grain_is_unique` — grain (source, motif).
- `assert_implausible_rooms_are_signalled` — toute valeur de pièces hors borne est signalée.
- `assert_rent_semantics_matches_target` — sémantique cohérente avec la cible.

### 11.3 Ce que la CI ne couvre **pas** encore

Depuis le lot C (2026-10-16), la CI couvre le lint, les tests unitaires **et** les tests de
données (jeu synthétique → `pipelines load` → `dbt build` sur PostgreSQL) : les invariants
sont protégés automatiquement à chaque PR, plus seulement par des exécutions locales.
Restent hors CI, par conception, les étapes des phases suivantes : tests d'intégration
(Phase 8), build frontend (Phase 9), déploiement (Phase 12).

---

## 12. Limites connues, points ouverts et informations incertaines

### 12.1 Limites produit (à dire tel quel à l'équipe)

1. **Couverture déséquilibrée** : Douala 2 811 observations, Yaoundé 181. Le modèle est en
   pratique un modèle doualais.
2. **Cible censurée** : 2 564 prix sur 2 992 ne sont qu'une borne inférieure (« à partir de »),
   dont 89 % des prix à Douala et 31 % à Yaoundé. Le modèle est largement entraîné sur des
   prix minorants.
3. **Features manquantes** : superficie, meublé, parking, barrière, dates — **absentes des
   sources**. La précision est plafonnée par l'information collectée : collecter la surface
   ferait plus pour la précision que n'importe quel algorithme. **Reste hors périmètre tant que
   la décision 6 ne l'autorise pas.**
4. **Républications** : 2 001 annonces quasi identiques réparties entre entraînement et test →
   évaluation potentiellement **optimiste**.
5. **Yaoundé sous seuil** : 25 observations de test (seuil de publication : 30) — segment
   signalé, jamais masqué.

### 12.2 Limites techniques et de reproductibilité

1. **Reproductibilité de bout en bout non garantie** (point ouvert P1) : `data/raw/`,
   `data/processed/`, `ml/models/` et `mlruns/` sont ignorés par git ; l'échantillon de Phase 0
   n'est pas versionné ; le backend de build de `pyproject.toml` est figé depuis le lot C,
   mais cela ne remplace pas des données non versionnées. **Aucun tiers ne peut recalculer aujourd'hui les chiffres publiés** à partir d'un
   clone.
2. **`pyarrow` absent du venv local** (historique) : 1 test Parquet ignoré en local. Corrigé
   le 2026-10-16 (dépendance cœur installée) : **182 tests, 0 ignoré** en local comme en CI —
   critère §8.1 tenu dans les deux environnements.
3. **Registre local** : l'état « quel modèle sert » vit dans une base PostgreSQL **non
   versionnée** ; la source de vérité versionnée est `ml/models/champion.json` + le rapport.
4. **84 runs** dans `rent_prediction`, **sans politique de rétention**.
5. **Ports** : le conteneur expose **5433** (5432 occupé par un PostgreSQL système).
   `.env.example` porte bien 5433 (vérifié le 16/10/2026) — l'écart relevé par l'audit (P8)
   est **résolu** ; la CI utilise la même cohérence (port et schémas) depuis le lot C.
6. **`dev` et `prod` dbt séparés depuis le lot C** (2026-10-16) : `analytics` (défaut, via
   `DBT_SCHEMA_DEV` avec fallback `DBT_SCHEMA`) et `analytics_prod` (`DBT_SCHEMA_PROD`) —
   séparation **non destructive**, le schéma `analytics` existant est intact ; le premier
   `dbt build --target prod` créera `analytics_prod` à côté.

### 12.3 Informations incertaines ou non vérifiées à ce jour

| Point | Nature | Ce qu'il faut faire |
|---|---|---|
| Chiffres des phases 0-7 | **datés** (rejeux des 09 → 16/10/2026) | rejeu avant toute reprise |
| `data/samples/` (jeu tiers sans licence) | **non versionné** | ne pas redistribuer |
| Endpoints MINFI / INS | documents bruts, **non validés** | validation avant usage |
| Représentativité réelle du marché | **jamais mesurée** (une seule journée de collecte) | à mesurer avant toute communication publique |
| Décision sur les quartiers exacts du MVP | **non arrêtée** (Ville : Yaoundé et Douala arrêté, liste des quartiers à définir) | décision ouverte |
| Rôles internes après `admin` | **non définis** (décision 7) | à définir avec 13/14 |
| Dossier `inspire/` et branches anciennes du dépôt | **non clarifié** dans les sources | à confirmer auprès du porteur du projet |
| Couverture utile de la fourchette au-delà de 90 % | **mesurée à 90,7 %**, pas à d'autres niveaux | ne pas promettre d'autre niveau |

---

## 13. Glossaire

| Terme | Définition |
|---|---|
| **Raw / Bronze** données brutes collectées, **jamais modifiées** (`data/raw/`, JSONL daté) |
| **Silver** données nettoyées, typées, dédupliquées, drapeaux conservés (`data/processed/*.parquet`) |
| **Gold / marts** tables analytiques prêtes pour l'analyse, le ML et l'API |
| **Quarantine** zone des observations **rejetées** avec motif — jamais de suppression |
| **`outlier_flags`** drapeau des valeurs extrêmes conservées (ex. `bathrooms_outlier`) |
| **`price_is_bound`** le prix n'est qu'une borne inférieure (« à partir de ») |
| **`is_republication`** même logement republié, conservé et signalé |
| **`rent_semantics`** sémantique de la cible : `asking_rent` (loyer demandé) / `unknown` |
| **dbt** outil de transformations SQL versionnées, testées et documentées |
| **Test dbt** contrôle automatisé sur un modèle (`not_null`, `unique`, `within_range`…) |
| **Test singulier** test dbt personnalisé, écrit en SQL (invariants complexes) |
| **`min_publish_n`** seuil (30 observations) en dessous duquel aucune médiane n'est publiée |
| **Baseline** prédiction naïve de référence (médiane par ville / quartier+type) |
| **MAE / MedAE** erreur absolue moyenne / **médiane** — MedAE plus robuste aux valeurs extrêmes |
| **IC bootstrap** intervalle de confiance par rééchantillonnage (définit le seuil à battre) |
| **`log1p`** transformation logarithmique `log(1+x)` de la cible, corrige l'asymétrie |
| **Fourchette calibrée** intervalle de prédiction validé par sa **couverture** mesurée |
| **Split-conformal** méthode d'intervalle calibrée sur un jeu de validation dédié |
| **Registre / `champion`** MLflow et alias du modèle **servable** |
| **Promotion approuvée** attribution de l'alias `champion` validée nominativement par un admin |
| **Lot** un changement cohérent, vérifiable et réversible du plan de réalignement |
| **Data leakage** fuite d'information de la cible vers les features (interdite) |

---

## 14. Sources de vérité et entretien du document

| Besoin | Fichier de référence |
|---|---|
| Règles de travail, interdits, git | `AGENTS.md` |
| Workflow, périmètre, lots | `context/ai-workflow-rules.md` |
| Produit, utilisateurs, MVP | `context/project-overview.md` |
| Architecture, sous-systèmes, invariants | `context/architecture-context.md` |
| Conventions de code | `context/code-standards.md` |
| **État réel d'avancement** | `context/progress-tracker.md` |
| Recadrage produit | `context/product/camrent-product-realignment.md` |
| Audit + 10 décisions + lots | `context/plans/camrent-audit-and-realignment-plan.md` |
| Une spec par phase (00 → 15) | `context/feature-specs/` |
| Ce qui a été livré, avec les chiffres | `docs/phase-0` → `docs/phase-7` |
| Interface (provisoire) | `context/ui-context.md` |

**Conflits éventuels** : si deux documents se contredisent, le signaler et trancher
**explicitement** dans le fichier de contexte concerné — ne jamais résoudre par supposition.

**Ce document** : support de présentation. Il n'est pas une source de vérité ; en cas de
divergence, les fichiers ci-dessus prévalent.

---

## 15. Annexes

### 15.1 Commandes pour vérifier soi-même les chiffres présentés

```bash
# lint + tests unitaires (176 tests en CI)
ruff check .
python -m pytest tests -q

# données : reconstruire le Silver puis charger (DATABASE_URL requis)
python -m pipelines silver --report docs/phase-2/cleaning-report.md
python -m pipelines load
cd dbt && dbt build && cd ..          # 137/137 attendu

# ML
python -m ml.src baselines            # Phase 5
python -m ml.src models               # Phase 6
python -m ml.src registry             # Phase 7 (promotion exige --confirm-promotion)

# contrôles en base (conteneur camrent-postgres, port 5433)
docker exec camrent-postgres psql -U camrent -d camrent \
  -tAc "select count(*) from landing.silver_listings"
docker exec camrent-postgres psql -U camrent -d camrent \
  -tAc "select quarantine_reason, count(*) from analytics_marts.mart_data_quality group by 1"
```

### 15.2 Arborescence réelle du dépôt

```
camrent/
├── AGENTS.md                 # règles de travail (prime sur les habitudes par défaut)
├── context/                  # CERVEAU DU PROJET — règles, specs, suivi, plan
│   ├── feature-specs/        # 00 → 15 (une spec par phase)
│   ├── plans/                # audit + plan de réalignement validé
│   └── product/              # recadrage produit
├── assets/                   # documents de conception d'amont
├── docs/                     # phase-0 → phase-7 (livrables vérifiés)
├── ingestion/                # Phase 1 : collecte contrôlée
├── pipelines/                # Phase 2 + 4 : Silver et chargement
├── dbt/                      # Phase 4 : transformations SQL testées
├── eda/                      # Phase 3 : rapports dérivés
├── ml/                       # Phases 5-7 : baselines, modèles, registre
├── backend/                  # Phase 8   → .gitkeep uniquement
├── frontend/                 # Phase 9   → .gitkeep uniquement
├── infrastructure/           # Phase 12  → .gitkeep uniquement
├── tests/                    # unit/ (actifs) + integration/ (vide)
└── .github/workflows/        # CI (lint + tests) ; CD = placeholder
```

### 15.3 Les cinq phrases à retenir

1. **Les phases 0 à 7 existent vraiment** : données brutes immuables, Silver testé, marts dbt
   testés, baselines mesurées, modèle qui bat sa baseline de 22,31 %, registre MLflow gouverné.
2. **Ce qui manque est le produit visible** : API, interface, orchestration, observabilité,
   production — tout est spécifié, **rien n'est construit**.
3. **Le recadrage du 15/10/2026 a verrouillé 10 décisions** : périmètre (Yaoundé/Douala,
   Conakry séparée), marketplace conditionnée, MVP finalisé avant nouvelle collecte,
   promotion de modèle approuvée par un admin, `dbt build` en CI.
4. **Le travail avance par lots vérifiés** : A1, A2, B sont fusionnés ; **C (CI de données) est
   le prochain** ; D (API) exige B **et** C.
5. **Le produit affiche toujours ses limites** : nombre d'observations, fourchette mesurée,
   prix demandé et non prix payé — aucune fausse précision.

---

*Document généré le 16 octobre 2026 à partir des fichiers du dépôt. Chaque chiffre y est daté ;
avant de le reprendre dans une présentation externe, re-vérifiez-le avec les commandes de
l'annexe 15.1.*
