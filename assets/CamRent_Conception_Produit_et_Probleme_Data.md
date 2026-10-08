# CamRent — Conception du produit et du problème Data

**Nom du produit proposé : CamRent**  
**Nom complet : CamRent — Analyse et estimation des loyers au Cameroun**  
**Version du document : 1.0**  
**Périmètre initial : Yaoundé et Douala**

---

## 1. Vision du projet

### 1.1 Problème général

Le marché locatif à Yaoundé et Douala est caractérisé par une forte variation des prix selon la localisation, le type de logement, ses caractéristiques et son niveau de confort.

Pour un locataire, il est souvent difficile de savoir si un loyer demandé est cohérent avec le marché local.

Pour un propriétaire, fixer un prix pertinent peut également être difficile sans disposer d'une vision suffisamment objective des logements comparables.

CamRent a pour objectif d'exploiter des données immobilières pour fournir une estimation objective et contextualisée du prix d'un logement.

### 1.2 Reformulation du projet

> **Développer une plateforme intelligente d'analyse et d'estimation des loyers à Yaoundé et Douala, capable d'exploiter des données immobilières pour estimer le prix d'un logement, analyser les tendances du marché local et aider locataires et propriétaires à prendre de meilleures décisions.**

Le produit ne doit donc pas être pensé comme un simple formulaire connecté à un modèle de Machine Learning. Il doit être conçu comme une **plateforme d'analyse du marché locatif**, dont le modèle ML constitue l'un des composants centraux.

---

# 2. Proposition de nom du produit

## CamRent

**CamRent** est court, mémorisable et directement associé au contexte camerounais et à la location.

### Positionnement

> **CamRent — Comprendre le marché. Estimer juste.**

Ce slogan est une proposition et pourra être modifié plus tard.

### Autres noms possibles

- **LoyerCam**
- **ImmoPredict**
- **Rent237**
- **Loca237**
- **CamImmo**
- **RentScope**
- **ImmoPrice Cameroon**

Pour le développement du projet, **CamRent** sera retenu comme nom de travail.

---

# 3. Utilisateurs cibles

CamRent cible principalement trois catégories d'utilisateurs.

## 3.1 Locataires

Ils cherchent à :

- savoir si un loyer est raisonnable ;
- comparer plusieurs logements ;
- connaître les prix moyens dans un quartier ;
- comprendre les facteurs qui influencent le prix ;
- identifier les quartiers correspondant à leur budget.

### Exemple

> « Je cherche un appartement de 2 chambres à Douala avec un budget de 180 000 FCFA. Quels quartiers correspondent à mon budget ? »

---

## 3.2 Propriétaires / bailleurs

Ils cherchent à :

- estimer le prix auquel louer leur logement ;
- comparer leur logement à des biens similaires ;
- éviter de sous-évaluer leur bien ;
- éviter de fixer un prix trop élevé par rapport au marché.

### Exemple

> « J'ai un appartement de 3 chambres à Bonamoussadi avec parking et barrière. Quel loyer serait cohérent ? »

---

## 3.3 Personnes souhaitant simplement analyser le marché

Cette catégorie peut inclure :

- étudiants ;
- chercheurs ;
- journalistes ;
- professionnels de l'immobilier ;
- développeurs ;
- analystes Data ;
- investisseurs.

Ils peuvent utiliser CamRent pour explorer les tendances du marché locatif.

---

# 4. Questions métier auxquelles CamRent doit répondre

Le produit doit répondre à des questions concrètes.

### Estimation

- Combien pourrait coûter ce logement ?
- Quelle fourchette de prix est raisonnable ?
- Quel est le niveau de confiance de cette estimation ?

### Comparaison

- Ce logement est-il plus cher ou moins cher que des logements similaires ?
- Quel est le prix moyen dans ce quartier ?
- Comment deux logements comparables se différencient-ils ?

### Exploration

- Quels sont les quartiers les plus chers ?
- Quels quartiers sont les plus accessibles ?
- Comment les prix varient-ils selon le nombre de chambres ?
- Quel est le prix moyen d'un studio, d'un appartement de 2 chambres ou de 3 chambres ?

### Aide à la décision

- Où trouver un logement correspondant à un budget donné ?
- Quel prix un propriétaire pourrait-il raisonnablement demander ?
- Quelles caractéristiques ont le plus d'influence sur le prix ?

---

# 5. Fonctionnalités du produit

## 5.1 Estimation d'un loyer

L'utilisateur renseigne les caractéristiques du logement.

Exemples :

- ville ;
- quartier ;
- type de logement ;
- nombre de chambres ;
- nombre de salles de bain ;
- superficie ;
- logement meublé ou non ;
- parking ;
- barrière ;
- sécurité ;
- disponibilité de l'eau ;
- disponibilité de l'électricité ;
- groupe électrogène ;
- énergie solaire ;
- niveau dans l'immeuble ;
- etc.

Le système retourne :

```text
Loyer estimé
185 000 FCFA / mois

Fourchette estimée
165 000 – 205 000 FCFA

Niveau de confiance
82 %
```

La présentation exacte du niveau de confiance dépendra de la méthode statistique retenue. Il ne faudra pas afficher arbitrairement un pourcentage si le modèle ne permet pas de le justifier.

---

# 6. Exploration du marché locatif

CamRent doit permettre d'explorer les prix sans nécessairement effectuer une prédiction individuelle.

Exemples :

```text
Ville : Douala
Quartier : Bonamoussadi
Type : Appartement
Chambres : 2
```

Résultat possible :

```text
Prix moyen : 155 000 FCFA
Prix médian : 150 000 FCFA
Fourchette courante : 130 000 – 190 000 FCFA
Nombre d'observations : 248
```

Les statistiques devront toujours être accompagnées du nombre d'observations afin d'éviter de donner une impression de précision lorsque les données sont insuffisantes.

---

# 7. Comparaison de logements

L'utilisateur pourra comparer deux ou plusieurs logements.

### Exemple

**Logement A**

- Bonamoussadi
- 2 chambres
- Parking
- Barrière
- 180 000 FCFA

**Logement B**

- Makepe
- 2 chambres
- Parking
- Barrière
- 150 000 FCFA

CamRent pourra présenter :

- différence de prix ;
- différence par rapport aux estimations ;
- prix moyen de chaque zone ;
- caractéristiques qui peuvent expliquer l'écart.

L'objectif est d'aider l'utilisateur à comprendre la différence plutôt que de simplement déclarer quel logement est « meilleur ».

---

# 8. Aide à la fixation du prix

Cette fonctionnalité cible principalement les propriétaires.

Exemple :

```text
Prix demandé : 220 000 FCFA

Estimation CamRent :
185 000 – 205 000 FCFA

Positionnement :
Au-dessus de la fourchette estimée
```

CamRent pourra proposer un prix indicatif, mais devra clairement présenter celui-ci comme une **estimation basée sur les données disponibles**, et non comme une valeur officielle du bien.

---

# 9. Recherche par budget

Une évolution importante du produit sera de permettre l'approche inverse.

Au lieu de :

> « Combien coûte ce logement ? »

l'utilisateur pourra demander :

> « Que puis-je trouver avec 150 000 FCFA par mois ? »

Filtres possibles :

- ville ;
- budget ;
- type de logement ;
- nombre minimum de chambres ;
- quartier ;
- équipements.

Cette fonctionnalité pourra être développée après le MVP.

---

# 10. Périmètre géographique initial

Le MVP se concentrera sur :

## Yaoundé

Quelques quartiers représentatifs seront sélectionnés selon la disponibilité et la qualité des données.

## Douala

Quelques quartiers représentatifs seront également sélectionnés.

### Important

Il ne faudra pas chercher à couvrir immédiatement tous les quartiers des deux villes.

La couverture géographique doit être déterminée par :

- la disponibilité des données ;
- le volume d'observations ;
- la qualité des données ;
- la diversité des logements ;
- la capacité du modèle à produire des estimations raisonnables.

Un quartier avec très peu de données ne doit pas être présenté comme statistiquement fiable.

---

# 11. Définition du problème Data

Le problème central peut être formulé comme un problème de **régression supervisée**.

## Variable cible

La variable cible principale sera :

```text
rent_price
```

correspondant au loyer mensuel observé dans les données.

Exemple :

```text
rent_price = 180000 FCFA
```

### Attention à la nature de cette variable

Si les données proviennent principalement d'annonces immobilières, `rent_price` représente généralement un **prix demandé**, et non nécessairement le prix réellement payé par le locataire.

Le produit devra donc communiquer clairement cette limitation.

---

# 12. Unité d'observation

Chaque observation du dataset doit représenter un logement ou une annonce correspondant à un logement.

Exemple conceptuel :

| city | neighborhood | property_type | bedrooms | bathrooms | furnished | parking | gated | area_m2 | rent_price |
|---|---|---|---:|---:|---|---|---|---:|---:|
| Douala | Bonamoussadi | apartment | 2 | 2 | no | yes | yes | 110 | 180000 |

Une attention particulière devra être portée aux doublons et aux annonces représentant plusieurs fois le même logement.

---

# 13. Variables/features potentielles

Les variables seront classées en plusieurs catégories.

## 13.1 Localisation

- ville ;
- quartier ;
- sous-quartier, si disponible ;
- latitude ;
- longitude ;
- distance par rapport à certains points d'intérêt ;
- proximité d'une route principale ;
- niveau de centralité.

## 13.2 Caractéristiques du logement

- type ;
- nombre de chambres ;
- nombre de salles de bain ;
- superficie ;
- nombre de pièces ;
- étage ;
- nombre d'étages du bâtiment ;
- année de construction, si disponible.

## 13.3 Équipements et services

- parking ;
- garage ;
- barrière ;
- gardien ;
- sécurité ;
- eau disponible ;
- électricité ;
- groupe électrogène ;
- énergie solaire ;
- climatisation ;
- cuisine équipée ;
- balcon ;
- terrasse ;
- jardin ;
- piscine ;
- internet ;
- ascenseur.

## 13.4 État et standing

Lorsque les données permettent de le représenter de manière suffisamment objective :

- ancien / récent ;
- rénové ;
- standing ;
- finition ;
- qualité générale.

Ces variables devront être définies avec des règles cohérentes afin de limiter les biais subjectifs.

## 13.5 Données temporelles

- date de publication ;
- mois ;
- année ;
- ancienneté de l'annonce ;
- éventuellement évolution temporelle des prix.

Ces variables pourront permettre de prendre en compte l'évolution du marché.

---

# 14. Données géographiques

La localisation constitue probablement l'un des facteurs les plus importants du problème.

Le projet devra donc progressivement évoluer de :

```text
quartier = "Bonamoussadi"
```

vers une représentation plus riche :

```text
latitude
longitude
quartier
ville
```

Cela permettra éventuellement de calculer :

- distances ;
- zones géographiques ;
- proximité de services ;
- densité des logements ;
- caractéristiques locales.

Cette partie pourra devenir une composante importante du projet Data Engineering.

---

# 15. Sources de données

Les données devront provenir de sources légitimes et exploitables.

Sources potentielles :

### 15.1 Données publiques

- jeux de données ouverts ;
- statistiques publiques ;
- données géographiques ;
- données issues d'organismes publics lorsque disponibles.

### 15.2 Annonces immobilières

Les plateformes immobilières et autres sources publiques peuvent constituer une source importante pour les annonces.

Avant toute collecte automatisée, il faudra vérifier :

- les conditions d'utilisation ;
- les règles de robots.txt ;
- les droits sur les données ;
- les restrictions concernant le scraping ;
- la possibilité de stocker et réutiliser les informations.

### 15.3 Données collectées directement

Une fonctionnalité pourra permettre aux utilisateurs de contribuer volontairement à la base.

Exemple :

> « Combien payez-vous actuellement pour votre logement ? »

Les données personnelles ne devront pas être nécessaires pour exploiter cette fonctionnalité.

---

# 16. Qualité des données

La qualité des données sera une partie fondamentale du projet.

Les problèmes à anticiper :

- valeurs manquantes ;
- doublons ;
- prix aberrants ;
- erreurs de saisie ;
- unités différentes ;
- quartiers écrits de plusieurs façons ;
- annonces expirées ;
- annonces dupliquées ;
- logements annoncés plusieurs fois ;
- informations contradictoires.

Exemple :

```text
Bonamoussadi
bonamoussadi
Bonamoussadi, Douala
Bonamoussadi - Douala
```

Ces valeurs devront être normalisées.

---

# 17. Détection des valeurs aberrantes

Un prix comme :

```text
50 000 FCFA
```

ou :

```text
5 000 000 FCFA
```

n'est pas automatiquement une erreur.

Il peut correspondre à un type de logement différent ou à un logement haut de gamme.

Il faudra donc éviter de supprimer automatiquement les valeurs extrêmes.

La détection devra combiner :

- analyse statistique ;
- contexte du logement ;
- type de propriété ;
- localisation ;
- vérification des données sources.

---

# 18. Prix demandé vs prix réellement payé

C'est une limitation importante du projet.

Le dataset peut principalement contenir :

> **prix demandé dans l'annonce**

alors que le modèle cherche idéalement à représenter :

> **prix réellement pratiqué sur le marché**

Le projet devra donc distinguer clairement ces deux notions.

Dans la première version :

```text
Estimation basée sur les prix observés dans les annonces disponibles.
```

Plus tard, les données déclarées volontairement par les locataires pourront aider à améliorer cette distinction.

---

# 19. Approche Machine Learning

Le projet ne doit pas commencer directement avec un modèle complexe.

Une progression raisonnable sera :

### Baseline

- moyenne ;
- médiane ;
- estimation par quartier/type.

### Modèles classiques

- Linear Regression ;
- Ridge / Lasso ;
- Random Forest ;
- Gradient Boosting ;
- éventuellement XGBoost / LightGBM selon l'environnement retenu.

Le choix final dépendra des résultats expérimentaux.

L'objectif n'est pas de choisir le modèle « le plus sophistiqué », mais celui qui fournit le meilleur compromis entre :

- précision ;
- robustesse ;
- interprétabilité ;
- coût ;
- simplicité de maintenance.

---

# 20. Métriques d'évaluation

Pour un problème de prédiction de prix, plusieurs métriques seront étudiées.

## MAE

**Mean Absolute Error**

Exemple :

> MAE = 18 000 FCFA

Interprétation :

> Le modèle se trompe en moyenne d'environ 18 000 FCFA.

Cette métrique est particulièrement facile à expliquer à un utilisateur.

## RMSE

Permet de pénaliser davantage les grosses erreurs.

## R²

Permet d'évaluer la proportion de variation expliquée par le modèle.

Mais R² ne devra pas être utilisé seul pour juger la qualité du système.

---

# 21. Fourchette de prédiction

Le produit ne devra idéalement pas retourner uniquement :

```text
185 000 FCFA
```

mais plutôt :

```text
Estimation : 185 000 FCFA

Intervalle estimé :
165 000 – 205 000 FCFA
```

La méthode permettant de construire cet intervalle devra être déterminée techniquement après expérimentation.

L'objectif est de représenter l'incertitude du modèle plutôt que de donner une fausse précision.

---

# 22. Explicabilité

CamRent devra progressivement pouvoir répondre à :

> « Pourquoi le modèle estime-t-il ce prix ? »

Exemple :

```text
Facteurs ayant le plus contribué à l'estimation :

+ Localisation
+ Nombre de chambres
+ Superficie
+ Parking
+ Niveau de standing
```

L'approche exacte pourra utiliser des méthodes d'explicabilité adaptées au modèle retenu.

---

# 23. Architecture Data cible

Une architecture initiale peut être pensée ainsi :

```text
                    SOURCES
                       │
           ┌───────────┴───────────┐
           │                       │
      Annonces                 Données
      immobilières             utilisateurs
           │                       │
           └───────────┬───────────┘
                       ↓
                DATA INGESTION
                       ↓
                  RAW DATA
                       ↓
                DATA CLEANING
                       ↓
              DATA TRANSFORMATION
                       ↓
                DATASET ANALYTIQUE
                       ↓
              ┌────────┴────────┐
              │                 │
         DATA ANALYSIS       ML TRAINING
                                  │
                                  ↓
                              MODEL
                                  │
                                  ↓
                             PREDICTION API
                                  │
                                  ↓
                              CAMRENT
                                  │
                                  ↓
                              UTILISATEUR
```

---

# 24. Architecture applicative cible

Une architecture possible :

```text
Frontend
Next.js + TypeScript
        │
        ↓
Backend / API
        │
        ├── Prediction API
        ├── Market API
        ├── Comparison API
        └── Analytics API
        │
        ↓
Database
PostgreSQL
        │
        ↓
ML / Data Pipeline
Python
```

Les technologies définitives seront choisies dans le plan d'implémentation.

---

# 25. Principe important : séparer les responsabilités

Le projet devra éviter de mélanger :

```text
Frontend
Data processing
Training
Prediction
Database
```

dans une seule application.

Une organisation plus professionnelle serait :

```text
camrent/
│
├── data/
├── data-pipeline/
├── ml/
├── backend/
├── frontend/
├── docs/
└── infrastructure/
```

La structure exacte sera définie plus tard.

---

# 26. MVP proposé

Le premier produit fonctionnel devra rester volontairement limité.

## MVP V1

### Villes

- Yaoundé
- Douala

### Fonctionnalité principale

**Estimation du loyer**

### Fonctionnalités secondaires

- exploration des prix ;
- statistiques par quartier ;
- comparaison de logements.

### Variables initiales

- ville ;
- quartier ;
- type ;
- nombre de chambres ;
- nombre de salles de bain ;
- superficie, si suffisamment disponible ;
- meublé/non meublé ;
- parking ;
- barrière ;
- quelques équipements importants ;
- prix.

### Résultat

```text
Prix estimé
Fourchette
Statistiques de la zone
Nombre d'observations
Informations sur la fiabilité des données
```

---

# 27. Ce qui ne doit pas être fait dans le MVP

Pour éviter de disperser le projet, les fonctionnalités suivantes pourront attendre :

- couverture de toutes les villes du Cameroun ;
- application mobile native ;
- recommandations très avancées ;
- prédiction des prix de vente ;
- système complet de gestion d'annonces ;
- chatbot immobilier ;
- fonctionnalités sociales ;
- géolocalisation extrêmement détaillée ;
- modèles Deep Learning complexes.

Le projet doit d'abord démontrer que :

> **les données disponibles permettent de produire une estimation utile et suffisamment fiable.**

---

# 28. Critères de réussite du projet

CamRent sera considéré comme réussi si :

### Data

- les données sont suffisamment propres ;
- les sources sont documentées ;
- le pipeline est reproductible ;
- les transformations sont traçables.

### Machine Learning

- le modèle bat une baseline simple ;
- les erreurs sont mesurées ;
- les résultats sont analysés par ville et par zone ;
- les limites du modèle sont documentées.

### Produit

- l'utilisateur comprend facilement le résultat ;
- l'estimation est accompagnée de contexte ;
- l'application ne donne pas une fausse impression de certitude.

### Technique

- frontend, backend, data et ML sont correctement séparés ;
- l'API de prédiction est reproductible ;
- le projet peut être déployé ;
- la documentation permet à un autre développeur de comprendre le système.

---

# 29. Vision à long terme

CamRent pourrait évoluer vers une véritable plateforme de données immobilières camerounaise.

```text
                    CAMRENT
                       │
       ┌───────────────┼────────────────┐
       │               │                │
   Estimation       Analyse          Recherche
    de loyer        marché            logement
       │               │                │
       └───────────────┼────────────────┘
                       │
                 DATA PLATFORM
                       │
          ┌────────────┼────────────┐
          │            │            │
       Locataires   Propriétaires  Analystes
```

À terme, les données accumulées pourraient permettre :

- suivi de l'évolution des loyers ;
- cartes de prix ;
- détection des quartiers émergents ;
- analyse de l'accessibilité au logement ;
- recommandations selon le budget ;
- estimation de prix pour différents types de biens ;
- tableaux de bord immobiliers ;
- APIs de données immobilières.

---

# 30. Décision de conception

À ce stade, le projet est donc défini comme :

> **CamRent est une plateforme Data/ML d'analyse et d'estimation du marché locatif à Yaoundé et Douala. Elle exploite des données immobilières pour estimer le prix d'un logement, fournir une fourchette d'estimation, explorer les prix par zone et comparer différents logements afin d'aider locataires et propriétaires à prendre des décisions plus éclairées.**

Le projet sera construit avec une priorité donnée à :

1. **la qualité des données ;**
2. **la compréhension du problème métier ;**
3. **la reproductibilité du pipeline Data ;**
4. **la qualité du modèle ;**
5. **l'explicabilité des résultats ;**
6. **l'expérience utilisateur ;**
7. **la transparence sur les limites des estimations.**

---

# 31. Prochaine étape

Avant de commencer le développement, la prochaine étape consiste à établir le **plan technique complet du projet**.

Il devra notamment définir :

- les sources de données à utiliser ;
- le schéma du dataset ;
- les variables exactes du MVP ;
- la stratégie de collecte ;
- le pipeline Data ;
- la base de données ;
- l'analyse exploratoire ;
- le feature engineering ;
- les modèles ML à tester ;
- les métriques ;
- l'architecture backend ;
- l'API de prédiction ;
- l'architecture frontend ;
- le déploiement ;
- le monitoring ;
- les phases de développement ;
- les livrables de chaque phase.

**Principe directeur : ne pas commencer par coder l'interface. Commencer par prouver que le problème Data est correctement défini et que les données permettent réellement de construire une estimation utile.**
