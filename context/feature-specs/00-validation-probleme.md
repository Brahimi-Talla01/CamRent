# Phase 0 — Validation du problème

Lire `context/project-overview.md` et `context/ai-workflow-rules.md` avant de commencer.

Objectif : **prouver que le problème Data est correctement défini et que les données disponibles
permettent de construire une estimation utile.** Aucune architecture complexe ne doit être
considérée comme définitive avant cette phase.

## Implementation

1. Consolider le **Data Discovery Report** (`assets/Data_Discovery_Report.md`) et vérifier qu'il couvre
   pour chaque source : URL / origine, type, méthode de collecte, fréquence, volume estimé, structure,
   variables disponibles, qualité, contraintes, utilisation possible.

2. Vérifier les **contraintes légales et d'usage** avant toute collecte :

   - conditions d'utilisation (CGU) ;
   - règles `robots.txt` ;
   - droits sur les données et possibilité de stockage / réutilisation ;
   - restrictions concernant le scraping.

3. Produire un **échantillon exploratoire** dans `data/samples/` :

   ```
   data/samples/
   ├── geloka_sample.csv
   ├── koutchoumi_sample.csv
   └── jumia_sample.csv        (si disponible)
   ```

   Priorité : **Koutchoumi** (volume) + **Geloka** (qualité/fiabilité).

4. Produire le **profiling** :

   ```
   profiling/
   ├── missing_values_report.md
   ├── duplicates_report.md
   └── distributions
   ```

   Mesurer notamment : proportion de valeurs manquantes par colonne, doublons probables entre
   sources, devises mixtes (FCFA / € / $), quartiers écrits de plusieurs façons.

5. Produire un **rapport de qualité** (`quality_report/`) : score qualité + recommandations.

6. Conclure explicitement sur la **faisabilité ML** :

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

## Dependencies

- Aucune dépendance technique imposée à ce stade.
- Python + outils de profiling (pandas, et un outil de profiling de DataFrame) une fois l'outillage figé.

## Scope Limits

- Ne pas commencer l'architecture cible ni le frontend.
- Ne pas figer la stack (MongoDB, Airflow, dbt, cloud) pendant cette phase.
- Ne pas lancer de collecte automatisée à grande échelle avant validation des contraintes légales.
- Ne pas nettoyer ni modéliser : cette phase **mesure** les données, elle ne les transforme pas.

## Check When Done

- Le Data Discovery Report est complet (10 points ci-dessus renseignés).
- Les contraintes légales par source sont documentées.
- Les échantillons bruts sont présents dans `data/samples/`.
- Les rapports de manquants et de doublons sont produits.
- Un verdict clair de faisabilité (volume, variables, limites) est écrit.
- Une décision explicite existe sur la stack à retenir (ou son report).
