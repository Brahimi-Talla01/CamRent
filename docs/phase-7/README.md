# Phase 7 — Model registry (MLflow)

Objectif (spec : `context/feature-specs/07-model-registry.md`) : tracer les
expériences et versionner les modèles, pour ne pas choisir un modèle « sur la
base d'une impression ». Chaque run consigne le dataset, les features, les
hyperparamètres, les métriques, la version du code et la date ; le modèle retenu
est enregistré sous une version explicite (`rent-model-vN`), et une règle de
promotion écrite décide de ce qui est servable.

## Livrables

1. **Code** : `ml/src/` — `tracking` (runs MLflow), `registry` (version +
   règle de promotion), `registry_report` (rendu dérivé), `run_registry`
   (orchestration), sous-commande CLI `python -m ml.src registry`.
2. **Rapport** : `docs/phase-7/registry-report.md` (entièrement régénérable —
   aucun chiffre en dur, mot de passe masqué).
3. **Registre** : expérience MLflow `rent_prediction` (12 runs) et modèle
   `rent-model-v1` (`alias champion`) — vivent dans une base PostgreSQL dédiée
   `mlflow`, non versionnée.
4. **Tests** : `tests/unit/test_ml_{tracking,registry}.py` (**14 tests**) —
   résolution de l'URI, déterminisme de la version du dataset, journalisation
   des runs, enregistrement, règle de promotion, refus d'un backend sans base.

## Méthode

- **Source des runs** : les résultats de la Phase 6 (`run_models.build_results`),
  sur la **même séparation** (70/15/15, graine `20261009`) — les 12 candidats
  sont journalisés, pas seulement le retenu.
- **Par run** : nom/version du modèle, dataset/version, features,
  hyperparamètres, métriques MAE/RMSE/R² (+ MedAE, P90, prix moyen observé) sur
  entraînement/validation/test, **métriques par segment** (artefact
  `segments_validation.json` — ville, type, chambres, niveau de prix, quartier),
  version du code et date. Le run du modèle retenu porte aussi le nom de la
  version enregistrée (`modele_enregistre`).
- **Backend** : une base PostgreSQL **dédiée** `mlflow` est dérivée de
  `DATABASE_URL` (le registre ne mélange pas ses tables avec celles de
  l'application). Un backend SQLite sert aux tests ; un file store local sert de
  repli hors-ligne (mais **ne supporte pas** le Model Registry — l'erreur est
  explicite).
- **Version du dataset** : identifiant documenté — hash MD5 du contenu
  (`listing_key` + cible) + nombre d'observations. DVC / lakeFS ne sont pas
  introduits : les volumes du MVP ne les justifient pas.
- **Version du code** : SHA Git, branche et état « modifié », consignés dans
  chaque run (pas dans le rapport, qui ne peut pas référencer son propre commit).
- **Dépendances** : `mlflow-skinny` (+ `alembic` pour le store SQLAlchemy et
  `skops` pour la sérialisation sklearn) plutôt que `mlflow` complet — le
  serveur/UI et ses 50 Mo de `pyarrow` ne servent pas au suivi ni au registre.
- **Sérialisation** : `cloudpickle` et non `skops` pour le modèle retenu, car
  `TransformedTargetRegressor` porte des ufuncs numpy (`log1p`/`expm1`) que skops
  refuse ; le modèle est le nôtre, ce qui rend cloudpickle acceptable.

## Règle de promotion

Un modèle est promu (`alias champion`, donc servable) uniquement si **toutes**
les conditions sont satisfaites :

1. **`bat_la_baseline`** — gain > 0 face à `baseline_neighborhood` sur la graine
   de référence **et** baseline battue sur toutes les séparations de robustesse ;
2. **`seuil_phase_5`** — MAE de validation sous la borne basse de l'IC 95 %
   (seuil de la Phase 5) ;
3. **`reproductible`** — confirmé sur au moins deux séparations, version du code
   et version du dataset consignées dans le run.

La promotion est **explicite** : aucun déploiement automatique.

## Résultats (rejeu du 2026-10-14)

- Expérience `rent_prediction` : **12 runs** (6 familles × cible brute/`log1p`).
- Dataset : `mart_ml_dataset@21774b224bdb` — 2 992 observations.
- Modèle retenu (issu de la Phase 6) : `random_forest_log1p` — MAE validation
  75 425 FCFA (seuil 79 773), gain **22,31 %**.
- Décision de promotion : **promu** — les trois conditions satisfaites
  (baseline battue 3/3, seuil franchi, 3 séparations évaluées).
- Modèle enregistré : **`rent-model-v1`**, alias `champion`.

## Invariants respectés

- Aucun modèle déployable sans être **enregistré et versionné**.
- Aucun **secret** dans le rapport : l'URI est masquée (le rapport est versionné).
- Reproductibilité : dataset (hash) et code consignés par run ; le modèle
  enregistré est rejouable à partir de son run.
- Aucune exclusion silencieuse : les 12 candidats sont journalisés, y compris
  ceux écartés.

## Limites

- Le registre vit dans PostgreSQL local : il n'est pas versionné par Git (par
  construction) ; le livrable reproductible reste le rapport et le code.
- Pas de serveur MLflow ni d'UI (non nécessaires au MVP) ; `mlflow ui` peut être
  lancé ponctuellement pour l'inspection.
- Combiné à la Phase 6 : la cible est approximative pour 2 564 observations sur
  2 992 (prix bornés) — le registre trace les runs, il ne corrige pas la donnée.

## Reproductibilité

```bash
# identifiants locaux du docker-compose (voir ml/README.md)
export DATABASE_URL=postgresql://camrent:<mot-de-passe>@localhost:5433/camrent
# base de registre dédiée (une fois)
createdb -h localhost -p 5433 -U camrent mlflow
# Phase 6 puis Phase 7
python -m ml.src models
python -m ml.src registry
```

## Suites ouvertes

- Brancher l'API (Phase 8) sur `models:/rent-model@champion`.
- Étudier l'automatisation du ré-entraînement et la politique de rétention des
  runs (Phase 10/11).
