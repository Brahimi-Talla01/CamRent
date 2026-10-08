# Phase 2 — Data cleaning

Lire `context/architecture-context.md` et `context/code-standards.md` avant de commencer.

Objectif : produire le **Silver dataset** — jeux de données nettoyés et standardisés à partir du
Raw immuable, sans jamais perdre l'origine d'une valeur.

## Implementation

1. **Gestion des types** : convertir `rent_price` en numérique, `bedrooms` / `bathrooms` en entiers,
   `area_m2` en numérique.

2. **Normalisation des devises** : convertir les prix en € / $ vers le FCFA (taux documenté).

3. **Normalisation des quartiers** : résoudre les variantes comme

   ```
   Bonamoussadi
   bonamoussadi
   Bonamoussadi, Douala
   Bonamoussadi - Douala
   ```

   vers une valeur canonique, associée à une ville connue.

4. **Standardisation des catégories** : `property_type`, `furnished` (oui/non → booléen),
   équipements (`parking`, `gated`, `water`, `electricity`…).

5. **Déduplication** en distinguant :

   - doublon technique ;
   - même logement publié plusieurs fois ;
   - logements réellement différents.

6. **Valeurs manquantes** : les identifier et les marquer ; documenter une stratégie (aucune
   imputation permissive sans validation).

7. **Détection des valeurs aberrantes** : **ne pas supprimer automatiquement**. Un prix de 50 000 ou
   5 000 000 FCFA n'est pas forcément une erreur. Croiser avec le type de logement, la localisation
   et la vérification des données sources.

8. **Quarantine** : router les observations invalides vers une zone dédiée au lieu de les supprimer :

   ```
   raw → validation ├── valid   → silver
                    └── invalid → quarantine
   ```

9. Écrire le **Silver dataset** (Parquet / tables staging) dans `data/processed/` ou en base selon
   la décision de la Phase 4.

## Dependencies

- pandas (ou Polars) pour la transformation Python.
- SQL lorsque la transformation structurée est plus appropriée.
- Référentiel de quartiers / villes construit à partir des données et des sources géographiques.

## Scope Limits

- Ne pas écraser `data/raw/`.
- Ne pas supprimer les données extrêmes : les isoler et les analyser.
- Pas d'EDA complète ici (c'est la Phase 3) : on nettoie et on standardise.
- Pas de feature engineering ML (c'est après l'EDA).

## Check When Done

- Le Silver dataset est produit et reproductible depuis le Raw.
- Les colonnes clés non nulles : `city`, `neighborhood`, `rent_price`, `property_type`.
- Types corrects ; ranges plausibles (`rent_price > 0`, `bedrooms >= 0`, `area_m2 > 0`).
- Les doublons sont traités et documentés.
- Les données invalides sont en quarantine, pas supprimées.
- Un rapport de nettoyage documente chaque règle appliquée et son volume d'impact.
