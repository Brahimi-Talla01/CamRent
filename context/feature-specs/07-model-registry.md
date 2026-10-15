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

   La **version servie** est épinglée dans un fichier **versionné** (`ml/models/champion.json` :
   nom, version, `run_id`, empreinte du dataset, SHA Git, approbation). Le serving lit cette version
   épinglée, jamais un artefact local implicite.

4. Définir la règle de **promotion** d'un modèle : critères de performance et de vérification
   (battre la baseline, respecter le seuil de la Phase 5, être reproductible).

   La règle est évaluée automatiquement, mais la promotion est **explicite** : l'attribution de
   l'alias de référence (`champion`) exige une **approbation d'un administrateur** (rôle `admin`),
   fournie en argument (`--confirm-promotion --approved-by <nom>`) et consignée dans le run et dans
   la version (approbateur + date). Une règle satisfaite sans approbation **ne promeut pas**.

5. Versionner également les **datasets** (au minimum : identifiant de version documenté ; DVC / lakeFS
   étudiés si les volumes l'exigent). L'identifiant de version doit couvrir **tout le contenu du
   mart** (schéma et valeurs des colonnes, cible comprise) : ajouter ou modifier une feature doit
   produire une nouvelle version.

## Dependencies

- MLflow.
- Modèles de la Phase 6.

## Scope Limits

- Pas de plateforme ML lourde : MLflow suffit au MVP.
- Ne pas déployer un modèle non enregistré / non versionné.
- Aucune promotion sans **approbation explicite** : une suppression ou un déplacement automatique de
  l'alias `champion` est interdit.
- Les artefacts de runs ne sont pas écrits dans le répertoire courant : l'emplacement est **épinglé**
  (`MLFLOW_ARTIFACT_LOCATION`, par défaut `ml/artifacts/mlflow`) et non versionné.

## Check When Done

- L'expérience `rent_prediction` contient les runs des modèles testés.
- Chaque run trace dataset, features, hyperparamètres, métriques, version de code, date.
- Les modèles retenus sont enregistrés avec une version (`rent-model-vN`).
- La règle de promotion est écrite et applicable **avec approbation explicite** : une règle satisfaite
  sans approbation ne promeut pas (comportement couvert par un test).
- La version servie est **épinglée dans un fichier versionné**, cohérent avec l'état du registre.
- L'identifiant de version du dataset change dès qu'une **feature** change (comportement couvert par
  un test).
- N'importe quel résultat de modèle est rejouable à partir de son run.
