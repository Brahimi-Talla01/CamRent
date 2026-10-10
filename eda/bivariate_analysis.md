# Analyse bivariée — Silver dataset

**Phase :** 3 — Analyse exploratoire (EDA)
**Source :** `data/processed/silver_listings.parquet` (Silver, Phase 2)
**Périmètre :** 2,992 observations.

> Chaque statistique est accompagnée du nombre d'observations utilisées.

## 1. Corrélations entre variables numériques

| Variable | `rent_price` | `bedrooms` | `bathrooms` |
|---|---|---|---|
| `rent_price` | 1.000 | 0.119 | 0.046 |
| `bedrooms` | 0.119 | 1.000 | 0.188 |
| `bathrooms` | 0.046 | 0.188 | 1.000 |

- `rent_price` est faiblement corrélé avec `bedrooms` (N = 2,992).
- `bathrooms` est faiblement corrélé avec `bedrooms` et `rent_price`.

## 2. Prix médian par ville

| Ville | N | Médiane | Moyenne |
|---|---|---|---|
| Douala | 2,811 | 100,000 | 227,372 |
| Yaoundé | 181 | 150,000 | 466,978 |

## 3. Effet du nombre de chambres

| N chambres | N | Médiane | Moyenne |
|---|---|---|---|
| 1 | 681 | 60,000 | 102,980 |
| 2 | 1,654 | 100,000 | 231,905 |
| 3 | 628 | 225,000 | 395,955 |
| 4 | 23 | 400,000 | 844,348 |
| 5 | 1 | 1,500,000 | 1,500,000 |

- La médiane augmente avec le nombre de chambres (tendance directionnelle),
  mais sans surface et avec très peu d'observations pour 4-5 chambres.

## 4. Quartiers les plus chers / les plus accessibles

Top-5 par nombre d'observations (les plus fiables) :

| Quartier | N | Médiane | Part de prix bornés |
|---|---|---|---|
| Makepe | 1,026 | 80,000 | 98.1 % |
| Logpom | 318 | 90,000 | 94.3 % |
| Bonamoussadi | 304 | 120,000 | 95.1 % |
| Bonapriso | 234 | 725,000 | 80.3 % |
| Akwa I | 173 | 300,000 | 100.0 % |

Parmi les quartiers comptant au moins 30 observations :

**Les plus chers (médiane la plus élevée) :**

| Quartier | N | Médiane |
|---|---|---|
| Bonapriso | 234 | 725,000 |
| Bonanjo | 54 | 675,000 |
| Bastos | 35 | 500,000 |
| Akwa | 30 | 500,000 |
| Bali | 96 | 300,000 |

**Les plus accessibles (médiane la plus faible) :**

| Quartier | N | Médiane |
|---|---|---|
| Makepe | 1,026 | 80,000 |
| Cite Ubo Palmiers | 32 | 90,000 |
| Logpom | 318 | 90,000 |
| Malangue | 109 | 100,000 |
| Kotto | 93 | 110,000 |

- 582 observations portent sur des quartiers
  **non reconnus** : signalées, non agrégées ici.

## 5. Effet surface, parking, meublé, barrière

| Caractéristique | Statut dans Silver |
|---|---|
| `furnished` | **Entièrement absent** (0 observation) |
| `parking` | **Entièrement absent** (0 observation) |
| `gated` | **Entièrement absent** (0 observation) |
| `area_m2` | **Entièrement absent** (0 observation) |

→ Aucune analyse bivariée possible : ces attributs sont absents de toutes les
sources collectées (0 observation chacun).

## 6. Dimension temporelle

| Statut | Résultat |
|---|---|
| Colonne `posted_at` | **Absente** (0 observation disponible) |

→ Aucune analyse temporelle possible : la source ne fournit pas de date de publication.

---
*Rapport dérivé de `eda/statistics.json` (généré par `eda/compute_statistics.py`)*
*Aucune valeur n'est saisie manuellement : rejouer les scripts régénère ces chiffres.*
