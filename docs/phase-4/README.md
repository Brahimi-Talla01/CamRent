# Phase 4 — Data warehouse / marts

Objectif (spec : `context/feature-specs/04-data-marts.md`) : construire les
tables analytiques (Gold) à partir du Silver, prêtes pour l'analyse, l'API
(Phase 8) et le ML (Phases 5-6).

## Livrables

1. **Chargement du Silver dans PostgreSQL** : `pipelines/db.py` +
   `python -m pipelines load` → table d'atterrissage
   `landing.silver_listings` (idempotent, `replace` ; la source de vérité du
   Silver reste `data/processed/silver_listings.parquet`, rejouable).
2. **Projet dbt** (`dbt/`) : transformations SQL versionnées ;
   chaîne `stg_listings` → `int_clean_listings` → faits/dims → marts.
3. **Tables** :
   - dimensions : `dim_city`, `dim_neighborhood`, `dim_property_type`,
     `dim_date` (dates observées, pas de calendrier artificiel) ;
   - faits : `fct_rent_observations`, `fct_listings` ;
   - marts : `mart_neighborhood_prices`, `mart_city_prices`,
     `mart_property_prices`, `mart_ml_dataset`.
4. **Tests dbt** : not_null, unique, relationships (faits → dims),
   accepted_values — `dbt/models/marts/marts_schema.yml`.
5. **Data Catalog** : `data-catalog.md` (description, grain, source,
   fréquence, owner, sensibilité, qualité pour chaque dataset).

## Exécution de bout en bout

```bash
# 1. Construire le Silver (Phase 2)
python -m pipelines silver --report docs/phase-2/cleaning-report.md

# 2. Charger dans PostgreSQL (Phase 4)
python -m pipelines load

# 3. Construire les marts + exécuter les tests dbt
cd dbt && dbt build && dbt test
```

Voir `dbt/README.md` pour les variables d'environnement attendues.

## Résultats de la construction (rejeu du 2026-10-12)

Base : PostgreSQL 16 (docker-compose, PostgreSQL système déjà occupant 5432 → port **5433**), dbt-core 1.12.5 + dbt-postgres 1.11.0.

| Étape | Résultat |
|---|---|
| `python -m pipelines load` | **2 992 lignes** → `landing.silver_listings` |
| `dbt build` | **74/74 PASS** : 12 modèles (2 vues + 10 tables) + **62 tests dbt** |
| Grain fat/dim/mart | cohérent : 2 992 lignes de landing à `mart_ml_dataset` |
| `mart_city_prices` | Douala N=2 811 méd. 100 000 · Yaoundé N=181 méd. 150 000 (conforme EDA Phase 3) |
| `mart_neighborhood_prices` | 253 groupes (ville, quartier, type, chambres) ; médiane **null sous N<30** (0 violation : 0 publiée sous 30, 0 absente à ≥ 30) |
| Anomalies signalées, jamais supprimées | 101 quartiers non reconnus, 2 001 républications, 2 564 prix bornés, 17 aberrations (lignes conservées + drapeaux) |

À noter : deux lignes aux prix extrêmes (`rent_price` = 1 FCFA → Douala ; 50 FCFA →
Yaoundé) restent dans les faits avec `price_outlier` — elles sont signalées,
conformément aux invariants (pas de suppression silencieuse).

## Invariants appliqués

- La donnée brute n'est jamais écrasée ; l'atterrissage est une copie dérivée
  du Silver, recréable.
- Aucune exclusion silencieuse : républications, prix bornés et quartiers non
  reconnus restent dans les données, signalés par drapeaux — les marts les
  quantifient (N, `pct_price_bound`).
- Toute statistique de marché embarque son **nombre d'observations**.
- Sous le seuil de publication (N < 30, décision Phase 3), la médiane par
  quartier n'est pas publiée (null), mais le N reste visible.
- `mart_ml_dataset` : pas de `rent_per_m2` (anti-leakage) ; cible =
  `target_rent_price` = rent_price (prix demandé dans l'annonce).

## Hors périmètre (spec Phase 4)

- Pas de Data Warehouse (BigQuery/Snowflake/Redshift) : PostgreSQL suffit.
- Pas de MongoDB.
- Pas de logique ML ici : `mart_ml_dataset` expose les features et la cible.
