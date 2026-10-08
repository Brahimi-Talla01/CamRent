# CamRent — Analyse et estimation des loyers au Cameroun

**Nom de travail :** CamRent
**Slogan provisoire :** Comprendre le marché. Estimer juste.
**Périmètre initial :** Yaoundé et Douala
**Version :** 1.0

## Overview

CamRent est une plateforme Data/ML d'analyse et d'estimation du marché locatif à Yaoundé et Douala. Elle exploite des données immobilières — principalement des annonces — pour estimer le prix d'un logement, fournir une fourchette d'estimation, explorer les prix par zone et comparer des logements, afin d'aider locataires et propriétaires à prendre de meilleures décisions.

Le produit n'est **pas** un simple formulaire branché sur un modèle ML : c'est une **plateforme d'analyse du marché** dont le modèle est un composant central.

## Objectifs

1. Estimer de manière objective et contextualisée le loyer d'un logement.
2. Fournir une fourchette et un contexte plutôt qu'un chiffre unique.
3. Explorer les prix par ville, quartier, type de logement et nombre de chambres.
4. Comparer des logements comparables et expliquer les écarts.
5. Aider les propriétaires à positionner un prix de façon raisonnable.
6. Toujours exposer l'incertitude et le nombre d'observations — jamais de fausse précision.

## Utilisateurs cibles

- **Locataires** — savoir si un loyer est raisonnable, comparer des logements, connaître les prix d'un quartier, identifier les quartiers correspondant à un budget.
- **Propriétaires / bailleurs** — estimer un loyer cohérent, comparer à des biens similaires, éviter de sous-évaluer ou de surévaluer.
- **Analystes** — étudiants, chercheurs, journalistes, professionnels de l'immobilier, développeurs, investisseurs.

## Flux utilisateur principal (MVP)

1. L'utilisateur renseigne les caractéristiques d'un logement (ville, quartier, type, chambres, salles de bain, surface si disponible, meublé, parking, barrière, équipements).
2. Il lance l'estimation.
3. Le système retourne : loyer estimé, fourchette, contexte de la zone, nombre d'observations, informations sur la fiabilité des données.
4. Il peut explorer le marché par zone ou comparer des logements.

## Fonctionnalités

### MVP (V1)

- **Estimation du loyer** — fonctionnalité principale
- **Exploration des prix** — statistiques par quartier, par type
- **Statistiques par quartier** — moyenne, médiane, fourchette, nombre d'observations
- **Comparaison de logements** — différence de prix, écart aux estimations, explication des écarts

### Après le MVP

- Aide à la fixation du prix (positionnement par rapport à la fourchette)
- Recherche par budget (« Que puis-je trouver avec 150 000 FCFA par mois ? »)
- Suivi temporel des loyers, cartes de prix, détection de quartiers émergents
- APIs de données immobilières, tableaux de bord

## Variables initiales du MVP

- ville
- quartier
- type de logement
- nombre de chambres
- nombre de salles de bain
- superficie, si suffisamment disponible
- meublé / non meublé
- parking
- barrière
- quelques équipements importants
- **cible : `rent_price`**

## Hors périmètre (MVP)

- Couverture de toutes les villes du Cameroun
- Application mobile native
- Recommandations très avancées
- Prédiction des prix de vente
- Système complet de gestion d'annonces
- Chatbot immobilier
- Fonctionnalités sociales
- Géolocalisation extrêmement détaillée
- Modèles Deep Learning complexes

## Critères de réussite

### Data
- données suffisamment propres ;
- sources documentées ;
- pipeline reproductible ;
- transformations traçables.

### ML
- le modèle bat une baseline simple ;
- les erreurs sont mesurées ;
- les résultats sont analysés par ville et par zone ;
- les limites du modèle sont documentées.

### Produit
- le résultat est facilement compréhensible ;
- l'estimation est accompagnée de contexte ;
- l'application ne donne pas une fausse impression de certitude.

### Technique
- frontend, backend, data et ML correctement séparés ;
- API de prédiction reproductible ;
- projet déployable ;
- documentation suffisante pour un autre développeur.

## Limitation structurelle à communiquer

La cible représente le **prix demandé dans les annonces**, pas nécessairement le prix réellement payé par le locataire. Le produit doit l'expliciter, par exemple :

> « Estimation basée sur les prix observés dans les annonces disponibles. »

## Documents de référence

- `assets/CamRent_Conception_Produit_et_Probleme_Data.md`
- `assets/CamRent_Plan_Technique_Implementation_Architecture_Data_ML.md`
- `assets/Data_Discovery_Report.md`
