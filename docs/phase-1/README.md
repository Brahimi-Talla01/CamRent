# Phase 1 — Data ingestion

Collecte des sources retenues en Phase 0, stockage brut **immuable** dans
`data/raw/`, métadonnées de lot et validations **Bronze**. Voir
`context/feature-specs/01-data-ingestion.md` et `ingestion/README.md`.

## Livrables

| Livrable | Emplacement |
|---|---|
| Package d'ingestion (HTTP, sources, stockage, CLI) | `ingestion/` |
| Porte légale + `robots.txt` + débit + UA transparent | `ingestion/http_client.py`, `ingestion/sources/base.py` |
| Stockage brut daté + métadonnées de lot (provenance : version de connecteur, empreinte de contenu, statut de validation) | `ingestion/storage.py` |
| Validations Bronze | `ingestion/bronze.py` |
| Tests unitaires (parsing, stockage, Bronze, porte légale) | `tests/unit/test_ingestion_*.py` |
| Revue légale des sources | `docs/phase-1/legal-review.md` |

## Sources collectées

| Source | Catégorie | Droits | Confirmation légale |
|---|---|---|---|
| `geloka` | `reference_data` | uncertain (citation obligatoire) | requise |
| `koutchoumi` | `listings` | uncertain (aucune CGU publiée) | requise |
| `reference_local` | `reference_data` | local (sans réseau) | non requise |
| `minfi_open_data` / `ins_cameroon` | `reference_data` | uncertain | requise |

## Vérifications effectuées (9 octobre 2026 ; provenance revérifiée le 16 octobre 2026)

- **Tests** : `24` tests unitaires d'ingestion, verts (17 en Phase 1 ; 7 ajoutés avec la
  provenance renforcée du lot B : empreinte de contenu, statut de validation, validation d'un lot).
- **Lint** : `ruff` sans erreur.
- **Collectes réelles** :
  - `geloka` → **8** observations (baromètre agrégé) ;
  - `reference_local` → **3 065** lignes (échantillon local, non versionné) ;
  - `koutchoumi` → collecte vérifiée de bout en bout (3 obs. en `--limit 3`,
    volume complet borné par `--limit` / `CAMRENT_KOUTCHOUMI_MAX_PAGES`).
- **Validations Bronze** : `16/16` contrôles réussis (présence, format, volume,
  clés, métadonnées, fraîcheur) — revérifié le 2026-10-16 sur le brut existant.
- **Provenance (2026-10-16)** : un lot rejoué (`reference_local`, `--limit 20`) écrit
  `connector_version`, `content_sha256` et `lot_validation_status: "ok"` ; l'empreinte
  recalculée indépendamment (`sha256sum`) correspond exactement.
- **Idempotence** : deux runs successifs produisent deux fichiers horodatés
  distincts, sans écrasement.
- **Minimisation** : aucune donnée personnelle dans le brut (le texte brut des
  pages Koutchoumi n'est pas conservé).

## Critères « Check When Done »

| Critère | État |
|---|---|
| Données brutes d'au moins une collecte complète dans `data/raw/` | ✅ (3 sources) |
| Métadonnées de collecte pour chaque lot | ✅ |
| Empreinte de contenu et version du connecteur traçables par lot | ✅ (lot B, 2026-10-16) |
| Validations Bronze passent (présence, volume, format, fraîcheur) | ✅ 16/16 |
| Raw dataset v1 produit et immuable | ✅ (fichiers datés, jamais écrasés; non versionné) |
| Aucune source sans vérification légale collectée | ✅ (porte `--confirm-legal`) |

## Décisions de mise en œuvre

- **Couche HTTP** : `requests` (ajouté à `pyproject.toml`), robots.txt + token
  bucket + retries + UA transparent.
- **Pas de normalisation** en Phase 1 : les valeurs de source sont conservées
  telles quelles dans `fields` ; le schéma cible est appliqué en Phase 2.
- **Pas de base analytique ni d'orchestration** (hors périmètre, cf. spec).
- **Layout `data/raw/`** conforme à la spec : `listings/`, `reference_data/`,
  `user_submissions/`, `metadata/`.
- **Aucune donnée personnelle** : le brut Koutchoumi exclut téléphones, e-mails
  et noms.

## Points ouverts transmis à la Phase 2

- Parsing du **slug** Koutchoumi (ville, quartier, type, pièces, prix) vers le
  schéma cible.
- Prix **censurés** et **surface** (cf. `docs/phase-0/`) : stratégie à figer.
- **Référentiel géographique** (ville → quartiers canoniques).
- Endpoints **MINFI / INS** à valider (documents stockés bruts).
