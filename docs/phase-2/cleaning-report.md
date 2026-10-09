# Rapport de nettoyage — Silver dataset

**Phase :** 2 — Data cleaning
**Généré le :** 2026-10-09 07:06 UTC
**Source :** Raw immuable (`data/raw/`) → ne sont jamais modifiés.

## Récapitulatif

| Étape | Volume |
|---|---|
| Observations brutes lues | 3078 |
| Observations adaptées (source gérée) | 3070 |
| **Lignes Silver** | **2992** |
| **Lignes en quarantine** | **78** |

## Règles appliquées et impact

| Règle | Volume |
|---|---|
| Ville absente ou hors périmètre — quarantine | 7 |
| Prix ≤ 0 — quarantine | 1 |
| Prix absent — quarantine | 52 |
| Même logement republié — conservé et marqué `is_republication` | 1970 |
| Type de bien non reconnu — quarantine | 18 |

- **Aberrations signalées** (gardées, `outlier_flags`) : 17
- **Prix bornés** (minimums, `price_is_bound`) : 2564
- **Quartiers non reconnus** (`neighborhood_recognized=false`) : 582

## Répartition par source

| Source | Volume |
|---|---|
| jumia.csv | 423 |
| koutchoumi (live) | 5 |
| koutchoumi1.csv | 2564 |

## Répartition par ville

| Ville | Volume |
|---|---|
| Douala | 2811 |
| Yaoundé | 181 |

## Rappel des invariants

- `data/raw/` n'est **jamais** modifié.
- Aucune valeur aberrante n'est supprimée : elles sont signalées (`outlier_flags`).
- Les observations invalides vont en **quarantine**, jamais dans le vide.
- Aucune imputation permissive n'est appliquée.
