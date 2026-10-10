# Insights — Silver dataset (Phase 3)

**Phase :** 3 — Analyse exploratoire (EDA)
**Source :** `data/processed/silver_listings.parquet` (Silver, Phase 2)
**Périmètre :** 2,992 observations.

> Chaque insight est accompagné du nombre d'observations. Les zones à faible
> volume sont explicitement signalées comme **non fiables**.

## Synthèse exécutive

- `2,992` observations Silver
  (Douala : 2,811, Yaoundé : 181).
- `2,564` prix bornés (85.70%) :
  la cible est majoritairement un `> X` (borne inférieure), pas un prix exact.
- `1,970` republications (65.84%) :
  les données sont très dupliquées.
- Distribution **très asymétrique** (skewness ≈ 35.0) :
  une **transformation log est nécessaire**.
- **Aucune surface** (`area_m2` absent) et **aucune date** (`posted_at` absent) :
  pas de `rent_per_m2`, pas d'analyse temporelle.
- **Aucun meublé, parking, barrière** : ces features sont inutilisables pour le MVP.

## Insights détaillés

### 1. Distribution des loyers

- Moyenne 241,867 FCFA contre médiane 100,000 FCFA
  (N = 2,992) → distribution très asymétrique.
- Prix typique : 80,000–200,000 FCFA (Q1–Q3).
- La transformation `log1p` rend la distribution quasi-normale
  (skewness ≈ 0.11 contre 35.0 avant).

### 2. Géographie

- **Douala** domine (93.95% des lignes) ;
  Yaoundé (181 lignes) est beaucoup plus petit.
- 2,410 observations sur des quartiers reconnus,
  582 sur des quartiers non reconnus
  (noms à normaliser au référentiel).
- Médianes par ville : Douala 100,000 FCFA
  (N = 2,811) vs Yaoundé 150,000 FCFA
  (N = 181) — l'écart de volume rend la comparaison fragile.

### 3. Effet du type de bien

- `apartment` domine :
  2,903/2,992 =
  97.03%.
- Les autres types sont marginaux, ce qui limite l'analyse de segment.

### 4. Effet du nombre de chambres

- La médiane augmente avec le nombre de chambres, mais les observations pour
  4-5 chambres sont rares (voir §4 du rapport bivarié) → à utiliser avec précaution.

### 5. Prix bornés et republications

- 2,564 prix bornés
  (85.70%) : conservés avec `price_is_bound=true`,
  à pondérer/exclure à l'entraînement (Phases 5-6).
- 1,970 republications
  (65.84%) : à décider (conserver / pondérer / dédupliquer).

### 6. Quartiers sous-représentés

- 172 quartiers distincts au total.
- 103 n'apparaissent
  qu'**une seule fois**.
- 152 quartiers comptent
  ≤ 10 observations (soit
  299 lignes) : leurs statistiques sont
  **non fiables** et ne sont pas publiées comme médianes de référence.
- Aucune médiane par quartier n'est publiée en dessous de
  30 observations.

### 7. Biais de couverture

- Les 5 quartiers les plus présents concentrent 68.7 % des
  lignes et les 10 premiers 82.2 % → **fort biais de couverture**.
- `price_is_bound=true` sur 85.70% des lignes :
  ces prix sont des bornes inférieures (`> X`), donc le loyer réel est ≥ la valeur observée.
- 582 observations hors référentiel de quartiers :
  risque de zones populaires mal représentées.

### 8. Décisions de feature engineering (issues de l'EDA)

- **Cible** : entraîner sur `log1p(rent_price)` (distribution rendue quasi-normale).
- **À conserver** : `city`, `neighborhood`, `property_type`, `bedrooms`, `bathrooms`,
  `price_is_bound`, `neighborhood_recognized`, `is_republication`, `outlier_flags`.
- **À écarter (vides)** : `area_m2`, `furnished`, `parking`, `gated`, `posted_at`.
- **À traiter** : pondérer/exclure les prix bornés ; décider du sort des republications ;
  enrichir/canonicaliser les quartiers non reconnus.
- **Interdit** : toute feature dérivée de la cible (ex. `rent_per_m2`).

### 9. Conclusion sur la transformation de la cible

La transformation `log1p` est **recommandée** : elle ramène l'asymétrie de
~35.0 à 0.11 sur 2,992 observations,
condition nécessaire pour exploiter une régression linéaire (baseline de la Phase 5).

### 10. Zones à faible volume

- **Yaoundé** : 181 observations
  (6.05%) → comparaisons inter-villes fragiles.
- **Sources secondaires** : voir §7 du rapport univarié — certaines sources
  contribuent trop peu pour être analysées séparément.
- **Quartiers sous-représentés** : voir §6.

---
*Rapport dérivé de `eda/statistics.json` (généré par `eda/compute_statistics.py`)*
*Aucune valeur n'est saisie manuellement : rejouer les scripts régénère ces chiffres.*
