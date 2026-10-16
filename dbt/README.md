# dbt — transformations SQL versionnées (Phase 4)

Transforme le Silver (chargé dans PostgreSQL par `python -m pipelines load`)
en faits, dimensions et marts prêts pour l'API, l'analyse et le ML.

Flux : `landing.silver_listings` → `staging.stg_listings` →
`intermediate.int_clean_listings` → marts (`schema marts/`), et — depuis le lot B
(qualité et provenance) — `landing.quarantine_listings` → `staging.stg_quarantine`
→ `mart_data_quality`, et `landing.ingestion_runs` → `staging.stg_ingestion_runs`
→ `mart_ingestion_lots`.

En base, les schémas sont préfixés par le schéma de profil (`DBT_SCHEMA`,
défaut `analytics`) : `analytics_staging`, `analytics_intermediate`,
`analytics_marts`. Les trois tables d'atterrissage (`landing.silver_listings`,
`landing.quarantine_listings`, `landing.ingestion_runs`) sont créées hors dbt,
par `python -m pipelines load`.

## Prérequis

- `pip install dbt-postgres` (dbt-core ≥ 1.12 + adaptateur postgres).
- PostgreSQL accessible : la chaîne de connexion passe par des **variables
  d'environnement** (aucun secret en dur) :

```bash
export DBT_HOST=localhost
export DBT_PORT=5433
export DBT_USER=camrent
export DBT_PASSWORD=change-me
export DBT_DBNAME=camrent
export DBT_SCHEMA=analytics     # optionnel (défaut : analytics)
```

Ou simplement : `source .env` puis adapter `DATABASE_URL` → les variables
`DBT_*` (voir `.env.example` à l'avenir pour les defaults).

## Utilisation

```bash
cd dbt
dbt deps          # (pas de packages externes au MVP ; no-op)
dbt seed          # (aucun seed au MVP)
dbt build         # staging → intermediate → marts + tests
dbt test          # replay des tests seuls
dbt docs generate # lineage (docs/generated)
```

## Structure

```
dbt/
├── dbt_project.yml       # nommage stg_/int_/dim_/fct_/mart_, par couche
├── profiles.yml           # connexion par env vars (dev/prod)
├── macros/
│   └── tests/             # within_range (test générique de bornes)
├── tests/                 # tests singuliers (invariants trop complexes pour
│                          #   un test de colonne)
└── models/
    ├── staging/           # stg_listings, stg_quarantine, stg_ingestion_runs
    │                      #   + sources.yml (+ tests)
    ├── intermediate/      # int_clean_listings (+ tests)
    └── marts/             # dim_*, fct_*, mart_* (+ schema de tests)
```

## Modèles et grain

| Modèle | Grain | Rôle |
|---|---|---|
| `stg_listings` | 1 ligne Silver | typage, `listing_key` |
| `stg_quarantine` | 1 observation rejetée | quarantaine typée + motif |
| `stg_ingestion_runs` | 1 lot brut | lots typés + `has_provenance` |
| `int_clean_listings` | 1 ligne Silver | enrichissement minimal |
| `dim_city` | ville | dimension + volume d'observations |
| `dim_neighborhood` | (ville, quartier) | dimension ; `is_canonical` signale le référentiel |
| `dim_property_type` | type | dimension + volume |
| `dim_date` | jour observé | dates réellement présentes (pas de calendrier artificiel) |
| `fct_rent_observations` | 1 ligne Silver | fait des observations de loyers |
| `fct_listings` | 1 ligne Silver | fait d'annonce (traçabilité url/source) |
| `mart_neighborhood_prices` | (ville, quartier, type, chambres) | stats + N |
| `mart_city_prices` | ville | stats + N |
| `mart_property_prices` | (type, ville) | stats + N |
| `mart_data_quality` | (source, motif) | motifs de rejet agrégés + volumes |
| `mart_ingestion_lots` | 1 lot brut | lots + provenance (version, empreinte, validation) |
| `mart_ml_dataset` | 1 ligne Silver | features MVP + cible `target_rent_price` + `rent_semantics` |

## Gardes-fous codés dans les modèles

- Chaque agrégat de marché embarque **`n_observations`** (invariant 8).
- `median_rent_price` de `mart_neighborhood_prices` est `null` sous le seuil
  de publication `min_publish_n` (var dbt, défaut 30 — décision Phase 3) ;
  N et la moyenne restent visibles.
- Républications, prix bornés (Koutchoumi) et quartiers non reconnus
  **restent dans les données** ; seuls des drapeaux les signalent
  (`is_republication`, `price_is_bound`, `neighborhood_recognized`,
  `outlier_flags`).
- `mart_ml_dataset` ne contient **pas** de `rent_per_m2` (anti-leakage) ;
  `rent_price` devient `target_rent_price`, accompagné de `rent_semantics`
  (`asking_rent` / `unknown`) pour que la sémantique de la cible soit **lue dans
  les données**, jamais supposée.
- `mart_data_quality` accompagne chaque part de rejets de son **nombre de rejets**
  et du total de la source (invariant 8) ; aucun rejet n'est masqué.
- `mart_ingestion_lots` signale par `has_provenance` les lots antérieurs à la
  version de connecteur et à l'empreinte de contenu : l'absence est visible, pas
  comblée par une valeur inventée.

## Tests

- `dbt test` : not_null, unique, relationships, accepted_values sur
  stg/intermediate/marts (voir `models/marts/marts_schema.yml`).
- Bornes inclusives : test générique `within_range` (macro
  `macros/tests/within_range.sql`), déclaré par colonne avec `min_value` et/ou
  `max_value` — prix ≥ 1, chambres 0-10, N ≥ 1, année/mois/jour, cible ≥ 1.
  Les extrêmes conservés (1 FCFA, 40 000 000 FCFA) restent dans les bornes :
  ils sont signalés par `outlier_flags`, jamais supprimés.
- Relations : `relationships` vers `dim_city`, `dim_property_type` et
  `dim_date` ; la paire (ville, quartier) étant composite, elle est contrôlée
  par le test singulier `assert_neighborhood_key_exists_in_dim_neighborhood`.
- Invariant de publication :
  `assert_median_published_only_at_or_above_threshold` échoue si une médiane de
  quartier est publiée sous `min_publish_n` ou absente au-dessus.
- Bornes de pièces (spec 02 §12) : `assert_implausible_rooms_are_signalled`
  échoue si un `bedrooms` / `bathrooms` au-delà de la borne documentée
  (var `rooms_max_plausible`, défaut 10) apparaît **sans** son drapeau
  `_outlier` dans `outlier_flags`. La valeur reste dans les données : c'est le
  **signalement** qui est contrôlé, pas la suppression. Exemple réel conservé :
  `bathrooms = 80` (3 observations).
- Qualité (lot B) : `assert_data_quality_motifs_sum_to_quarantine_total`
  (la somme des motifs égale la quarantaine réelle — aucun rejet perdu dans
  l'agrégation) et `assert_data_quality_grain_is_unique` (grain
  source × motif).
- Sémantique de cible : `assert_rent_semantics_matches_target` (une observation
  à prix connu est `asking_rent`, une observation sans prix interprétable reste
  `unknown`).
- Les tests singuliers vivent dans `dbt/tests/` et échouent en remontant des
  lignes.
