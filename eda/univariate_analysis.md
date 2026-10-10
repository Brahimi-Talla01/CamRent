# Analyse univariée — Silver dataset

**Phase :** 3 — Analyse exploratoire (EDA)
**Source :** `data/processed/silver_listings.parquet` (Silver, Phase 2)
**Périmètre :** 2,992 observations, 23 colonnes.

- **Villes :** Douala (2,811), Yaoundé (181).
- **Colonnes entièrement vides** (0 observation) : `furnished`, `parking`, `gated`, `area_m2`, `posted_at`.

> Chaque statistique est accompagnée du nombre d'observations utilisées.

## 1. Distribution globale de `rent_price`

| Statistique | Valeur |
|---|---|
| Nombre d'observations | 2,992 |
| Moyenne | 241,867 FCFA |
| Médiane | 100,000 FCFA |
| Ecart-type | 908,366 FCFA |
| Min | 1 FCFA |
| Max | 40,000,000 FCFA |
| 1er quartile (Q1) | 80,000 FCFA |
| 3e quartile (Q3) | 200,000 FCFA |
| Asymétrie (skewness) | 34.964 |
| Kurtosis | 1411.642 |
| Nuls | 0 |
| Négatifs | 0 |

### Observations

- Distribution **fortement asymétrique à droite** : skewness ≈ 35.0,
  kurtosis ≈ 1412 (N = 2,992).
- 14 prix signalés hors des bornes
  plausibles de la Phase 2 (voir §9).

### Transformation de la cible

Une **transformation logarithmique est fortement pertinente**. Sur `log1p(rent_price)` :

| Statistique (log1p) | Valeur |
|---|---|
| Moyenne | 11.824 |
| Médiane | 11.513 |
| Ecart-type | 0.919 |
| Asymétrie | 0.113 |

L'asymétrie passe de ~35.0 à 0.11 (N = 2,992) :
la distribution log-transformée est quasi-normale.
Recommandation pour la Phase 5 : entraîner sur `log1p(rent_price)` puis retransformer.

## 2. Distribution par ville

| Ville | N | Moyenne | Médiane | Min | Max | Ecart-type |
|---|---|---|---|---|---|---|
| Douala | 2,811 | 227,372 | 100,000 | 1 | 25,000,000 | 557,739 |
| Yaoundé | 181 | 466,978 | 150,000 | 50 | 40,000,000 | 2,966,557 |

## 3. Distribution par type de bien

| Type | N | Moyenne | Médiane | Min | Max |
|---|---|---|---|---|---|
| apartment | 2,903 | 242,992 | 100,000 | 50 | 40,000,000 |
| studio | 73 | 206,986 | 80,000 | 1 | 1,500,000 |
| room | 15 | 193,333 | 40,000 | 30,000 | 1,050,000 |
| house | 1 | 250,000 | 250,000 | 250,000 | 250,000 |

## 4. Quartiers reconnus vs non reconnus

| Reconnu | N | Moyenne | Médiane |
|---|---|---|---|
| Oui | 2,410 | 222,655 | 100,000 |
| Non | 582 | 321,418 | 130,000 |

## 5. Republications

| Ligne republication ? | N | Médiane |
|---|---|---|
| Oui | 1,970 | 100,000 |
| Non | 1,022 | 150,000 |

## 6. Prix bornés (`price_is_bound = true`)

| Borné | N | Médiane |
|---|---|---|
| Oui | 2,564 | 100,000 |
| Non | 428 | 185,000 |

## 7. Sources

| Source | N | Moyenne | Médiane | Max |
|---|---|---|---|---|
| reference_local | 2,987 | 242,143 | 100,000 | 40,000,000 |
| koutchoumi | 5 | 77,000 | 40,000 | 230,000 |

- La source la moins fournie (`koutchoumi`) ne compte que
  5 lignes : trop peu pour évaluer son bruit.

## 8. Qualité

### 8.1 Colonnes avec valeurs manquantes

| Colonne | N manquant | % du total |
|---|---|---|
| `bedrooms` | 5 | 0.17% |
| `bathrooms` | 6 | 0.20% |
| `furnished` | 2,992 | 100.00% |
| `parking` | 2,992 | 100.00% |
| `gated` | 2,992 | 100.00% |
| `area_m2` | 2,992 | 100.00% |
| `posted_at` | 2,992 | 100.00% |

Les colonnes à 100 % manquant (`furnished`, `parking`, `gated`, `area_m2`, `posted_at`) sont inutilisables en l'état.

### 8.2 Cohérence ville / quartier

- 34 quartiers canoniques reconnus utilisés
  (Douala : 19, Yaoundé : 15).
- 0 quartier reconnu rattaché à plus d'une ville
  (attendu : 0 → cohérence ville/quartier vérifiée).
- 582 observations portent sur des
  quartiers non reconnus.

## 9. Valeurs aberrantes (`outlier_flags`)

17 lignes signalées, **conservées** (jamais supprimées).
Répartition : bathrooms_outlier : 3, price_outlier : 14.

| Source | Ville | Type | Prix | Drapeau |
|---|---|---|---|---|
| reference_local | Douala | studio | 1,200,000 | bathrooms_outlier |
| reference_local | Yaoundé | apartment | 50 | price_outlier |
| reference_local | Douala | studio | 80,000 | bathrooms_outlier |
| reference_local | Douala | studio | 1 | price_outlier |
| reference_local | Yaoundé | apartment | 40,000,000 | price_outlier |
| reference_local | Douala | studio | 80,000 | bathrooms_outlier |
| reference_local | Douala | apartment | 2,500,000 | price_outlier |
| reference_local | Douala | apartment | 2,500,000 | price_outlier |
| reference_local | Douala | apartment | 2,500,000 | price_outlier |
| reference_local | Douala | apartment | 2,900,000 | price_outlier |
| reference_local | Douala | apartment | 2,600,000 | price_outlier |
| reference_local | Douala | apartment | 3,800,000 | price_outlier |
| reference_local | Douala | apartment | 2,500,000 | price_outlier |
| reference_local | Douala | apartment | 25,000,000 | price_outlier |
| reference_local | Douala | apartment | 2,500,000 | price_outlier |
| reference_local | Douala | apartment | 2,800,000 | price_outlier |
| reference_local | Douala | apartment | 2,900,000 | price_outlier |

## 10. Chambres et salles de bain

| Statistique | Chambres | Salles de bain |
|---|---|---|
| N | 2,987 | 2,986 |
| Moyenne | 2 | 2 |
| Médiane | 2 | 2 |
| Min | 1 | 1 |
| Max | 5 | 80 |
| Nuls | 0 | 0 |
| Hors plage | 0 | 3 |

---
*Rapport dérivé de `eda/statistics.json` (généré par `eda/compute_statistics.py`)*
*Aucune valeur n'est saisie manuellement : rejouer les scripts régénère ces chiffres.*
