# Phase 5 — Rapport des baselines (ML)

**Généré le :** 2026-10-13 06:55 UTC

Baselines mesurées avant tout modèle : elles fixent le niveau à battre et
répondent à une seule question — un modèle ML apporte-t-il un gain réel ?

## Méthode

- **Source :** `analytics_marts.mart_ml_dataset` (Phase 4), cible `target_rent_price` en XAF.
- **Observations :** 2 992, 139 quartiers distincts, 175 triplets (ville, quartier, type).
- **Features d'entrée :** `city`, `neighborhood`, `property_type`, `bedrooms`, `bathrooms`.
- **Drapeaux qualité (jamais des features) :** `price_is_bound`, `is_republication`, `outlier_flags`, `neighborhood_recognized`.

### Qualité des données (aucune exclusion silencieuse)

| Marqueur | Observations |
|---|---|
| Prix borné (borne inférieure, « à partir de ») | 2 564 |
| Républication | 2 001 |
| Aberration signalée (`outlier_flags`) | 17 |
| Quartier non reconnu | 101 |
| Chambres manquantes | 5 |
| Salles de bain manquantes | 6 |

Ces marqueurs ne filtrent rien dans le scénario principal : ils décrivent le
dataset et alimentent les scénarios de sensibilité.

### Séparation entraînement / validation / test

- Proportions : 70 % entraînement, 15 % validation, 15 % test — graine fixe `20261009` (reproductible).
- Séparation **aléatoire**, pas chronologique : `posted_at` renseigné sur 0 observation(s) et `collected_at` couvrant 1 journée(s) de collecte — aucune information temporelle exploitable.

| Ensemble | Observations | Part | Douala | Yaoundé | Républications | Prix bornés | Aberrations |
|---|---|---|---|---|---|---|---|
| entraînement | 2 094 | 70.0 % | 1 962 | 132 | 1 384 | 1 782 | 12 |
| validation | 449 | 15.0 % | 425 | 24 | 317 | 393 | 3 |
| test | 449 | 15.0 % | 424 | 25 | 300 | 389 | 2 |

### Baselines

| Baseline | Définition | Groupes appris | Repli |
|---|---|---|---|
| `baseline_global` | moyenne des prix d'entraînement | 1 | — |
| `baseline_city` | médiane par ville | 2 | `baseline_global` |
| `baseline_neighborhood` | médiane par (ville, quartier, type de logement) | 145 | `baseline_city_type` |

Une baseline de groupe ne connaît pas les groupes absents de l'entraînement : la
chaîne de repli est explicite (quartier+type → ville+type → ville → moyenne
globale) et la table des niveaux de prédiction montre quel niveau a servi.

### Scénarios d'évaluation

| Scénario | Description | Observations |
|---|---|---|
| `toutes_observations` | Toutes les observations du mart (aucune exclusion) — scénario principal. | 2 992 |
| `hors_republications` | Observations hors républications (`is_republication = false`) : réduit le risque d'annonces quasi identiques entre entraînement et test. | 991 |
| `prix_exacts_sans_aberration` | Observations à prix exact (`price_is_bound = false`) et sans aberration (`outlier_flags` vide) : cible la plus fiable, mais volumes faibles. | 422 |

## Résultats globaux

### `toutes_observations` — 2 992 observations

| Baseline | N entraînement | MAE entraînement | MAE validation | MedAE validation | RMSE validation | R² validation | MAE test | MedAE test | RMSE test | R² test |
|---|---|---|---|---|---|---|---|---|---|---|
| `baseline_global` | 2 094 | 202 720 | 190 141 | 145 906 | 292 198 | -0.001 | 275 818 | 140 906 | 1 901 031 | -0.002 |
| `baseline_city` | 2 094 | 156 136 | 147 296 | 40 000 | 315 762 | -0.169 | 234 258 | 40 000 | 1 908 743 | -0.010 |
| `baseline_neighborhood` | 2 094 | 100 723 | 97 079 | 40 000 | 221 216 | 0.426 | 185 261 | 35 000 | 1 896 704 | 0.003 |

Niveaux de prédiction utilisés en validation :

| Baseline | N prédit | baseline_global | baseline_city | baseline_city_type | baseline_neighborhood |
|---|---|---|---|---|---|
| `baseline_global` | 449 | 449 | 0 | 0 | 0 |
| `baseline_city` | 449 | 0 | 449 | 0 | 0 |
| `baseline_neighborhood` | 449 | 0 | 1 | 15 | 433 |

### `hors_republications` — 991 observations

| Baseline | N entraînement | MAE entraînement | MAE validation | MedAE validation | RMSE validation | R² validation | MAE test | MedAE test | RMSE test | R² test |
|---|---|---|---|---|---|---|---|---|---|---|
| `baseline_global` | 693 | 398 392 | 300 774 | 249 795 | 408 696 | -0.053 | 299 733 | 279 795 | 384 419 | -0.075 |
| `baseline_city` | 693 | 309 882 | 210 950 | 80 000 | 428 555 | -0.158 | 204 929 | 70 000 | 399 324 | -0.160 |
| `baseline_neighborhood` | 693 | 235 010 | 155 081 | 67 500 | 301 317 | 0.428 | 184 376 | 75 000 | 348 877 | 0.115 |

Niveaux de prédiction utilisés en validation :

| Baseline | N prédit | baseline_global | baseline_city | baseline_city_type | baseline_neighborhood |
|---|---|---|---|---|---|
| `baseline_global` | 149 | 149 | 0 | 0 | 0 |
| `baseline_city` | 149 | 0 | 149 | 0 | 0 |
| `baseline_neighborhood` | 149 | 0 | 0 | 20 | 129 |

### `prix_exacts_sans_aberration` — 422 observations

| Baseline | N entraînement | MAE entraînement | MAE validation | MedAE validation | RMSE validation | R² validation | MAE test | MedAE test | RMSE test | R² test |
|---|---|---|---|---|---|---|---|---|---|---|
| `baseline_global` | 296 | 322 608 | 300 975 | 247 645 | 390 647 | -0.001 | 288 986 | 257 645 | 373 530 | -0.000 |
| `baseline_city` | 296 | 264 030 | 236 111 | 70 000 | 422 841 | -0.172 | 247 222 | 100 000 | 413 755 | -0.227 |
| `baseline_neighborhood` | 296 | 85 264 | 176 587 | 60 000 | 294 364 | 0.432 | 156 786 | 50 000 | 297 842 | 0.364 |

Niveaux de prédiction utilisés en validation :

| Baseline | N prédit | baseline_global | baseline_city | baseline_city_type | baseline_neighborhood |
|---|---|---|---|---|---|
| `baseline_global` | 63 | 63 | 0 | 0 | 0 |
| `baseline_city` | 63 | 0 | 63 | 0 | 0 |
| `baseline_neighborhood` | 63 | 0 | 1 | 16 | 46 |

### Robustesse : la MAE dépend-elle de l'échantillon ?

Les prix sont très asymétriques et les valeurs extrêmes sont conservées
(aucune suppression). La MAE est donc sensible à la composition de l'ensemble,
contrairement à l'erreur absolue médiane (MedAE) :

| Scénario | Baseline | MAE validation | MAE test | Écart MAE | MedAE validation | MedAE test | Écart MedAE |
|---|---|---|---|---|---|---|---|
| `toutes_observations` | `baseline_global` | 190 141 | 275 818 | +45.1 % | 145 906 | 140 906 | −3.4 % |
| `toutes_observations` | `baseline_city` | 147 296 | 234 258 | +59.0 % | 40 000 | 40 000 | +0.0 % |
| `toutes_observations` | `baseline_neighborhood` | 97 079 | 185 261 | +90.8 % | 40 000 | 35 000 | −12.5 % |
| `hors_republications` | `baseline_global` | 300 774 | 299 733 | −0.3 % | 249 795 | 279 795 | +12.0 % |
| `hors_republications` | `baseline_city` | 210 950 | 204 929 | −2.9 % | 80 000 | 70 000 | −12.5 % |
| `hors_republications` | `baseline_neighborhood` | 155 081 | 184 376 | +18.9 % | 67 500 | 75 000 | +11.1 % |
| `prix_exacts_sans_aberration` | `baseline_global` | 300 975 | 288 986 | −4.0 % | 247 645 | 257 645 | +4.0 % |
| `prix_exacts_sans_aberration` | `baseline_city` | 236 111 | 247 222 | +4.7 % | 70 000 | 100 000 | +42.9 % |
| `prix_exacts_sans_aberration` | `baseline_neighborhood` | 176 587 | 156 786 | −11.2 % | 60 000 | 50 000 | −16.7 % |

Pour la meilleure baseline (`baseline_neighborhood`), la MAE passe de 97 079 FCFA en validation à 185 261 FCFA en test (90.8 % d'écart), alors que l'erreur médiane varie de 12.5 %.
Conséquence : le seuil de référence est défini sur la MAE (métrique demandée par
la spec), mais la Phase 6 devra confirmer le gain sur la MedAE et sur plusieurs
graines, faute de quoi le gain ne serait pas démontré.

À noter également : 2 564 observations sur 2 992 n'ont qu'une borne inférieure de prix
(« à partir de ») — la cible est donc approximative pour la majorité du dataset,
ce que les scénarios de sensibilité quantifient.

## Performance par segment (scénario principal)

Aucun segment n'est masqué : chaque MAE est accompagnée de son effectif ; un `*` signale un segment sous le seuil de publication de 30 observations (décision Phase 3) dont la MAE n'est pas robuste. `—` : segment absent de l'ensemble ; quartiers limités aux 10 plus volumineux.

### Ville — validation

| Segment | N | MAE `baseline_global` | MAE `baseline_city` | MAE `baseline_neighborhood` |
|---|---|---|---|---|
| Douala | 425 | 193 311 | 149 296 | 98 949 |
| Yaoundé * | 24 | 133 995 | 111 875 | 63 958 |

`*` effectif < 30 : MAE à lire avec prudence.

### Ville — test

| Segment | N | MAE `baseline_global` | MAE `baseline_city` | MAE `baseline_neighborhood` |
|---|---|---|---|---|
| Douala | 424 | 191 196 | 148 932 | 98 236 |
| Yaoundé * | 25 | 1 710 999 | 1 681 400 | 1 661 200 |

`*` effectif < 30 : MAE à lire avec prudence.

### Type de logement — validation

| Segment | N | MAE `baseline_global` | MAE `baseline_city` | MAE `baseline_neighborhood` |
|---|---|---|---|---|
| apartment | 437 | 188 736 | 145 002 | 92 188 |
| studio * | 11 | 261 485 | 238 182 | 286 591 |
| house * | 1 | 19 094 | 150 000 | 150 000 |

`*` effectif < 30 : MAE à lire avec prudence.

### Type de logement — test

| Segment | N | MAE `baseline_global` | MAE `baseline_city` | MAE `baseline_neighborhood` |
|---|---|---|---|---|
| apartment | 443 | 277 457 | 236 065 | 184 485 |
| studio * | 5 | 151 543 | 113 000 | 287 000 |
| room * | 1 | 170 906 | 40 000 | 20 000 |

`*` effectif < 30 : MAE à lire avec prudence.

### Nombre de chambres — validation

| Segment | N | MAE `baseline_global` | MAE `baseline_city` | MAE `baseline_neighborhood` |
|---|---|---|---|---|
| 2 chambre(s) | 241 | 163 747 | 111 747 | 74 942 |
| 1 chambre(s) | 108 | 172 981 | 67 454 | 82 106 |
| 3 chambre(s) | 97 | 256 982 | 301 959 | 133 918 |
| 4 chambre(s) * | 2 | 1 150 000 | 1 250 000 | 1 350 000 |
| inconnu * | 1 | 906 | 130 000 | 970 000 |

`*` effectif < 30 : MAE à lire avec prudence.

### Nombre de chambres — test

| Segment | N | MAE `baseline_global` | MAE `baseline_city` | MAE `baseline_neighborhood` |
|---|---|---|---|---|
| 2 chambre(s) | 265 | 309 708 | 258 736 | 215 019 |
| 3 chambre(s) | 91 | 264 797 | 300 132 | 172 165 |
| 1 chambre(s) | 88 | 154 723 | 52 898 | 89 716 |
| 4 chambre(s) * | 5 | 811 457 | 930 000 | 528 000 |

`*` effectif < 30 : MAE à lire avec prudence.

### Niveau de prix (quartiles calculés sur l'entraînement) — validation

| Segment | N | MAE `baseline_global` | MAE `baseline_city` | MAE `baseline_neighborhood` |
|---|---|---|---|---|
| Q1 | 146 | 167 755 | 38 219 | 27 825 |
| Q4 | 113 | 359 955 | 487 434 | 258 274 |
| Q3 | 103 | 81 527 | 46 175 | 77 485 |
| Q2 | 87 | 135 733 | 8 276 | 27 126 |

### Niveau de prix (quartiles calculés sur l'entraînement) — test

| Segment | N | MAE `baseline_global` | MAE `baseline_city` | MAE `baseline_neighborhood` |
|---|---|---|---|---|
| Q3 | 136 | 82 045 | 46 875 | 73 621 |
| Q1 | 134 | 165 085 | 34 925 | 29 067 |
| Q4 | 104 | 772 977 | 900 212 | 652 856 |
| Q2 | 75 | 135 639 | 6 733 | 18 367 |

### Quartier (ville / quartier) — validation

| Segment | N | MAE `baseline_global` | MAE `baseline_city` | MAE `baseline_neighborhood` |
|---|---|---|---|---|
| Douala / Makepe | 152 | 137 956 | 32 191 | 29 230 |
| Douala / Logpom | 58 | 138 409 | 30 052 | 29 060 |
| Douala / Bonamoussadi | 46 | 140 482 | 90 543 | 93 152 |
| Douala / Akwa | 39 | 267 881 | 363 590 | 232 564 |
| Douala / Bonapriso | 38 | 520 696 | 637 105 | 336 579 |
| Douala / Malangue * | 16 | 122 781 | 8 125 | 8 125 |
| Douala / Kotto * | 15 | 115 331 | 50 667 | 52 000 |
| Douala / Bali * | 14 | 225 197 | 321 429 | 202 857 |
| Douala / Ndogbong * | 7 | 135 906 | 33 571 | 40 714 |
| Douala / Bonanjo * | 7 | 483 380 | 614 286 | 185 714 |

`*` effectif < 30 : MAE à lire avec prudence.

### Quartier (ville / quartier) — test

| Segment | N | MAE `baseline_global` | MAE `baseline_city` | MAE `baseline_neighborhood` |
|---|---|---|---|---|
| Douala / Makepe | 152 | 133 354 | 37 257 | 34 625 |
| Douala / Bonamoussadi | 54 | 111 301 | 62 296 | 58 222 |
| Douala / Logpom | 48 | 132 468 | 33 229 | 32 812 |
| Douala / Akwa | 36 | 215 709 | 303 056 | 194 722 |
| Douala / Bonapriso | 30 | 563 275 | 674 667 | 315 667 |
| Douala / Malangue * | 15 | 127 239 | 8 333 | 8 333 |
| Douala / Kotto * | 15 | 118 572 | 36 333 | 35 000 |
| Douala / Bali * | 15 | 188 244 | 256 000 | 177 333 |
| Douala / Bonanjo * | 11 | 703 969 | 812 727 | 532 727 |
| Douala / Ndogbong * | 9 | 108 482 | 57 778 | 47 778 |

`*` effectif < 30 : MAE à lire avec prudence.

## Seuil de référence à battre

| Scénario | N | Meilleure baseline | MAE validation | IC 95 % MAE validation | Seuil à battre | Gain relatif exigé | MAE test (référence) |
|---|---|---|---|---|---|---|---|
| `toutes_observations` | 2 992 | `baseline_neighborhood` | 97 079 | 79 773 – 116 491 | 79 773 | 17.83 % | 185 261 |
| `hors_republications` | 991 | `baseline_neighborhood` | 155 081 | 115 721 – 200 316 | 115 721 | 25.38 % | 184 376 |
| `prix_exacts_sans_aberration` | 422 | `baseline_neighborhood` | 176 587 | 120 069 – 236 758 | 120 069 | 32.01 % | 156 786 |

Règle de décision (appliquée en Phase 6) : un modèle ML n'est retenu que s'il
ramène la MAE de **validation** sous la borne basse de l'intervalle de confiance
bootstrap à 95 % de la meilleure baseline, soit sous **79 773 FCFA** pour le scénario principal — un gain d'au moins 17 306 FCFA (17.83 %), **et** que la
réduction se confirme sur le test. Un gain inférieur à cet intervalle n'est pas
distinguable du bruit d'échantillonnage (N validation = 449).

## Conclusion

- Meilleure baseline : `baseline_neighborhood` — MAE validation 97 079 FCFA, MAE test 185 261 FCFA.
- Seuil à battre : **79 773 FCFA** en validation (gain minimal exigé : 17.83 %).
- Aucun modèle ML n'est entraîné à cette phase (hors périmètre) : la Phase 6 doit
  démontrer ce gain, sinon la baseline reste la référence du produit.

Segments les plus difficiles pour la meilleure baseline (MAE décroissante) :

| Famille | Segment | N | MAE |
|---|---|---|---|
| quartier | Douala / Bonapriso | 38 | 336 579 |
| niveau_de_prix | Q4 | 113 | 258 274 |
| quartier | Douala / Akwa | 39 | 232 564 |
| nombre_de_chambres | 3 chambre(s) | 97 | 133 918 |
| ville | Douala | 425 | 98 949 |

## Limites connues

- **Prix censurés** : 2 564 observations sur 2 992 ne donnent qu'une borne inférieure (« à partir de ») ; la cible est alors approximative.
- **Républications** : 2 001 observations signalées, réparties aléatoirement entre les ensembles ; des annonces très proches peuvent
apparaître en entraînement et en test, ce qui rend l'évaluation légèrement optimiste.
- **Quartiers non reconnus** : 101 observations portent un libellé absent du référentiel ; elles restent évaluées.
- **Petits segments** : les quartiers sous 30 observations ne sont pas publiés (aucune fusion silencieuse).
- **Features absentes** : `area_m2`, `furnished`, `parking`, `gated` sont vides
  dans le Silver : les baselines n'exploitent que ville, quartier, type, chambres
  et salles de bain.
- Une estimation n'est jamais une valeur officielle du bien (invariant 9).

## Reproductibilité

```bash
python -m pipelines silver --report docs/phase-2/cleaning-report.md
python -m pipelines load
cd dbt && dbt build && cd ..
python -m ml.src baselines
```

Versions : Python 3.14.4, pandas 3.0.6, numpy 2.5.3, scikit-learn 1.9.1 ; graine `20261009`, bootstrap 2 000 itérations.
