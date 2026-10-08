# UI Context

> ⚠️ Ce fichier est **provisoire**. Le thème, la palette et la typographie de CamRent ne sont pas
> encore définis dans les documents produits. Ils seront figés en **Phase 9 (Frontend)**.
> Tant que ce fichier n'est pas complété, ne pas inventer de design system : utiliser les
> principes ci-dessous et poser un point ouvert dans `progress-tracker.md`.

## Principes d'interface (MVP)

- **Comprendre avant de prédire** : l'interface sert la compréhension du marché, pas la démonstration technique.
- **Transparence sur l'incertitude** : tout résultat affiche une fourchette et le nombre d'observations.
- **Pas de fausse précision** : jamais de pourcentage de confiance si le modèle ne peut pas le justifier statistiquement.
- **Pas de dashboards surchargés** : hiérarchie claire, une question par écran.
- **Accessibilité** : contrastes suffisants, tailles de texte lisibles, responsive par défaut.
- **Contextualisation** : une estimation s'accompagne toujours du contexte de la zone et des limites de la donnée.

## Structure d'écran visée (MVP)

```
Accueil
  ↓
Estimer mon loyer        (formulaire)
  ↓
Résultat                 (loyer estimé + fourchette + stats de zone + n observations)
  ↓
Explorer le marché       (statistiques par quartier / type)
  ↓
Comparer                 (2+ logements : écarts, explications)
```

## Formats de réponse à respecter

Estimation :

```
Loyer estimé          185 000 FCFA / mois
Fourchette estimée    165 000 – 205 000 FCFA
Fiabilité             (basée sur n observations dans la zone)
```

Exploration :

```
Prix moyen     155 000 FCFA
Prix médian    150 000 FCFA
Fourchette     130 000 – 190 000 FCFA
Observations   248
```

## À définir en Phase 9

- Palette de couleurs (variables CSS / tokens).
- Typographie et échelle de tailles.
- Composants de base et échelle d'arrondis.
- Design mobile / breakpoints.
- Style des graphiques (distributions, cartes de prix).

Toute décision ci-dessus doit être écrite ici **avant** d'être implémentée, puis suivie sans exception.
