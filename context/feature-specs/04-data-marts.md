# Phase 4 — Data warehouse / marts

Lire `context/architecture-context.md` et `context/code-standards.md` avant de commencer.

Objectif : construire les **tables analytiques (Gold)** à partir du Silver, prêtes pour l'analyse,
l'API et le ML.

## Implementation

1. Charger le Silver dans **PostgreSQL** (base opérationnelle + analytique au MVP).

2. Créer les **tables de faits et dimensions** :

   ```
   dim_city
   dim_neighborhood
   dim_property_type
   dim_date

   fct_rent_observations
   fct_listings
   ```

3. Créer les **marts** :

   ```
   mart_neighborhood_prices
   mart_city_prices
   mart_property_prices
   mart_ml_dataset
   ```

4. Introduire **dbt** pour gérer les transformations SQL versionnées :

   ```
   Raw tables → dbt staging → dbt intermediate → dbt marts
   ```

   Nommage : `stg_listings` → `int_clean_listings` → `fct_rent_observations` → `mart_neighborhood_prices`.

5. Ajouter les **tests dbt** sur les modèles transformés (cf. Phase 11 pour l'observabilité continue) :
   not null, uniqueness, relations, ranges.

6. Définir le **grain** de chaque table et documenter chaque dataset important (Data Catalog) :
   description, grain, source, fréquence, owner, sensibilité, qualité.

## Dependencies

- PostgreSQL (+ PostGIS si les colonnes géographiques sont introduites).
- dbt.
- Silver dataset (Phase 2).

## Scope Limits

- Ne pas introduire de Data Warehouse (BigQuery / Snowflake / Redshift / Databricks) : PostgreSQL suffit au MVP.
- Ne pas introduire MongoDB à cette phase.
- Ne pas écrire de logique ML ici : le mart ML expose juste les features et la cible.

## Check When Done

- Les tables de faits/dimensions existent en base et sont alimentées.
- Les marts sont construits via dbt et versionnés dans `dbt/`.
- Les tests dbt passent sur les modèles critiques.
- `mart_ml_dataset` contient les features du MVP + `rent_price`.
- Chaque dataset important est documenté (grain, source, fréquence, owner, sensibilité).
- Le lineage est traçable de la source au mart.
