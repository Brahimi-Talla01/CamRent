# Phase 6 — Modèles ML

Objectif (spec : `context/feature-specs/06-modeles-ml.md`) : tester les familles de
modèles dans l'ordre recommandé et retenir celui qui bat la baseline de la Phase 5
de façon **vérifiable**, en tenant compte de la précision, de la robustesse, de
l'interprétabilité et du coût.

## Livrables

1. **Code** : `ml/src/` — `features` (construction sans leakage), `models` (zoo
   + pipelines), `training` (comparaison, sélection, robustesse), `uncertainty`
   (fourchettes calibrées), `interpretability` (importance, dépendance, explication
   locale), `persistence` (modèle retenu), `model_report` (rendu dérivé),
   `run_models` + CLI `python -m ml.src models`.
2. **Rapport** : `docs/phase-6/model-report.md` (entièrement régénérable — aucun
   chiffre en dur) ; artefacts bruts dans `ml/models/` (ignoré par git).
3. **Modèle retenu** : `ml/models/rent_model_v1.joblib` (pipeline complet :
   features → pré-traitement → modèle) + `rent_model_v1.json` (métadonnées).
4. **Tests** : `tests/unit/test_ml_{features,models,training,uncertainty,interpretability}.py`    (**59 tests**) — imputation ajustée sur l'entraînement uniquement, cible en FCFA,
   calibration et couverture des intervalles, importance par permutation, persistance.

## Méthode

- **Source** : `analytics_marts.mart_ml_dataset` (Phases 4-5), cible
  `target_rent_price` en XAF, 2 992 observations → 2 094 entraînement / 449
  validation / 449 test.
- **Séparation identique à la Phase 5** (70/15/15, graine `20261009`) : sans quoi
  la comparaison avec la baseline ne vaudrait rien.
- **Seuil de référence recalculé** sur cette séparation (pas lu d'un artefact) :
  79 773 FCFA, borne basse de l'IC bootstrap de `baseline_neighborhood` (97 079 FCFA).
- **Candidats** : `linear`, `ridge`, `lasso`, `random_forest`, `gradient_boosting`,
  `lightgbm` — chacun sur la cible brute **et** sur `log1p(cible)`, soit
  **12 candidats**. Hyperparamètres raisonnables **fixés** : la phase compare des
  familles, elle n'optimise pas.
- **Features** : `city`, `neighborhood`, `property_type`, `bedrooms`, `bathrooms`
  + deux dérivées sans leakage : `total_pieces` et `logements_dans_quartier`
  (profondeur de marché, comptée **sur l'entraînement uniquement**).
  Features écartées et pourquoi : surface, meublé, parking, barrière (vides dans
  le Silver), coordonnées (absentes), `property_age` (absente), drapeaux de qualité
  (pas une caractéristique du bien) et `rent_per_m2` (interdit : dérivé de la cible).
- **Sélection en deux temps** : (1) présélection des 3 meilleurs de la graine de
  référence ; (2) choix du **gain médian** face à la baseline **recalculée sur
  chaque graine** (3 graines). Sélectionner sur une seule séparation reviendrait à
  choisir du bruit — c'est précisément ce que la Phase 5 a révélé.

## Résultats (rejeu du 2026-10-13)

Modèle retenu : **`random_forest_log1p`** (forêt aléatoire, cible `log1p`).

| Ensemble | MAE | MedAE | RMSE | R² |
|---|---|---|---|---|
| entraînement | 84 880 | 19 990 | 560 629 | 0,185 |
| validation | **75 425** | **20 710** | 195 073 | 0,554 |
| test | 159 130 | 20 710 | 1 892 032 | 0,008 |

- **La baseline est battue de façon vérifiable** : MAE de validation 75 425 FCFA
  contre 97 079 FCFA pour `baseline_neighborhood` (**−22,31 %**), soit sous le seuil
  de référence de 79 773 FCFA.
- **La MedAE est divisée par près de deux** : 20 710 contre 40 000 FCFA en
  validation (−48 %) — la prévision **typique** est deux fois plus juste que la
  médiane locale, et cette mesure est stable contrairement à la MAE.
- **La conclusion tient sur 3 séparations** : la baseline est battue sur **3/3
  graines** (gain médian 12,35 %, gain minimal 11,99 %), le seuil de 79 773 FCFA
  n'étant franchi que sur la graine de référence.
- Lecture produit (test) : **53,9 %** des prévisions tombent à ±20 % du loyer observé.

Comparaison des familles (MAE validation, graine de référence) : les trois modèles
d'ensemble sur `log1p` sont au coude-à-coude (75 161 à 75 425 FCFA), très loin
devant les modèles linéaires (82 032 à 151 066) et devant la même forêt entraînée
sur la cible brute (79 065). **La transformation `log1p` fait gagner ~4 000 à
10 000 FCFA par famille**, ce qui confirme — mesuré, pas supposé — que la
distribution asymétrique des loyers pèse sur l'apprentissage.

## Robustesse et arbitrage

Le rang sur la graine de référence ne fait pas autorité : `random_forest_log1p`
n'est que **3ᵉ** sur la graine de référence (75 425 contre 75 161 pour le
gradient boosting) alors qu'il est **1ᵉʳ sur les 2 autres graines**. L'écart de
0,35 % au sommet est du bruit ; la différence de gain médian (12,35 % contre
11,43 %) est le critère retenu. LightGBM (3ᵉ famille du classement, 75 281 FCFA)
ajoute une dépendance et du temps d'entraînement pour un gain non démontré : il
n'est pas retenu, il reste comparé et documenté.

| Candidat | Gain médian vs baseline | Baseline battue | Seuil IC battu |
|---|---|---|---|
| `random_forest_log1p` | **12,35 %** | 3/3 | 1/3 |
| `gradient_boosting_log1p` | 11,43 % | 3/3 | 1/3 |
| `lightgbm_log1p` | 11,23 % | 3/3 | 1/3 |

Le seuil IC (borne basse) n'est franchi que sur 1 graine sur 3 : la marge de
bruit est large, et tout arbitrage produit ne doit pas s'appuyer sur un écart
inférieur à cette marge. La robustesse est donc **relative à la baseline**
(gain confirmé partout), pas **absolue** (seuil IC confirmé une fois).

## Fourchette de prédiction

Deux méthodes calibrées puis comparées au niveau visé de **90 %** :

| Méthode | Couverture validation | Largeur médiane validation | Couverture test | Largeur médiane test |
|---|---|---|---|---|
| `split_conformal` | 90,0 % | 302 604 | 92,7 % | 302 604 |
| **`quantile_regression`** | **90,7 %** | **116 998** | **90,7 %** | **135 995** |

Retenue : **`quantile_regression`** — elle couvre le niveau visé et propose une
fourchette deux fois plus étroite sur la moitié des annonces (largeur médiane).
La largeur *moyenne* reste élevée (326 838 FCFA en test) : quelques annonces très
incertaines tirent la queue. La couverture de test sert de vérification, jamais de
réglage — la calibration n'utilise que la validation.

## Explicabilité (« pourquoi ce prix ? »)

Importance par permutation sur la validation, mesurée en **erreur médiane**
supplémentaire (l'importance sur la MAE deviendrait négative dès que quelques
loyers extrêmes conservés dominent l'erreur moyenne) :

| Feature | Erreur médiane supplémentaire |
|---|---|
| `neighborhood` | +33 756 |
| `bedrooms` | +14 190 |
| `bathrooms` | +10 182 |
| `city` | +1 070 |
| `property_type` | +990 |

Le quartier porte l'essentiel du signal, devant les chambres. La dépendance
partielle confirme un effet monotone : prévision médiane de 81 396 FCFA pour
1 chambre, 109 990 pour 2, 138 690 pour 3, 183 303 pour 4.

Exemple expliqué : annonce à Makepe (Douala), appartement, 3 chambres,
2 salles de bain → prévision **127 115 FCFA**, fourchette 80 000 – 215 995 FCFA,
contre 120 000 FCFA observés, et une médiane locale de 80 000 FCFA sur 721
observations publiée à l'appui.

## Points faibles identifiés

- **Yaoundé** : 25 observations en test (sous le seuil de publication de 30) —
  MAE 1 665 748 FCFA, tirée par quelques loyers extrêmes, mais **signalée et non
  masquée**. Le modèle est en pratique entraîné sur Douala.
- **Segments haut de gamme** : quartile de prix Q4 (N=104, MAE 602 359 FCFA),
  `Douala / Bonapriso` (N=30, MAE 240 663), `Douala / Akwa` (N=36, MAE 145 075).
  Le modèle est juste sur le marché courant, imprécis sur le luxe.
- **Segments bien servis** : `Douala / Makepe` (N=152, MAE 23 354, MedAE 10 010),
  `Douala / Logpom` (N=48, MAE 24 501), quartile Q1 (N=134, MAE 14 866).
- **R² de test global (0,008)** : la variance expliquée est nulle quand on
  mesure l'erreur quadratique, dominée par quelques cas extrêmes. Ne jamais
  communiquer ce chiffre seul — la MedAE et le MAE par segment sont parlants.

## Limites

- **Cible approximative pour 2 564 observations sur 2 992** (borne inférieure de
  prix, « à partir de ») : aucune méthode ne peut corriger cela.
- **2 001 républications** réparties aléatoirement : des annonces quasi identiques
  peuvent se retrouver en entraînement et en test, ce qui rend l'évaluation
  **optimiste**. La stratégie de pondération/exclusion reste à figer (suites ouvertes).
- **101 observations hors référentiel** : le modèle bascule alors sur la ville et
  le type (profondeur de marché nulle pour ces quartiers).
- **Features indisponibles** : la précision est plafonnée par l'information
  collectée, pas par le choix du modèle. Collecter surface et coordonnées
  (Phase 2/8) ferait plus pour la précision que n'importe quel algorithme.
- **Hyperparamètres non optimisés** et pas de registre de modèles (MLflow, Phase 7).

## Invariants respectés

- Zéro data leakage : aucune feature dérivée de la cible ; `logements_dans_quartier`
  et l'imputation médiane sont ajustés **sur le seul entraînement** (vérifié par
  test) ; l'intervalle est calibré sur la validation, pas sur le test.
- Aucune statistique sans son nombre d'observations, y compris par segment ;
  les segments sous 30 observations sont signalés `*`, jamais masqués.
- Aucune fourchette publiée sans mesure de sa couverture ; borne basse planchée
  à 1 FCFA (un loyer négatif n'a aucun sens).
- Reproductibilité : graines fixes (sélection et robustesse), versions consignées,
  rapport intégralement dérivé du JSON de métriques. La mesure est stable d'un
  rejeu à l'autre (vérifié : JSON identique hors durées) : seules les **durées**
  d'entraînement et de prédiction varient, par nature.

## Reproductibilité

```bash
python -m pipelines silver --report docs/phase-2/cleaning-report.md
python -m pipelines load
cd dbt && dbt build && cd ..
python -m ml.src baselines   # Phase 5
python -m ml.src models      # Phase 6
```

## Suites ouvertes

- Figer la stratégie vis-à-vis des **prix bornés et des républications** (les
  drapeaux sont exposés dans `mart_ml_dataset`) : pondération explicite plutôt
  qu'exclusion silencieuse.
- Étendre l'évaluation aux **scénarios de sensibilité de la Phase 5**
  (`hors_republications`, `prix_exacts_sans_aberration`) pour mesurer à quel point
  le gain tient à des annonces dupliquées.
- Registre de modèles et suivi des runs (Phase 7), puis intégration dans
  l'API (Phase 8).
