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

10. **Motifs de rejet en base** (lot B du plan de réalignement) : charger la quarantaine et les
    métadonnées de lot dans PostgreSQL et exposer une **table de qualité** (motifs de rejet
    agrégés, volumes) — support du module « Qualité » du back-office (Phase 13).

11. **Sémantique de cible** (décision 9) : documenter que `rent_price` est un loyer **demandé**
    dans l'annonce, via une colonne `rent_semantics` (`asking_rent` / `unknown`), sans renommer
    la cible.

12. **Bornes de pièces** : contrôler `bedrooms` et `bathrooms` au-delà de la borne plausible
    (`ROOMS_MAX_PLAUSIBLE`, 10 par défaut). Une borne supérieure n'est **pas** un filtre :
    `bathrooms = 80` (3 observations réelles) est conservé et **signalé** dans `outlier_flags`
    (`bathrooms_outlier`), conformément à l'invariant « aucune valeur extrême supprimée ».
    Le signalement est vérifié côté warehouse par le test singulier
    `assert_implausible_rooms_are_signalled`. Documenter également le traitement des prix
    extrêmes (signalés, jamais supprimés).

13. **Drapeaux à trois états** : distinguer `false` (vérifié, absent), `true` (présent) et
    `unknown` (non vérifiable) pour les équipements (`furnished`, `parking`, `gated`) — ne jamais
    conclure une absence d'un simple manque d'information.

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
- La quarantaine et les motifs de rejet sont interrogeables en base (table de qualité).
- `rent_semantics` documente la sémantique de la cible dans le dataset.
- Les bornes de pièces sont contrôlées et leur signalement est vérifié (test dbt).

## État d'implémentation (2026-10-16)

- **Provenance renforcée** (lot B) : chaque nouveau lot consigne `connector_version`,
  `content_sha256` et `lot_validation_status` dans ses métadonnées (`ingestion/storage.py`).
- **Qualité en base** (lot B) : `landing.quarantine_listings` et `landing.ingestion_runs` sont
  chargées par `python -m pipelines load` ; `mart_data_quality` agrège les motifs de rejet et
  `mart_ingestion_lots` expose les lots. Somme des motifs = 78 rejets (réconciliée par test).
- **`rent_semantics`** (lot B) : exposé par `mart_ml_dataset` ; `asking_rent` sur les 2 992
  observations actuelles (aucune cible sans prix dans le Silver, les prix manquants étant en
  quarantaine).
- **Bornes de pièces** (lot B) : règle confirmée appliquée en Phase 2 (`pipelines/silver.py`),
  vérifiée par `assert_implausible_rooms_are_signalled`.
