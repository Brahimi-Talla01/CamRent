# Data Discovery Report – Plateforme d'Analyse et d'Estimation des Loyers (Yaoundé & Douala)

**Date :** 8 octobre 2026
**Auteur :** TechKula
**Objectif :** Évaluer la disponibilité, la qualité et la structure des données immobilières pour alimenter un modèle d'estimation de loyers au Cameroun.

---

## 1. Sources de Données Identifiées

### 1.1. Portails Immobiliers en Ligne

| Source                           | URL                                      | Type                  | Méthode de collecte            | Fréquence    | Volume estimé             | Structure    | Variables disponibles                                   | Qualité                                | Contraintes                                         | Utilisation possible                      |
| -------------------------------- | ---------------------------------------- | --------------------- | ------------------------------ | ------------ | ------------------------- | ------------ | ------------------------------------------------------- | -------------------------------------- | --------------------------------------------------- | ----------------------------------------- |
| **Geloka**                       | https://www.geloka.com/fr/rent-barometer | Agrégateur d'annonces | Scraping / API (si disponible) | Hebdomadaire | ~84 annonces (oct. 2026)  | JSON / HTML  | Ville, type de bien, loyer médian, fourchette, quartier | Moyenne (données agrégées)             | Données limitées, pas d'accès direct à l'historique | Benchmark, validation de tendances        |
| **Koutchoumi**                   | https://koutchoumi.com/fr                | Portail immobilier    | Scraping                       | Quotidienne  | ~100 000 annonces (cumul) | HTML         | Ville, type, prix, chambres, surface, quartier          | Bonne (détails par annonce)            | Pas d'API publique, risque de blocage IP            | Dataset principal pour entraînement       |
| **Jumia House**                  | https://house.jumia.cm                   | Portail immobilier    | Scraping                       | Quotidienne  | ~13 000 clients (cumul)   | HTML         | Ville, type, prix, chambres, localisation               | Moyenne (certaines annonces obsolètes) | Site peu mis à jour, risque de données dupliquées   | Complément à Koutchoumi                   |
| **Lewambi**                      | http://lewambi.com                       | Portail immobilier    | Scraping                       | Irrégulière  | Non communiqué            | HTML         | Ville, type, prix, contact                              | Faible (peu d'annonces)                | Site peu actif                                      | Source secondaire                         |
| **Appartementaloueryaounde.com** | https://appartementaloueryaounde.com     | Blog / Agrégateur     | Scraping / Manuel              | Mensuelle    | Non communiqué            | HTML / Texte | Quartier, prix, tendances, analyse                      | Bonne (analyses qualitatives)          | Pas de données brutes structurées                   | Analyse de tendances, features textuelles |

### 1.2. Autres Sources Potentielles

| Source                                     | Type                    | Méthode                     | Fréquence   | Volume                | Variables                               | Qualité                                    | Contraintes                              | Utilisation                                    |
| ------------------------------------------ | ----------------------- | --------------------------- | ----------- | --------------------- | --------------------------------------- | ------------------------------------------ | ---------------------------------------- | ---------------------------------------------- |
| **Facebook Marketplace**                   | Annonces utilisateurs   | Scraping / API Facebook     | Quotidienne | Élevé (non quantifié) | Prix, localisation, photos, description | Faible (données non structurées, arnaques) | Accès API limité, modération             | Complément, détection de tendances informelles |
| **Groupes Facebook (Immobilier Cameroun)** | Annonces communautaires | Scraping / Manuel           | Quotidienne | Élevé                 | Prix, quartier, type, contact           | Faible (non vérifié)                       | Accès limité, données éphémères          | Analyse de sentiment, tendances                |
| **MINHAB / INS Cameroun**                  | Données officielles     | Demande formelle / OpenData | Annuelle    | Limité                | Statistiques logement, prix moyens      | Bonne (officielle)                         | Accès difficile, pas de granularité fine | Validation macro, benchmark                    |
| **Projets GitHub (ex: deegeorgie)**        | Datasets existants      | Téléchargement              | Ponctuelle  | 3 068 observations    | Prix, chambres, salles de bain, ville   | Moyenne (données nettoyées)                | Dataset modeste, besoin de mise à jour   | Point de départ, baseline ML                   |

---

## 2. Analyse Préliminaire des Données

### 2.1. Volume et Couverture

- **Geloka** : 84 annonces analysées (oct. 2026), couvrant Douala, Yaoundé, Bafoussam. [5]
- **Koutchoumi** : ~100 000 annonces cumulées depuis 2009, mais volume actif inconnu. [31][35]
- **Jumia House** : ~13 000 clients revendiqués, mais activité récente incertaine. [29]
- **Dataset GitHub (deegeorgie)** : 3 068 observations (Jumia House, Koutchoumi, Lewambi), 7 features. [16]

**Conclusion :** Le volume total de données brutes disponibles est estimé entre **3 000 et 10 000 annonces actives** sur les principaux portails. Cela est **suffisant pour un MVP**, mais insuffisant pour un modèle de production robuste sans enrichissement.

### 2.2. Variables Disponibles

| Variable                                    | Disponibilité         | Commentaires                                |
| ------------------------------------------- | --------------------- | ------------------------------------------- |
| **Prix / Loyer**                            | ✅ Toutes sources     | En FCFA, parfois en €/$                     |
| **Ville**                                   | ✅ Toutes sources     | Douala, Yaoundé principalement              |
| **Quartier**                                | ✅ Geloka, Koutchoumi | Parfois imprécis (ex: "Douala")             |
| **Type de bien**                            | ✅ Toutes sources     | Studio, appartement, maison, boutique       |
| **Nombre de chambres**                      | ✅ Koutchoumi, Jumia  | Parfois manquant                            |
| **Nombre de salles de bain**                | ✅ Koutchoumi         | Souvent manquant                            |
| **Surface (m²)**                            | ❌ Rare               | Seulement sur certaines annonces Koutchoumi |
| **Meublé / Non meublé**                     | ⚠️ Partiel            | Mentionné dans le texte, pas structuré      |
| **Équipements (parking, générateur, etc.)** | ⚠️ Partiel            | Dans la description textuelle               |
| **Date de publication**                     | ❌ Rare               | Sauf sur Geloka (mis à jour hebdo)          |
| **Photos**                                  | ✅ Koutchoumi, Jumia  | Utile pour validation, pas pour ML          |
| **Contact (téléphone, email)**              | ✅ Toutes sources     | À exclure du modèle                         |

### 2.3. Qualité des Données

- **Données manquantes** : ~30-40% des annonces n'ont pas le nombre de chambres/salles de bain. La surface est rare (<10%).
- **Doublons** : Probables entre Koutchoumi et Jumia House (mêmes annonces repostées).
- **Fiabilité** : Geloka semble le plus fiable (données vérifiées). Koutchoumi a du volume mais moins de contrôle.
- **Fraîcheur** : Geloka mis à jour hebdomadairement. Koutchoumi/Jumia : inconnu, risque d'annonces obsolètes.

### 2.4. Contraintes d'Utilisation

| Source           | Contraintes                                     | Risques                        |
| ---------------- | ----------------------------------------------- | ------------------------------ |
| **Geloka**       | Citation requise, pas d'API publique            | Scraping possible mais limité  |
| **Koutchoumi**   | Pas d'API, conditions d'utilisation non claires | Blocage IP, CGU à vérifier     |
| **Jumia House**  | Site peu actif, risque de données obsolètes     | Faible fraîcheur               |
| **Facebook**     | API limitée, modération stricte                 | Risque de bannissement         |
| **MINHAB / INS** | Accès formel requis                             | Délais longs, données agrégées |

---

## 3. Structure Brute des Données (Exemple)

### 3.1. Extrait de Dataset (basé sur deegeorgie + Geloka)

```csv
ville,quartier,type,loyer_fcfa,chambres,salles_de_bain,surface_m2,meuble,source,date
Douala,Bonamoussadi,Appartement,300000,3,2,,Non,Geloka,2026-10-07
Douala,Kotto,Appartement,100000,2,1,,Non,Koutchoumi,
Yaoundé,Bastos,Appartement,500000,3,2,,Oui,Appartementaloueryaounde,
Yaoundé,Elig Essono,Studio,65000,1,1,,Non,Geloka,2026-10-07
```

### 3.2. Problèmes Identifiés

- **Surface manquante** : Critère important pour l'estimation, mais rarement disponible.
- **Date de publication** : Absente sur la plupart des sources, complique l'analyse temporelle.
- **Quartier imprécis** : Parfois seulement la ville est indiquée.
- **Devises mixtes** : Certaines annonces en FCFA, d'autres en €/$ (nécessite conversion).

---

## 4. Faisabilité du Problème ML

### 4.1. Alimentation du Modèle

| Critère                   | Évaluation            | Commentaires                                                                             |
| ------------------------- | --------------------- | ---------------------------------------------------------------------------------------- |
| **Volume de données**     | ⚠️ Suffisant pour MVP | 3 000-10 000 annonces, mais besoin de plus pour production                               |
| **Variables prédictives** | ✅ Partiel            | Prix, ville, quartier, type, chambres disponibles. Surface manquante.                    |
| **Qualité des labels**    | ✅ Bonne              | Les prix sont généralement explicites                                                    |
| **Fraîcheur**             | ⚠️ Variable           | Geloka fiable, autres sources à vérifier                                                 |
| **Biais potentiels**      | ⚠️ Oui                | Sur-représentation des quartiers haut standing, sous-représentation des zones populaires |

### 4.2. Recommandations

1. **Prioriser Koutchoumi + Geloka** : Volume + qualité.
2. **Enrichir avec Facebook Marketplace** : Pour capter le marché informel (avec précaution).
3. **Créer un pipeline de scraping robuste** : Avec rotation d'IP, gestion des erreurs, stockage brut.
4. **Nettoyer et dédupliquer** : Avant toute modélisation.
5. **Imputer les variables manquantes** : Surface, nombre de salles de bain (via moyennes par quartier/type).
6. **Ajouter des features externes** : Distance au centre, densité de population, sécurité (données OpenStreetMap, INS).

---

## 5. Prochaines Étapes (Livrables)

### 5.1. Data Discovery Report (ce document)

- ✅ Sources identifiées
- ✅ Volume estimé
- ✅ Variables disponibles
- ✅ Qualité et contraintes évaluées

### 5.2. Dataset Exploratoire

```
raw_sample/
├── geloka_sample.csv (84 annonces)
├── koutchoumi_sample.csv (500-1000 annonces)
└── jumia_sample.csv (si disponible)

profiling/
├── missing_values_report.md
├── duplicates_report.md
└── distribution_plots.png

quality_report/
├── data_quality_score.md
└── recommendations.md

eda/
├── univariate_analysis.md
├── bivariate_analysis.md
└── insights.md
```

### 5.3. Architecture Technique (à figer après EDA)

- **Base de données** : MongoDB (flexible pour données semi-structurées)
- **Pipeline ETL** : Airflow (orchestration des scrapings)
- **Transformation** : dbt (nettoyage, features engineering)
- **ML** : Scikit-learn / XGBoost (régression pour estimation de loyers)
- **Cloud** : AWS / GCP (scalabilité, stockage)

---

## 6. Conclusion

**Le problème ML est suffisamment alimenté pour un MVP**, mais nécessite un enrichissement significatif des données pour une production robuste. Les principales limites sont :

- **Surface manquante** (critère clé pour l'estimation)
- **Fraîcheur des données** (certaines sources peu actives)
- **Couverture géographique** (quartiers populaires sous-représentés)

**Recommandation :** Lancer un scraping ciblé sur Koutchoumi + Geloka, produire un dataset de ~5 000 annonces nettoyées, puis itérer sur le modèle avec des features externes (OpenStreetMap, données INS).

---

## 7. Références

- Geloka Baromètre des loyers, 7 octobre 2026 [5]
- Koutchoumi.com, "Plus de 100 000 annonces" [31][35]
- Jumia House Cameroon, ~13 000 clients [29]
- deegeorgie, "Predicting-house-prices-in-Cameroon", 3 068 observations [16]
- Appartementaloueryaounde.com, analyse marché 2026 [6]
