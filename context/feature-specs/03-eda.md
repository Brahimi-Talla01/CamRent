# Phase 3 — Analyse exploratoire (EDA)

Lire `context/architecture-context.md` avant de commencer.

Objectif : comprendre la structure, la distribution et les relations du Silver dataset, et produire
un **rapport EDA** qui guide le feature engineering et le choix des modèles.

## Implementation

1. **Distribution** :

   - distribution des loyers ;
   - asymétrie — une transformation logarithmique est-elle pertinente ?
   - valeurs extrêmes et leur plausibilité.

2. **Géographie** :

   - quartiers les plus chers / les plus accessibles ;
   - différences Yaoundé vs Douala ;
   - quartiers sous-représentés (peu d'observations) ;
   - biais de couverture (sur-représentation du haut standing, sous-représentation des zones populaires).

3. **Caractéristiques** :

   - effet du nombre de chambres ;
   - effet de la superficie ;
   - effet du parking ;
   - effet du meublé ;
   - effet de la sécurité / barrière ;
   - corrélations entre features.

4. **Qualité** :

   - colonnes les plus manquantes ;
   - sources les plus bruitées ;
   - cohérence ville / quartier.

5. **Dimension temporelle** : exploiter la date de publication lorsque disponible.

6. Produire le livrable `eda/` :

   ```
   eda/
   ├── univariate_analysis.md
   ├── bivariate_analysis.md
   └── insights.md
   ```

## Dependencies

- pandas / Polars, matplotlib ou seaborn pour les graphiques.
- Nettoyage (Phase 2) terminé.

## Scope Limits

- Pas d'entraînement de modèle ici.
- Ne pas « pousser » des insights que les données ne soutiennent pas : signaler explicitement les
  zones où le volume est insuffisant.
- Toute statistique affichée doit être accompagnée du **nombre d'observations**.

## Check When Done

- Le rapport EDA est produit (univarié, bivarié, insights).
- Les réponses aux questions de distribution / géographie / caractéristiques / qualité sont écrites.
- Les quartiers sous-représentés sont identifiés et leur non-fiabilité documentée.
- Les décisions de feature engineering qui en découlent sont listées.
- Une première conclusion existe sur la pertinence d'une transformation de la cible.
