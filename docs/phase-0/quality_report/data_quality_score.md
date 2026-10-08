# Rapport de qualité — Score

**Évaluation qualitative justifiée** (pas de note arbitraire) sur 5 dimensions.

## Grille

| Dimension | Koutchoumi | Jumia | Justification |
|---|---|---|---|
| **Complétude** | 2/5 | 3/5 | Surface absente partout ; prix Koutchoumi censuré ; 11 % de prix manquants chez Jumia |
| **Unicité** | 1/5 | 5/5 | 71,7 % de doublons (Koutchoumi) vs 0 % (Jumia) |
| **Validité** | 3/5 | 3/5 | Aberrations : prix `0`/`1`, `max 25–40 M`, chambres `20`, sdb `80` |
| **Cohérence** | 2/5 | 3/5 | Formats hétérogènes entre sources ; quartiers non normalisés (`Akwa` vs `Akwa I`) |
| **Fraîcheur** | ? /5 | ? /5 | Aucune date de publication → non évaluable |

**Score global indicatif : ~2,2 / 5** — utilisable pour une **exploration**, insuffisant tel quel pour
un modèle.

## Points bloquants (à traiter en Phases 1-2)

1. **Surface** absente → impossible d'estimer au m².
2. **Prix censurés** (`"> X"`) chez Koutchoumi.
3. **71,7 %** de doublons chez Koutchoumi.
4. **11 %** de prix manquants chez Jumia.
5. **Aucune date** → pas de suivi temporel ni de split chronologique.
6. **Aberrations** : `Price = 0` ou `1`, `max = 40 000 000`, `Bedrooms = 20`, `Bathrooms = 80`.
   → À **isoler en quarantine**, pas à supprimer automatiquement (règle projet).

## Ce qui est exploitable dès maintenant

- **Localisation** : ville + quartier (474 quartiers distincts au total, à normaliser).
- **Type de bien** et **nombre de chambres / salles de bain** (après conversion en entier).
- **Prix** (Jumia) et **bornes de prix** (Koutchoumi) pour une analyse de tendances.
- Assez pour **valider un pipeline** et une **baseline**, pas pour un modèle de production.
