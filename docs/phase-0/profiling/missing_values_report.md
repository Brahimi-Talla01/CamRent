# Profiling — Valeurs manquantes

**Échantillon :** `data/samples/koutchoumi1.csv` (2 565 lignes) et `data/samples/jumia.csv` (500 lignes)
**Méthode :** `python docs/phase-0/scripts/profile_sample.py data/samples`

## Par colonne

### koutchoumi1.csv

| Colonne | Vidés | Distinctes | Valeurs fréquentes |
|---|---|---|---|
| `Area` | 0 % | 48 | `Douala/Makepe` (1 005), `Douala/Logpom` (300) |
| `Bathrooms` | 0 % | 5 | `> 2 bathrooms` (1 118), `> 1 bathroom` (1 087) |
| `Bedrooms` | 0 % | 4 | `> 2 bedrooms` (1 424), `> 1 bedroom` (600) |
| `Price` | 0 % | 89 | `> 100 000 FCFA` (310), `> 80 000 FCFA` (267) |
| `Type` | 0 % | 8 | `2 bedrooms apartment to rent` (1 394) |

*Textuellement complet, **mais** : prix exprimés en bornes (`"> X"`) et chambres/sdb *bucketed*.*

### jumia.csv

| Colonne | Vidés | Distinctes | Valeurs fréquentes |
|---|---|---|---|
| `index` | 0 % | 500 | identifiant de ligne |
| `Address` | 0 % | 203 | `Bonapriso, Douala, Littoral` (62) |
| `Bathrooms` | 0 % | 13 | `2 Salles de bain` (267) |
| `Bedrooms` | **0,4 %** (2) | 13 | `2 Chambres` (273) |
| `Designation` | 0 % | 341 | texte libre |
| `Price` | 0 % (texte) | 63 | **`Prix : Contactez le vendeur` (55)** |

## Valeurs manquantes « effectives »

| Champ | Statut | Détail |
|---|---|---|
| **Surface** | **100 % absente** | Aucune colonne de surface dans les deux fichiers |
| **Prix (jumia)** | **11 % inexploitable** | 55/500 annonces = « Contactez le vendeur » |
| **Date de publication** | **100 % absente** | Aucune colonne de date |
| **Meublé** | Non structuré | Encodé dans `Type` (koutchoumi) / `Designation` (jumia) |
| **Équipements** (parking, barrière, eau…) | **Absents** | À extraire du texte, non disponible ici |
| **Salles de bain / chambres** | Non numériques | Texte *bucketed* ou libellés FR/EN |

## Conclusion

La complétude **textuelle** est trompeuse : les champs décisifs pour l'estimation (**surface**,
équipements, date) sont **absents**, et le prix est soit censuré (Koutchoumi), soit manquant
(Jumia, 11 %). Toute imputation de surface serait une **invention** et n'est pas retenue.
