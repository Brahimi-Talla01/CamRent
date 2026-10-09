# Pipelines — construction du Silver dataset (Phase 2)

Lit le **Raw immuable** (`data/raw/`) et produit des jeux nettoyés et standardisés
dans `data/processed/` : `silver_listings.parquet`, `quarantine_listings.parquet`.
Voir `context/feature-specs/02-data-cleaning.md`.

## Principe

- **Le Raw n'est jamais modifié** ni supprimé.
- Les valeurs **extrêmes** ne sont pas supprimées : elles restent dans le Silver
  avec un drapeau (`outlier_flags`).
- Les observations **invalides** sont routées vers la **quarantine** avec leur
  motif — jamais supprimées, jamais remplacées par du vide.
- Aucune **imputation** permissive : les valeurs manquantes restent nulles.
- Chaque ligne Silver conserve `source` + `source_listing_id` → **traçabilité** vers le Raw.

## Sources prises en charge

| Source (`source`) | Fichier | Traitement |
|---|---|---|
| `koutchoumi` | (collecte live) | titre « `<type> to rent at <ville>, <quartier> - <prix>` » + slug `/en/<id>/<slug>` |
| `reference_local` | `jumia.csv` | `Address` (ville/quartier), `Designation` (type), `Bedrooms`, `Bathrooms`, `Price` |
| `reference_local` | `koutchoumi1.csv` | `Area` = `ville/quartier`, `Type`, chambres/sdb/prix **bornés** (`> `) |

Geloka est **ignoré** ici : ce sont des médianes agrégées, pas des annonces.

## Règles de nettoyage

1. **Types** : `rent_price` / `bedrooms` / `bathrooms` en entiers, `area_m2` en numérique.
2. **Villes** : `Douala` / `Yaoundé` (canonique) ; hors périmètre → quarantine.
3. **Quartiers** : résolution vers un **référentiel seed curé** (`geo.py`), tolérante
   aux accents/casse/séparateurs + rapprochement flou. Non reconnu → conservé et
   signalé (`neighborhood_recognized = false`).
4. **Catégories** : `property_type` normalisé (`studio`, `apartment`, `house`,
   `office`, `shop`, `warehouse`, `room`, `land`).
5. **Valeurs bornées** : `> X` → valeur conservée + `price_is_bound` /
   `bedrooms_is_bound` / `bathrooms_is_bound` = `true` (minimum, pas prix exact).
6. **Déduplication** : doublon technique (`source`+`source_listing_id`) supprimé ;
   même logement republié conservé et marqué `is_republication`.
7. **Aberrations** : hors bornes plausibles → `outlier_flags` (jamais supprimées).
8. **Quarantine** : ville inconnue, quartier vide, type inconnu, prix absent/≤ 0.

## Utilisation

```bash
# nécessite pandas + pyarrow pour l'écriture Parquet
python -m pipelines silver --report docs/phase-2/cleaning-report.md
```

Options : `--raw-root`, `--out-dir`, `--report`.

## Sorties

| Fichier | Contenu |
|---|---|
| `data/processed/silver_listings.parquet` | observations nettoyées et standardisées |
| `data/processed/quarantine_listings.parquet` | observations invalides + `quarantine_reason` |
| `docs/phase-2/cleaning-report.md` | rapport : règles appliquées + volumes d'impact |

Les sorties de `data/processed/` ne sont **pas versionnées** (reproductibles depuis
le Raw).

## Structure

```
pipelines/
├── config.py     # chemins, seuils, schéma Silver
├── geo.py        # référentiel villes/quartiers (seed) + résolution
├── parsing.py    # prix, chambres, surface, type, oui/non
├── adapters.py   # Raw → Candidate (par source)
├── silver.py     # résolution, validation, déduplication, écriture
├── report.py     # rapport de nettoyage (markdown)
└── __main__.py   # CLI
```

## Limites connues

- Le **référentiel de quartiers** est un **seed** : 582 lignes Silver ont un
  quartier non reconnu (conservées, signalées). À enrichir en Phase 3.
- Le **prix de Koutchoumi** est très souvent **borné** (2 564 lignes `price_is_bound`) :
  utilisable pour la tendance, à exclure ou pondérer pour l'entraînement (Phases 5-6).
- La **surface** reste absente des sources collectées.
- `write_outputs` requiert `pandas` + `pyarrow` (non présents dans le sandbox de
  développement ; couvert par les tests en CI).
