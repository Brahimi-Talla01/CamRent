# Phase 8 — API

Lire `context/architecture-context.md` et `context/code-standards.md` (§API) avant de commencer.

Objectif : exposer le modèle et les données de marché via une API backend claire, versionnée et
reproductible.

> **Découpage (plan de réalignement §10, lot 4)** : la Phase 8 est livrée en deux temps —
> **08a API publique** (prédiction, marché, comparaison — le présent document) puis
> **08b API interne** (permissions, jobs, administration ; voir `13-backoffice-foundations.md`).
>
> **Statut (2026-10-15)** : payload corrigé après l'audit (plan §5, P6) — les champs non
> collectés en sont retirés.

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

   Payload (seuls les caractères réellement pris en charge par le modèle sont acceptés ;
   les champs non collectés — `area_m2`, `parking`, `gated`, `furnished` — ne font
   **pas** partie du schéma, qui est strict) :

   ```json
   {
     "city": "Douala",
     "neighborhood": "Bonamoussadi",
     "property_type": "apartment",
     "bedrooms": 2,
     "bathrooms": 2
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

   Précisions de contrat (ticket #53, 2026-10-19) :

   - `/market/neighborhoods` exige `city` ; sans elle, la requête est refusée (422).
   - `/market/prices` lit le mart dont le grain couvre exactement les filtres : ville
     seule → `mart_city_prices` ; type seul → `mart_property_prices` ; quartier ou
     chambres → `mart_neighborhood_prices`. Aucun mélange de grains dans une statistique.
   - La médiane n'est publiée qu'à partir du seuil `min_publish_n` (défaut 30) ; la réponse
     porte `median_published`. `/market/neighborhoods` ne publie **pas** de médiane
     agrégée (agréger des médianes n'est pas valide) : elle expose effectifs, moyenne
     pondérée, minimum, maximum et drapeaux de qualité.
   - `period` suit les marts : tant qu'ils couvrent un seul mois, ce mois est accepté et
     tout autre renvoie une réponse vide explicite (`n_observations: 0`). Si les marts
     couvrent plusieurs mois sans dimension temporelle, le filtre est refusé (400).
   - Filtre sans résultat : liste vide explicite, jamais une statistique inventée.
     `neighborhood` sans `city` → 400 (un quartier n'est pas unique entre villes).

4. **API de comparaison** :

   ```
   POST /api/v1/comparisons
   ```

   Compare : prix demandé, prix estimé, prix moyen local, caractéristiques.

   Précisions de contrat (ticket #54, 2026-10-19) :

   - Entrée : `{"listings": [...]}` avec **1 à 10** logements, chacun portant les
     cinq champs du modèle (`city`, `neighborhood`, `property_type`, `bedrooms`,
     `bathrooms`) et `asking_rent` (loyer mensuel demandé, FCFA). Les champs non
     collectés restent refusés (même schéma strict que `/predictions`).
   - Sortie, par logement : l'estimation et sa fourchette, la référence locale
     (groupe, `n_observations`, moyenne, médiane et `median_published`, qualité),
     puis les écarts **signés** `asking_rent - référence` (`absolute` et
     `relative_pct`). Un écart positif signifie « au-dessus de la référence ».
   - **Groupe de comparaison = grain du mart** `(ville, quartier, type, chambres)`.
     Les salles de bain entrent dans l'estimation mais pas dans la référence
     locale : les marts n'exposent pas ce grain. Le groupe est explicite dans la
     réponse.
   - **Réutilisation stricte** : la comparaison appelle le service d'estimation
     de 08a.2 et le service de marché de 08a.4 ; elle ne recalcule ni estimation
     ni statistique. Les valeurs doivent être identiques aux endpoints directs.
   - Médiane sous le seuil : `median_rent_price: null`, `median_published: false`,
     `gaps.to_market_median: null` — jamais un écart calculé sur une médiane non
     publiée. Groupe de marché absent : `market: null` et écarts marché nuls, sans
     élargir silencieusement la référence ; l'estimation reste fournie.
   - Quartier inconnu du modèle → **404** comme `/predictions` ; requête invalide
     (liste vide, plus de 10 logements, prix demandé < 1) → **422**.
   - Aucun score de confiance, aucune note, aucune recommandation : l'API informe
     sur l'écart, elle ne certifie pas une valeur officielle.

5. Charger le modèle **épinglé** (version servie consignée dans `ml/models/champion.json`,
   Phase 7) côté serving ; exposer le `model_version` dans chaque réponse.

6. Valider les entrées avec des schémas stricts ; retourner des erreurs prévisibles (400 / 404 / 422).

7. **API interne (08b)** — application **distincte** de l'API publique, servie séparément :

   ```
   GET  /internal/api/v1/health
   POST /internal/api/v1/auth/login
   POST /internal/api/v1/auth/logout
   GET  /internal/api/v1/me
   POST /internal/api/v1/users
   GET  /internal/api/v1/audit
   ```

   Précisions de contrat (ticket #61, 2026-10-20) :

   - Authentification par jeton `Authorization: Bearer`, sans session ni cookie (donc
     sans CSRF) ; le jeton n'est affiché qu'une fois et seule son empreinte est stockée.
   - Un seul rôle ouvert : `admin` (spec 13 §Scope Limits). Chaque route déclare l'action
     qu'elle protège ; le contrôle échoue fermé (action inconnue ou rôle non déclaré → 403).
   - Refus : **401** `unauthenticated` (jeton absent, invalide, expiré ou révoqué) et
     **403** `forbidden` (rôle insuffisant). Comme pour le public, un compte inconnu et un
     mot de passe faux donnent la même réponse.
   - Toute action sensible est journalisée avec auteur, action, cible, date et résultat ;
     le journal est consultable. Aucun mot de passe ni jeton n'y est écrit.
   - Les deux applications ne montent aucune route l'une de l'autre (ticket #61).

## Dependencies

- FastAPI (+ uvicorn) pour l'API **publique** ; Django pour l'API **interne** (08b),
  application séparée.
- PostgreSQL pour les données de marché et pour les comptes/audit internes.
- Modèle enregistré (Phase 7).

## Scope Limits

- Pas d'authentification sur l'API **publique** (08a) ; l'API **interne** (08b) exige
  authentification et rôle `admin` (services communs, `13-backoffice-foundations.md`).
- Le handler ne fait pas d'entraînement : il charge le modèle **épinglé** et prédit.
- Pas de logique métier lourde dans les routes : elle va dans `services/` / `domain/`.

## Check When Done

- Les endpoints prédiction / marché / comparaison répondent avec les formes définies.
- La réponse de prédiction inclut toujours `lower_bound`, `upper_bound` et `model_version`.
- Les statistiques de marché incluent le nombre d'observations.
- Les entrées invalides produisent des erreurs prévisibles.
- L'API est reproductible : même entrée + même version de modèle → même sortie.
