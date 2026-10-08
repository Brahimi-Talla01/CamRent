# Phase 7 — Model registry

Lire `context/architecture-context.md` avant de commencer.

Objectif : tracer les expériences et versionner les modèles, pour ne pas choisir un modèle « sur la
base d'une impression ».

## Implementation

1. Introduire **MLflow** et créer l'expérience `rent_prediction`.

2. Pour chaque run, journaliser :

   - nom et version du modèle ;
   - dataset / version du dataset ;
   - features utilisées ;
   - hyperparamètres ;
   - métriques (MAE, RMSE, R², + métriques par segment) ;
   - version du code ;
   - date d'entraînement.

3. Enregistrer les modèles dans le **Model Registry** avec une version explicite :

   ```
   rent-model-v1
   rent-model-v2
   rent-model-v3
   ```

4. Définir la règle de **promotion** d'un modèle : critères de performance et de vérification
   (battre la baseline, respecter le seuil de la Phase 5, être reproductible).

5. Versionner également les **datasets** (au minimum : identifiant de version documenté ; DVC / lakeFS
   étudiés si les volumes l'exigent).

## Dependencies

- MLflow.
- Modèles de la Phase 6.

## Scope Limits

- Pas de plateforme ML lourde : MLflow suffit au MVP.
- Ne pas déployer un modèle non enregistré / non versionné.

## Check When Done

- L'expérience `rent_prediction` contient les runs des modèles testés.
- Chaque run trace dataset, features, hyperparamètres, métriques, version de code, date.
- Les modèles retenus sont enregistrés avec une version (`rent-model-vN`).
- La règle de promotion est écrite et applicable.
- N'importe quel résultat de modèle est rejouable à partir de son run.
