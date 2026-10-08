# Échantillon exploratoire (Phase 0)

Fichiers attendus dans ce dossier :

| Fichier | Source | Lignes | Statut |
|---|---|---|---|
| `koutchoumi1.csv` | [deegeorgie/Predicting-house-prices-in-Cameroon](https://github.com/deegeorgie/Predicting-house-prices-in-Cameroon) | 2 565 | local uniquement |
| `jumia.csv` | idem | 500 | local uniquement |

## Provenance et licence

Ces fichiers proviennent d'un **dépôt GitHub public tiers** (échantillons de Jumia House et
Koutchoumi) qui **ne déclare aucune licence** (`license: null`).

En conséquence :

- les fichiers **ne sont pas versionnés** (voir `.gitignore`) : ils existent localement pour
  l'analyse, mais ne sont pas redistribués dans ce dépôt ;
- seuls les **rapports dérivés** (`docs/phase-0/`) et le **script reproductible**
  (`docs/phase-0/scripts/profile_sample.py`) sont versionnés.

Pour reproduire l'analyse, se procurer les fichiers depuis le dépôt source et les déposer ici,
puis lancer :

```bash
python docs/phase-0/scripts/profile_sample.py data/samples
```

Voir `docs/phase-0/legal-assessment.md` pour la décision juridique détaillée.
