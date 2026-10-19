# Data Catalog — Phase 4 (Data marts)

Chaque dataset est documenté selon le modèle du Plan Technique §28 :
description, grain, source, fréquence, owner, sensibilité, qualité.
Le lineage de bout en bout figure en fin de document (§29).

**Nommage des schémas.** dbt préfixe le schéma du profil par le schéma déclaré sur
chaque modèle (`analytics` + `staging` / `intermediate` / `marts`) : en base, les
schémas réels sont donc `analytics_staging`, `analytics_intermediate` et
`analytics_marts` (voir `dbt/profiles.yml` et `DBT_SCHEMA`). Par concision, ce
catalogue écrit `staging.`, `intermediate.` et `marts.` pour ces schémas ; la table
d'atterrissage `pipelines/db.py` reste dans `landing`, créé hors dbt.

## Données sources

### landing.silver_listings

| Attribut | Valeur |
|---|---|
| Description | Table d'atterrissage du Silver dataset (Phase 2) dans PostgreSQL. Copie dérivée rejouable : la vérité reste `data/raw/` (immuable) / `data/processed/silver_listings.parquet`. |
| Grain | Une ligne par annonce nettoyée après validation/dédup de la Phase 2. |
| Source | `data/processed/silver_listings.parquet` (chargé par `python -m pipelines load`). |
| Fréquence | Changement à chaque rejou du Silver (batch, cf. Phase 10). |
| Owner | Data Engineering. |
| Sensibilité | Non — données d'annonces publiques, minimisation (aucune donnée personnelle). |
| Qualité | Garantie par la Phase 2 (drapeaux + quarantine) et testée par dbt (tests ci-dessous). |

### landing.quarantine_listings

| Attribut | Valeur |
|---|---|
| Description | Table d'atterrissage des **observations rejetées** par la Phase 2, avec leur motif. Créée par le **lot B** (plan de réalignement §7.6) : la quarantaine devient interrogeable en base, au lieu de vivre uniquement dans un Parquet local. |
| Grain | Une ligne par observation rejetée (une ligne par ligne de `quarantine_listings.parquet`). |
| Source | `data/processed/quarantine_listings.parquet` (chargé par `python -m pipelines load`). |
| Fréquence | Changement à chaque rejou du Silver (batch, cf. Phase 10). |
| Owner | Data Engineering. |
| Sensibilité | Non (annonces publiques, minimisation). |
| Qualité | `quarantine_reason` et `source` not_null ; la somme des motifs est réconciliée avec le total réel par le test singulier `assert_data_quality_motifs_sum_to_quarantine_total`. |

### landing.ingestion_runs

| Attribut | Valeur |
|---|---|
| Description | Table d'atterrissage des **métadonnées de collecte** : un lot par fichier de `data/raw/metadata/`. Porte la provenance — version du connecteur, empreinte SHA-256 du contenu, statut de validation du lot (lot B, spec Phase 1 §6). Les lots antérieurs à cette provenance ont des champs nuls : l'absence est signalée, jamais comblée. |
| Grain | Une ligne par lot brut. |
| Source | `data/raw/metadata/<date>/<source>_<HHMMSS>.json` (chargé par `python -m pipelines load`). |
| Fréquence | À chaque nouvelle collecte (batch, cf. Phase 10). |
| Owner | Data Engineering. |
| Sensibilité | Non (métadonnées de collecte, aucune donnée personnelle). |
| Qualité | `raw_file` not_null ; concordance volume déclaré / volume réel contrôlée en Bronze (`python -m ingestion --validate-bronze`). |

## Staging / Intermediate

### staging.stg_listings

| Attribut | Valeur |
|---|---|
| Description | Vue : lignes Silver typées (entiers, booleans, bigint (prix)). Ajoute la clé technique `listing_key`. |
| Grain | Une ligne par ligne silver_listings. |
| Source | `landing.silver_listings`. |
| Fréquence | Reconstruite à chaque `dbt build`. |
| Owner | Data Engineering. |
| Sensibilité | Non. |
| Qualité | tests dbt : unique `listing_key`, `rent_price` not_null, `city`/`property_type` dans les valeurs acceptées. |

### intermediate.int_clean_listings

| Attribut | Valeur |
|---|---|
| Description | Vue : passthrough enrichi expoitable par les dims/marts. Grain inchangé ; les drapeaux de qualité sont portés tels quels. |
| Grain | Une ligne par ligne Silver. |
| Source | `staging.stg_listings`. |
| Fréquence | Reconstruite à chaque `dbt build` (vue). |
| Owner | Data Engineering. |
| Sensibilité | Non. |
| Qualité | tests dbt : unique `listing_key`, not_null `rent_price`, `city`. |

### staging.stg_quarantine

| Attribut | Valeur |
|---|---|
| Description | Vue : quarantaine typée, une ligne par rejet, avec `quarantine_reason`. Aucun filtrage ni correction. |
| Grain | Une ligne par observation rejetée. |
| Source | `landing.quarantine_listings`. |
| Fréquence | Reconstruite à chaque `dbt build`. |
| Owner | Data Engineering. |
| Sensibilité | Non. |
| Qualité | not_null `source_name`, `quarantine_reason`, `listing_key` ; accepted_values sur les motifs (prix_manquant, type_inconnu, city_inconnue, prix_invalide). |

### staging.stg_ingestion_runs

| Attribut | Valeur |
|---|---|
| Description | Vue : lots de collecte typés, avec `has_provenance` (vrai si version de connecteur et empreinte de contenu sont renseignées). |
| Grain | Une ligne par lot brut. |
| Source | `landing.ingestion_runs`. |
| Fréquence | Reconstruite à chaque `dbt build`. |
| Owner | Data Engineering. |
| Sensibilité | Non. |
| Qualité | unique + not_null `raw_file` ; accepted_values `source_name` et `lot_validation_status` ; `record_count` borné (≥ 0). |

## Dimensions

### marts.dim_city

| Attribut | Valeur |
|---|---|
| Description | Une ligne par ville canonique (Douala, Yaoundé), avec le volume d'observations du Silver. |
| Grain | Ville. |
| Source | `int_clean_listings`. |
| Fréquence | Rejouée à chaque `dbt build` (pas d'historisation au MVP). |
| Owner | Data Engineering. |
| Sensibilité | Public. |
| Qualité | unique `city_name` ; accepted_values `Douala`, `Yaoundé`. |

### marts.dim_neighborhood

| Attribut | Valeur |
|---|---|
| Description | Une ligne par (ville, quartier) tel qu'observé ; `is_canonical` indique si le libellé est reconnu par le référentiel seed (`pipelines/geo.py`, issue #20 — aucun mapping inventé). |
| Grain | (ville, quartier). |
| Source | `int_clean_listings`. |
| Fréquence | Rejouée à chaque `dbt build` (pas d'historisation au MVP). |
| Owner | Data Engineering. |
| Sensibilité | Public. |
| Qualité | not_null ville/quartier ; la paire (ville, quartier) des faits est contrôlée par le test singulier `assert_neighborhood_key_exists_in_dim_neighborhood`. |

### marts.dim_property_type

| Attribut | Valeur |
|---|---|
| Description | Une ligne par type de logement canonique (studio, apartment, house, office, shop, warehouse, room, land), avec volumes. |
| Grain | Type de logement. |
| Source | `int_clean_listings`. |
| Fréquence | Rejouée à chaque `dbt build` (pas d'historisation au MVP). |
| Owner | Data Engineering. |
| Sensibilité | Public. |
| Qualité | unique + accepted_values sur `property_type_name`. |

### marts.dim_date

| Attribut | Valeur |
|---|---|
| Description | Dates réellement présentes dans les données (priorité `posted_at`, fallback `collected_at`). Pas de calendrier artificiel : au MVP, `posted_at` est quasi absent (EDA Phase 3). |
| Grain | Jour. |
| Source | `int_clean_listings`. |
| Fréquence | Rejouée à chaque `dbt build` (pas d'historisation au MVP). |
| Owner | Data Engineering. |
| Sensibilité | Public. |
| Qualité | unique `date_day` ; bornes `within_range` sur année (2000-2100), mois (1-12) et jour (1-31). |

## Faits

### marts.fct_rent_observations

| Attribut | Valeur |
|---|---|
| Description | Fait des observations de loyer (une ligne = une observation Silver), features du bien + drapeaux qualité + clés de dimensions. Base de toutes les stats de marché. |
| Grain | Une ligne par observation Silver. |
| Source | `int_clean_listings`. |
| Fréquence | Rejouée à chaque `dbt build`. |
| Owner | Data Engineering. |
| Sensibilité | Public (annonces). |
| Qualité | unique `listing_key` ; relationships vers `dim_city`, `dim_property_type`, `dim_date` ; paire (ville, quartier) contrôlée par test singulier ; `rent_price` not_null et borné (≥ 1) ; bornes sur chambres (0-10). Les valeurs `bedrooms` / `bathrooms` hors bornes plausibles (var `rooms_max_plausible`, défaut 10) sont **conservées et signalées** dans `outlier_flags` (`bathrooms_outlier` pour les 3 observations à 80) — signalement vérifié par le test singulier `assert_implausible_rooms_are_signalled`. |

### marts.fct_listings

| Attribut | Valeur |
|---|---|
| Description | Fait d'annonce : même grain que `fct_rent_observations`, colonnes d'origine conservées (`source_name`, `source_file`, `source_listing_id`, `url`) pour la traçabilité « d'où vient cette valeur ? » (Plan Technique §29). |
| Grain | Une ligne par observation Silver. |
| Source | `int_clean_listings`. |
| Fréquence | Rejouée à chaque `dbt build`. |
| Owner | Data Engineering. |
| Sensibilité | Public. |
| Qualité | unique `listing_key`, not_null `source_listing_id`. |

## Marts

### marts.mart_neighborhood_prices

| Attribut | Valeur |
|---|---|
| Description | Statistiques de marché par (ville, quartier, type, chambres) : N, moyenne, médiane, p10, p90, min, max, volumes et parts de prix bornés et de republications. **La médiane n'est pas publiée sous N < 30** (var `min_publish_n`, décision Phase 3) mais N reste visible. |
| Grain | (ville, quartier, type, chambres). |
| Source | `fct_rent_observations`. |
| Fréquence | Rejouée à chaque `dbt build`. |
| Owner | Data Engineering. |
| Sensibilité | Public. |
| Qualité | not_null N/moyenne/compteurs ; invariant de publication des médianes contrôlé par le test singulier `assert_median_published_only_at_or_above_threshold` (var `min_publish_n`) ; bornes `within_range` : N ≥ 1, moyenne ≥ 0, médiane ≥ 0, parts entre 0 et 100. |

### marts.mart_city_prices

| Attribut | Valeur |
|---|---|
| Description | Statistiques de marché par ville (grain ville) : mêmes conventions (N toujours, p10/p90, volumes et parts de prix bornés, de republications et de quartiers non reconnus). |
| Grain | Ville. |
| Source | `fct_rent_observations`. |
| Fréquence | Rejouée à chaque `dbt build`. |
| Owner | Data Engineering. |
| Sensibilité | Public. |
| Qualité | unique `city` + accepted_values ; not_null `median_rent_price` (au-dessus de 2 811 / 181 observations, toujours publiée au MVP) et des compteurs de qualité ; bornes `within_range` : N ≥ 1, médiane ≥ 0, parts entre 0 et 100. |

### marts.mart_property_prices

| Attribut | Valeur |
|---|---|
| Description | Statistiques de marché par (type de logement, ville) : N, moyenne, médiane, p10/p90, min/max, prix bornés et republications. Même forme que les deux autres marts de marché pour que l'API expose un contrat unique. |
| Grain | (type, ville). |
| Source | `fct_rent_observations`. |
| Fréquence | Rejouée à chaque `dbt build`. |
| Owner | Data Engineering. |
| Sensibilité | Public. |
| Qualité | not_null type/ville/N/médiane/p10/p90/compteurs ; bornes `within_range` : N ≥ 1, prix ≥ 0, parts entre 0 et 100. |

### marts.mart_data_quality

| Attribut | Valeur |
|---|---|
| Description | Motifs de rejet agrégés par source (lot B) : combien d'observations ont été écartées, et pourquoi. Chaque ligne porte son nombre de rejets **et** le total des rejets de la source : jamais un pourcentage sans son volume (invariant 8). Aucun rejet n'est masqué (invariant 5). Support du module « Qualité » du back-office (Phase 13) et de l'observabilité (Phase 11). |
| Grain | (source, motif de rejet). |
| Source | `stg_quarantine`. |
| Fréquence | Rejouée à chaque `dbt build`. |
| Owner | Data Engineering. |
| Sensibilité | Non. |
| Qualité | not_null source/motif/compteurs ; accepted_values sur les motifs ; `pct_of_source_rejections` borné (0-100) ; grain unique et réconciliation des volumes par tests singuliers (`assert_data_quality_grain_is_unique`, `assert_data_quality_motifs_sum_to_quarantine_total`). |

### marts.mart_ingestion_lots

| Attribut | Valeur |
|---|---|
| Description | Lots de collecte et leur provenance (lot B) : quoi, quand, avec quelle version du code, avec quelle empreinte, et si le lot a été validé. `has_provenance` est faux pour les lots collectés avant l'introduction de ces champs — l'absence est signalée, jamais inventée. Support du module « Sources » du back-office. |
| Grain | Un lot brut. |
| Source | `stg_ingestion_runs`. |
| Fréquence | Rejouée à chaque `dbt build`. |
| Owner | Data Engineering. |
| Sensibilité | Non. |
| Qualité | unique + not_null `raw_file` ; not_null `source_name`, `record_count` (≥ 0), `has_provenance` ; accepted_values `lot_validation_status` (`ok`, `failed`, `unreadable`). |

### marts.mart_ml_dataset

| Attribut | Valeur |
|---|---|
| Description | Dataset prêt pour l'entraînement (Phases 5-6) : features du MVP (ville, quartier, type, chambres, salles de bain, drapeaux) + cible `target_rent_price` + `rent_semantics` (sémantique explicite de la cible : `asking_rent` / `unknown`, décision du 2026-10-15). **Sans `rent_per_m2`** (anti-leakage). Les colonnes `price_is_bound`, `is_republication`, `outlier_flags` servent à une pondération/exclusion **explicite** côté entraînement (décisions Phases 5-6, cf. points ouverts du progress tracker). |
| Grain | Une ligne par observation Silver. |
| Source | `int_clean_listings`. |
| Fréquence | Rejouée à chaque `dbt build`. |
| Owner | Data Engineering + ML. |
| Sensibilité | Public. |
| Qualité | unique `listing_key` ; not_null ville/quartier/type/cible ; accepted_values ville ; borne `within_range` sur la cible (≥ 1) ; `rent_semantics` not_null et dans `asking_rent` / `unknown`, cohérence avec la cible vérifiée par le test singulier `assert_rent_semantics_matches_target`. |

## Lineage (Plan Technique §29)

```
Annonce source (Koutchoumi live · jumia.csv · koutchoumi1.csv)   [Phase 1]
    ↓
data/raw/... (JSONL daté, immuable)
    ↓
data/processed/silver_listings.parquet                            [Phase 2, pipelines/silver.py]
data/processed/quarantine_listings.parquet     (rejets, jamais supprimés)
    ↓
landing.silver_listings · landing.quarantine_listings             [Phase 4, pipelines/db.py]
landing.ingestion_runs  ← data/raw/metadata/<date>/*.json  (provenance des lots, lot B)
    ↓
staging.stg_listings · stg_quarantine · stg_ingestion_runs
    ↓
intermediate.int_clean_listings
    ↓
├── marts.dim_city / dim_neighborhood / dim_property_type / dim_date
├── marts.fct_rent_observations / fct_listings
    ↓
marts.mart_neighborhood_prices / mart_city_prices / mart_property_prices
marts.mart_data_quality · mart_ingestion_lots                    (qualité et provenance, lot B)
    ↓
marts.mart_ml_dataset
    ↓
(ml/ Phases 5-6 → Model → backend/ Phase 8 → Prediction)
```

Le lineage interactif est disponible via `dbt docs generate && dbt docs serve`.
