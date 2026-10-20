# Phase 8 — API publique : socle (08a.1), prédiction (08a.2), provenance et serving durci (08a.3), marché (08a.4), comparaison (08a.5) ; API interne : socle (08b.1)

Objectif (spec : `context/feature-specs/08-api.md`) : exposer le modèle et les données de
marché via une API backend claire, versionnée et reproductible.

La phase 8 est livrée en **deux temps** (plan §10, lot 4) : **08a API publique** puis
**08b API interne**. Ce document couvre les **cinq incréments du 08a** — le
**socle** (ticket #50 : structure `backend/`, schémas stricts, erreurs au format unique,
route de version), **l'endpoint de prédiction** (ticket #51 : `POST
/api/v1/predictions`, modèle épinglé, fourchette, `model_version`), la **provenance
verrouillée** (ticket #52 : pin cohérent avec le mart vivant, vérification de l'alias au
chargement), les **endpoints de marché** (ticket #53 : villes, quartiers, prix, avec
nombre d'observations obligatoire et seuil de publication) et la **comparaison**
(ticket #54 : prix demandé, estimation, référence locale et écarts signés, sans second
calcul). L'API publique est ainsi complète.

Le **08b** (API interne) est ouvert par son **socle, 08b.1** (ticket #61) :
une application Django **distincte**, authentifiée, réservée au rôle `admin` et
journalisée. Les modules métier du back-office (13.1 à 13.5) et son interface
(09b) s'appuieront dessus sans la modifier.

## Livrables du socle (#50)

1. **Code** : paquet `backend/`, découpé selon la spec 08 §1.

   ```
   backend/
   ├── api/            application ASGI, route de santé, gestion d'erreurs
   │   └── routes/
   ├── domain/         vocabulaire réel des données (villes, types, bornes)
   ├── infrastructure/ configuration et accès PostgreSQL (sans secret en dur)
   ├── ml/             chargement du modèle épinglé (ticket #51)
   ├── repositories/   lectures PostgreSQL des marts (ticket #53)
   ├── schemas/        contrat d'entrée (Pydantic, strict)
   └── services/       logique métier (tickets #51, #53, #54)
   ```

2. **Tests** : `tests/unit/test_api_{schemas,app,infrastructure}.py` (**38 tests**) —
   refus des champs non collectés, vocabulaire, bornes de pièces, format d'erreur unique,
   absence de fuite technique, configuration explicite.
3. **Outillage** : l'extra `api` (fastapi, uvicorn) est installé par la CI
   (`pip install -e '.[dev,transform,ml,api]'`) ; `httpx` rejoint l'extra `dev` pour
   `fastapi.testclient`.
4. **Packaging** : les sous-paquets `backend*` sont déclarés dans `pyproject.toml`
   (layout plat, comme `ingestion` et `pipelines`).

## Contrat exposé par ce socle

```
GET /api/v1/health  →  {"status": "ok", "api_version": "0.1.0", "api_prefix": "/api/v1"}
```

Le contrat est **versionné** : la route n'existe pas hors `/api/v1` (vérifié : `/health`
répond 404). `api_version` décrit le contrat, pas le modèle — la version servie est
exposée par l'endpoint de prédiction (`model_version`, ci-dessous).

## Contrat de prédiction (08a.2, ticket #51)

```
POST /api/v1/predictions
```

Entrée (le schéma strict du socle, inchangé) :

```json
{"city": "Douala", "neighborhood": "Makepe", "property_type": "apartment", "bedrooms": 2, "bathrooms": 2}
```

Réponse — **réelle**, servie par le modèle épinglé (vérification du 2026-10-18) :

```json
{
  "estimated_rent": 109990,
  "currency": "XAF",
  "lower_bound": 80000,
  "upper_bound": 150002,
  "model_version": "rent-model-v4"
}
```

Points de conception :

- **Modèle épinglé, jamais entraîné dans la requête** : le bundle vient de
  `ml/models/champion.json` — le pipeline est chargé à l'URI de registre épinglée
  (`model_uri`), pas depuis un fichier local implicite. `model_version` est l'étiquette
  du pin, identique à chaque réponse tant que le pin ne change pas.
- **Fourchette par le modèle retenu** : l'intervalle **quantile** 5 % / 95 % déjà
  calibré en Phase 6 est journalisé avec le modèle et relu dans les **artefacts du
  run épinglé** (`pin.run_id`). Une seule version est donc servie — modèle et
  fourchette — sans fichier local implicite. Si l'artefact manque, le service
  échoue explicitement plutôt que de servir une estimation sans fourchette :
  jamais de fourchette improvisée, jamais de pourcentage arbitraire.
- **Domaine servi** : le service refuse tout couple (ville, quartier) que le modèle
  chargé n'a jamais vu à l'entraînement — **404 `not_found`**. C'est nécessaire : hors
  domaine, le pipeline traiterait silencieusement la saisie (profondeur de marché nulle,
  one-hot ignoré) et produirait une estimation faussement plausible. Une ville ou un type
  hors vocabulaire reste un **422** du schéma ; le choix 404 / 422 pour une valeur
  inconnue a été tranché par le porteur du projet (2026-10-17) : 404 pour une valeur
  inconnue, 422 pour un contrat d'entrée violé.
- **Cache et démarrage** : le bundle est chargé une seule fois (verrou), au premier appel
  utile ; l'application démarre et sert la santé sans registre ni artefact joignables.

Vérifications HTTP réelles (serveur `uvicorn`, modèle épinglé v4) : 200 avec fourchette
ordonnée (80 000 ≤ 109 990 ≤ 150 002 FCFA) ; deux appels identiques → réponses
**identiques** ; quartier inconnu → 404 `not_found` ; quartier réel mais jamais vu avec
cette ville → 404 ; `area_m2` → 422 `validation_error` avec le détail du champ.

### Provenance verrouillée (08a.3, ticket #52)

Le modèle épinglé est **`rent-model-v4`**, promu le 2026-10-18 avec approbation
nominative, sur le mart **courant** :

| Élément | Valeur |
|---|---|
| version servie | `rent-model-v4` (alias `champion` → v4) |
| dataset d'entraînement | `mart_ml_dataset@d3c11c225f48` — 2 992 observations, 21 colonnes |
| pin | `ml/models/champion.json` (approbation, run, SHA Git, hash du dataset) |

L'écart de la v3 est **clos** : son pin décrivait `mart_ml_dataset@5050042e720e`, le
schéma d'avant l'ajout de `rent_semantics` par le lot B, alors que le mart vivant est
`mart_ml_dataset@d3c11c225f48`. Le modèle n'utilisait pas la colonne ajoutée — les
prédictions sont identiques à la v3 (mêmes features, mêmes valeurs) — mais la provenance
publiée ne décrivait plus les données servies. La correction est passée par la **voie
gouvernée** : `python -m ml.src registry --confirm-promotion --approved-by "Ibrahim Talla"`.
`ml/models/champion.json` n'est **jamais** modifié à la main.

Trois contrôles rendent un écart **impossible à servir en silence** :

1. **Pin complet exigé** : le pin doit porter sa provenance de données (`dataset.version`,
   `dataset.hash_md5`) — un pin incomplet est refusé au chargement, avec le nom des clés
   manquantes ;
2. **Alias vérifié** : au premier chargement, l'alias `champion` doit pointer **la même
   version et la même URI** que le pin. Un alias déplacé à la main, une version supprimée
   ou un pin divergent lèvent une erreur explicite, jamais une prédiction servie ;
3. **Lecture défensive** : un fichier absent, illisible ou non JSON échoue avec un message
   qui nomme le fichier (et, côté CLI, un code de sortie non nul).

Deux conséquences pour le déploiement, vérifiées à part plutôt qu'à chaque requête :

- **Préflight pin ↔ mart** : `python -m ml.src pin --check-dataset` compare le hash du pin
  au mart vivant et sort en **erreur (code 1)** en cas de dérive ; le serving ne relit pas
  la base à chaque appel (couplage et coût injustifiés) ;
- **Une seule provenance d'artefacts** : modèle **et** intervalle viennent du run épinglé du
  registre — plus de fichier local non versionné dont la correspondance avec le modèle ne
  serait vérifiable qu'à la main. C'est aussi ce qui rend le chemin de production testable
  en CI (`tests/unit/test_serving_registry.py`, registre MLflow SQLite).

### Schéma d'entrée strict

`PredictionRequest` accepte **cinq** champs seulement : `city`, `neighborhood`,
`property_type`, `bedrooms`, `bathrooms`. Les champs que la plateforme data ne collecte
pas (`area_m2`, `parking`, `gated`, `furnished`) sont **refusés** (`extra="forbid"`), pas
ignorés : accepter un champ que le modèle n'utilise pas laisserait croire que l'estimation
en tient compte (spec 08 §Scope Limits, décision 6).

Le vocabulaire est fermé sur les valeurs **réellement présentes** dans les marts
(`backend/domain/vocabulary.py`) :

| Élément | Valeurs | Source |
|---|---|---|
| villes | `Douala`, `Yaoundé` | `mart_ml_dataset` (2 811 / 181) |
| types de biens | `apartment`, `studio`, `room`, `house` | Silver normalisé (2 903 / 73 / 15 / 1) |
| chambres, salles de bain | entier **0 à 10** inclus | `pipelines/config.py::ROOMS_MAX_PLAUSIBLE`, borne haute des tests dbt `within_range` |

Au-delà de 10 pièces, la plateforme data **signale** la valeur (`outlier_flags`) sans la
supprimer : l'API ne l'accepte pas en entrée (les 3 observations à `bathrooms = 80` ne
sont pas une entrée valide).

### Erreurs : un seul format

```json
{
  "error": {
    "code": "validation_error",
    "message": "Entrée invalide.",
    "details": [{"field": "area_m2", "message": "Extra inputs are not permitted"}]
  }
}
```

| Code | HTTP | Cas |
|---|---|---|
| `validation_error` | 422 | entrée hors contrat (champ non collecté, valeur hors bornes, champ manquant) |
| `bad_request` | 400 | requête mal formée mais comprise |
| `method_not_allowed` | 405 | méthode absente pour cette route |
| `not_found` | 404 | route ou valeur inconnue |
| `internal_error` | 500 | échec interne, **message générique** |

Deux points de conception :

- les gestionnaires sont branchés sur les classes **Starlette** (et non `fastapi.HTTPException`) :
  une route inconnue (404) et une méthode non autorisée (405) sont levées par Starlette en
  amont de FastAPI — les brancher sur la classe FastAPI laissait ces deux cas hors du format
  unique (constaté par test avant correction) ;
- un échec interne ne renvoie **aucun** détail technique : seule la classe de l'exception et
  le chemin sont journalisés, jamais le message ni la charge utile, qui peuvent contenir une
  donnée sensible (AGENTS.md §9). Un test le vérifie avec un message d'exception piégé.

## Contrat de marché (08a.4, ticket #53)

```
GET /api/v1/market/cities
GET /api/v1/market/neighborhoods?city=Douala[&property_type=apartment][&bedrooms=2]
GET /api/v1/market/prices[?city=Douala][&neighborhood=Makepe][&property_type=apartment][&bedrooms=2][&period=2026-10]
```

Les trois routes lisent **exclusivement** les marts dbt — aucune statistique n'est
recalculée dans la route ni dans le service :

| Filtres demandés | Mart lu | Grain de la réponse |
|---|---|---|
| aucun, ou `city` seul | `mart_city_prices` | ville |
| `property_type` seul (avec `city` facultative) | `mart_property_prices` | type × ville |
| `neighborhood` et/ou `bedrooms` | `mart_neighborhood_prices` | ville × quartier × type × chambres |

Chaque groupe retourné porte **ses propres dimensions** et son propre `n_observations`.
On ne mélange jamais deux grains dans une même statistique : `neighborhood: null`
signifie « statistique de ville », pas « quartier inconnu ».

### Forme de la réponse (`/market/prices`)

```json
{
  "currency": "XAF",
  "min_publish_n": 30,
  "observed_period": {"start": "2026-10-09", "end": "2026-10-09"},
  "n_observations": 632,
  "groups": [
    {
      "city": "Douala",
      "neighborhood": "Makepe",
      "neighborhood_recognized": true,
      "property_type": "apartment",
      "bedrooms": 2,
      "stats": {
        "n_observations": 632,
        "mean_rent_price": 98498,
        "median_rent_price": 90000,
        "median_published": true,
        "p10_rent_price": 70000,
        "p90_rent_price": 150000,
        "min_rent_price": 11000,
        "max_rent_price": 750000
      },
      "quality": {
        "n_price_bound": 621, "pct_price_bound": 98.0,
        "n_republication": 586, "pct_republication": 93.0,
        "n_neighborhood_unrecognized": null,
        "pct_neighborhood_unrecognized": null
      }
    }
  ]
}
```

Points de conception :

- **N obligatoire par construction** : `n_observations` n'a pas de valeur par défaut dans
  `MarketStatsResponse` ; un test vérifie qu'on ne peut pas construire la réponse sans.
- **Seuil appliqué deux fois** : dbt met la médiane à `null` sous `min_publish_n` ; le
  service réapplique le seuil (défense en profondeur) et expose `median_published`. Une
  médiane sous 30 observations ne peut donc pas sortir, même si un mart était mal
  construit.
- **Synthèse quartier sans médiane** : `/market/neighborhoods` agrège des effectifs et des
  moyennes pondérées (exactes), mais **pas** les médianes ni les centiles — agréger des
  médianes de sous-groupes ne donne pas la médiane du quartier. Le détail par
  (type, chambres), avec le seuil, reste dans `/market/prices`.
- **Période honnête** : les marts n'ont pas de dimension temporelle et les observations
  tiennent dans un seul mois. `period=YYYY-MM` est accepté pour ce mois ; tout autre mois
  renvoie **200 avec `n_observations: 0` et `groups: []`** (résultat vide explicite). Si les
  données venaient à couvrir plusieurs mois, le filtre est **refusé en 400** plutôt que de
  servir des statistiques toutes périodes sous une étiquette mensuelle.
- **Filtres invalides** : ville ou type hors vocabulaire, chambres hors 0–10, mois mal
  formé → **422** ; `neighborhood` sans `city` → **400** (un nom de quartier n'est pas
  unique entre villes).

### Qualité exposée, jamais masquée

Les marts portent désormais le volume **et** la part des prix bornés, des republications
et (au niveau ville) des quartiers non reconnus. L'API les rend tels quels : un prix
borné reste compté, mais le client sait quelle part de la statistique il représente.
Aucune ligne n'est exclue pour embellir la moyenne.

## Contrat de comparaison (08a.5, ticket #54)

```
POST /api/v1/comparisons
```

Entrée : un à dix logements, chacun avec les cinq champs du modèle et le prix demandé.

```json
{
  "listings": [
    {
      "city": "Douala", "neighborhood": "Makepe", "property_type": "apartment",
      "bedrooms": 2, "bathrooms": 2, "asking_rent": 150000
    }
  ]
}
```

Réponse — **réelle**, servie par le modèle épinglé et les marts du 2026-10-19 :

```json
{
  "currency": "XAF",
  "min_publish_n": 30,
  "model_version": "rent-model-v4",
  "comparisons": [
    {
      "listing": {
        "city": "Douala", "neighborhood": "Makepe", "property_type": "apartment",
        "bedrooms": 2, "bathrooms": 2, "asking_rent": 150000
      },
      "estimate": {"estimated_rent": 109990, "lower_bound": 80000, "upper_bound": 150002},
      "market": {
        "city": "Douala", "neighborhood": "Makepe", "property_type": "apartment",
        "bedrooms": 2,
        "n_observations": 632,
        "mean_rent_price": 98498,
        "median_rent_price": 90000,
        "median_published": true,
        "quality": {
          "n_price_bound": 621, "pct_price_bound": 98.0,
          "n_republication": 586, "pct_republication": 93.0,
          "n_neighborhood_unrecognized": null,
          "pct_neighborhood_unrecognized": null
        }
      },
      "gaps": {
        "to_estimate": {"absolute": 40010, "relative_pct": 36.4},
        "to_market_mean": {"absolute": 51502, "relative_pct": 52.3},
        "to_market_median": {"absolute": 60000, "relative_pct": 66.7}
      }
    }
  ]
}
```

Points de conception :

- **Réutilisation stricte, aucune divergence** : le service de comparaison appelle
  `EstimationService.estimate` (08a.2) et `MarketService.prices` (08a.4). Il ne calcule
  que l'écart signé `asking_rent - référence` et son pourcentage. Les tests comparent
  valeur par valeur la comparaison aux deux endpoints directs.
- **Groupe de comparaison explicite** : c'est le grain du mart
  `(ville, quartier, type, chambres)`. Les salles de bain servent à l'estimation mais
  **pas** à la référence locale, que les marts n'exposent pas à ce grain ; le groupe est
  donc répété dans la réponse pour que le client sache à quoi il compare.
- **Écart signé** : `absolute = asking_rent - référence` ; positif = prix demandé au-dessus
  de la référence. `relative_pct` est arrondi à une décimale. Aucun score de confiance, aucune
  note, aucune recommandation.
- **Seuil respecté jusqu'au bout** : sous 30 observations, `median_rent_price` est `null`,
  `median_published` vaut `false` et `gaps.to_market_median` est `null` — jamais un écart
  calculé sur une médiane non publiée.
- **Groupe absent, réponse explicite** : si le mart n'a aucun groupe pour la combinaison,
  `market` vaut `null` et les écarts marché sont nuls ; l'estimation reste fournie. Aucune
  référence plus large n'est inventée en silence.
- **Erreurs** : quartier inconnu du modèle → **404** (comme `/predictions`) ; liste vide,
  plus de dix logements, prix demandé < 1, champ non collecté ou chambres hors 0–10 → **422**.

## API interne (08b.1, ticket #61)

L'API interne du back-office est une **seconde application**, servie séparément
(`uvicorn backend.internal.asgi:application`, port 8001 par convention). Partager une
application aurait mêlé deux régimes d'accès opposés : le public est ouvert et sans
authentification, l'interne exige un compte, un rôle et un journal.

Technologies : **Django** pour l'interne (décision actée dans le ticket #61), FastAPI pour
le public. Aucune des deux applications ne monte une route de l'autre.

| Élément | Choix | Conséquence |
|---|---|---|
| Comptes | modèle dédié `InternalUser` (e-mail unique, rôle) | pas de `django.contrib.admin` ni de permissions Django : l'autorisation est explicite |
| Authentification | jeton opaque, `Authorization: Bearer` | ni cookie ni session, donc pas de CSRF ; le jeton n'est affiché qu'une fois |
| Stockage du jeton | empreinte SHA-256 seulement | un vol de base ne donne pas de session utilisable |
| Rôle | `admin` uniquement | aucun rôle intermédiaire sans besoin mesuré (spec 13 §Scope Limits) |
| Autorisation | table action → rôles, déclarée route par route | ajouter un rôle se fait par cette table, pas par des conditions dispersées |
| Journal | table `internal_audit_entries` | qui, quoi, sur quoi, quand, résultat |

### Routes

```
GET  /internal/api/v1/health      →  état du service (seule route sans jeton)
POST /internal/api/v1/auth/login  →  {token, expires_at, user}
POST /internal/api/v1/auth/logout →  204, jeton révoqué
GET  /internal/api/v1/me          →  {user: {email, role}}
POST /internal/api/v1/users       →  201, crée un compte `admin` (action sensible)
GET  /internal/api/v1/audit       →  {total, limit, offset, entries[]}
```

`/auth/login` échange e-mail + mot de passe contre un jeton valable **12 h** par défaut
(`INTERNAL_TOKEN_TTL_HOURS`), et répond `Cache-Control: no-store`. Un compte inconnu et un
mot de passe faux produisent **la même** réponse (401 `invalid_credentials`, message
générique) : pas d'énumération de comptes.

### Autorisation par action

| Action | Route | Rôles |
|---|---|---|
| `auth.logout` | `POST /auth/logout` | `admin` |
| `auth.read` | `GET /me` | `admin` |
| `users.create` | `POST /users` | `admin` |
| `audit.read` | `GET /audit` | `admin` |

Chaque vue déclare l'action qu'elle protège. Le contrôle **échoue fermé** : une action
absente de la table ou un rôle inconnu en base n'ouvre aucun accès (403, jamais un accès
implicite). Aucun second rôle n'étant ouvert, le test du refus « rôle insuffisant »
utilise un compte au rôle non déclaré — il vérifie du même coup la robustesse à une donnée
inattendue.

### Journal d'audit

Les actions sensibles sont journalisées avec **auteur, action, cible, date, résultat**
(`success` / `failed` / `denied`) et consultables par `GET /audit` (pagination `limit` 1–200,
`offset`, filtre `action`).

- connexion réussie **et** refusée (l'adresse tentée est conservée, jamais le mot de passe) ;
- déconnexion, avec révocation effective du jeton ;
- création d'un compte interne, y compris par la commande de bootstrap (source `cli`) ;
- **refus pour rôle insuffisant** — l'auteur est connu, le refus est donc tracé.

Deux règles de minimisation : un 401 (auteur inconnu) n'écrit **rien**, pour qu'un appelant
anonyme ne puisse pas remplir le journal ; et le service d'écriture filtre les clés
`password`, `token`, `secret`, `authorization` — un mot de passe ne peut pas être journalisé
par inadvertance (testé). L'adresse de l'auteur est conservée dans l'entrée (`actor_email`)
pour que la suppression d'un compte n'efface pas son historique.

### Erreurs

Même enveloppe que l'API publique (`{"error": {"code", "message", "details"}}`), avec
deux codes propres à l'interne : `unauthenticated` (401) et `forbidden` (403), plus
`invalid_credentials` (401) et `conflict` (409). Une route inconnue (`handler404`) et un
échec interne (`handler500`) répondent aussi en JSON, avec un message **générique** pour le
500. Une erreur prévue n'est jamais transformée en 500 : Django convertit désormais toute
exception en réponse avant le middleware applicatif, le refus est donc intercepté au plus
près de la vue.

### Démarrage et amorçage

```bash
python manage.py migrate                       # tables comptes + audit
python manage.py create_internal_user --email admin@camrent.local
uvicorn backend.internal.asgi:application --port 8001
```

La commande de bootstrap est le **seul** chemin pour le premier compte : `POST /users` est
réservé à un `admin` déjà authentifié. Le mot de passe n'est jamais affiché (saisie masquée
si `--password` est omis) et la création est elle-même journalisée.

### Configuration

| Variable | Rôle | Défaut |
|---|---|---|
| `INTERNAL_SECRET_KEY` | clé Django, **obligatoire** | — (erreur nommant la variable) |
| `DATABASE_URL` | base PostgreSQL, **obligatoire** | — (déjà utilisée par pipelines, ML et API publique) |
| `INTERNAL_ALLOWED_HOSTS` | hôtes autorisés | `localhost,127.0.0.1` |
| `INTERNAL_DEBUG` | mode debug local | `False` |
| `INTERNAL_TOKEN_TTL_HOURS` | durée de vie d'un jeton | `12` |

Aucun secret dans le code ni dans un fichier suivi : les valeurs de `.env.example` sont des
placeholders, et les réglages de **test** (SQLite en mémoire, clé factice) ne servent qu'à la
suite unitaire, qui reste exécutable sans base ni variable d'environnement.

## Configuration de l'API publique

Aucun secret ni chemin en dur : `backend/infrastructure/config.py` lit `DATABASE_URL` **à
l'appel**, ainsi que `DBT_MARTS_SCHEMA` (défaut `analytics_marts`) pour suivre le schéma
construit par dbt. Conséquences voulues et testées :

- l'application démarre et répond sur `/health` **sans base joignable** ;
- une configuration absente produit une erreur explicite (`MissingConfigurationError`) qui
  **nomme la variable** sans jamais reprendre d'identifiant.

## Vérifications (2026-10-17)

| Contrôle | Résultat |
|---|---|
| `ruff check .` | 0 erreur |
| `pytest -q` (suite complète) | **220 réussis** (182 avant l'incrément → +38) |
| serveur réel (`uvicorn backend.api.app:app`) | `/api/v1/health` → **200** `{"status":"ok","api_version":"0.1.0","api_prefix":"/api/v1"}` |
| route inconnue, HTTP réel | `/api/v1/inconnu` → **404** au format unique |
| route hors préfixe versionné | `/health` → **404** |
| contrat OpenAPI | `paths = ['/api/v1/health']`, titre « CamRent — API publique », version 0.1.0 |
| fuite technique | test dédié : le message d'une exception interne n'apparaît pas dans la réponse |

Vérifications de l'incrément de prédiction (#51, 2026-10-17) :

| Contrôle | Résultat |
|---|---|
| `ruff check .` | 0 erreur |
| `pytest -q` (suite complète) | **240 réussis** (220 avant l'incrément → +20) |
| prédiction réelle (modèle épinglé) | **200** — `{"estimated_rent":109990,"currency":"XAF","lower_bound":80000,"upper_bound":150002,"model_version":"rent-model-v4"}` |
| reproductibilité | deux `POST` identiques → réponses **identiques** |
| hors domaine | quartier inconnu et quartier jamais vu avec la ville → **404 `not_found`** |
| champ non collecté | `area_m2` → **422** `validation_error` avec détail par champ |
| contrat OpenAPI | `paths = ['/api/v1/health', '/api/v1/predictions']` |
| échec de serving | test : 500 `internal_error` générique, ni chemin ni classe d'exception fuités |

Vérifications de l'incrément de provenance (#52, 2026-10-18) :

| Contrôle | Résultat |
|---|---|
| re-promotion gouvernée | `python -m ml.src registry --confirm-promotion --approved-by "Ibrahim Talla"` → **`rent-model-v4`**, alias `champion` → 4, pin réécrit |
| dataset du pin | `mart_ml_dataset@d3c11c225f48` — identique au mart vivant (2 992 observations, 21 colonnes) |
| contrôle de provenance réel | alias `champion` → v4 et URI `models:/m-517f4fb9...` conformes au pin ; un pin divergent (v3 + URI v3) → **refus explicite** |
| prédiction réelle | **200** — mêmes valeurs qu'en v3 (features inchangées), `model_version` = `rent-model-v4`, deux `POST` identiques → réponses identiques |
| lecture défensive | pin absent → `FileNotFoundError` ; pin illisible / incomplet / sans `dataset.hash_md5` → erreur explicite nommant le fichier ou les clés |
| contrôle avant serving | `python -m ml.src pin` → **exit 0** avec `rent-model-v4` / `mart_ml_dataset@d3c11c225f48` ; pin absent → **exit 1** et message nommant le fichier |
| préflight pin ↔ mart | `python -m ml.src pin --check-dataset` → **exit 0** (mart vivant conforme) ; pin périmé → **exit 1** nommant les deux versions ; base injoignable → **exit 1** |
| intervalle servi depuis le registre | fichier local `ml/models/rent_model_v1_intervalle.joblib` **retiré** : la prédiction reste **200** et identique (mêmes bornes) |
| test d'intégration en CI | `tests/unit/test_serving_registry.py` : registre MLflow **SQLite** + artefacts temporaires → modèle et intervalle chargés, alias périmé refusé, artefact absent signalé |
| fixture isolé | le serving est testé **sans** registre, sans base et sans artefact du poste (fixture `tests/unit/serving_fixture.py`) — exécuté en CI |

Vérifications de l'incrément de marché (#53, 2026-10-19) :

| Contrôle | Résultat |
|---|---|
| `ruff check .` | 0 erreur |
| `pytest -q` (suite complète, base réelle chargée) | **279 réussis** — 256 avant l'incrément, +16 tests unitaires, +7 tests d'intégration |
| `dbt build` local | **169/169** (16 modèles, 153 tests) — 137/137 avant l'enrichissement des marts |
| endpoints réels (`TestClient`, marts du 2026-10-19) | `/market/cities` → Douala N=2 811 (méd. 100 000), Yaoundé N=181 (méd. 150 000) ; `/market/neighborhoods?city=Douala` → 88 quartiers, N total 2 811 ; `/market/prices?city=Douala&neighborhood=Makepe&property_type=apartment&bedrooms=2` → **N=632**, médiane 90 000, `median_published=true` |
| seuil sur données réelles | groupe sous 30 observations → `median_rent_price: null`, `median_published: false`, N et moyenne présents |
| comparaison aux marts | `tests/integration/test_market_api.py` relit les marts en SQL et compare **toutes** les valeurs (N, moyenne, médiane, p10/p90, min/max, qualité, période) |
| filtre sans résultat | quartier inexistant → **200** `n_observations: 0`, `groups: []` ; mois hors période → **200** vide explicite ; `neighborhood` sans `city` → **400** |
| filtre invalide | ville hors vocabulaire, `bedrooms=11`, `period=2026-13` → **422** `validation_error` |
| contrat OpenAPI | `paths` contient `/api/v1/market/cities`, `/neighborhoods`, `/prices` |

Vérifications de l'incrément de comparaison (#54, 2026-10-19) :

| Contrôle | Résultat |
|---|---|
| `ruff check .` | 0 erreur |
| `pytest -q --ignore=tests/integration` | **286 réussis** (272 avant l'incrément, +14 tests de comparaison) |
| `pytest -q tests/integration` | **11 réussis** (7 marché + 4 comparaison) |
| `dbt build` | **169/169** inchangé — aucun changement de données dans cet incrément |
| comparaison réelle | Makepe × appartement × 2 ch. à 150 000 FCFA → estimation **109 990**, marché **N=632** (moyenne 98 498, médiane 90 000), écarts **+40 010 (+36,4 %)**, **+51 502 (+52,3 %)**, **+60 000 (+66,7 %)** |
| seuil sur données réelles | Bonapriso × appartement × 1 ch. → marché **N=25**, médiane `null`, `median_published=false`, `to_market_median=null`, moyenne et écart moyen présents |
| comparaison multiple | deux logements (Makepe N=632 publiée, Bastos N=9 non publiée) → deux entrées dans l'ordre, un seul `model_version` (`rent-model-v4`) |
| cohérence avec les endpoints | `tests/integration/test_comparison_api.py` compare chaque estimation et chaque valeur de marché aux réponses directes de `/predictions` et `/market/prices` |
| groupe de marché absent | combinaison sans ligne de mart → **200** avec `market: null`, écarts marché nuls, estimation fournie |
| quartier inconnu | **404** `not_found`, aucune estimation dans la réponse |
| requête invalide | liste vide, 11 logements, `asking_rent=0`, `area_m2`, `bathrooms=11`, ville hors vocabulaire → **422** |
| CI synthétique | jeu de 360 lignes chargé dans une base séparée → `dbt build` 169/169 puis **11 tests d'intégration réussis** |

Vérifications de l'incrément d'API interne (#61, 2026-10-20) :

| Contrôle | Résultat |
|---|---|
| `ruff check .` | 0 erreur |
| `pytest -q --ignore=tests/integration` | **357 réussis** (286 avant l'incrément, +71) |
| `makemigrations --check --dry-run` | « No changes detected » |
| migrations réelles (PostgreSQL local) | `accounts.0001_initial` puis `audit.0001_initial` appliquées |
| bootstrap réel | `create_internal_user --email admin@camrent.local` → compte `admin` créé et entrée d'audit `users.create` (source `cli`) |
| serveur réel (Django ASGI, port 8001) | `/internal/api/v1/health` → **200** |
| session réelle | `POST /auth/login` → **200** (jeton de 43 caractères) ; `/me` avec jeton → **200** ; `/me` sans jeton → **401 `unauthenticated`** |
| mot de passe faux | **401 `invalid_credentials`**, réponse identique à celle d'un compte inconnu |
| rôle insuffisant (HTTP réel) | compte au rôle `reader` → `/me` et `/users` **403 `forbidden`** ; refus journalisé (`denied`, acteur et cible) ; aucune création de compte |
| création de compte | **201** ; doublon → **409 `conflict`** |
| déconnexion | **204**, puis `/me` avec le même jeton → **401** |
| frontière public/interne | route publique sur l'interne → **404** JSON ; route interne sur le public → **404** ; `/api/v1/health` public toujours **200** sans authentification |
| audit consultable | `GET /audit` → entrées les plus récentes d'abord, avec auteur, action, cible, date et résultat |
| minimisation | test : ni mot de passe ni jeton dans une réponse d'audit ; clés sensibles filtrées à l'écriture |

## Lancer et rejouer

```bash
uvicorn backend.api.app:app --reload              # API publique (développement)
python -m pytest tests/unit/test_api_*.py -q      # contrat HTTP public + interne (dépôts simulés)
python -m pytest tests/integration -q             # comparaison aux marts (DATABASE_URL requise)

# API interne (Django) — application distincte
python manage.py migrate
python manage.py create_internal_user --email admin@camrent.local
uvicorn backend.internal.asgi:application --port 8001
python -m pytest tests/unit/test_api_internal_*.py -q
```

## Invariants respectés

- Aucune base ni aucun modèle n'est requis pour démarrer : le socle ne simule aucune capacité.
- Aucun champ affiché ou accepté que le modèle ignore.
- Aucun secret dans le code, les tests ou les logs ; l'erreur interne est générique.
- L'API publique et l'API interne restent **deux applications distinctes** :
  `backend/api/app.py` sert uniquement le public, `backend/internal/` uniquement l'interne,
  et aucune des deux ne monte une route de l'autre (vérifié par test et sur serveur réel).
- Le journal d'audit ne reçoit **aucun** secret : ni mot de passe, ni jeton, ni en-tête
  d'autorisation (filtre à l'écriture, testé).

## Limites connues

- **API publique complète, API interne amorcée** : les cinq incréments du 08a sont livrés,
  et le socle du 08b (08b.1 : authentification, rôle `admin`, audit) est livré. Les modules
  métier du back-office (13.1 à 13.5) et son interface (09b) restent à ouvrir.
- **API interne — session sans rafraîchissement** : le jeton vit 12 h et se révoque par
  `POST /auth/logout` ; il n'y a ni rafraîchissement automatique ni liste des sessions
  actives. À ajuster quand l'interface d'administration (09b.1) sera construite.
- **API interne — lecture de l'audit non journalisée** : consulter le journal n'écrit pas
  d'entrée (seules les actions de mutation, les connexions et les refus le font), pour
  éviter qu'une simple consultation ne fasse grossir la table.
- **Comparaison — pas de salles de bain dans la référence** : le groupe local est le grain
  du mart `(ville, quartier, type, chambres)`. Les salles de bain influencent l'estimation
  mais pas le groupe, faute de mart à ce grain ; la réponse l'explicite en répétant le groupe.
- **Comparaison — groupe absent** : `market: null` plutôt qu'une référence élargie. C'est
  volontaire : une moyenne de quartier ou de ville ne décrit pas le même logement.
- **Marché — période unique** : les marts de marché n'ont pas de dimension temporelle et
  les observations tiennent dans un seul mois (2026-10-09). `period` est accepté pour ce
  mois et renvoie un vide explicite pour un autre ; il sera refusé en 400 si une collecte
  étalée dans le temps rend les marts multi-mois sans que le filtre soit implémenté.
- **Marché — pas de médiane par quartier agrégée** : `/market/neighborhoods` expose
  effectifs, moyenne pondérée et bornes, pas de médiane ni de centiles (agrégation non
  mathématiquement valide). Le détail médian reste par groupe dans `/market/prices`.
- **Marché et comparaison — base requise** : contrairement à `/health` et à la prédiction
  seule, ces routes exigent `DATABASE_URL` et les marts construits ; une base absente
  produit une erreur interne générique, sans fuite de configuration.
- **Provenance du modèle** : le pin décrit le mart vivant (`rent-model-v4`,
  `mart_ml_dataset@d3c11c225f48`), l'alias `champion` est vérifié au chargement et le
  préflight `python -m ml.src pin --check-dataset` compare le pin au mart avant
  déploiement. La cohérence n'est volontairement **pas** revérifiée à chaque requête
  (ce serait un couplage base → serving, coûteux et inutile par appel).
- **Registre indispensable au serving** : modèle et intervalle viennent du registre
  MLflow. Un poste sans registre joignable ne peut pas servir — c'est le prix d'une
  provenance unique et vérifiable.
- **Chargement réel** : le chemin de production (registre + artefacts du run épinglé)
  est exercé **en CI** par `tests/unit/test_serving_registry.py` (MLflow SQLite et
  artefacts temporaires) ; le fixture isolé reste utilisé pour les tests rapides de
  logique métier.
- **Avertissement de bibliothèque** : `starlette.testclient` signale que l'usage d'`httpx`
  est déprécié au profit d'`httpx2`. Le test fonctionne ; c'est un choix de dépendance à
  réévaluer lors d'une montée de version de Starlette.

## Incréments suivants

| Ticket | Contenu |
|---|---|
| #55 à #58 | Interface publique d'estimation (09a.1 à 09a.4) — consommation de l'API publique |
| #62 à #66 | Modules du back-office (13.1 sources, 13.2 datasets, 13.3 qualité, 13.4 jobs ML, 13.5 registre) — s'appuient sur l'API interne |
| #68 | Interface d'administration : socle et navigation (09b.1) |
| #60 | Tests d'intégration API → base → modèle et parcours de bout en bout |
