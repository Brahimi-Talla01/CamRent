# Phase 7 — Rapport du registre de modèles (MLflow)

**Généré le :** 2026-10-14 08:13 UTC

Objectif : tracer chaque expérience et versionner le modèle retenu, pour ne pas choisir un modèle « sur la base d'une impression » — et n'en déployer aucun qui ne soit enregistré (spec `context/feature-specs/07-model-registry.md`).

## Protocole

- **Expérience :** `rent_prediction` (identifiant `3`).
- **URI de suivi :** `postgresql+psycopg://camrent:***@localhost:5433/mlflow`.
- **Runs journalisés :** 12 candidats de la Phase 6 (chaque famille × transformation de cible).
- **Dataset :** `analytics_marts.mart_ml_dataset` — 2 992 observations, version `mart_ml_dataset@21774b224bdb` (hash du contenu).
- **Version du code :** consignée dans chaque run (SHA Git + versions logicielles, ex. Python 3.14.4, scikit-learn 1.9.1).
- **Cible :** `target_rent_price` en XAF, graine `20261009`.

## Runs journalisés

| Candidat | Famille | Cible | MAE entraînement | MAE validation | MAE test | Run |
|---|---|---|---|---|---|---|
| `gradient_boosting_log1p` | ensemble d'arbres (boosting) | log1p | 89 512 | 75 161 | 162 361 | `76fc6e11` |
| `lightgbm_log1p` | ensemble d'arbres (boosting) | log1p | 89 288 | 75 281 | 162 280 | `2f07ff09` |
| `random_forest_log1p` | ensemble d'arbres (bagging) | log1p | 84 880 | 75 425 | 159 130 | `c04e80d7` |
| `random_forest_brut` | ensemble d'arbres (bagging) | brut | 95 670 | 79 065 | 166 064 | `cd44d510` |
| `ridge_log1p` | linéaire régularisé | log1p | 94 671 | 82 032 | 166 734 | `eb4062b9` |
| `linear_log1p` | linéaire | log1p | 91 174 | 82 169 | 165 525 | `6be8d62f` |
| `lightgbm_brut` | ensemble d'arbres (boosting) | brut | 100 277 | 83 021 | 172 409 | `952e6cdb` |
| `gradient_boosting_brut` | ensemble d'arbres (boosting) | brut | 100 491 | 83 195 | 173 868 | `29faa5cf` |
| `ridge_brut` | linéaire régularisé | brut | 110 681 | 96 560 | 183 116 | `37149eeb` |
| `linear_brut` | linéaire | brut | 107 243 | 97 084 | 182 445 | `876253b8` |
| `lasso_brut` | linéaire régularisé | brut | 116 358 | 98 455 | 185 972 | `a9bfd4cb` |
| `lasso_log1p` | linéaire régularisé | log1p | 159 990 | 151 066 | 235 167 | `3263b4bd` |

## Modèle enregistré

- **Étiquette :** `rent-model-v1` (nom `rent-model`, version 1).
- **Alias :** `champion`
- **Run source :** `c04e80d703874fbaa3d7e59983614d5d`.
- **Promu :** True.

## Règle de promotion

Un modèle est promu (alias `champion`) uniquement si **toutes** les conditions suivantes sont satisfaites :

- ✅ **bat_la_baseline** — gain 22.31 % sur la graine de référence ; baseline battue sur 3/3 séparations.
- ✅ **seuil_phase_5** — MAE validation 75425 FCFA vs seuil 79773 FCFA (baseline_neighborhood).
- ✅ **reproductible** — 3 séparations évaluées ; version du code et version du dataset journalisées dans le run.

**Décision :** promu.

La promotion rend le modèle servable (`alias champion`) ; elle est **explicite** : aucun déploiement automatique.

## Reproductibilité

Chaque run conserve la version du dataset (hash), la version du code, les features, les hyperparamètres et les métriques des trois ensembles : le modèle enregistré est rejouable à partir de son run.

```bash
# identifiants locaux du docker-compose (voir ml/README.md) :
export DATABASE_URL=postgresql://camrent:<mot-de-passe>@localhost:5433/camrent
# base de registre dédiée (une fois) :
#   createdb -h localhost -p 5433 -U camrent mlflow
python -m ml.src registry
```
