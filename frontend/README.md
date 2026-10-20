# Frontend — CamRent (Phase 9a)

Application publique Next.js + TypeScript. La Phase 9a : thème figé, mise en
page, navigation du parcours et client de l'API publique (ticket 09a.1),
puis le **formulaire d'estimation** (ticket 09a.2) : cinq champs, fourchette
calibrée et contexte de marché du quartier. L'exploration (09a.3) et la
comparaison (09a.4) suivent.

## Démarrage

```bash
cd frontend
cp .env.example .env.local      # renseigner NEXT_PUBLIC_API_BASE_URL
npm install
npm run dev                     # http://localhost:3000
```

L'API publique doit tourner à côté, **avec l'origine du frontend déclarée en CORS**
(le navigateur refuse les appels cross-origin sinon) :

```bash
# depuis la racine du dépôt
CORS_ALLOWED_ORIGINS=http://localhost:3000 uvicorn backend.api.app:app --port 8000
```

Sans cette variable, l'API répond but les écrans du navigateur restent sans donnée
(la liste des quartiers indique alors qu'elle est indisponible) — aucune erreur
technique n'est exposée.

## Commandes

| Commande | Rôle |
|---|---|
| `npm run dev` | serveur de développement |
| `npm run build` | build de production |
| `npm run start` | sert le build (`next start`) |
| `npm run lint` | ESLint (règles Next.js + TypeScript) |
| `npm run typecheck` | `next typegen` puis `tsc --noEmit` (types de routes générés avant le contrôle) |
| `npm test` | tests unitaires Vitest (`lib/*.test.ts`) |

## Configuration

Une seule variable, **publique** et non secrète :

| Variable | Rôle |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | base de l'API publique, ex. `http://localhost:8000` |

Elle est inlinée **au build** par Next.js : une valeur absente ou invalide ne
casse pas le démarrage, mais tout appel API lève une `ApiError` de type `config`
qui nomme la variable. Aucune URL d'API n'est écrite en dur.

## Structure

```
frontend/
├── app/                 App Router : layout, accueil, étapes du parcours, 404
│   ├── globals.css      thème figé (tokens) — source unique des couleurs
│   ├── estimer/         écran 09a.2 : formulaire + résultat + contexte de marché
│   ├── explorer/        écran 09a.3 (à venir, explicite)
│   └── comparer/        écran 09a.4 (à venir, explicite)
├── components/          en-tête, pied de page, carte d'étape, formulaire d'estimation
├── lib/
│   ├── api.ts           client HTTP de l'API publique (erreurs typées)
│   ├── api-types.ts     types du contrat 08a consommés à l'écran
│   ├── estimation-errors.ts  traduction des échecs d'estimation en phrases du produit
│   ├── format.ts        montants FCFA (`Intl.NumberFormat("fr-FR")`)
│   ├── market.ts        URLs, options de quartier, groupe de marché
│   └── *.test.ts        tests Vitest des modules purs
└── vitest.config.mts
```

## Thème

Le thème est **figé** dans `context/ui-context.md` (palette, typographie,
espacements, arrondis, breakpoints, style des graphiques) et implémenté une
seule fois dans `app/globals.css` (`:root`). Une couleur, une taille ou un
espacement écrit en dur dans un composant est un défaut de revue.

## Limites assumées

- L'écran d'estimation n'est **pas** une valeur officielle : le montant est
  toujours accompagné de la fourchette et du rappel « prix demandés ».
- Un quartier absent des données est refusé en 404, jamais « estimé à l'aveugle ».
- Le formulaire liste les quartiers réellement suivis (optionnel : la saisie
  libre reste possible) ; un groupe de marché sans observation est annoncé
  comme tel, jamais remplacé par un chiffre approchant.
- `/explorer` et `/comparer` annoncent encore leurs tickets (09a.3 / 09a.4).
- Thème clair uniquement (le mode sombre est hors MVP).
- Aucune bibliothèque de composants ni de graphiques : les tokens et le CSS
  suffisent à ce stade ; une dépendance sera ajoutée seulement si un écran
  l'exige réellement.
- La logique pure (erreurs, formatage, marché) est testée par Vitest ; le
  formulaire lui-même est vérifié par `next build`, le rendu réel et une
  session Chrome headless contre l'API réel (uvicorn + CORS).
