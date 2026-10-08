# CamRent — Plan technique d’implémentation

**Produit :** CamRent — Analyse et estimation des loyers au Cameroun  
**Périmètre initial :** Yaoundé et Douala  
**Document :** Architecture Data, ML et applicative  
**Version :** 1.0  
**Statut :** Architecture cible pour le MVP et évolutions

---

# 1. Objectif du document

Ce document transforme la conception fonctionnelle de CamRent en une architecture technique professionnelle.

L'objectif n'est pas simplement de construire une application capable de prédire un prix, mais de mettre en place une **plateforme Data/ML reproductible, testable, observable et évolutive**.

L'architecture doit permettre de :

- collecter différentes sources de données immobilières ;
- conserver les données brutes sans les altérer ;
- nettoyer et normaliser les données ;
- contrôler leur qualité ;
- historiser les transformations ;
- construire une base analytique fiable ;
- entraîner et évaluer des modèles ML ;
- exposer les prédictions via une API ;
- alimenter le frontend ;
- surveiller la qualité des données et les performances du système ;
- faire évoluer progressivement CamRent vers une plateforme immobilière plus large.

---

# 2. Principes d’architecture

Les choix techniques seront guidés par les principes suivants :

### 2.1 Data before model

Le modèle ML ne sera pas considéré comme le cœur unique du projet.

La priorité sera :

> **qualité des données → pipeline fiable → analyse → modèle → produit**

### 2.2 Raw data immuable

Les données collectées doivent être conservées dans leur état brut.

On ne doit pas remplacer les données originales après nettoyage.

Architecture :

```text
RAW
 ↓
CLEAN
 ↓
TRANSFORMED
 ↓
ANALYTICAL
```

Cela permet de rejouer les traitements si une erreur est découverte.

### 2.3 Reproductibilité

Un même jeu de données et une même version du code doivent pouvoir produire les mêmes transformations et, autant que possible, les mêmes modèles.

### 2.4 Séparation des responsabilités

Les responsabilités suivantes doivent être séparées :

- ingestion ;
- stockage ;
- qualité ;
- transformation ;
- analyse ;
- entraînement ML ;
- serving ;
- application.

### 2.5 Observabilité

Le système doit permettre de savoir :

- si les pipelines fonctionnent ;
- si les données arrivent ;
- si leur qualité se dégrade ;
- si les volumes changent brutalement ;
- si le modèle devient moins performant.

---

# 3. Architecture globale cible

```text
                         SOURCES
                            │
             ┌──────────────┼──────────────┐
             │              │              │
       Web / annonces    Données CSV    Contributions
       immobilières      / fichiers      utilisateurs
             │              │              │
             └──────────────┼──────────────┘
                            ↓
                    INGESTION LAYER
                            ↓
                ┌──────────────────────┐
                │  Raw Storage / Lake  │
                │   JSON / CSV / HTML  │
                └──────────────────────┘
                            ↓
                    DATA QUALITY
                            ↓
                 CLEAN / STANDARDIZE
                            ↓
                 TRANSFORMATION / ETL
                            ↓
                 ANALYTICAL DATABASE
                      PostgreSQL
                            ↓
          ┌─────────────────┼─────────────────┐
          │                 │                 │
       Analytics        ML Dataset       API / Product
          │                 │                 │
          │                 ↓                 │
          │            ML Training            │
          │                 ↓                 │
          │            Model Registry         │
          │                 ↓                 │
          └────────────── Prediction API ─────┘
                            ↓
                       Next.js App
                            ↓
                         Users
```

---

# 4. Architecture de stockage des données

CamRent pourra utiliser plusieurs systèmes de stockage, chacun avec une responsabilité précise.

Le but n'est pas d'utiliser plusieurs bases « parce que c'est professionnel », mais de choisir le stockage adapté à chaque étape.

---

# 5. Raw Data Storage : Data Lake / Object Storage

La première couche doit conserver les données telles qu'elles ont été collectées.

Exemples :

```text
raw/
├── listings/
│   ├── 2026-10-01/
│   ├── 2026-10-02/
│   └── ...
│
├── user_submissions/
├── reference_data/
└── metadata/
```

Les formats possibles :

- JSON ;
- CSV ;
- Parquet ;
- HTML ou snapshots lorsque cela est légalement et techniquement pertinent.

## Technologie recommandée

Pour le développement local :

- filesystem organisé ;
- éventuellement MinIO pour simuler un Object Storage compatible S3.

En production :

- S3-compatible Object Storage ;
- Cloudflare R2, AWS S3 ou autre solution selon le budget et les besoins.

### Pourquoi ?

Le stockage objet est adapté aux données brutes, volumineuses et historisées.

Il permet notamment de conserver les fichiers originaux indépendamment des bases transactionnelles.

---

# 6. MongoDB : rôle éventuel dans l’ingestion

MongoDB peut être utilisé pour les données semi-structurées collectées lors de certaines phases d'ingestion.

Exemple :

```json
{
  "source": "example-source",
  "collected_at": "2026-10-08T10:00:00Z",
  "raw_listing": {
    "title": "...",
    "description": "...",
    "price": "180,000 FCFA",
    "location": "...",
    "features": ["parking", "barriere"]
  }
}
```

## Pourquoi MongoDB peut être intéressant ?

Les annonces immobilières provenant de sources différentes peuvent avoir des structures différentes.

Une source peut fournir :

```text
title
price
location
description
```

Une autre :

```text
name
amount
district
amenities
```

MongoDB peut servir temporairement de **landing/ingestion store** lorsque les données sont très variables.

## Mais MongoDB ne sera pas forcément obligatoire

Il ne faut pas introduire MongoDB uniquement parce que CamRent est un projet Data Engineering.

Si les sources sont principalement des fichiers JSON/CSV et que le volume reste modéré, un stockage objet peut suffire.

### Décision proposée

Pour le MVP :

```text
Sources
  ↓
Raw Object Storage
  ↓
Parquet
  ↓
PostgreSQL
```

MongoDB pourra être ajouté si l'évolution du système justifie réellement un stockage documentaire intermédiaire.

---

# 7. PostgreSQL : base analytique et applicative

PostgreSQL sera la base relationnelle principale.

Elle pourra contenir :

### Données immobilières normalisées

```text
properties
locations
neighborhoods
cities
property_features
amenities
listings
```

### Données de marché

```text
rent_observations
market_statistics
```

### Données applicatives

```text
users
prediction_requests
predictions
feedback
```

### Pourquoi PostgreSQL ?

- excellent support SQL ;
- contraintes d'intégrité ;
- relations complexes ;
- agrégations ;
- index ;
- transactions ;
- extensions géographiques possibles ;
- excellente intégration avec Python ;
- bonne compatibilité avec les outils Data.

---

# 8. PostgreSQL + PostGIS

La dimension géographique est importante pour CamRent.

PostGIS pourra être utilisé pour stocker :

- latitude ;
- longitude ;
- points ;
- quartiers ;
- zones ;
- distances.

Exemples de futures requêtes :

```text
Quels logements sont à moins de 2 km d'un point donné ?
```

ou :

```text
Quelle est la distribution des prix dans un rayon donné ?
```

PostGIS permettra également d'aller progressivement au-delà du simple champ :

```text
neighborhood = "Bonamoussadi"
```

---

# 9. Data Warehouse ou PostgreSQL ?

Pour le MVP, il n'est pas nécessaire de mettre immédiatement en place :

- BigQuery ;
- Snowflake ;
- Redshift ;
- Databricks.

Le volume initial de CamRent ne le justifie probablement pas.

PostgreSQL peut jouer le rôle de :

> **Operational Database + Analytical Database**

au début.

Lorsque les volumes ou les besoins analytiques augmenteront, une architecture avec Data Warehouse pourra être introduite.

---

# 10. Architecture des données : Bronze / Silver / Gold

Une organisation inspirée du modèle Medallion sera utilisée.

## Bronze

Données brutes.

```text
Bronze
↓
Données originales
↓
Peu ou pas de transformation
```

Exemple :

```json
{
  "price": "180 000 FCFA",
  "location": "Bonamoussadi",
  "description": "Appartement moderne..."
}
```

---

## Silver

Données nettoyées et standardisées.

Exemple :

```text
price = 180000
city = Douala
neighborhood = Bonamoussadi
property_type = apartment
```

À cette étape :

- types corrigés ;
- valeurs normalisées ;
- doublons traités ;
- valeurs manquantes identifiées ;
- unités harmonisées.

---

## Gold

Données prêtes pour :

- analyse ;
- dashboards ;
- Machine Learning ;
- API.

Exemple :

```text
ml_rent_dataset
```

avec les features finales.

---

# 11. ETL ou ELT ?

CamRent utilisera principalement une approche **ELT**, avec certaines étapes ETL lorsque cela est nécessaire.

## ELT

```text
Extract
   ↓
Load
   ↓
Transform
```

Les données sont chargées relativement tôt dans le système de stockage puis transformées.

Avantages :

- conservation des données originales ;
- transformations reproductibles ;
- possibilité de retraiter les données ;
- séparation claire entre ingestion et transformation.

---

## ETL

Certaines transformations pourront être réalisées avant le chargement.

Exemple :

```text
Source
 ↓
Parsing
 ↓
Validation minimale
 ↓
Load
```

Cela est utile lorsqu'il faut :

- parser un fichier ;
- extraire des informations ;
- convertir un format ;
- éliminer des données manifestement invalides.

### Décision

CamRent adoptera donc :

> **ELT comme philosophie principale, avec des étapes ETL ciblées dans l'ingestion.**

---

# 12. Pipeline de données

Le pipeline principal pourra suivre ce flux :

```text
Extract
 ↓
Ingest
 ↓
Raw Storage
 ↓
Validate
 ↓
Clean
 ↓
Standardize
 ↓
Deduplicate
 ↓
Enrich
 ↓
Transform
 ↓
Quality Checks
 ↓
Analytical Tables
 ↓
ML Dataset
```

---

# 13. Ingestion des données

Les sources pourront être :

### Sources web

Collecte périodique d'informations publiques lorsque les conditions d'utilisation l'autorisent.

### Fichiers

```text
CSV
JSON
Excel
Parquet
```

### API

Lorsque certaines sources proposent une API.

### Contributions utilisateur

Données déclarées directement dans CamRent.

---

# 14. Batch vs Streaming

## Batch

Le batch sera le mode principal du MVP.

Exemple :

```text
Tous les jours à 02:00
        ↓
Collecte des nouvelles données
        ↓
Pipeline
        ↓
Mise à jour de la base
```

C'est parfaitement adapté au marché immobilier.

Les loyers n'ont pas besoin d'être recalculés toutes les secondes.

---

## Streaming

Le streaming n'est pas nécessaire au MVP.

Il pourrait devenir intéressant plus tard pour :

- événements utilisateurs ;
- nouvelles annonces en temps quasi réel ;
- systèmes de notifications ;
- tracking produit.

Technologies possibles à long terme :

- Kafka ;
- Redpanda ;
- Kafka Connect.

Mais elles ne doivent pas être introduites prématurément.

---

# 15. Orchestration

Les pipelines devront être orchestrés.

L'orchestrateur doit permettre :

- planification ;
- dépendances ;
- retries ;
- logs ;
- monitoring ;
- historique des exécutions.

## Option recommandée pour le projet

**Apache Airflow** peut être utilisé comme orchestrateur principal.

Exemple :

```text
DAG daily_rent_pipeline

extract
   ↓
load_raw
   ↓
quality_raw
   ↓
transform
   ↓
quality_silver
   ↓
build_gold
   ↓
build_ml_dataset
```

Airflow est particulièrement intéressant pour démontrer des compétences Data Engineering.

---

# 16. Alternative légère

Pour un premier prototype, Airflow peut être plus lourd que nécessaire.

Une progression possible :

### Phase 1

Python + scripts + cron

### Phase 2

Airflow

Cette approche évite de consacrer trop de temps à l'infrastructure avant d'avoir validé le pipeline.

---

# 17. Transformation des données

Les transformations seront réalisées principalement avec :

- SQL ;
- Python ;
- éventuellement Pandas ;
- éventuellement Polars selon les besoins.

Pour les transformations structurées, SQL devra être privilégié lorsqu'il est plus approprié.

Exemple :

```sql
SELECT
    city,
    neighborhood,
    property_type,
    AVG(rent_price) AS avg_rent
FROM rent_observations
GROUP BY city, neighborhood, property_type;
```

---

# 18. dbt

**dbt** pourra être introduit pour gérer les transformations SQL.

Architecture :

```text
Raw tables
    ↓
dbt staging
    ↓
dbt intermediate
    ↓
dbt marts
```

Exemple :

```text
stg_listings
      ↓
int_clean_listings
      ↓
fct_rent_observations
      ↓
mart_neighborhood_prices
```

### Pourquoi dbt ?

- transformations SQL versionnées ;
- dépendances explicites ;
- tests ;
- documentation ;
- lineage ;
- reproductibilité.

Pour un projet Data Engineering professionnel, dbt est particulièrement pertinent.

---

# 19. Data Quality

La qualité des données sera traitée comme une fonctionnalité du système, pas comme une tâche ponctuelle.

Chaque étape critique devra avoir des tests.

---

# 20. Tests de qualité — niveau Bronze

Exemples :

### Présence de données

```text
Le fichier existe-t-il ?
```

### Volume

```text
Le nombre de lignes est-il raisonnable ?
```

### Format

```text
Le JSON est-il valide ?
```

### Fraîcheur

```text
La dernière collecte est-elle récente ?
```

---

# 21. Tests de qualité — niveau Silver

### Null checks

Certaines colonnes importantes ne doivent pas être nulles :

```text
city
neighborhood
rent_price
property_type
```

### Type checks

```text
rent_price → numeric
bedrooms → integer
area_m2 → numeric
```

### Range checks

Exemple :

```text
rent_price > 0
bedrooms >= 0
area_m2 > 0
```

Les seuils devront être adaptés au contexte et non choisis arbitrairement.

---

# 22. Tests d'unicité

Identifier les doublons.

Exemple :

```text
source
source_listing_id
```

ou une clé composite.

Attention : deux annonces peuvent représenter le même logement.

La déduplication devra donc distinguer :

- doublon technique ;
- même logement publié plusieurs fois ;
- logements réellement différents.

---

# 23. Tests de cohérence

Exemples :

```text
city = Douala
neighborhood appartient aux quartiers connus de Douala
```

ou :

```text
property_type = apartment
bedrooms >= 0
```

Autre exemple :

```text
furnished = false
monthly_rent existe
```

---

# 24. Tests statistiques

Il faudra surveiller la distribution des données.

Exemple :

```text
Prix moyen
Prix médian
Minimum
Maximum
Percentiles
```

Mais aussi :

```text
distribution par ville
distribution par quartier
distribution par type
```

Une variation brutale peut révéler un problème d'ingestion.

---

# 25. Tests de dérive des données

Exemple :

Pendant plusieurs mois :

```text
Prix médian Douala ≈ 180 000
```

Puis soudain :

```text
Prix médian ≈ 450 000
```

Cela peut être :

- une vraie évolution ;
- un changement de source ;
- un problème de parsing ;
- une erreur d'unité.

Le système devra détecter ce genre de changement.

---

# 26. Outils de Data Quality

Plusieurs outils pourront être étudiés :

### Great Expectations

Pour les validations de données.

### dbt tests

Pour les données transformées dans PostgreSQL.

### Pandera

Pour les DataFrames Python.

### Soda

Pour les contrôles de qualité et monitoring.

### Choix MVP

Une combinaison raisonnable :

```text
dbt tests
+
Pandera ou Great Expectations
```

Le choix définitif dépendra de l'implémentation réelle du pipeline.

---

# 27. Data Governance

La gouvernance consiste notamment à savoir :

- d'où vient la donnée ;
- quand elle a été collectée ;
- comment elle a été transformée ;
- qui peut y accéder ;
- quelles sont ses limitations ;
- quelle version est utilisée.

---

# 28. Data Catalog

Chaque dataset important devra être documenté.

Exemple :

```text
Dataset : rent_observations

Description :
Observations de loyers issues de sources immobilières.

Grain :
Une observation correspond à une annonce/logement observé.

Source :
Source immobilière X.

Fréquence :
Daily.

Owner :
Data Engineering.

Sensitive :
Non / à vérifier.

Quality :
Validated.
```

---

# 29. Data lineage

Nous devons pouvoir répondre à :

> « D'où vient cette valeur ? »

Exemple :

```text
Annonce source
    ↓
raw_listing
    ↓
stg_listing
    ↓
rent_observation
    ↓
ml_rent_dataset
    ↓
Model v3
    ↓
Prediction
```

Cela devient particulièrement important lorsqu'une prédiction semble incorrecte.

---

# 30. Versionnement des données

Le code doit être versionné avec Git.

Les datasets et modèles doivent également avoir une stratégie de versionnement.

Exemples :

```text
dataset_v1
dataset_v2
model_v1
model_v2
```

Pour des volumes plus importants, des outils comme :

- DVC ;
- MLflow ;
- lakeFS ;

pourront être étudiés.

---

# 31. MLflow

MLflow pourra gérer :

- expériences ;
- hyperparamètres ;
- métriques ;
- modèles ;
- versions.

Exemple :

```text
Experiment: rent_prediction

Run 01
Model: Linear Regression
MAE: 32000

Run 02
Model: Random Forest
MAE: 21000

Run 03
Model: Gradient Boosting
MAE: 18500
```

Cela permettra de ne pas choisir un modèle uniquement sur la base d'une impression.

---

# 32. Dataset ML

Le dataset ML sera construit à partir des données Gold.

Exemple :

```text
city
neighborhood
property_type
bedrooms
bathrooms
area_m2
furnished
parking
gated
water
electricity
floor
...
rent_price
```

La séparation entre features et target sera explicite.

```text
X = caractéristiques du logement
y = rent_price
```

---

# 33. Train / Validation / Test

Il faudra éviter une fuite de données.

Une séparation possible :

```text
Training
70 %

Validation
15 %

Test
15 %
```

Mais pour des données temporelles, une séparation chronologique peut être plus pertinente :

```text
Anciennes données
        ↓
Training

Données plus récentes
        ↓
Validation / Test
```

Cette stratégie devra être étudiée avant l'entraînement final.

---

# 34. Data Leakage

Une attention particulière devra être portée au Data Leakage.

Exemple :

Si une information calculée à partir du prix cible est utilisée comme feature, le modèle pourrait obtenir artificiellement de très bons résultats.

Toutes les transformations devront donc être conçues pour respecter le moment où l'information serait réellement disponible lors d'une prédiction.

---

# 35. Feature Engineering

Les features pourront inclure :

### Features directes

```text
bedrooms
bathrooms
area_m2
parking
gated
```

### Features géographiques

```text
neighborhood
latitude
longitude
distance_to_center
```

### Features dérivées

```text
rent_per_m2
property_age
```

Attention : `rent_per_m2` ne doit pas être utilisé comme feature si elle dépend directement du prix que l'on cherche à prédire.

---

# 36. Baseline ML

Avant tout modèle complexe :

```text
Baseline 1
→ moyenne globale

Baseline 2
→ médiane par ville

Baseline 3
→ médiane par quartier + type de logement
```

Le modèle ML devra démontrer qu'il apporte une amélioration réelle.

---

# 37. Modèles à tester

Ordre recommandé :

```text
1. Linear Regression
2. Ridge / Lasso
3. Random Forest
4. Gradient Boosting
5. XGBoost / LightGBM
```

Le choix final sera déterminé expérimentalement.

Le Deep Learning n'est pas une priorité pour le MVP.

---

# 38. Métriques ML

Les métriques principales :

### MAE

```text
Erreur moyenne en FCFA
```

Très utile pour communiquer les résultats.

### RMSE

Pour surveiller les grosses erreurs.

### R²

Pour analyser la variance expliquée.

### MAPE

À utiliser avec prudence, notamment lorsque les valeurs peuvent être faibles.

---

# 39. Évaluation par segment

Une métrique globale ne suffit pas.

Il faudra mesurer les performances par :

- ville ;
- quartier ;
- type de logement ;
- nombre de chambres ;
- niveau de prix.

Exemple :

```text
MAE Yaoundé      : 18 000
MAE Douala       : 22 000

MAE appartements : 19 000
MAE maisons      : 35 000
```

Cela peut révéler que le modèle fonctionne bien sur certaines catégories et mal sur d'autres.

---

# 40. Incertitude de la prédiction

L'API devra idéalement retourner :

```json
{
  "estimated_rent": 185000,
  "lower_bound": 165000,
  "upper_bound": 205000
}
```

La méthode utilisée pour calculer les bornes devra être validée statistiquement.

---

# 41. API de prédiction

Exemple :

```http
POST /api/v1/predictions
```

Payload :

```json
{
  "city": "Douala",
  "neighborhood": "Bonamoussadi",
  "property_type": "apartment",
  "bedrooms": 2,
  "bathrooms": 2,
  "area_m2": 110,
  "parking": true,
  "gated": true
}
```

Réponse :

```json
{
  "estimated_rent": 185000,
  "currency": "XAF",
  "lower_bound": 165000,
  "upper_bound": 205000,
  "model_version": "rent-model-v3"
}
```

---

# 42. API de marché

Exemples :

```http
GET /api/v1/market/cities
```

```http
GET /api/v1/market/neighborhoods
```

```http
GET /api/v1/market/prices
```

Paramètres possibles :

```text
city
neighborhood
property_type
bedrooms
period
```

---

# 43. API de comparaison

Exemple :

```http
POST /api/v1/comparisons
```

Le backend pourra comparer :

- prix demandé ;
- prix estimé ;
- prix moyen local ;
- caractéristiques.

---

# 44. Backend

Le backend aura principalement les responsabilités suivantes :

```text
Authentication
Market data
Prediction
Comparison
Analytics
Feedback
```

Une architecture possible :

```text
backend/
├── api/
├── domain/
├── services/
├── repositories/
├── ml/
├── schemas/
└── infrastructure/
```

La technologie backend pourra être :

- FastAPI ;
- ou une autre solution Python adaptée.

FastAPI est particulièrement intéressante pour exposer le modèle ML et rester dans l'écosystème Python.

---

# 45. Frontend

Le frontend pourra être construit avec :

```text
Next.js
TypeScript
```

Fonctionnalités :

```text
Accueil
  ↓
Estimer mon loyer
  ↓
Résultat
  ↓
Explorer le marché
  ↓
Comparer
```

Les interfaces devront mettre l'accent sur la compréhension des données plutôt que sur des dashboards surchargés.

---

# 46. Observabilité des pipelines

Il faudra surveiller :

### Pipeline health

```text
success
failed
duration
retries
```

### Data freshness

```text
last_successful_ingestion
```

### Data volume

```text
rows_ingested
rows_valid
rows_rejected
```

### Data quality

```text
null_rate
duplicate_rate
invalid_rate
```

---

# 47. Observabilité du modèle

Le monitoring ML devra suivre :

- distribution des features ;
- distribution des prédictions ;
- erreurs lorsque le feedback est disponible ;
- performance par segment ;
- dérive des données ;
- dérive des prédictions.

À terme :

```text
Data Drift
Prediction Drift
Model Performance Drift
```

---

# 48. Logs

Chaque pipeline doit produire des logs structurés.

Exemple :

```text
pipeline = daily_rent_pipeline
run_id = 2026-10-08-001
stage = transform_listings
input_rows = 12543
output_rows = 11782
rejected_rows = 761
duration = 42s
status = success
```

---

# 49. Gestion des erreurs

Les pipelines doivent pouvoir :

- retry automatiquement ;
- isoler les données invalides ;
- ne pas supprimer les données précédentes ;
- signaler les erreurs ;
- permettre une reprise.

Exemple :

```text
Raw
 ↓
Transform
 ↓
ERROR
 ↓
Pipeline failed
 ↓
Previous Gold dataset remains available
```

Le pipeline ne doit pas remplacer une donnée valide par un dataset vide simplement parce qu'une collecte a échoué.

---

# 50. Dead Letter / Quarantine

Les données problématiques pourront être isolées.

```text
raw
 ↓
validation
 ├── valid → silver
 │
 └── invalid → quarantine
```

Exemple :

```text
price = "contactez-nous"
```

Cette observation n'est pas nécessairement supprimée définitivement.

Elle peut être conservée pour analyse.

---

# 51. Sécurité et confidentialité

Même si le projet n'est pas initialement très sensible, certaines données utilisateur peuvent le devenir.

Principes :

- minimisation des données ;
- pas de collecte inutile de données personnelles ;
- contrôle des accès ;
- secrets dans des variables d'environnement ;
- chiffrement en transit ;
- sauvegardes ;
- logs sans informations sensibles.

Les contributions utilisateurs doivent être conçues avec une attention particulière à la confidentialité.

---

# 52. Environnements

Trois environnements sont recommandés :

```text
development
staging
production
```

### Development

Tests locaux.

### Staging

Validation avant production.

### Production

Données réelles.

---

# 53. CI/CD

Le pipeline CI devra pouvoir exécuter :

```text
Lint
 ↓
Unit tests
 ↓
Data tests
 ↓
Integration tests
 ↓
Build
 ↓
Deploy
```

Le modèle et les transformations devront également être validés avant déploiement.

---

# 54. Tests logiciels

Le projet devra inclure plusieurs niveaux de tests.

## Unit tests

Tester :

- parsing ;
- normalisation ;
- fonctions de feature engineering ;
- services API.

## Integration tests

Tester :

```text
API → Database
API → Model
Pipeline → Database
```

## Data tests

Tester :

- nulls ;
- types ;
- ranges ;
- unicité ;
- fraîcheur ;
- distribution.

## End-to-end tests

Tester un scénario complet :

```text
Utilisateur
 ↓
Frontend
 ↓
API
 ↓
Model
 ↓
Prediction
 ↓
Response
```

---

# 55. Structure de projet cible

Une structure initiale possible :

```text
camrent/
│
├── docs/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── samples/
│
├── ingestion/
│
├── pipelines/
│
├── dbt/
│
├── ml/
│   ├── notebooks/
│   ├── src/
│   ├── models/
│   └── evaluation/
│
├── backend/
│
├── frontend/
│
├── tests/
│
├── infrastructure/
│
├── .github/
│
├── docker-compose.yml
└── README.md
```

Cette structure pourra évoluer avec le projet.

---

# 56. Docker

Docker pourra standardiser l'environnement local.

Services possibles :

```text
postgres
minio
airflow
redis
backend
frontend
```

Tous ces services ne seront pas nécessairement introduits dès le premier jour.

Le principe est :

> **ajouter une infrastructure uniquement lorsqu'elle répond à un besoin réel.**

---

# 57. Architecture MVP recommandée

Pour éviter le sur-engineering, la première version technique peut être :

```text
                SOURCES
                   ↓
             Python ingestion
                   ↓
             Raw Parquet/JSON
                   ↓
             PostgreSQL
                   ↓
                 dbt
                   ↓
            Quality checks
                   ↓
              Gold tables
                   ↓
            Python / scikit-learn
                   ↓
               MLflow
                   ↓
               FastAPI
                   ↓
               Next.js
```

Puis :

```text
             Airflow
                ↓
        Orchestration complète
```

pour automatiser les pipelines.

---

# 58. Architecture Data Engineering cible

À maturité :

```text
                         SOURCES
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
       Web                 API              Users
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ↓
                     INGESTION LAYER
                            ↓
                  OBJECT STORAGE / LAKE
                       Bronze
                            ↓
                    QUALITY CHECKS
                            ↓
                     TRANSFORMATIONS
                         dbt/SQL
                            ↓
                        Silver
                            ↓
                    ENRICHMENT / GEO
                            ↓
                         Gold
                            ↓
              ┌─────────────┴─────────────┐
              │                           │
         Analytics                   ML Dataset
              │                           │
              │                      Training
              │                           │
              │                       MLflow
              │                           │
              └─────────────┬─────────────┘
                            ↓
                       MODEL SERVING
                            ↓
                         FastAPI
                            ↓
                         Next.js
```

---

# 59. Roadmap technique

## Phase 0 — Validation du problème

Objectif :

> Vérifier que suffisamment de données sont accessibles.

Livrables :

- sources identifiées ;
- contraintes légales étudiées ;
- échantillon de données ;
- première analyse du volume ;
- première analyse de qualité.

---

## Phase 1 — Data ingestion

Construire :

- scripts de collecte ;
- stockage Raw ;
- métadonnées ;
- premières validations.

Livrable :

```text
Raw dataset version 1
```

---

## Phase 2 — Data cleaning

Construire :

- normalisation ;
- déduplication ;
- gestion des valeurs manquantes ;
- standardisation des quartiers ;
- conversion des prix ;
- validation.

Livrable :

```text
Silver dataset
```

---

## Phase 3 — EDA

Explorer :

- distribution des loyers ;
- quartiers ;
- villes ;
- types ;
- chambres ;
- superficie ;
- corrélations ;
- valeurs aberrantes ;
- données temporelles.

Livrable :

```text
EDA report
```

---

# 60. EDA — Analyse exploratoire détaillée

L'EDA devra répondre à des questions telles que :

### Distribution

- Quelle est la distribution des prix ?
- Les prix sont-ils fortement asymétriques ?
- Une transformation logarithmique est-elle pertinente ?

### Géographie

- Quels quartiers ont les prix les plus élevés ?
- Quels quartiers sont les plus accessibles ?
- Comment les prix diffèrent-ils entre Yaoundé et Douala ?

### Caractéristiques

- Quel est l'effet du nombre de chambres ?
- Quel est l'effet de la superficie ?
- Quel est l'effet du parking ?
- Quel est l'effet du meublé ?
- Quel est l'effet de la sécurité ?

### Qualité

- Quelles colonnes contiennent le plus de valeurs manquantes ?
- Quels quartiers sont sous-représentés ?
- Existe-t-il des sources de données particulièrement bruitées ?

---

# 61. Phase 4 — Data warehouse / marts

Créer les tables analytiques :

```text
dim_city
dim_neighborhood
dim_property_type
dim_date

fct_rent_observations
fct_listings
```

Puis des marts :

```text
mart_neighborhood_prices
mart_city_prices
mart_property_prices
mart_ml_dataset
```

---

# 62. Phase 5 — Baseline ML

Construire :

```text
baseline_global
baseline_city
baseline_neighborhood
```

Comparer les résultats.

Objectif :

> savoir si le ML apporte réellement une valeur ajoutée.

---

# 63. Phase 6 — Modèles ML

Tester progressivement :

```text
Linear Regression
↓
Ridge
↓
Random Forest
↓
Gradient Boosting
↓
XGBoost / LightGBM
```

Comparer :

- MAE ;
- RMSE ;
- R² ;
- performances par segment ;
- temps d'entraînement ;
- complexité.

---

# 64. Phase 7 — Model Registry

Introduire MLflow.

Exemple :

```text
rent-model-v1
rent-model-v2
rent-model-v3
```

Chaque modèle devra conserver :

- dataset/version ;
- features ;
- hyperparamètres ;
- métriques ;
- code version ;
- date d'entraînement.

---

# 65. Phase 8 — API

Construire FastAPI :

```text
POST /api/v1/predictions
GET  /api/v1/market/cities
GET  /api/v1/market/neighborhoods
GET  /api/v1/market/prices
POST /api/v1/comparisons
```

---

# 66. Phase 9 — Frontend

Construire progressivement :

### Page d'accueil

Présentation de CamRent.

### Estimation

Formulaire.

### Résultat

Prix + intervalle + contexte.

### Explorer

Statistiques du marché.

### Comparer

Comparaison de logements.

---

# 67. Phase 10 — Orchestration

Une fois les pipelines stabilisés :

```text
Airflow
 ↓
Daily ingestion
 ↓
Quality
 ↓
Transformation
 ↓
Analytics
 ↓
ML dataset
```

Le réentraînement du modèle pourra être automatisé uniquement lorsque cela sera justifié.

---

# 68. Phase 11 — Observabilité

Mettre en place :

- logs ;
- métriques pipeline ;
- alertes ;
- data quality monitoring ;
- freshness monitoring ;
- model monitoring.

---

# 69. Phase 12 — Production

Déploiement :

```text
Frontend
    ↓
Backend
    ↓
PostgreSQL
    ↓
Object Storage
    ↓
ML Model
```

Avec :

- HTTPS ;
- secrets ;
- backups ;
- monitoring ;
- CI/CD.

---

# 70. Ordre réel de développement recommandé

Il est important de ne pas suivre uniquement l'ordre des couches techniques.

L'ordre recommandé est :

```text
1. Identifier les sources
        ↓
2. Collecter un petit échantillon
        ↓
3. Mesurer la qualité
        ↓
4. Définir le schéma
        ↓
5. Construire le pipeline Raw → Silver
        ↓
6. Faire l'EDA
        ↓
7. Construire la première baseline
        ↓
8. Tester les modèles
        ↓
9. Valider que la prédiction est utile
        ↓
10. Construire l'API
        ↓
11. Construire le frontend
        ↓
12. Automatiser
        ↓
13. Observer
        ↓
14. Déployer
```

---

# 71. Décisions techniques provisoires

| Domaine | Choix initial | Évolution possible |
|---|---|---|
| Raw storage | Parquet + Object Storage | S3/R2/MinIO |
| Document store | MongoDB si nécessaire | MongoDB cluster |
| Base relationnelle | PostgreSQL | Data Warehouse |
| Géospatial | PostGIS | Infrastructure géospatiale avancée |
| Transformation | SQL + Python | dbt |
| Orchestration | Python/cron au début | Airflow |
| Data quality | dbt tests + Pandera/GE | Soda/GE avancé |
| ML | scikit-learn | XGBoost/LightGBM |
| Experiment tracking | MLflow | ML platform |
| API | FastAPI | architecture distribuée si nécessaire |
| Frontend | Next.js + TypeScript | — |
| Conteneurisation | Docker | Kubernetes si réellement nécessaire |
| CI/CD | GitHub Actions/GitLab CI | — |
| Streaming | Non nécessaire MVP | Kafka/Redpanda |
| Cache | Non nécessaire initialement | Redis |

---

# 72. Ce qu'il faut éviter

CamRent ne doit pas tomber dans le piège du « Data Engineering pour impressionner ».

Il ne faut pas commencer avec :

```text
Kafka
Kubernetes
Spark
Databricks
Snowflake
Airflow
MongoDB
PostgreSQL
Redis
```

tous en même temps.

Une architecture professionnelle n'est pas celle qui utilise le plus d'outils.

C'est celle où :

> **chaque technologie répond à un problème réel.**

---

# 73. Architecture progressive

La progression recommandée est :

## Niveau 1 — Prototype Data

```text
Python
CSV/JSON
Parquet
PostgreSQL
Pandas/Polars
scikit-learn
```

## Niveau 2 — Pipeline professionnel

```text
Object Storage
PostgreSQL
dbt
Airflow
Data Quality
MLflow
FastAPI
```

## Niveau 3 — Plateforme Data

Selon les besoins réels :

```text
Object Storage
Data Warehouse
Streaming
Feature Store éventuel
Model Monitoring
Data Catalog
```

---

# 74. Critères de passage entre les niveaux

On ne passe pas au niveau suivant simplement parce qu'une technologie est intéressante.

### Ajouter Airflow lorsque :

- plusieurs pipelines existent ;
- des dépendances deviennent complexes ;
- la planification manuelle devient problématique.

### Ajouter MongoDB lorsque :

- les données semi-structurées deviennent importantes ;
- PostgreSQL ou le Raw Storage ne répond plus correctement au besoin.

### Ajouter Kafka lorsque :

- des événements temps réel deviennent réellement nécessaires.

### Ajouter Spark lorsque :

- les volumes dépassent les capacités raisonnables de l'architecture actuelle.

### Ajouter un Data Warehouse lorsque :

- PostgreSQL devient insuffisant pour les workloads analytiques.

---

# 75. Objectif final

CamRent doit devenir un projet capable de démontrer une chaîne complète :

```text
DATA COLLECTION
      ↓
DATA STORAGE
      ↓
DATA QUALITY
      ↓
DATA TRANSFORMATION
      ↓
DATA ANALYSIS
      ↓
FEATURE ENGINEERING
      ↓
MACHINE LEARNING
      ↓
MODEL TRACKING
      ↓
API
      ↓
APPLICATION
      ↓
MONITORING
```

Ce parcours est particulièrement important pour le positionnement Data Engineering + ML du projet.

---

# 76. Première étape concrète

Avant de choisir définitivement MongoDB, Airflow, dbt ou même l'infrastructure cloud, la première tâche technique doit être :

> **réaliser une étude des données réellement disponibles pour Yaoundé et Douala.**

Cette étude devra déterminer :

1. quelles sources sont accessibles ;
2. combien d'observations peuvent être obtenues ;
3. quelles variables sont disponibles ;
4. quelle proportion de données est manquante ;
5. quelles données sont dupliquées ;
6. quelles sources sont suffisamment fiables ;
7. quelles contraintes d'utilisation existent ;
8. à quelle fréquence les données peuvent être collectées ;
9. quelle structure brute elles présentent ;
10. si le problème ML est suffisamment alimenté pour produire une estimation utile.

**Aucune architecture complexe ne doit être considérée comme définitive avant cette étude.**

---

# 77. Livrable attendu avant le développement

Le prochain livrable devra être un **Data Discovery Report** contenant :

```text
Source
├── URL / origine
├── Type
├── Méthode de collecte
├── Fréquence
├── Volume estimé
├── Structure
├── Variables disponibles
├── Qualité
├── Contraintes
└── Utilisation possible
```

Puis un premier dataset exploratoire :

```text
raw_sample/
    ↓
profiling/
    ↓
quality_report/
    ↓
eda/
```

C'est seulement après cette étape que nous pourrons figer le schéma de données et l'architecture technique finale.
