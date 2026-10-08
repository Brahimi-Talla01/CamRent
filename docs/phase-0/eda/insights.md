# EDA — Enseignements

1. **Le volume réel est bien plus faible qu'annoncé.**
   3 065 lignes brutes → **≈ 1 226 lignes uniques** après déduplication (71,7 % de doublons
   Koutchoumi). C'est un point que le rapport amont surestimait.

2. **Les deux sources ne mesurent pas la même chose.**
   Jumia donne des prix **exacts** ; Koutchoumi donne des **bornes** (`≥ X`). Les fusionner sans
   précaution produirait un **biais systématique vers le bas**.

3. **Le nombre de chambres est le signal le plus fiable.**
   Relation monotone et cohérente entre les deux sources (médiane : 1 → 80 k, 2 → ~150 k,
   3 → 200-300 k FCFA). C'est le meilleur candidat de feature du MVP.

4. **La surface et la date sont absentes.**
   Or la surface est un critère clé d'estimation. Sans collecte supplémentaire, le MVP **ne peut pas**
   proposer d'estimation au m², ni de suivi temporel.

5. **La couverture est très déséquilibrée.**
   Koutchoumi = 98 % Douala et un quartier (Makepe) concentre 39 % des lignes. Un modèle entraîné
   là-dessus **sur-apprendrait** quelques quartiers.

6. **La qualité brute est faible mais réparable.**
   Aberrations (`Price = 0/1`, `20` chambres, `80` sdb), formats hétérogènes, quartiers non
   normalisés. Rien d'irréparable, à condition d'un pipeline de nettoyage soigné (Phase 2).

7. **Un référentiel géographique est indispensable.**
   `Akwa` vs `Akwa I`, `Makepe` vs `Makepe II`… La localisation est le facteur le plus important du
   problème : elle doit être **normalisée** avant tout.

## Implications pour la suite

| Constat | Action |
|---|---|
| Volume insuffisant | Collecte supplémentaire (Phase 1) **après** vérification des CGU |
| Prix censurés | Décider : exclure, ou modéliser comme bornes |
| Surface absente | La collecter, ou concevoir le MVP sans elle |
| Pas de date | Ajouter `collected_at` et viser des sources datées |
| Sources hétérogènes | Normaliser par un schéma cible unique (Phase 2) |
| Quartiers multiples | Construire un référentiel ville → quartiers |

**Verdict :** données suffisantes pour **valider la démarche** et amorcer une **baseline**, mais
**insuffisantes** pour un modèle robuste. Voir `../feasibility.md`.
