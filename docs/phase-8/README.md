# Phase 8 — API publique : socle (08a.1) et prédiction (08a.2)

Objectif (spec : `context/feature-specs/08-api.md`) : exposer le modèle et les données de
marché via une API backend claire, versionnée et reproductible.

La phase 8 est livrée en **deux temps** (plan §10, lot 4) : **08a API publique** puis
**08b API interne**. Ce document couvre les deux premiers incréments du 08a — le
**socle** (ticket #50 : structure `backend/`, schémas stricts, erreurs au format unique,
route de version) puis **l'endpoint de prédiction** (ticket #51 : `POST
/api/v1/predictions`, modèle épinglé, fourchette, `model_version`). Les endpoints de
marché (#53) et de comparaison (#54) suivent.

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

Réponse — **réelle**, servie par le modèle épinglé (vérification du 2026-10-17) :

```json
{
  "estimated_rent": 109990,
  "currency": "XAF",
  "lower_bound": 80000,
  "upper_bound": 150002,
  "model_version": "rent-model-v3"
}
```

Points de conception :

- **Modèle épinglé, jamais entraîné dans la requête** : le bundle vient de
  `ml/models/champion.json` — le pipeline est chargé à l'URI de registre épinglée
  (`model_uri`), pas depuis un fichier local implicite. `model_version` est l'étiquette
  du pin, identique à chaque réponse tant que le pin ne change pas.
- **Fourchette par le modèle retenu** : l'intervalle **quantile** 5 % / 95 % déjà
  calibré en Phase 6, chargé depuis l'artefact local
  `ml/models/rent_model_v1_intervalle.joblib` (décision du porteur du projet,
  2026-10-17). Ce fichier n'est pas versionné : s'il manque, le service échoue
  explicitement plutôt que de servir une estimation sans fourchette — jamais de
  fourchette improvisée, jamais d'application de pourcentage arbitraire.
- **Domaine servi** : le service refuse tout couple (ville, quartier) que le modèle
  chargé n'a jamais vu à l'entraînement — **404 `not_found`**. C'est nécessaire : hors
  domaine, le pipeline traiterait silencieusement la saisie (profondeur de marché nulle,
  one-hot ignoré) et produirait une estimation faussement plausible. Une ville ou un type
  hors vocabulaire reste un **422** du schéma ; le choix 404 / 422 pour une valeur
  inconnue a été tranché par le porteur du projet (2026-10-17) : 404 pour une valeur
  inconnue, 422 pour un contrat d'entrée violé.
- **Cache et démarrage** : le bundle est chargé une seule fois (verrou), au premier appel
  utile ; l'application démarre et sert la santé sans registre ni artefact joignables.

Vérifications HTTP réelles (serveur `uvicorn`, modèle épinglé v3) : 200 avec fourchette
ordonnée (80 000 ≤ 109 990 ≤ 150 002 FCFA) ; deux appels identiques → réponses
**identiques** ; quartier inconnu → 404 `not_found` ; quartier réel mais jamais vu avec
cette ville → 404 ; `area_m2` → 422 `validation_error` avec le détail du champ.

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

## Configuration

Aucun secret ni chemin en dur : `backend/infrastructure/config.py` lit `DATABASE_URL` **à
l'appel**. Conséquences voulues et testées :

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
| prédiction réelle (modèle épinglé) | **200** — `{"estimated_rent":109990,"currency":"XAF","lower_bound":80000,"upper_bound":150002,"model_version":"rent-model-v3"}` |
| reproductibilité | deux `POST` identiques → réponses **identiques** |
| hors domaine | quartier inconnu et quartier jamais vu avec la ville → **404 `not_found`** |
| champ non collecté | `area_m2` → **422** `validation_error` avec détail par champ |
| contrat OpenAPI | `paths = ['/api/v1/health', '/api/v1/predictions']` |
| échec de serving | test : 500 `internal_error` générique, ni chemin ni classe d'exception fuités |

## Lancer et rejouer

```bash
uvicorn backend.api.app:app --reload          # développement
python -m pytest tests/unit/test_api_*.py -q   # tests de l'incrément
```

## Invariants respectés

- Aucune base ni aucun modèle n'est requis pour démarrer : le socle ne simule aucune capacité.
- Aucun champ affiché ou accepté que le modèle ignore.
- Aucun secret dans le code, les tests ou les logs ; l'erreur interne est générique.
- L'API publique et l'API interne resteront **deux applications distinctes** : le socle
  n'expose aucune route interne, et `backend/api/app.py` sert uniquement le public.

## Limites connues

- **Endpoints restants** : marché (#53) et comparaison (#54) restent à livrer ; l'API
  n'affiche encore aucune donnée de marché.
- **Provenance du modèle** : `model_version` est désormais exposé (`rent-model-v3`), et
  l'écart mesuré entre le dataset du pin `champion` (`mart_ml_dataset@5050042e720e`) et le
  mart vivant (`mart_ml_dataset@d3c11c225f48`) reste traité par le ticket #52 — l'écart est
  documenté, jamais silencieux.
- **Fourchette liée à un artefact local** : l'intervalle calibré vient d'un fichier non
  versionné (`ml/models/rent_model_v1_intervalle.joblib`) — sa présence est exigée au
  chargement (erreur explicite sinon), mais un déploiement sur une machine neuve doit le
  régénérer (`python -m ml.src models`) ou le transférer. Couplage à trancher en #52.
- **Chargement réel testé en local** : les tests unitaires et la CI utilisent un fixture de
  modèle isolé (sans registre ni artefact) ; le chargement depuis le registre MLflow n'est
  exercé que sur le poste de développement. Le fixture de serving durci est le périmètre de #52.
- **Avertissement de bibliothèque** : `starlette.testclient` signale que l'usage d'`httpx`
  est déprécié au profit d'`httpx2`. Le test fonctionne ; c'est un choix de dépendance à
  réévaluer lors d'une montée de version de Starlette.

## Incréments suivants

| Ticket | Contenu |
|---|---|
| #52 | Provenance du modèle épinglé + fixture de modèle isolée |
| #53 | Endpoints de marché (villes, quartiers, prix) — nombre d'observations obligatoire |
| #54 | Endpoint de comparaison |
| #60 | Tests d'intégration API → base → modèle et parcours de bout en bout |
