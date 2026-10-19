# Phase 4 — Data warehouse / marts

Objectif (spec : `context/feature-specs/04-data-marts.md`) : construire les
tables analytiques (Gold) à partir du Silver, prêtes pour l'analyse, l'API
(Phase 8) et le ML (Phases 5-6).

## Livrables

1. **Chargement du Silver dans PostgreSQL** : `pipelines/db.py` +
   `python -m pipelines load` → table d'atterrissage
   `landing.silver_listings` (idempotent : la table est **vidée** (`TRUNCATE`)
   puis remplie, jamais droppée — les vues dbt qui en dépendent survivent au
   rejeu ; la source de vérité du Silver reste
   `data/processed/silver_listings.parquet`, rejouable).
2. **Projet dbt** (`dbt/`) : transformations SQL versionnées ;
   chaîne `stg_listings` / `stg_quarantine` / `stg_ingestion_runs` →
   `int_clean_listings` → faits/dims → marts.
3. **Tables** :
   - atterrissage (`landing`, créé hors dbt) : `silver_listings`,
     `quarantine_listings` (rejets de la Phase 2) et `ingestion_runs`
     (métadonnées et provenance des lots) — les deux dernières ajoutées par le
     **lot B** ;
   - dimensions : `dim_city`, `dim_neighborhood`, `dim_property_type`,
     `dim_date` (dates observées, pas de calendrier artificiel) ;
   - faits : `fct_rent_observations`, `fct_listings` ;
   - marts : `mart_neighborhood_prices`, `mart_city_prices`,
     `mart_property_prices`, `mart_data_quality`, `mart_ingestion_lots`,
     `mart_ml_dataset`.
4. **Tests dbt** : not_null, unique, relationships (faits → dims),
   accepted_values — `dbt/models/marts/marts_schema.yml`.
5. **Data Catalog** : `data-catalog.md` (description, grain, source,
   fréquence, owner, sensibilité, qualité pour chaque dataset).
6. **Tests dbt de conformité** : bornes inclusives (`within_range`, macro
   `dbt/macros/tests/within_range.sql`) sur les prix, chambres et volumes ;
   relations faits → dims complètes (ville, type, date, plus la paire
   ville/quartier par test singulier) ; invariant de publication des médianes
   gardé par `dbt/tests/assert_median_published_only_at_or_above_threshold.sql`.
7. **Qualité de marché exposée (2026-10-19, préparation du ticket #53)** : les trois
   marts de prix portent désormais le volume **et** la part des prix bornés et des
   republications (`n_price_bound` / `pct_price_bound`, `n_republication` /
   `pct_republication`) ; `mart_city_prices` ajoute les quartiers non reconnus, et
   `mart_property_prices` reçoit p10/p90 pour un contrat d'API homogène. Aucune
   ligne n'est exclue : ces colonnes quantifient les biais au lieu de les masquer.
8. **Qualité et provenance en base (lot B, 2026-10-16)** : la quarantaine et les
   métadonnées de collecte sont chargées dans `landing`, puis exposées par
   `mart_data_quality` (motifs de rejet agrégés par source) et
   `mart_ingestion_lots` (lots, version de connecteur, empreinte de contenu,
   statut de validation). `mart_ml_dataset` expose en outre `rent_semantics`
   (`asking_rent` / `unknown`).

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

## Résultats de la construction (rejeu du 2026-10-13)

Base : PostgreSQL 16 (docker-compose, PostgreSQL système déjà occupant 5432 → port **5433**), dbt-core 1.12.5 + dbt-postgres 1.11.0.

Schémas réels en base : `analytics_staging`, `analytics_intermediate`,
`analytics_marts` (dbt préfixe le schéma de profil `analytics`) ; la table
d'atterrissage est dans `landing`, créée hors dbt.

| Étape | Résultat |
|---|---|
| `python -m pipelines load` | **2 992 lignes** → `landing.silver_listings` |
| `dbt build` | **95/95 PASS** : 12 modèles (2 vues + 10 tables) + **83 tests dbt** (not_null, unique, relationships, accepted_values, bornes `within_range`, 2 tests singuliers) |

> **Rejeu du lot B (2026-10-16)** — voir la section dédiée plus bas :
> `python -m pipelines load` charge désormais **3 tables** d'atterrissage
> (`silver_listings` 2 992 · `quarantine_listings` 78 · `ingestion_runs` 3 lots) et
> `dbt build` passe **137/137** (16 modèles, 121 tests dont 6 tests singuliers).
> Les chiffres du tableau ci-dessus restent ceux du rejeu du 2026-10-13.
| Grain fat/dim/mart | cohérent : 2 992 lignes de landing à `mart_ml_dataset` |
| `mart_city_prices` | Douala N=2 811 méd. 100 000 · Yaoundé N=181 méd. 150 000 (conforme EDA Phase 3) |
| `mart_neighborhood_prices` | 253 groupes (ville, quartier, type, chambres) ; médiane **null sous N<30** (0 violation : 0 publiée sous 30, 0 absente à ≥ 30) |
| Anomalies signalées, jamais supprimées | 101 quartiers non reconnus, 2 001 républications, 2 564 prix bornés, 17 aberrations (lignes conservées + drapeaux) |

À noter : deux lignes aux prix extrêmes (`rent_price` = 1 FCFA → Douala ; 50 FCFA →
Yaoundé) restent dans les faits avec `price_outlier` — elles sont signalées,
conformément aux invariants (pas de suppression silencieuse).

Rejeu du chargement vérifié : `python -m pipelines load` exécuté deux fois → la
table reste à **2 992 lignes** (vidage puis réinsertion, pas de doublon), et
`dbt build` rejoué juste après le chargement passe **95/95** (les vues `staging`
ne sont plus cassées par un `DROP` de la table d'atterrissage).

## Rejeu du lot B — qualité et provenance (2026-10-16)

| Étape | Résultat |
|---|---|
| `python -m pipelines load` | `landing.silver_listings` **2 992** · `landing.quarantine_listings` **78** · `landing.ingestion_runs` **3 lots** |
| `dbt build` | **137/137 PASS** : 16 modèles (4 vues + 12 tables) + **121 tests** dont **6 tests singuliers** |
| `mart_data_quality` | 4 lignes (source `reference_local` × 4 motifs) : `prix_manquant` 52, `type_inconnu` 18, `city_inconnue` 7, `prix_invalide` 1 = **78 rejets** (réconciliés avec la quarantaine) |
| `mart_ingestion_lots` | 3 lots (koutchoumi 5 · geloka 8 · reference_local 3 065 observations) ; `has_provenance = false` pour ces trois lots antérieurs à la provenance renforcée — absence **signalée**, pas inventée |
| `mart_ml_dataset` | `rent_semantics` = `asking_rent` sur les **2 992** lignes (aucune valeur nulle) ; cible toujours `target_rent_price` (non renommée) |
| Volumes inchangés | 2 992 lignes de `landing` à `mart_ml_dataset` ; invariant de publication intact (234 médianes non publiées sur 253 groupes, plus petit N publié = 31) |

Contrôle négatif du test de bornes : `dbt test --select assert_implausible_rooms_are_signalled --vars '{rooms_max_plausible: 0}'` remonte 2 987 lignes et **échoue** — le test n'est pas vide, il détecte bien une rupture de la règle de signalement.

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
  `target_rent_price` = rent_price (prix demandé dans l'annonce), avec sa
  sémantique explicite (`rent_semantics`).
- Les **rejets** et la **provenance des lots** sont interrogeables en base
  (`quarantine_listings`, `ingestion_runs`) et exposés en marts : la qualité
  cesse d'être un artefact local non vérifiable (lot B).

## Hors périmètre (spec Phase 4)

- Pas de Data Warehouse (BigQuery/Snowflake/Redshift) : PostgreSQL suffit.
- Pas de MongoDB.
- Pas de logique ML ici : `mart_ml_dataset` expose les features et la cible.
