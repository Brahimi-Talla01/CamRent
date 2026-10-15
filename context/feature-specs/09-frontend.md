# Phase 9 — Frontend

Lire `context/ui-context.md`, `context/project-overview.md` et `context/code-standards.md` (§Frontend) avant de commencer.

Objectif : construire l'application utilisateur qui rend l'estimation et l'analyse du marché
compréhensibles par des non-techniciens.

> **Découpage (plan de réalignement §10)** : la Phase 9 se découpe en **09a estimation
> publique** (le présent document) et **09b administration** (interface du back-office,
> fondée sur `13-backoffice-foundations.md` et `14-backoffice-reporting-observability.md`).
>
> **Statut (2026-10-15)** : formulaire corrigé après l'audit — il ne demande que les
> caractéristiques réellement prises en charge par le modèle.

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

3. **Formulaire d'estimation** : ville, quartier, type, chambres, salles de bain. Les
   caractéristiques non collectées (superficie, meublé, parking, barrière, équipements)
   ne sont **pas** demandées tant que la décision 6 (finaliser le MVP d'abord) ne les
   autorise pas — afficher un champ que le modèle ignore biaiserait la confiance.

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
