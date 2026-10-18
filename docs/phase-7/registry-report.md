# Phase 7 — Rapport du registre de modèles (MLflow)

**Généré le :** 2026-10-18 15:04 UTC

Objectif : tracer chaque expérience et versionner le modèle retenu, pour ne pas choisir un modèle « sur la base d'une impression » — et n'en déployer aucun qui ne soit enregistré (spec `context/feature-specs/07-model-registry.md`).

## Protocole

- **Expérience :** `rent_prediction` (identifiant `3`).
- **URI de suivi :** `postgresql+psycopg://camrent:***@localhost:5433/mlflow`.
- **Runs journalisés :** 12 candidats de la Phase 6 (chaque famille × transformation de cible).
- **Dataset :** `analytics_marts.mart_ml_dataset` — 2 992 observations, version `mart_ml_dataset@d3c11c225f48` (hash de tout le contenu : schéma et valeurs).
- **Version du code :** consignée dans chaque run (SHA Git + versions logicielles, ex. Python 3.14.4, scikit-learn 1.9.1).
- **Cible :** `target_rent_price` en XAF, graine `20261009`.

## Runs journalisés

| Candidat | Famille | Cible | MAE entraînement | MAE validation | MAE test | Run |
|---|---|---|---|---|---|---|
| `gradient_boosting_log1p` | ensemble d'arbres (boosting) | log1p | 89 512 | 75 161 | 162 361 | `ac1b1263` |
| `lightgbm_log1p` | ensemble d'arbres (boosting) | log1p | 89 288 | 75 281 | 162 280 | `afe9e3e0` |
| `random_forest_log1p` | ensemble d'arbres (bagging) | log1p | 84 880 | 75 425 | 159 130 | `77c7bf49` |
| `random_forest_brut` | ensemble d'arbres (bagging) | brut | 95 670 | 79 065 | 166 064 | `3eb4f97b` |
| `ridge_log1p` | linéaire régularisé | log1p | 94 671 | 82 032 | 166 734 | `205364e5` |
| `linear_log1p` | linéaire | log1p | 91 174 | 82 169 | 165 525 | `a40347b2` |
| `lightgbm_brut` | ensemble d'arbres (boosting) | brut | 100 277 | 83 021 | 172 409 | `9c5a3809` |
| `gradient_boosting_brut` | ensemble d'arbres (boosting) | brut | 100 491 | 83 195 | 173 868 | `8f51b8e6` |
| `ridge_brut` | linéaire régularisé | brut | 110 681 | 96 560 | 183 116 | `c4510be4` |
| `linear_brut` | linéaire | brut | 107 243 | 97 084 | 182 445 | `548899ab` |
| `lasso_brut` | linéaire régularisé | brut | 116 358 | 98 455 | 185 972 | `e9cb6374` |
| `lasso_log1p` | linéaire régularisé | log1p | 159 990 | 151 066 | 235 167 | `3788ea21` |

## Modèle enregistré

- **Étiquette :** `rent-model-v4` (nom `rent-model`, version 4).
- **Alias :** `champion`
- **Run source :** `77c7bf49fb21431e882d6e98a9b43175`.
- **Promu :** True.
- **Approbation :** Ibrahim Talla (2026-10-18T15:04:08+00:00)
- **Version servie épinglée :** `ml/models/champion.json`

## Règle de promotion

Un modèle est promu (alias `champion`) uniquement si **toutes** les conditions suivantes sont satisfaites **et** si la promotion est **approuvée explicitement** par un administrateur (`--confirm-promotion --approved-by <nom>`) :

- ✅ **bat_la_baseline** — gain 22.31 % sur la graine de référence ; baseline battue sur 3/3 séparations.
- ✅ **seuil_phase_5** — MAE validation 75425 FCFA vs seuil 79773 FCFA (baseline_neighborhood).
- ✅ **reproductible** — 3 séparations évaluées ; version du code et version du dataset journalisées dans le run.

**Décision automatique :** promouvable.

L'alias de référence n'est jamais déplacé automatiquement : sans approbation nominative, aucune version ne devient servable.

La promotion rend le modèle servable (`alias champion`) ; elle est **explicite** : aucun déploiement automatique.

## Reproductibilité

Chaque run conserve la version du dataset (hash), la version du code, les features, les hyperparamètres et les métriques des trois ensembles : le modèle enregistré est rejouable à partir de son run.

```bash
# identifiants locaux du docker-compose (voir ml/README.md) :
export DATABASE_URL=postgresql://camrent:<mot-de-passe>@localhost:5433/camrent
# base de registre dédiée (une fois) :
#   createdb -h localhost -p 5433 -U camrent mlflow
# la promotion est nominative (rôle administrateur) :
python -m ml.src registry --confirm-promotion --approved-by <nom>
```
