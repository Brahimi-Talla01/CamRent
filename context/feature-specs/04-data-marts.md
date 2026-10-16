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

7. **Sémantique de cible** (décision 9) : `mart_ml_dataset` expose `rent_semantics`
   (`asking_rent` / `unknown`) ; la cible `target_rent_price` n'est pas renommée.

8. **Qualité en base** (lot B) : quarantaine et métadonnées de lot chargées dans `landing`, avec
   une table de qualité agrégant les motifs de rejet — support de la Phase 11 et du module
   « Qualité » (Phase 13).

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
- `mart_ml_dataset` contient les features du MVP + `rent_price` + `rent_semantics`.
- Chaque dataset important est documenté (grain, source, fréquence, owner, sensibilité).
- Le lineage est traçable de la source au mart.

## État d'implémentation (2026-10-16)

- **Sémantique de cible** (lot B) : `mart_ml_dataset.rent_semantics` (`asking_rent` / `unknown`),
  cible non renommée ; `asking_rent` sur les 2 992 observations (aucune valeur nulle).
- **Qualité en base** (lot B) : `landing.quarantine_listings` (78 rejets) et
  `landing.ingestion_runs` (3 lots) chargées par `python -m pipelines load` ; marts
  `mart_data_quality` (4 lignes, motifs 52/18/7/1 = 78 rejets réconciliés par test singulier) et
  `mart_ingestion_lots` (une ligne par lot, provenance et `has_provenance`).
- **Vérifié** : `dbt build` **137/137** — 16 modèles, 121 tests dont 6 singuliers (volumes de
  `landing.silver_listings` à `mart_ml_dataset` inchangés : 2 992 lignes ; invariant de publication
  des médianes intact : 234 non publiées sur 253 groupes, plus petit N publié = 31).
