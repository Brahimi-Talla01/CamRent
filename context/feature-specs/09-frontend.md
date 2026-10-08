# Phase 9 — Frontend

Lire `context/ui-context.md`, `context/project-overview.md` et `context/code-standards.md` (§Frontend) avant de commencer.

Objectif : construire l'application utilisateur qui rend l'estimation et l'analyse du marché
compréhensibles par des non-techniciens.

> Avant d'implémenter : compléter `context/ui-context.md` (palette, typographie, composants,
> breakpoints). Ne pas inventer de design system : figer d'abord le thème, puis l'appliquer.

## Implementation

1. Initialiser le projet dans `frontend/` (Next.js + TypeScript).

2. Construire les écrans selon le flux :

   ```
   Accueil
     ↓
   Estimer mon loyer        (formulaire)
     ↓
   Résultat                 (loyer estimé + fourchette + contexte + n observations)
     ↓
   Explorer le marché       (statistiques par quartier / type)
     ↓
   Comparer                 (2+ logements)
   ```

3. **Formulaire d'estimation** : ville, quartier, type, chambres, salles de bain, superficie (si
   disponible), meublé, parking, barrière, équipements.

4. **Écran résultat** : loyer estimé, fourchette, statistiques de la zone, nombre d'observations,
   information sur la fiabilité des données, et la mention que l'estimation repose sur les prix
   demandés dans les annonces.

5. **Explorer** : prix moyen / médian, fourchette courante, nombre d'observations par zone.

6. **Comparer** : différence de prix, écart aux estimations, prix moyen de chaque zone, facteurs
   expliquant l'écart.

7. Brancher le frontend sur l'API (Phase 8).

## Dependencies

- Next.js + TypeScript.
- API de prédiction / marché / comparaison (Phase 8).
- `context/ui-context.md` complété.

## Scope Limits

- Ne pas afficher de pourcentage de confiance non justifié statistiquement.
- Ne pas afficher de statistique sans nombre d'observations.
- Pas de dashboard surchargé.
- Pas de recherche par budget (post-MVP).

## Check When Done

- Les écrans principaux existent et suivent le flux défini.
- Le formulaire appelle l'API et affiche estimation + fourchette + contexte.
- L'exploration et la comparaison fonctionnent sur les données réelles.
- Les limites de l'estimation sont visibles dans l'interface.
- Aucun chiffre n'est présenté comme une valeur officielle.
- `ui-context.md` reflète le thème réellement implémenté.
