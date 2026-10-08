# Phase 8 — API

Lire `context/architecture-context.md` et `context/code-standards.md` (§API) avant de commencer.

Objectif : exposer le modèle et les données de marché via une API backend claire, versionnée et
reproductible.

## Implementation

1. Construire le backend dans `backend/` :

   ```
   backend/
   ├── api/
   ├── domain/
   ├── services/
   ├── repositories/
   ├── ml/
   ├── schemas/
   └── infrastructure/
   ```

2. **API de prédiction** :

   ```
   POST /api/v1/predictions
   ```

   Payload :

   ```json
   {
     "city": "Douala",
     "neighborhood": "Bonamoussadi",
     "property_type": "apartment",
     "bedrooms": 2,
     "bathrooms": 2,
     "area_m2": 110,
     "parking": true,
     "gated": true
   }
   ```

   Réponse :

   ```json
   {
     "estimated_rent": 185000,
     "currency": "XAF",
     "lower_bound": 165000,
     "upper_bound": 205000,
     "model_version": "rent-model-v3"
   }
   ```

3. **API de marché** :

   ```
   GET /api/v1/market/cities
   GET /api/v1/market/neighborhoods
   GET /api/v1/market/prices
   ```

   Paramètres : `city`, `neighborhood`, `property_type`, `bedrooms`, `period`.
   Toute statistique renvoyée inclut le **nombre d'observations**.

4. **API de comparaison** :

   ```
   POST /api/v1/comparisons
   ```

   Compare : prix demandé, prix estimé, prix moyen local, caractéristiques.

5. Charger le modèle versionné (Phase 7) côté serving ; exposer le `model_version` dans chaque réponse.

6. Valider les entrées avec des schémas stricts ; retourner des erreurs prévisibles (400 / 404 / 422).

## Dependencies

- FastAPI (+ uvicorn) pour rester dans l'écosystème Python.
- PostgreSQL pour les données de marché.
- Modèle enregistré (Phase 7).

## Scope Limits

- Pas d'authentification complexe au MVP (elle ne sera introduite qu'en Phase 12 si nécessaire).
- Le handler ne fait pas d'entraînement : il charge le modèle et prédit.
- Pas de logique métier lourde dans les routes : elle va dans `services/` / `domain/`.

## Check When Done

- Les endpoints prédiction / marché / comparaison répondent avec les formes définies.
- La réponse de prédiction inclut toujours `lower_bound`, `upper_bound` et `model_version`.
- Les statistiques de marché incluent le nombre d'observations.
- Les entrées invalides produisent des erreurs prévisibles.
- L'API est reproductible : même entrée + même version de modèle → même sortie.
