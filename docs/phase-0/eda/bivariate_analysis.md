# EDA — Analyse bivariée

## Loyer médian par ville

| Ville | koutchoumi1 | jumia |
|---|---|---|
| Douala | 100 000 (n = 2 509) | 250 000 (n = 309) |
| Yaoundé | 257 500 (n = 56) | 120 000 (n = 131) |

- Les deux sources donnent des **signaux opposés** sur le classement Douala/Yaoundé. Les expliquer :
  Koutchoumi est **censuré** et **quasi exclusivement Douala** ; Jumia couvre mieux Yaoundé.
  → **Ne pas fusionner naïvement** les deux sources pour comparer les villes.
- Le faible `n` de Yaoundé chez Koutchoumi (56) rend toute conclusion **non fiable**.

## Loyer médian par nombre de chambres

**jumia**

| Chambres | n | Médiane |
|---|---|---|
| 1 | 84 | 80 000 |
| 2 | 242 | 162 500 |
| 3 | 110 | 300 000 |
| 4 | 4 | 825 000 |
| 5 | 3 | 1 500 000 |

**koutchoumi1** (bornes)

| Chambres | n | Médiane |
|---|---|---|
| 1 | 600 | 60 000 |
| 2 | 1 424 | 100 000 |
| 3 | 521 | 200 000 |
| 4 | 20 | 400 000 |

- **Relation nette et monotone** entre nombre de chambres et loyer, **cohérente entre les deux
  sources** → le nombre de chambres est un **prédicteur utile** et robuste.
- Au-delà de 4 chambres, les effectifs deviennent trop faibles pour conclure.

## Loyer × salles de bain

Non calculé de façon fiable ici : la variable SdB est *bucketed* chez Koutchoumi (`> 2 bathrooms`)
et sa corrélation avec les chambres est forte (redondance probable). À traiter en feature engineering
(Phase 6), avec prudence sur la colinéarité.

## Effet « source »

| | Koutchoumi | Jumia |
|---|---|---|
| Prix | bornes (`≥ X`) | exacts |
| Villes | Douala 98 % | Douala 71 % |
| Doublons | 71,7 % | 0 % |
| Prix manquants | 0 % | 11 % |

- Chaque source a un **biais propre**. Une future collecte devra **homogénéiser** (source, date,
  identifiant) avant toute comparaison ou entraînement.

## Corrélations

- **Chambres ↔ loyer** : positive, attendue et exploitable.
- **Chambres ↔ salles de bain** : forte (redondance) — à surveiller pour éviter la multicolinéarité.
- **Ville ↔ loyer** : dépendante de la source ; à traiter par ville, pas globalement.
