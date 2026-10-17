# Phase 8 — API publique : socle (08a.1)

Objectif (spec : `context/feature-specs/08-api.md`) : exposer le modèle et les données de
marché via une API backend claire, versionnée et reproductible.

La phase 8 est livrée en **deux temps** (plan §10, lot 4) : **08a API publique** puis
**08b API interne**. Ce document couvre le premier incrément du 08a — le **socle**
(ticket #50) : structure `backend/`, schémas stricts, erreurs au format unique, route de
version. Aucun endpoint métier n'est encore exposé.

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
répond 404). `api_version` décrit le contrat, pas le modèle — la version servie sera
exposée par l'endpoint de prédiction (ticket #51).

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

- **Aucun endpoint métier** : prédiction (#51), marché (#53) et comparaison (#54) restent à
  livrer ; le socle n'affiche donc encore aucune donnée de marché.
- **Provenance du modèle** : l'écart mesuré entre le dataset du pin `champion`
  (`mart_ml_dataset@5050042e720e`) et le mart vivant (`mart_ml_dataset@d3c11c225f48`) est
  traité par le ticket #52, avant que l'API n'expose `model_version`.
- **Tests isolés du poste local** : le chargement du modèle épinglé et son fixture de test
  (emplacements d'artefacts enregistrés en chemins absolus) sont dans le périmètre de #52.
- **Avertissement de bibliothèque** : `starlette.testclient` signale que l'usage d'`httpx`
  est déprécié au profit d'`httpx2`. Le test fonctionne ; c'est un choix de dépendance à
  réévaluer lors d'une montée de version de Starlette.

## Incréments suivants

| Ticket | Contenu |
|---|---|
| #51 | `POST /api/v1/predictions` (modèle épinglé, fourchette, `model_version`) |
| #52 | Provenance du modèle épinglé + fixture de modèle isolée |
| #53 | Endpoints de marché (villes, quartiers, prix) — nombre d'observations obligatoire |
| #54 | Endpoint de comparaison |
| #60 | Tests d'intégration API → base → modèle et parcours de bout en bout |
