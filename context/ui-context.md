# UI Context — thème figé

> **Statut (2026-10-20) : thème figé, première version.** Décisions prises lors du socle
> Next.js (ticket **09a.1**, Phase 9a). Ce fichier est la **référence** : toute couleur,
> taille ou espacement utilisé dans `frontend/` vient de ces tokens. Une couleur écrite en
> dur dans un composant est un défaut de revue.
>
> Le thème est volontairement simple : pas de bibliothèque de composants, pas de thème
> sombre au MVP, pas de police téléchargée (aucune requête réseau pour l'affichage).

## Principes d'interface (MVP)

- **Comprendre avant de prédire** : l'interface sert la compréhension du marché, pas la démonstration technique.
- **Transparence sur l'incertitude** : tout résultat affiche une fourchette et le nombre d'observations.
- **Pas de fausse précision** : jamais de pourcentage de confiance si le modèle ne peut pas le justifier statistiquement.
- **Pas de tableaux de bord surchargés** : hiérarchie claire, une question par écran.
- **Accessibilité** : contrastes suffisants (WCAG AA), tailles lisibles, navigation au clavier, responsive.
- **Contextualisation** : une estimation s'accompagne toujours du contexte de la zone et des limites de la donnée.

## Palette (tokens CSS)

Les valeurs sont définies une seule fois dans `frontend/app/globals.css` (`:root`) et
consommées via `var(--…)`. Une couleur de composant ne doit **jamais** être une valeur littérale.

| Token | Valeur | Usage |
|---|---|---|
| `--color-bg` | `#F7F5F0` | fond de page (sable clair) |
| `--color-surface` | `#FFFFFF` | cartes, en-tête, champs |
| `--color-surface-muted` | `#EFEBE3` | zones secondaires, lignes alternées |
| `--color-ink` | `#152420` | texte principal |
| `--color-ink-muted` | `#4F625B` | texte secondaire, légendes |
| `--color-border` | `#DBD5C9` | séparateurs, contours |
| `--color-primary` | `#0E5B4A` | actions principales, liens, séries |
| `--color-primary-strong` | `#0A4638` | survol / pression |
| `--color-primary-soft` | `#E3F0EB` | fonds d'accent, sélection |
| `--color-on-primary` | `#FFFFFF` | texte sur aplat primaire |
| `--color-accent` | `#B26A00` | point d'attention, valeur mise en avant |
| `--color-accent-soft` | `#FBF0DF` | fond d'encart d'attention |
| `--color-accent-ink` | `#6B3F00` | texte sur `--color-accent-soft` |
| `--color-danger` | `#A32A2A` | erreurs, refus |
| `--color-danger-soft` | `#FBE9E9` | fond d'erreur |
| `--color-focus` | `#0E5B4A` | anneau de focus (3 px, décalé de 2 px) |

Contrastes vérifiés (texte sur fond) : `--color-ink` sur `--color-bg` ≈ 15:1 ;
`--color-ink-muted` sur `--color-bg` ≈ 6:1 ; `--color-on-primary` sur `--color-primary`
≈ 8:1 ; `--color-accent-ink` sur `--color-accent-soft` ≈ 7:1. Aucun texte informatif sous
4,5:1.

Séries de graphique (dans l'ordre) : `--chart-1 #0E5B4A`, `--chart-2 #B26A00`,
`--chart-3 #4B6EA8`, `--chart-4 #7A5A8F`, `--chart-5 #8A8F8A` ; grille `--chart-grid #E4DFD4` ;
repère `--chart-reference #4F625B`.

## Typographie

- **Famille** : pile système — `ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto,
  "Helvetica Neue", Arial, sans-serif`. Aucune police distante : zéro requête réseau, zéro
  décalage de rendu.
- **Chiffres** : `font-variant-numeric: tabular-nums` dans les tableaux et les montants, pour
  que les colonnes s'alignent.
- **Échelle** (taille / interligne) :

| Token | Taille | Interligne | Usage |
|---|---|---|---|
| `--text-xs` | 0,75 rem (12 px) | 1,4 | légendes, unités |
| `--text-sm` | 0,875 rem (14 px) | 1,5 | textes secondaires |
| `--text-base` | 1 rem (16 px) | 1,6 | corps |
| `--text-lg` | 1,125 rem (18 px) | 1,5 | chapeaux |
| `--text-xl` | 1,375 rem (22 px) | 1,3 | titres de carte |
| `--text-2xl` | 1,75 rem (28 px) | 1,2 | titres de section |
| `--text-3xl` | 2,25 rem (36 px) | 1,15 | titre de page |
| `--text-4xl` | 3 rem (48 px) | 1,1 | accroche d'accueil (≥ 768 px) |

- Graisses : 400 corps, 600 titres et boutons. Longueur de ligne visée : 60–72 caractères.

## Espacements, arrondis, ombres

- Espacements (base 4 px) : `--space-1 4px`, `--space-2 8px`, `--space-3 12px`,
  `--space-4 16px`, `--space-6 24px`, `--space-8 32px`, `--space-12 48px`,
  `--space-16 64px`, `--space-24 96px`.
- Arrondis : `--radius-sm 6px` (champs, badges), `--radius-md 12px` (cartes),
  `--radius-pill 999px`.
- Ombres : `--shadow-sm 0 1px 2px rgba(21, 36, 32, 0.06)`,
  `--shadow-md 0 8px 24px rgba(21, 36, 32, 0.08)` — réservées aux cartes cliquables et aux
  menus ; le reste est bordé.

## Mise en page et breakpoints

Mobile d'abord, quatre paliers :

| Nom | Largeur | Conséquence |
|---|---|---|
| `sm` | ≥ 480 px | deux colonnes de cartes possibles |
| `md` | ≥ 768 px | navigation sur une ligne, accroche en 48 px |
| `lg` | ≥ 1024 px | conteneur à 1120 px, grille 3 colonnes |
| `xl` | ≥ 1280 px | marges latérales plus larges, pas de colonne supplémentaire |

Conteneur : `max-width: 1120px`, gouttières 16 px (mobile), 24 px (`md`), 32 px (`lg`).
Hauteur de cible tactile : 44 px minimum. `prefers-reduced-motion` respecté : aucune
transition si l'utilisateur le demande.

## Composants de base

- **En-tête** : fond `--color-surface`, bordure basse, nom du produit, navigation du flux
  (Accueil, Estimer, Explorer, Comparer), lien d'évitement « Aller au contenu ».
- **Bouton** : primaire (aplat `--color-primary`, texte `--color-on-primary`) et secondaire
  (contour `--color-border`, texte `--color-ink`). Hauteur 44 px, rayon `--radius-sm`,
  focus visible.
- **Carte** : surface, bordure, rayon `--radius-md`, padding `--space-6`, titre `--text-xl`.
  Une carte cliquable est un lien dont toute la surface est active, avec `--shadow-md` au survol.
- **Badge** : pastille `--radius-pill`, `--text-xs`, fond `--color-surface-muted` ou
  `--color-accent-soft` pour une mise en garde.
- **Champ** : libellé au-dessus, aide en `--text-sm` `--color-ink-muted`, erreur en
  `--color-danger` avec le champ marqué `aria-invalid`.
- **Encart** : fond `--color-primary-soft` (information) ou `--color-accent-soft` (limite,
  avertissement), texte respectif `--color-ink` / `--color-accent-ink`.
- **Tableau de statistiques** : en-tête `--text-sm` `--color-ink-muted`, lignes séparées par
  `--color-border`, chiffres alignés à droite et tabulaires, colonne « Observations » toujours
  présente.
- **État vide** : phrase explicite (« Aucune observation pour ce filtre ») + action de retour,
  jamais une statistique inventée.
- **Pied de page** : rappel que les prix sont **demandés** dans les annonces, lien vers les
  limites de l'estimation.

## Style des graphiques

Pas de bibliothèque de graphiques dans le socle : le style est figé pour les écrans 09a.3.

- Une seule série par défaut (`--chart-1`) ; les séries multiples suivent l'ordre de la palette.
- Grille horizontale seule, 1 px `--chart-grid`, jamais de fond coloré.
- Axes : libellés `--text-xs` `--color-ink-muted`, pas de bord supérieur ni de bord droit.
- Étiquettes directes de valeur ; pas de légende quand une seule série.
- Pas de 3D, pas de dégradé, pas d'animation d'entrée.
- Chaque graphique porte sa **taille d'échantillon** (`N = …`) et son unité (FCFA/mois).

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
Prix médian    150 000 FCFA            (seulement si N ≥ seuil de publication)
Prix médian    Non publiée (< 30 obs.)  (sous le seuil : N et moyenne restent affichés)
Fourchette     130 000 – 190 000 FCFA
Observations   248
```

Dans un tableau d'exploration, la colonne **Observations** est toujours présente ;
une médiane absente est écrite en `--color-accent-ink`, jamais remplacée par une
moyenne ou une valeur approchée. Les biais de la donnée (prix bornés,
republications, quartiers non reconnus) sont listés avec leur volume et leur part,
au niveau agrégé de la ville, sans dépasser quelques lignes.

Séparateur de milliers : espace insécable étroite (`Intl.NumberFormat("fr-FR")`) ; unité
`FCFA / mois` écrite en `--text-sm` `--color-ink-muted` à côté du montant.

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

## Public vs administration (découpage 09a / 09b)

Le parcours ci-dessus est **public** (Phase **09a**). L'interface d'**administration**
(Phase **09b**, fondée sur `feature-specs/13-backoffice-foundations.md` et
`14-backoffice-reporting-observability.md`) suit d'autres règles : densité d'information
acceptée, actions sensibles confirmées et journalisées, aucun écran qui simule une capacité
absente du backend. Le thème est **commun** ; l'administration pourra ajouter une densité
(espacements réduits) mais pas une autre palette.

## Décisions et limites (2026-10-20)

- Thème clair uniquement : le mode sombre est hors MVP et demanderait une palette complète.
- Pas de bibliothèque de composants ni de graphiques dans 09a.1 : les tokens suffisent, une
  dépendance lourde serait ajoutée sans besoin.
- Polices système : la typographie est figée sans téléchargement, au prix d'une apparence
  légèrement différente selon l'OS — assumé.
- Les tokens sont la seule source de vérité ; le thème de l'administration réutilise les
  mêmes variables.
