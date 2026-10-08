# Phase 6 — Modèles ML

Lire `context/code-standards.md` (§ML) avant de commencer.

Objectif : tester progressivement des modèles de régression et retenir celui qui offre le meilleur
compromis précision / robustesse / interprétabilité / coût / maintenance — **en battant la baseline**
de la Phase 5.

## Implementation

1. Tester les modèles dans l'ordre recommandé :

   ```
   1. Linear Regression
   2. Ridge / Lasso
   3. Random Forest
   4. Gradient Boosting
   5. XGBoost / LightGBM
   ```

2. **Feature engineering** (`ml/src/`) :

   - features directes : `bedrooms`, `bathrooms`, `area_m2`, `parking`, `gated` ;
   - features géographiques : `neighborhood`, `latitude`, `longitude`, `distance_to_center` ;
   - features dérivées : `property_age` (et **pas** `rent_per_m2`) ;
   - encodage des catégorielles, gestion contrôlée des manquants (surface).

3. Comparer systématiquement :

   - MAE ; RMSE ; R² ;
   - performances **par segment** ;
   - temps d'entraînement ;
   - complexité / maintenabilité ;
   - interprétabilité.

4. Étudier l'**incertitude** : construire une **fourchette de prédiction** (`lower_bound` / `upper_bound`)
   avec une méthode statistiquement justifiée (quantiles, quantile regression, bootstrapping…), à
   valider expérimentalement.

5. Étudier l'**explicabilité** : pouvoir répondre à « pourquoi ce prix ? » (contribution des facteurs :
   localisation, chambres, superficie, parking, standing).

6. Sauvegarder le modèle retenu et ses artefacts dans `ml/models/`.

## Dependencies

- scikit-learn, puis XGBoost / LightGBM selon les résultats.
- Séparation train/val/test et baseline fixées en Phase 5.

## Scope Limits

- Pas de Deep Learning (non prioritaire au MVP).
- Ne pas retenir un modèle uniquement parce qu'il est sophistiqué.
- Ne pas introduire de feature à fort risque de leakage.
- Ne pas afficher un intervalle dont la méthode n'a pas été validée.

## Check When Done

- Chaque modèle testé est évalué avec les mêmes métriques et la même séparation de données.
- Le modèle retenu **bat la baseline** de façon vérifiable.
- Les performances sont rapportées par segment, avec les points faibles identifiés.
- La méthode d'intervalle de prédiction est définie et validée.
- L'explicabilité des facteurs principaux est disponible.
- Les limites du modèle sont écrites.
