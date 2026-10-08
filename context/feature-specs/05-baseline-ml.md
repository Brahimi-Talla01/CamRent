# Phase 5 — Baseline ML

Lire `context/code-standards.md` (§ML) avant de commencer.

Objectif : établir des **baselines** mesurées, afin de savoir si le ML apporte réellement une valeur
ajoutée. Aucun modèle complexe ne doit être construit avant cette étape.

## Implementation

1. Construire les baselines dans `ml/src/` :

   ```
   baseline_global        → moyenne globale
   baseline_city          → médiane par ville
   baseline_neighborhood  → médiane par quartier + type de logement
   ```

2. Définir la séparation **train / validation / test** :

   - 70 % / 15 % / 15 %, ou séparation **chronologique** si la date de publication le permet ;
   - éviter toute fuite de données entre ensembles.

3. Évaluer chaque baseline avec les métriques :

   - **MAE** (en FCFA — métrique principale de communication) ;
   - **RMSE** (pénalise les grosses erreurs) ;
   - **R²** (variance expliquée, jamais utilisé seul).

4. Mesurer les performances **par segment** (ville, quartier, type, nombre de chambres, niveau de prix)
   pour situer les zones où la baseline échoue.

5. Fixer le **seuil de référence** : quel MAE un vrai modèle doit-il battre pour être retenu ?

## Dependencies

- scikit-learn.
- `mart_ml_dataset` (Phase 4).
- MLflow peut être introduit dès la Phase 7, mais des runs simples suffisent ici.

## Scope Limits

- Aucun modèle d'ensemble / boosting à cette phase.
- Pas de tuning d'hyperparamètres.
- Ne pas utiliser `rent_per_m2` ni aucune feature dérivée de la cible (data leakage).

## Check When Done

- Les trois baselines sont implémentées et exécutées.
- Les métriques (MAE / RMSE / R²) sont mesurées sur les ensembles de validation et de test.
- Les performances sont rapportées par segment.
- Le seuil de référence à battre est documenté.
- Une conclusion claire existe : le ML est-il justifié, et à partir de quel gain ?
