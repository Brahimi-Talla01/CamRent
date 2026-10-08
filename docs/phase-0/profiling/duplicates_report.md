# Profiling — Doublons

**Méthode :** `python docs/phase-0/scripts/profile_sample.py data/samples` (doublons = lignes strictement identiques)

## Résultats

| Fichier | Lignes brutes | Lignes uniques | Doublons | Taux |
|---|---|---|---|---|
| `koutchoumi1.csv` | 2 565 | **726** | **1 839** | **71,7 %** |
| `jumia.csv` | 500 | 500 | 0 | 0 % |
| **Total** | **3 065** | **1 226** | **1 839** | **60,0 %** |

## Analyse

- **Koutchoumi** : la duplication est **massive et quasi structurante**. À titre d'illustration,
  la seule valeur d'`Area` `Douala/Makepe` apparaît **1 005 fois**. Cela ressemble à un artefact de
  **pagination** lors du crawl (mêmes pages relues), et non à des logements réellement distincts.
  → Le volume réel vers Douala/Yaoundé est donc de l'ordre de **~700 lignes**, pas 2 565.
- **Jumia** : aucun doublon exact. Les annonces semblent distinctes.

## Nature des doublons

Ici, les doublons détectés sont des **doublons techniques** (lignes identiques), à distinguer de :

- **même logement republié** (annonces différentes décri­vant le même bien) — non détectable
  sans identifiant de bien ni date ;
- **logements réellement différents** partageant des caractéristiques proches.

L'absence d'**identifiant de source** et de **date** empêche de traiter proprement les deux derniers
cas. C'est une limite à corriger en Phase 1 (conserver `source_listing_id` et la date de collecte).

## Conséquence

La déduplication en Phase 2 devra :

1. supprimer les doublons **exacts** (règle simple et sûre) ;
2. conserver `source` + `source_listing_id` + date de collecte pour traiter les republications ;
3. **documenter** le volume retiré (ici ≈ 1 839 lignes, soit 71,7 % de Koutchoumi).
