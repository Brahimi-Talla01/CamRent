# Ingestion — collecte des données brutes (Phase 1)

Collecte des sources retenues en Phase 0 et écriture de la donnée **brute** et
**immuable** dans `data/raw/`, avec ses métadonnées de lot et des validations
Bronze. Aucun nettoyage ni normalisation : c'est la **Phase 2**.

Voir `context/feature-specs/01-data-ingestion.md` et `docs/phase-1/`.

## Principe : « raw immuable »

- chaque run écrit un fichier **horodaté** (`<source>_<HHMMSS>.jsonl`) ; relancer
  une collecte ne corrompt jamais les données existantes (idempotence) ;
- l'écriture est **incrémentale** (une ligne JSON par observation, `flush`
  immédiat) : un run interrompu conserve tout ce qui a déjà été collecté ;
- un run qui ne collecte rien ne laisse **aucun fichier vide** ;
- `data/raw/` n'est **jamais** versionné (`.gitignore`) : il vit en local.

## Layout produit

```
data/raw/
├── listings/<YYYY-MM-DD>/<source>_<HHMMSS>.jsonl        # annonces individuelles
├── reference_data/<YYYY-MM-DD>/<source>_<HHMMSS>.jsonl  # baromètres, jeux de référence
├── user_submissions/                                    # (vide au MVP)
└── metadata/<YYYY-MM-DD>/<source>_<HHMMSS>.json         # un fichier par lot
```

Métadonnées de lot : source, catégorie, méthode, format, date de collecte,
nombre d'enregistrements, fichier brut, URLs, statut de droits, notes.

## Sources et droits

| Source | Catégorie | Droits | Collecte |
|---|---|---|---|
| `geloka` | `reference_data` | `uncertain` (citation obligatoire, CGU restrictives) | baromètre agrégé — **confirmation légale requise** |
| `koutchoumi` | `listings` | `uncertain` (aucune CGU publiée) | annonces — **confirmation légale requise** |
| `reference_local` | `reference_data` | `local` (jeu tiers sans licence) | fichiers `data/samples/*.csv`, **sans réseau** |
| `minfi_open_data` | `reference_data` | `uncertain` | document brut (sans parsing) |
| `ins_cameroon` | `reference_data` | `uncertain` | document brut (sans parsing) |

Une source non `verified`/`local` **refuse de tourner** sans `--confirm-legal`
(invariant AGENTS.md : aucune collecte automatisée sans vérification). Détail des
vérifications : `docs/phase-1/legal-review.md`.

## Éthique de collecte intégrée au code

- `robots.txt` vérifié automatiquement avant chaque requête (`urllib.robotparser`) ;
  si `robots.txt` est inaccessible, la collecte est **refusée** par prudence ;
- débit limité par hôte (token bucket, 2 s par défaut) ;
- **User-Agent transparent** : `CamRentResearch/0.1 (data research; contact: …)`
  (contact via `CAMRENT_CONTACT_EMAIL`) ;
- **minimisation des données** : aucune donnée personnelle n'est stockée. Pour
  Koutchoumi, le texte brut des pages (qui contient téléphones/e-mails/noms) est
  volontairement **non conservé** — seuls l'URL, le slug et les champs structurés
  le sont.

## Utilisation

```bash
python -m ingestion --list-sources
python -m ingestion --source reference_local                 # local, sans réseau
python -m ingestion --source geloka --confirm-legal "CGU vérifiées le 2026-10-09"
python -m ingestion --source koutchoumi --confirm-legal "..." --limit 40
python -m ingestion --validate-bronze                        # validations Bronze
```

Options utiles : `--limit N` (borne le volume), `--verbose`.

Réglages par variable d'environnement : `CAMRENT_CONTACT_EMAIL`, `CAMRENT_RATE_LIMIT`,
`CAMRENT_REQUEST_TIMEOUT`, `CAMRENT_MAX_RETRIES`, `CAMRENT_DETAIL_BUDGET`,
`CAMRENT_KOUTCHOUMI_MAX_PAGES`, `CAMRENT_FRESHNESS_DAYS`, `CAMRENT_DATA_ROOT`.

## Validations Bronze

`python -m ingestion --validate-bronze` vérifie, sans modifier les données :

- présence et non-vacuité du fichier ;
- validité JSON ligne à ligne ;
- volume raisonnable ;
- présence des clés requises (`source`, `source_listing_id`, `collected_at`) ;
- concordance métadonnées ↔ nombre de lignes ;
- fraîcheur de la collecte la plus récente.

## Structure du package

```
ingestion/
├── config.py        # identité, réseau, registre des sources (droits)
├── models.py        # RawRecord (observation brute, non normalisée)
├── http_client.py   # requests + robots.txt + débit + retries + porte légale
├── storage.py       # JSONL daté immuable + métadonnées de lot
├── bronze.py        # validations Bronze
├── __main__.py      # CLI
└── sources/
    ├── base.py            # SourceCollector + budget de fetchs de détail
    ├── geloka.py          # baromètre agrégé
    ├── koutchoumi.py      # annonces (catégories + détails)
    ├── reference_local.py # jeux locaux (CSV)
    └── raw_document.py    # documents officiels bruts (MINFI / INS)
```

## Limites connues

- **Koutchoumi** : un run complet est long (pages de catégorie × `?page=N` ×
  détails, avec 2 s entre requêtes). `--limit` et `CAMRENT_KOUTCHOUMI_MAX_PAGES`
  bornent le volume. Le parsing est tolérant et s'appuie sur la structure observée
  le 2026-10-09.
- **Geloka** : ne fournit que des **médianes agrégées** (benchmark, pas
  d'entraînement).
- **MINFI / INS** : les documents sont stockés **bruts** ; les endpoints restent à
  valider et l'interprétation est différée.
- La mise au **schéma cible** (ville canonique, `property_type`, unités) est en
  **Phase 2**.
