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
| Qualité | unique `listing_key` ; relationships vers `dim_city`, `dim_property_type`, `dim_date` ; paire (ville, quartier) contrôlée par test singulier ; `rent_price` not_null et borné (≥ 1) ; bornes sur chambres (0-10). |

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
| Description | Statistiques de marché par (ville, quartier, type, chambres) : N, moyenne, médiane, p10, p90, min, max, part de prix bornés. **La médiane n'est pas publiée sous N < 30** (var `min_publish_n`, décision Phase 3) mais N reste visible. |
| Grain | (ville, quartier, type, chambres). |
| Source | `fct_rent_observations`. |
| Fréquence | Rejouée à chaque `dbt build`. |
| Owner | Data Engineering. |
| Sensibilité | Public. |
| Qualité | not_null N/moyenne ; invariant de publication des médianes contrôlé par le test singulier `assert_median_published_only_at_or_above_threshold` (var `min_publish_n`) ; bornes `within_range` : N ≥ 1, moyenne ≥ 0, médiane ≥ 0. |

### marts.mart_city_prices

| Attribut | Valeur |
|---|---|
| Description | Statistiques de marché par ville (grain ville) : mêmes conventions (N toujours, p10/p90, part de prix bornés visibles). |
| Grain | Ville. |
| Source | `fct_rent_observations`. |
| Fréquence | Rejouée à chaque `dbt build`. |
| Owner | Data Engineering. |
| Sensibilité | Public. |
| Qualité | unique `city` + accepted_values ; not_null `median_rent_price` (au-dessus de 2 811 / 181 observations, toujours publiée au MVP) ; bornes `within_range` : N ≥ 1, médiane ≥ 0. |

### marts.mart_property_prices

| Attribut | Valeur |
|---|---|
| Description | Statistiques de marché par (type de logement, ville). N toujours présent. |
| Grain | (type, ville). |
| Source | `fct_rent_observations`. |
| Fréquence | Rejouée à chaque `dbt build`. |
| Owner | Data Engineering. |
| Sensibilité | Public. |
| Qualité | not_null type/ville/N/médiane ; bornes `within_range` : N ≥ 1, médiane ≥ 0. |

### marts.mart_ml_dataset

| Attribut | Valeur |
|---|---|
| Description | Dataset prêt pour l'entraînement (Phases 5-6) : features du MVP (ville, quartier, type, chambres, salles de bain, drapeaux) + cible `target_rent_price`. **Sans `rent_per_m2`** (anti-leakage). Les colonnes `price_is_bound`, `is_republication`, `outlier_flags` servent à une pondération/exclusion **explicite** côté entraînement (décisions Phases 5-6, cf. points ouverts du progress tracker). |
| Grain | Une ligne par observation Silver. |
| Source | `int_clean_listings`. |
| Fréquence | Rejouée à chaque `dbt build`. |
| Owner | Data Engineering + ML. |
| Sensibilité | Public. |
| Qualité | unique `listing_key` ; not_null ville/quartier/type/cible ; accepted_values ville ; borne `within_range` sur la cible (≥ 1). |

## Lineage (Plan Technique §29)

```
Annonce source (Koutchoumi live · jumia.csv · koutchoumi1.csv)   [Phase 1]
    ↓
data/raw/... (JSONL daté, immuable)
    ↓
data/processed/silver_listings.parquet                            [Phase 2, pipelines/silver.py]
    + data/processed/quarantine_listings.parquet (hors Gold)
    ↓
landing.silver_listings                                           [Phase 4, pipelines/db.py]
    ↓
staging.stg_listings
    ↓
intermediate.int_clean_listings
    ↓
├── marts.dim_city / dim_neighborhood / dim_property_type / dim_date
├── marts.fct_rent_observations / fct_listings
    ↓
marts.mart_neighborhood_prices / mart_city_prices / mart_property_prices
    ↓
marts.mart_ml_dataset
    ↓
(ml/ Phases 5-6 → Model → backend/ Phase 8 → Prediction)
```

Le lineage interactif est disponible via `dbt docs generate && dbt docs serve`.
