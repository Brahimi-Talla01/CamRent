# Phase 5 — Baseline ML

Objectif (spec : `context/feature-specs/05-baseline-ml.md`) : établir des baselines
**mesurées** — moyenne globale, médiane par ville, médiane par quartier et type —
pour savoir si un modèle ML apporte réellement une valeur ajoutée. Aucun modèle
complexe n'est construit ici.

## Livrables

1. **Code** : `ml/src/` — `config`, `data` (lecture de `mart_ml_dataset`),
   `split` (séparation reproductible), `baselines` (les trois baselines + chaîne
   de repli), `evaluation` (MAE/RMSE/R², segments, IC bootstrap), `report`
   (rendu markdown dérivé), `run_baselines` + CLI `python -m ml.src baselines`.
2. **Rapport** : `docs/phase-5/baseline-report.md` (entièrement régénérable — aucun
   chiffre en dur) ; métriques brutes dans `ml/artifacts/` (ignoré par git).
3. **Tests** : `tests/unit/test_ml_{data,split,baselines,evaluation}.py`
   (**37 tests**) — valeurs apprises, chaîne de repli, métriques exactes,
   déterminisme de la séparation.

## Méthode

- **Source** : `analytics_marts.mart_ml_dataset` (Phase 4), cible
  `target_rent_price` en XAF.
- **Features** : `city`, `neighborhood`, `property_type`, `bedrooms`, `bathrooms`.
  Aucun drapeau de qualité n'est utilisé comme feature ; `rent_per_m2` est absent
  du mart (anti-leakage, Phase 4).
- **Séparation aléatoire 70 % / 15 % / 15 %**, graine fixe `20261009`. La
  séparation chronologique est impossible : `posted_at` est vide et `collected_at`
  couvre une seule journée de collecte (2026-10-09, 18 secondes d'écart).
- **Scénarios** (aucune exclusion silencieuse) : le scénario principal garde
  **toutes** les observations ; deux analyses de sensibilité sont étiquetées
  (`hors_republications`, `prix_exacts_sans_aberration`).
- **Baselines** :
  `baseline_global` (moyenne) ; `baseline_city` (médiane par ville) ;
  `baseline_neighborhood` (médiane par ville + quartier + type). Un groupe absent
  de l'entraînement bascule sur une chaîne de repli explicite
  (quartier+type → ville+type → ville → moyenne globale) et chaque prédiction est
  étiquetée par le niveau utilisé.

## Résultats (rejeu du 2026-10-13)

2 992 observations → 2 094 entraînement / 449 validation / 449 test.
175 triplets (ville, quartier, type), 139 quartiers distincts.

| Baseline | MAE validation | MedAE validation | R² validation | MAE test | MedAE test | R² test |
|---|---|---|---|---|---|---|
| `baseline_global` | 190 141 | 145 906 | −0,001 | 275 818 | 140 906 | −0,002 |
| `baseline_city` | 147 296 | 40 000 | −0,169 | 234 258 | 40 000 | −0,010 |
| **`baseline_neighborhood`** | **97 079** | **40 000** | **0,426** | **185 261** | 35 000 | 0,003 |

- La médiane par quartier et type divise la MAE par ~1,96 face à la moyenne
  globale en validation : la géographie et le type portent l'essentiel du signal.
- En validation, `baseline_neighborhood` a recours au repli pour 16 observations
  sur 449 (15 × ville+type, 1 × ville) — mesure du taux de repli, aucun repli
  silencieux.
- **Seuil de référence à battre** : MAE de validation < **79 773 FCFA**
  (borne basse de l'intervalle de confiance à 95 % de la MAE, 2 000 tirages
  bootstrap), soit **17,83 %** de mieux que `baseline_neighborhood`.
- Segments les plus difficiles pour la meilleure baseline (validation) :
  `Douala / Bonapriso` (N=38, MAE 336 579), quartile de prix **Q4** (N=113,
  MAE 258 274), `Douala / Akwa` (N=39, MAE 232 564), « 3 chambres » (N=97,
  MAE 133 918) ; les segments les mieux servis sont `Q1` (MAE 27 825) et `Douala / Makepe`
  (N=152, MAE 29 230).
- Scénarios de sensibilité — seuils à battre respectifs :
  `hors_republications` (N=991) → 115 721 FCFA (25,38 %) ;
  `prix_exacts_sans_aberration` (N=422) → 120 069 FCFA (32,01 %).

## Lecture et conclusion

- **Le ML est justifié à partir d'un gain réel** : un modèle n'est retenu que si
  sa MAE de validation passe sous 79 773 FCFA **et** si la réduction se confirme
  sur le test. En dessous, la baseline reste la référence du produit (et une API
  qui sert une médiane locale est déjà utile).
- **La MAE est instable sous cette distribution** : pour la meilleure baseline,
  la MAE passe de 97 079 (validation) à 185 261 FCFA (test), soit +90,8 %,
  alors que l'erreur médiane (MedAE) ne varie que de ~12 %. Quelques valeurs
  extrêmes conservées (invariant : aucune suppression) déplacent la MAE : c'est
  pourquoi le seuil est défini sur la borne basse de l'IC bootstrap et que la
  Phase 6 doit confirmer tout gain sur la MedAE et plusieurs graines.
- **La cible est approximative pour 2 564 observations sur 2 992** : elles ne
  portent qu'une borne inférieure de prix (« à partir de »). Le scénario
  `prix_exacts_sans_aberration` (N=422) donne une mesure plus fiable mais moins
  représentative — les deux sont rapportés.

## Invariants respectés

- Aucune exclusion silencieuse : toutes les observations sont évaluées dans le
  scénario principal ; républications, prix bornés et quartiers non reconnus
  restent présents et servent à définir les scénarios de sensibilité.
- Aucune statistique sans son **nombre d'observations** (global et par segment) ;
  les segments sous le seuil de publication (30 observations, décision Phase 3)
  sont **signalés** (`*`), jamais supprimés ni fusionnés.
- Zéro data leakage : pas de `rent_per_m2`, pas de feature dérivée de la cible,
  quartiles de prix calculés **sur l'entraînement** uniquement.
- Reproductibilité : graine fixe, métriques JSON **déterministes** (pas
  d'horodatage, md5 identique au rejeu), versions consignées dans le rapport.

## Hors périmètre (spec Phase 5)

- Aucun modèle d'ensemble ni boosting, aucun tuning d'hyperparamètres (Phase 6).
- Pas de MLflow (Phase 7) : runs simples, métriques sérialisées localement.

## Suites ouvertes

- `bathrooms` atteint 80 dans le Silver sans être signalé par `outlier_flags`
  (contrôle à reprendre côté Phase 2).
- Stratégie à figer en Phase 6 : pondération/exclusion explicite des prix bornés
  et des républications (les drapeaux sont exposés dans `mart_ml_dataset`).

  > Décision (2026-10-15, plan de réalignement) : **adapter la cible et l'intervalle** par une
  > expérience mesurée (lot E, décision 4) — plutôt que pondérer ou exclure.
