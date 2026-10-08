# EDA — Analyse univariée

**Échantillon :** 3 065 lignes brutes (koutchoumi1 2 565 ; jumia 500).

## Loyer (`Price`)

| Statistique | koutchoumi1 | jumia |
|---|---|---|
| Exploitables | 2 565 (100 %) | 445 / 500 (89 %) |
| Min | 0 | 1 |
| P25 | 80 000 | 100 000 |
| **Médiane** | **100 000** | **200 000** |
| P75 | 160 000 | 600 000 |
| Max | 25 000 000 | 40 000 000 |
| Moyenne | 204 270 | 501 726 |
| `≤ 0` | 1 | 0 |
| `< 20 000` | 7 | 2 |
| `> 2 M` | 11 | 4 |

- Distributions **fortement asymétriques** à droite (moyenne ≫ médiane) → une transformation
  **logarithmique** sera à étudier.
- Rappel : les prix Koutchoumi sont des **bornes inférieures** (`"> X"`), donc la médiane « 100 000 »
  signifie « au moins 100 000 ».

## Localisation

**Villes**

| Ville | koutchoumi1 | jumia |
|---|---|---|
| Douala | 2 509 (98 %) | 355 (71 %) |
| Yaoundé | 56 (2 %) | 138 (28 %) |
| Kribi / Buéa / Bafoussam | 0 | 7 (hors périmètre) |

**Quartiers (top)**

| koutchoumi1 | jumia |
|---|---|
| Makepe (1 005), Logpom (300), Bonamoussadi (289), Bonapriso (188), Akwa I (173) | Bonapriso (68), Akwa (33), Logpom (20), Makepe (20), Bonamoussadi (17), Bastos (15) |

- 48 quartiers distincts (koutchoumi) et 177 (jumia) → **référentiel à normaliser**.
- Concentration extrême chez Koutchoumi : un seul quartier (Makepe) = **39 %** des lignes.

## Chambres et salles de bain

| Valeur | Chambres (koutchoumi) | Chambres (jumia) | SdB (jumia) |
|---|---|---|---|
| 1 | 600 | 99 | 124 |
| 2 | 1 424 | 274 | 267 |
| 3 | 521 | 114 | 78 |
| 4 | 20 | 5 | 14 |
| 5+ | 0 | 3 (`5`) | 3 (`5`) |
| **Aberrant** | — | `20` (1) | `80` (2) |

## Type de bien (koutchoumi)

8 valeurs, dominées par `X bedrooms apartment to rent` (1, 2, 3 chambres), plus quelques
`... furnished ...`. Le **meublé** n'existe pas comme champ : il est encodé dans le libellé.

## Absences structurelles

- **Surface : absente** dans les deux fichiers.
- **Date de publication : absente**.
- **Équipements** (parking, barrière, eau, électricité) : absents.
