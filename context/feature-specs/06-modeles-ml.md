# Phase 6 — Modèles ML

Lire `context/code-standards.md` (§ML) avant de commencer.

Objectif : tester progressivement des modèles de régression et retenir celui qui offre le meilleur
compromis précision / robustesse / interprétabilité / coût / maintenance — **en battant la baseline**
de la Phase 5.

> **Statut (2026-10-15)** : corrigée après l'audit (plan §5, P6) — les features listées
> ci-dessous reflètent ce qui est **réellement collecté**, contrairement à la version
> initiale de la spec qui exigeait des colonnes absentes du Silver.

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

   - features directes disponibles : `city`, `neighborhood`, `property_type`, `bedrooms`,
     `bathrooms` ;
   - features dérivées sans leakage : `total_pieces`, `logements_dans_quartier`
     (profondeur de marché, comptée **sur l'entraînement uniquement**) ;
   - **jamais** `rent_per_m2` ni aucune feature dérivée de la cible ;
   - **indisponibles au MVP** (décision 2026-10-15 : finaliser d'abord, sans nouvelle
     collecte) : `area_m2`, `parking`, `gated`, `furnished`, `latitude`, `longitude`,
     `distance_to_center`, `property_age` — la précision est bornée par l'information
     collectée, pas par le choix du modèle.

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

7. **Prix censurés** : la grande majorité des observations porte une borne inférieure de
   prix (« à partir de »). Toute mesure de gain doit être confrontée aux scénarios de
   sensibilité ; la stratégie retenue (décision 4, 2026-10-15) est d'**adapter la cible et
   l'intervalle** par une expérience mesurée (lot E du plan de réalignement), pas
   d'exclure ou de pondérer à l'aveugle.

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
