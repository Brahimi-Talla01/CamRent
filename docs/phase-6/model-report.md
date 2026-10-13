# Phase 6 — Rapport des modèles (ML)

**Généré le :** 2026-10-13 12:25 UTC

Objectif : tester les familles de modèles dans l'ordre recommandé et retenir
celui qui bat la baseline de la Phase 5 de façon **vérifiable**, en tenant
compte de la précision, de la robustesse, de l'interprétabilité et du coût.

## Protocole

- **Source :** `analytics_marts.mart_ml_dataset` (Phases 4-5), cible `target_rent_price` en XAF ; 2 992 observations.
- **Séparation :** identique à la Phase 5 — 70 % / 15 % / 15 %, graine `20261009` (séparation chronologique impossible : `posted_at` vide, collecte sur une seule journée).
- **Features :** `city`, `neighborhood`, `property_type`, `bedrooms`, `bathrooms`, `total_pieces`, `logements_dans_quartier`.
- **Cible transformée :** chaque famille est testée sur la cible brute et sur
  `log1p(cible)` : la distribution des loyers est très asymétrique (Phase 3),
  l'effet de la transformation doit donc être mesuré, pas supposé.
- **Échelle d'apprentissage :** la cible brute est apprise en **milliers de FCFA**
  (sinon une pénalité `alpha` serait négligeable face à des loyers de l'ordre de
  240 000 FCFA) ; prévisions et métriques sont reconverties en FCFA, donc la
  comparaison avec la baseline reste directe.
- **Hyperparamètres :** valeurs raisonnables **fixées**, aucune recherche — la
  phase compare des familles, elle n'optimise pas.
- **Métriques :** MAE (principale, en FCFA), RMSE, R², MedAE (robustesse),
  temps d'entraînement, performance par segment (toujours avec son effectif).

### Features écartées et pourquoi

| Feature | Raison de l'exclusion |
|---|---|
| `area_m2` | entièrement vide dans le Silver (Phase 3) |
| `furnished` | entièrement vide dans le Silver |
| `parking` | entièrement vide dans le Silver |
| `gated` | entièrement vide dans le Silver |
| `latitude` | absent des données collectées |
| `longitude` | absent des données collectées |
| `property_age` | aucune date de construction dans les annonces |
| `price_is_bound` | drapeau de qualité, pas une caractéristique du bien |
| `is_republication` | drapeau de qualité, pas une caractéristique du bien |
| `outlier_flags` | drapeau de qualité, pas une caractéristique du bien |
| `neighborhood_recognized` | drapeau de qualité, pas une caractéristique du bien |
| `rent_per_m2` | dérivée de la cible (data leakage, interdit) |

## Seuil de référence à battre (recalculé sur cette séparation)

| Baseline | Définition | MAE validation | MedAE validation | MAE test | IC 95 % MAE validation |
|---|---|---|---|---|---|
| `baseline_global` | moyenne des prix d'entraînement | 190 141 | 145 906 | 275 818 | 171 441 – 212 236 |
| `baseline_city` | médiane par ville | 147 296 | 40 000 | 234 258 | 123 242 – 175 399 |
| `baseline_neighborhood` | médiane par (ville, quartier, type de logement) | 97 079 | 40 000 | 185 261 | 79 773 – 116 491 |
| **seuil à battre** | borne basse de l'IC de `baseline_neighborhood` | 79 773 | — | — | — |

Règle héritée de la Phase 5 : battre la borne basse de l'intervalle de confiance
à 95 % de la MAE de la meilleure baseline, soit **79 773 FCFA** en validation (17.83 % de mieux que `baseline_neighborhood`).

## Comparaison des candidats

| Candidat | Famille | Cible | MAE entraînement | MAE validation | MedAE validation | MAE test | Temps d'entraînement |
|---|---|---|---|---|---|---|---|
| `gradient_boosting_log1p` | ensemble d'arbres (boosting) | log1p | 89 512 | 75 161 | 21 365 | 162 361 | 0.63 s |
| `lightgbm_log1p` | ensemble d'arbres (boosting) | log1p | 89 288 | 75 281 | 21 176 | 162 280 | 1.48 s |
| `random_forest_log1p` | ensemble d'arbres (bagging) | log1p | 84 880 | 75 425 | 20 710 | 159 130 | 0.29 s |
| `random_forest_brut` | ensemble d'arbres (bagging) | brut | 95 670 | 79 065 | 21 110 | 166 064 | 0.26 s |
| `ridge_log1p` | linéaire régularisé | log1p | 94 671 | 82 032 | 24 866 | 166 734 | 0.02 s |
| `linear_log1p` | linéaire | log1p | 91 174 | 82 169 | 24 695 | 165 525 | 0.03 s |
| `lightgbm_brut` | ensemble d'arbres (boosting) | brut | 100 277 | 83 021 | 24 862 | 172 409 | 1.45 s |
| `gradient_boosting_brut` | ensemble d'arbres (boosting) | brut | 100 491 | 83 195 | 24 997 | 173 868 | 0.86 s |
| `ridge_brut` | linéaire régularisé | brut | 110 681 | 96 560 | 37 241 | 183 116 | 0.02 s |
| `linear_brut` | linéaire | brut | 107 243 | 97 084 | 37 734 | 182 445 | 0.03 s |
| `lasso_brut` | linéaire régularisé | brut | 116 358 | 98 455 | 43 084 | 185 972 | 0.02 s |
| `lasso_log1p` | linéaire régularisé | log1p | 159 990 | 151 066 | 64 713 | 235 167 | 0.02 s |

Lecture : `brut` = cible brute, `log1p` = cible transformée. Le classement suit la
MAE de validation (métrique de décision).

## Modèle retenu

- **`random_forest_log1p`** — ensemble d'arbres (bagging), cible log1p.
- Critère appliqué : Deux étapes : (1) présélection des meilleurs candidats sur la MAE de validation de la graine de référence, puis (2) choix, parmi eux, de celui dont le **gain médian** face à la baseline recalculée sur chaque graine est le plus élevé (3 graines) ; en cas d'égalité, la MAE de la graine de référence départage. Le seuil de référence (79773 FCFA) et la MedAE sont ensuite vérifiés sur le candidat retenu — ils ne servent pas de critère de tri, la MAE n'étant pas comparable d'une séparation à l'autre.
- Présélection (MAE de la graine de référence) : `gradient_boosting_log1p`, `lightgbm_log1p`, `random_forest_log1p`.
- Rang du modèle retenu sur la graine de référence : 3 (le classement d'une seule séparation ne décide pas).
- MAE validation **75 425 FCFA** (MedAE 20 710) ; MAE test 159 130 FCFA (MedAE 20 710).
- Gain face à la meilleure baseline : **22.31 %** en validation (baseline `baseline_neighborhood` : 97 079 FCFA).
- Seuil **battu** sur la graine de référence (79 773 FCFA).
- Baseline battue sur **3 / 3** graines de robustesse (seuil battu sur 1 / 3) — gain **médian** 12.35 %, gain moyen 15.55 %, gain minimal 11.99 %.

| Ensemble | N | MAE | RMSE | R² | MedAE | p90 des erreurs |
|---|---|---|---|---|---|---|
| entraînement | 2 094 | 84 880 | 560 629 | 0.185 | 19 990 | 178 019 |
| validation | 449 | 75 425 | 195 073 | 0.554 | 20 710 | 192 615 |
| test | 449 | 159 130 | 1 892 032 | 0.008 | 20 710 | 150 793 |

Lecture produit (test) : 53.9 % des
prévisions tombent à ±20 % du loyer observé.

## Robustesse (autres séparations)

La Phase 5 a montré que la MAE est instable sous cette distribution : le
classement sur une seule séparation est donc du bruit. Les candidats
présélectionnés sont réévalués sur 3 graines ; le **gain médian** face à la baseline recalculée sur chaque graine décide.

| Candidat | Graines évaluées | MAE validation moyenne | MAE validation min | MAE validation max | Gain médian vs baseline | Gain moyen vs baseline | Gain minimal | Baseline battue sur | Seuil battu sur |
|---|---|---|---|---|---|---|---|---|---|
| `gradient_boosting_log1p` | 20261009, 7, 1234 | 129 697 | 75 161 | 170 724 | **11.43 %** | 15.09 % | 11.27 % | 3 / 3 | 1 / 3 |
| `lightgbm_log1p` | 20261009, 7, 1234 | 129 971 | 75 281 | 171 359 | **11.23 %** | 14.93 % | 11.10 % | 3 / 3 | 1 / 3 |
| `random_forest_log1p` | 20261009, 7, 1234 | 128 809 | 75 425 | 168 967 | **12.35 %** | 15.55 % | 11.99 % | 3 / 3 | 1 / 3 |

Le seuil est recalculé sur **chaque** graine : sans cela, on comparerait des
découpages de données plutôt que des modèles.

- Meilleure baseline sur la graine de référence : 97 079 FCFA en validation (185 261 en test).

## Performance par segment (modèle retenu)

Aucun segment n'est masqué : un `*` signale un effectif inférieur à 30 observations (seuil de publication de la Phase 3).

### Ville — validation

| Segment | N | MAE | MedAE | R² |
|---|---|---|---|---|
| Douala | 425 | 76 655 | 19 990 | 0.551 |
| Yaoundé * | 24 | 53 642 | 32 980 | 0.750 |

`*` effectif < 30 : à lire avec prudence.

### Ville — test

| Segment | N | MAE | MedAE | R² |
|---|---|---|---|---|
| Douala | 424 | 70 297 | 19 990 | 0.647 |
| Yaoundé * | 25 | 1 665 748 | 73 995 | -0.047 |

`*` effectif < 30 : à lire avec prudence.

### Type de logement — validation

| Segment | N | MAE | MedAE | R² |
|---|---|---|---|---|
| apartment | 437 | 71 428 | 20 710 | 0.597 |
| studio * | 11 | 235 987 | 16 112 | -0.248 |
| house * | 1 | 55 896 | 55 896 | — |

`*` effectif < 30 : à lire avec prudence.

### Type de logement — test

| Segment | N | MAE | MedAE | R² |
|---|---|---|---|---|
| apartment | 443 | 160 097 | 20 601 | 0.007 |
| studio * | 5 | 100 519 | 21 256 | -0.590 |
| room * | 1 | 23 955 | 23 955 | — |

`*` effectif < 30 : à lire avec prudence.

### Nombre de chambres — validation

| Segment | N | MAE | MedAE | R² |
|---|---|---|---|---|
| 2 chambre(s) | 241 | 67 351 | 19 990 | 0.602 |
| 1 chambre(s) | 108 | 41 305 | 12 606 | 0.096 |
| 3 chambre(s) | 97 | 105 357 | 46 359 | 0.597 |
| 4 chambre(s) * | 2 | 1 313 975 | 1 313 975 | -0.626 |
| inconnu * | 1 | 325 876 | 325 876 | — |

`*` effectif < 30 : à lire avec prudence.

### Nombre de chambres — test

| Segment | N | MAE | MedAE | R² |
|---|---|---|---|---|
| 2 chambre(s) | 265 | 207 637 | 19 720 | -0.005 |
| 3 chambre(s) | 91 | 130 439 | 63 974 | 0.602 |
| 1 chambre(s) | 88 | 31 218 | 11 252 | 0.299 |
| 4 chambre(s) * | 5 | 361 730 | 57 703 | 0.633 |

`*` effectif < 30 : à lire avec prudence.

### Niveau de prix (quartiles d'entraînement) — validation

| Segment | N | MAE | MedAE | R² |
|---|---|---|---|---|
| Q1 | 146 | 15 296 | 8 299 | -1.997 |
| Q4 | 113 | 218 855 | 138 536 | 0.077 |
| Q3 | 103 | 48 099 | 30 710 | -10.417 |
| Q2 | 87 | 22 389 | 11 701 | -50.138 |

### Niveau de prix (quartiles d'entraînement) — test

| Segment | N | MAE | MedAE | R² |
|---|---|---|---|---|
| Q3 | 136 | 40 190 | 28 803 | -3.543 |
| Q1 | 134 | 14 866 | 7 606 | -2.113 |
| Q4 | 104 | 602 359 | 121 122 | -0.034 |
| Q2 | 75 | 17 951 | 11 701 | -20.497 |

### Quartier (ville / quartier) — validation

| Segment | N | MAE | MedAE | R² |
|---|---|---|---|---|
| Douala / Makepe | 152 | 20 086 | 11 701 | 0.482 |
| Douala / Logpom | 58 | 17 846 | 11 733 | 0.519 |
| Douala / Bonamoussadi | 46 | 55 465 | 14 659 | 0.161 |
| Douala / Akwa | 39 | 208 698 | 157 800 | 0.087 |
| Douala / Bonapriso | 38 | 253 480 | 138 536 | 0.186 |
| Douala / Malangue * | 16 | 801 | 246 | 0.960 |
| Douala / Kotto * | 15 | 32 733 | 25 060 | 0.491 |
| Douala / Bali * | 14 | 166 089 | 114 408 | 0.081 |
| Douala / Ndogbong * | 7 | 30 507 | 17 709 | 0.059 |
| Douala / Bonanjo * | 7 | 155 047 | 133 603 | -0.106 |

`*` effectif < 30 : à lire avec prudence.

### Quartier (ville / quartier) — test

| Segment | N | MAE | MedAE | R² |
|---|---|---|---|---|
| Douala / Makepe | 152 | 23 354 | 10 010 | 0.360 |
| Douala / Bonamoussadi | 54 | 32 255 | 18 965 | 0.610 |
| Douala / Logpom | 48 | 24 501 | 17 757 | 0.289 |
| Douala / Akwa | 36 | 145 075 | 97 200 | 0.227 |
| Douala / Bonapriso | 30 | 240 663 | 120 278 | -0.026 |
| Douala / Malangue * | 15 | 1 952 | 246 | 0.808 |
| Douala / Kotto * | 15 | 24 279 | 22 939 | 0.394 |
| Douala / Bali * | 15 | 103 591 | 76 824 | 0.634 |
| Douala / Bonanjo * | 11 | 341 864 | 112 431 | 0.502 |
| Douala / Ndogbong * | 9 | 47 899 | 17 709 | -0.255 |

`*` effectif < 30 : à lire avec prudence.

## Fourchette de prédiction

| Méthode | Couverture validation | Largeur médiane validation | Largeur moyenne validation | Couverture test | Largeur médiane test | Largeur moyenne test |
|---|---|---|---|---|---|---|
| `split_conformal` | 90.0 % | 302 604 | 313 410 | 92.7 % | 302 604 | 316 730 |
| `quantile_regression` | 90.7 % | 116 998 | 309 512 | 90.7 % | 135 995 | 326 838 |

Niveau visé : **90 %** (alpha = 0.1). Méthode retenue : `quantile_regression`.

Parmi les méthodes couvrant au moins le niveau visé (90 % de validation), la fourchette la plus étroite (largeur médiane) est retenue ; la couverture de test sert de vérification, jamais de réglage.

- Couverture observée en test : 90.7 % (validation : 90.7 %).
- Largeur moyenne en test : 326 838 FCFA (médiane 135 995 FCFA).

## Explicabilité

### Importance globale des facteurs (validation)

Augmentation de l'**erreur médiane** lorsque la variable est permutée : plus la
valeur est élevée, plus le modèle s'appuie sur la variable. Cette mesure
remplace l'importance sur la MAE, qui devient instable — voire négative — dès
que quelques loyers extrêmes conservés dominent l'erreur moyenne.

| Feature | N | Erreur médiane supplémentaire | Écart-type | Min | Max |
|---|---|---|---|---|---|
| `neighborhood` | 449 | 33 756 | 6 622 | 23 398 | 45 686 |
| `bedrooms` | 449 | 14 190 | 2 277 | 11 571 | 17 826 |
| `bathrooms` | 449 | 10 182 | 1 064 | 8 864 | 12 064 |
| `city` | 449 | 1 070 | 319 | 529 | 1 684 |
| `property_type` | 449 | 990 | 187 | 649 | 1 160 |

### Effet du nombre de chambres (dépendance partielle, test)

| Valeur | N | Prévision moyenne | Prévision médiane |
|---|---|---|---|
| 1.00 | 449 | 121 780 | 81 396 |
| 2.00 | 449 | 180 939 | 109 990 |
| 3.00 | 449 | 237 719 | 138 690 |
| 4.00 | 449 | 274 969 | 183 303 |

### Effet du nombre de salles de bain (dépendance partielle, test)

| Valeur | N | Prévision moyenne | Prévision médiane |
|---|---|---|---|
| 1.00 | 449 | 131 218 | 85 763 |
| 2.00 | 449 | 190 877 | 122 291 |
| 3.00 | 449 | 257 003 | 158 448 |
| 4.00 | 449 | 305 710 | 180 968 |

### Exemple expliqué (« pourquoi ce prix ? »)

- Annonce : Makepe (Douala), apartment, 3 chambre(s), 2 salle(s) de bain.
- Prévision : **127 115 FCFA** (fourchette 80 000 – 215 995 FCFA).
- Loyer observé dans l'annonce : 120 000 FCFA.
- Marché local (entraînement) : médiane **80 000 FCFA** sur 721 observation(s) de ce (quartier, type) — publiée : oui ; médiane ville 100 000 FCFA sur 1 962 observations.
- Écart de la prévision à la médiane locale : 58.89 %.

## Compromis par famille

| Candidat | Famille | Complexité | Interprétabilité | MAE validation | Temps d'entraînement |
|---|---|---|---|---|---|
| `gradient_boosting_log1p` | ensemble d'arbres (boosting) | moyenne | importance par permutation | 75 161 | 0.63 s |
| `lightgbm_log1p` | ensemble d'arbres (boosting) | moyenne | importance par permutation | 75 281 | 1.48 s |
| `random_forest_log1p` | ensemble d'arbres (bagging) | moyenne | importance par permutation | 75 425 | 0.29 s |
| `random_forest_brut` | ensemble d'arbres (bagging) | moyenne | importance par permutation | 79 065 | 0.26 s |
| `ridge_log1p` | linéaire régularisé | très faible | coefficients lisibles | 82 032 | 0.02 s |
| `linear_log1p` | linéaire | très faible | coefficients directement lisibles | 82 169 | 0.03 s |
| `lightgbm_brut` | ensemble d'arbres (boosting) | moyenne | importance par permutation | 83 021 | 1.45 s |
| `gradient_boosting_brut` | ensemble d'arbres (boosting) | moyenne | importance par permutation | 83 195 | 0.86 s |
| `ridge_brut` | linéaire régularisé | très faible | coefficients lisibles | 96 560 | 0.02 s |
| `linear_brut` | linéaire | très faible | coefficients directement lisibles | 97 084 | 0.03 s |
| `lasso_brut` | linéaire régularisé | très faible | coefficients lisibles, sélection de variables | 98 455 | 0.02 s |
| `lasso_log1p` | linéaire régularisé | très faible | coefficients lisibles, sélection de variables | 151 066 | 0.02 s |

## Limites du modèle

- **Cible approximative pour 2 564 observations sur 2 992** : ces annonces ne donnent qu'une borne
  inférieure de prix (« à partir de ») ; aucune méthode ne peut corriger cela.
- **Républications** : 2 001 observations signalées,
  réparties aléatoirement — des annonces quasi identiques peuvent se retrouver
  en entraînement et en test, ce qui rend l'évaluation optimiste.
- **Quartiers non reconnus** : 101 observations
  portent un libellé hors référentiel ; le modèle s'appuie alors sur la ville et le
  type (profondeur de marché nulle pour ces quartiers).
- **Features indisponibles** : surface, meublé, parking, barrière (vides dans le
  Silver) et coordonnées géographiques (absentes) : la précision est plafonnée par
  l'information collectée, pas par le choix du modèle.
- **Hyperparamètres non optimisés** : une recherche systématique (et son suivi
  MLflow) relève de la Phase 7.
- **MAE instable** : la borne basse de l'IC bootstrap sert de seuil ; les décisions
  produit ne doivent pas être prises sur une différence inférieure à cette marge.
- Une estimation n'est jamais une valeur officielle du bien (invariant 9) et doit
  toujours être présentée avec sa fourchette et le nombre d'observations local.

## Reproductibilité

```bash
python -m pipelines silver --report docs/phase-2/cleaning-report.md
python -m pipelines load
cd dbt && dbt build && cd ..
python -m ml.src baselines
python -m ml.src models
```

Versions : Python 3.14.4, scikit-learn 1.9.1, pandas 3.0.6, numpy 2.5.3, LightGBM 4.7.0 ; graines de robustesse 20261009, 7, 1234.

Artefacts (ignorés par git, régénérables) :

| Artefact | Chemin |
|---|---|
| modele | `ml/models/rent_model_v1.joblib` |
| metadonnees | `ml/models/rent_model_v1.json` |
| intervalle | `ml/models/rent_model_v1_intervalle.joblib` |
| selection | `ml/models/model_selection.json` |
| rapport | `docs/phase-6/model-report.md` |
