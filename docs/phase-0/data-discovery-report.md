# Data Discovery Report — CamRent

**Phase :** 0 — Validation du problème
**Date :** 8 octobre 2026
**Périmètre :** Yaoundé et Douala
**Échantillon analysé :** 3 065 lignes brutes (2 fichiers), voir `profiling/` et `eda/`

## 1. Sources identifiées

| Source | Type | Collecte | Volume estimé | Variables clés | Contraintes |
|---|---|---|---|---|---|
| **Koutchoumi** | Portail d'annonces | Scraping | ~100 000 annonces cumulées | ville, quartier, type, chambres, sdb, prix | pas d'API ; CGU à vérifier |
| **Geloka** | Baromètre agrégé | Scraping/API ? | ~84 annonces (oct. 2026) | ville, type, loyer médian, quartier | données agrégées, pas d'historique |
| **Jumia House** | Portail d'annonces | Scraping | ~13 000 clients cumulés | ville, type, prix, chambres | site peu actif, obsolescence |
| **Lewambi** | Portail d'annonces | Scraping | non communiqué | ville, type, prix | peu actif |
| **Facebook** | Annonces utilisateurs | API limitée | élevé | prix, localisation | conditions d'usage strictes |
| **MINHAB / INS** | Données officielles | Demande formelle | limité | statistiques agrégées | accès formel |
| **GitHub `deegeorgie`** | Dataset tiers | Téléchargement | 3 065 lignes réelles | ville, quartier, type, chambres, sdb, prix | **aucune licence** |

## 2. Échantillon réellement analysé

Deux fichiers issus du **dataset public `deegeorgie`** (voir `legal-assessment.md`) :

| Fichier | Lignes brutes | Lignes uniques | Colonnes |
|---|---|---|---|
| `koutchoumi1.csv` | 2 565 | **726** (71,7 % de doublons) | `Area, Bathrooms, Bedrooms, Price, Type` |
| `jumia.csv` | 500 | **500** | `index, Address, Bathrooms, Bedrooms, Designation, Price` |
| **Total** | **3 065** | **1 226** | — |

> ⚠️ Le volume réellement exploitable (**≈ 1 226 lignes**) est très inférieur au « 3 068 » souvent cité.

## 3. Questions du Plan Technique §76

1. **Sources accessibles** — Koutchoumi et Geloka le sont techniquement ; Jumia/Lewambi incertains ;
   Facebook nécessite l'API officielle ; MINHAB/INS sur demande.
2. **Observations mobilisables** — ≈ 1 226 lignes uniques à partir d'un seul dataset tiers, dont
   **726** seulement après déduplication de Koutchoumi.
3. **Variables disponibles** — ville, quartier, type de bien, chambres, salles de bain, prix.
4. **Données manquantes** — **surface absente (0 %)** ; prix manquant sur 11 % de Jumia ;
   « meublé » non structuré. Voir `profiling/missing_values_report.md`.
5. **Doublons** — 71,7 % sur Koutchoumi (voir `profiling/duplicates_report.md`).
6. **Fiabilité des sources** — Geloka (agrégé, fiable) ; Koutchoumi (volume mais dupliqué et prix
   censurés) ; Jumia (détails corrects mais 11 % sans prix) ; `deegeorgie` (sans licence).
7. **Contraintes d'usage** — voir `legal-assessment.md`. Aucune collecte automatisée tant que les CGU
   ne sont pas vérifiées.
8. **Fréquence de collecte** — Geloka hebdomadaire ; autres inconnue ; à cadrer.
9. **Structure brute** — formats hétérogènes entre sources (prix en texte, chambres/sdb *bucketed*,
   quartiers non normalisés). Voir `eda/univariate_analysis.md`.
10. **Faisabilité ML** — **partielle** : voir `feasibility.md`.

## 4. Limites structurelles identifiées

| Limite | Impact |
|---|---|
| **Surface absente** | Critère clé d'estimation indisponible |
| **Prix Koutchoumi en bornes** (`"> 100 000 FCFA"`) | Prix réel inconnu (censure) |
| **71,7 % de doublons (Koutchoumi)** | Volume réel fortement réduit |
| **11 % d'annonces sans prix (Jumia)** | Lignes inutilisables pour la cible |
| **Pas de date de publication** | Aucune dimension temporelle |
| **Schémas hétérogènes entre sources** | Normalisation lourde nécessaire |
| **Quartiers non normalisés** (`Akwa` vs `Akwa I`) | Référentiel géographique à construire |
| **Couverture déséquilibrée** | Koutchoumi quasi exclusivement Douala (98 %) |

## 5. Conclusion

Le Data Discovery Report **confirme partiellement** l'analyse amont : les données existent et le
problème est définissable, mais le volume réellement propre et les variables disponibles sont
**plus limités que ce que laissait penser le rapport initial**. Le détail du verdict est dans
`feasibility.md`.
