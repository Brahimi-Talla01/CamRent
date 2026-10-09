# Phase 2 — Data cleaning (Silver)

Produit le **Silver dataset** : observations nettoyées et standardisées à partir du
**Raw immuable**, sans jamais perdre l'origine d'une valeur.
Voir `context/feature-specs/02-data-cleaning.md` et `pipelines/README.md`.

## Livrables

| Livrable | Emplacement |
|---|---|
| Pipeline de transformation | `pipelines/` (config, geo, parsing, adapters, silver, report, CLI) |
| Référentiel géographique (seed) | `pipelines/geo.py` |
| Tests unitaires | `tests/unit/test_pipelines_*.py` |
| Rapport de nettoyage | `docs/phase-2/cleaning-report.md` |

## Décisions retenues

- **Périmètre Silver** : `koutchoumi` (live) + `reference_local` (jeux locaux
  `jumia.csv` / `koutchoumi1.csv`). Geloka exclu (médianes agrégées, pas des annonces).
- **Référentiel géographique** : **seed curé** (quartiers de Douala/Yaoundé) +
  résolution tolérante + rapprochement flou. Non reconnu → conservé et signalé.
- **Prix censurés** (`> X`) : **conservés** avec `price_is_bound = true`
  (borne inférieure, pas un prix exact).
- **Aberrations** : signalées (`outlier_flags`), jamais supprimées.
- **Invalides** : routées en **quarantine** avec motif, jamais supprimées.

## Vérifications (9 octobre 2026)

- `ruff` : OK ; `pytest` : **37** tests (36 sans dépendance lourde + 1 Parquet).
- **Construction Silver** réelle (raw local) :

  | Étape | Volume |
  |---|---|
  | Observations brutes lues | 3 078 |
  | Adaptées (source gérée) | 3 070 |
  | **Lignes Silver** | **2 992** |
  | **Quarantine** | **78** |

  - détail quarantine : `prix_manquant` 52, `type_inconnu` 18, `city_inconnue` 7, `prix_invalide` 1 ;
  - `republication` 1 970 (jeu `deegeorgie` fortement dupliqué → cohérent avec l'estimation Phase 0 d'≈ 1 226 uniques) ;
  - `price_is_bound` 2 564 ; aberrations signalées 17 ; quartiers non reconnus 582.

> Note : l'écriture **Parquet** (`pandas`/`pyarrow`) n'a pas pu être exécutée dans le
> sandbox de développement (téléchargement trop lent) ; elle est couverte par le test
> `test_write_outputs_columns` en CI.

## Critères « Check When Done »

| Critère | État |
|---|---|
| Silver produit et reproductible depuis le Raw | ✅ (rejouable : même Raw → même résultat) |
| Colonnes clés non nulles (`city`, `neighborhood`, `rent_price`, `property_type`) | ✅ (sinon quarantine) |
| Types corrects ; ranges plausibles | ✅ (`rent_price > 0`, `bedrooms >= 0`, `area_m2 > 0`) |
| Doublons traités et documentés | ✅ (technique supprimé, republication signalée) |
| Données invalides en quarantine, pas supprimées | ✅ (78 lignes) |
| Rapport documentant chaque règle + volume d'impact | ✅ (`cleaning-report.md`) |

## Points ouverts transmis à la Phase 3 (EDA)

- **Référentiel de quartiers** à enrichir (582 quartiers non reconnus).
- **Prix bornés** : part importante du dataset → stratégie de pondération/exclusion (Phases 5-6).
- **Surface** toujours absente.
- **Republications** : décider si elles sont conservées/pondérées pour l'entraînement.
