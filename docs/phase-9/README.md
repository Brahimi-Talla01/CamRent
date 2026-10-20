# Phase 9a — Frontend public : socle Next.js et thème figé (09a.1)

Objectif (spec : `context/feature-specs/09-frontend.md`) : rendre l'estimation et le marché
compréhensibles par des non-techniciens. La phase 9 est livrée en **deux temps** — **09a
estimation publique** puis **09b administration** (plan §10, lot 5) — et 09a se découpe en
quatre tickets (#55 à #58).

Ce document couvre le **premier incrément, 09a.1 (ticket #55)** : figer le thème, poser le
socle Next.js, la mise en page et le client d'API. Les écrans métier arrivent ensuite.

## Thème figé (écrit avant le code)

`context/ui-context.md` n'est plus provisoire : il porte la palette, la typographie, l'échelle
d'espacement, les arrondis, les breakpoints, les composants de base et le style des graphiques,
datés du 2026-10-20.

| Domaine | Décision |
|---|---|
| Couleurs | fond sable `#F7F5F0`, texte `#152420`, primaire vert profond `#0E5B4A`, accent ocre `#B26A00` |
| Contrastes | texte principal ≈ 15:1, secondaire ≈ 6:1, texte sur primaire ≈ 8:1 — au-delà de WCAG AA |
| Typographie | pile **système** (aucune police téléchargée), échelle de 12 à 48 px, chiffres tabulaires |
| Espacement | base 4 px (4 → 96 px) |
| Arrondis | 6 px (champs), 12 px (cartes), pastille |
| Breakpoints | 480 / 768 / 1024 / 1280 px, mobile d'abord |
| Graphiques | séries ordonnées, grille horizontale seule, pas de 3D ni de dégradé, `N` obligatoire |
| Mode sombre | hors MVP (documenté comme limite) |

Les tokens sont définis **une seule fois** dans `frontend/app/globals.css` (`:root`) ; les
composants les consomment via `var(--…)`. Une couleur littérale dans un composant est un défaut
de revue.

## Socle technique

| Élément | Choix |
|---|---|
| Framework | Next.js 16 (App Router), React 19, TypeScript strict (`noUncheckedIndexedAccess`) |
| Rendu | composants **serveur** par défaut ; aucun `"use client"` dans ce socle (aucun état client nécessaire) |
| Styles | CSS global + tokens, sans bibliothèque de composants |
| Lint | ESLint 9 + `eslint-config-next` (règles Next.js et TypeScript, flat config) |
| Tests | Vitest 5, environnement `node`, uniquement les modules purs (`lib/api.ts`) |
| Build | `next build` (statique : les cinq routes sont prérendues) |

## Pages livrées

```
/           accueil : parcours, ce que l'outil fait / ne fait pas, statut des écrans
/estimer    écran 09a.2 — explicitement « à venir », aucune donnée simulée
/explorer   écran 09a.3 — idem
/comparer   écran 09a.4 — idem
*           404 au thème, avec retour à l'accueil
```

Un écran non livré **le dit** (« Écran à venir », ticket concerné) au lieu d'afficher un
formulaire inerte ou un chiffre inventé : aucune capacité n'est simulée.

## Client de l'API publique

`frontend/lib/api.ts` :

- base lue dans `NEXT_PUBLIC_API_BASE_URL` (inlinée au build), **aucune URL en dur** ; variable
  absente ou invalide → `ApiError` de type `config` qui nomme la variable ;
- erreurs classées : `config`, `network`, `timeout` (8 s par défaut), `http`, `invalid` ;
- l'enveloppe d'erreur de l'API (`{"error": {code, message, details}}`) est conservée : code et
  détail par champ sont disponibles pour l'interface ;
- une réponse HTML ou illisible ne fuite jamais vers l'écran : message générique ;
- `apiGet` / `apiPost`, `Accept: application/json`, `Content-Type` posé seulement avec un corps.

## Vérifications (2026-10-20)

| Contrôle | Résultat |
|---|---|
| `npm run lint` | 0 erreur (ESLint 9, règles Next.js + TypeScript) |
| `npm run typecheck` | 0 erreur (`tsc --noEmit`, strict) |
| `npm test` | **11 tests réussis** (configuration, URL, en-têtes, réseau, délai, 422, 500 non JSON, 200 illisible) |
| `npm run build` | **succès** — routes prérendues : `/`, `/estimer`, `/explorer`, `/comparer`, `/_not-found` |
| serveur réel (`next start`, port 3000) | `/` 200 (16,7 Ko), `/estimer` 200, `/explorer` 200, `/comparer` 200, `/inconnu` **404** |
| thème centralisé | CSS servi (7,0 Ko) : tokens `--color-primary`, `--color-bg`, `--text-4xl`, media queries 1024 px, `prefers-reduced-motion` présents |
| accessibilité de base | lien d'évitement, `nav aria-label`, `aria-hidden` sur les décorations, cibles de 44 px, contrastes documentés |
| rendu responsive | captures Chrome headless **1280×1600** et **390×1600** de l'accueil (vérification visuelle des breakpoints) |
| aucune donnée simulée | `/estimer` affiche « Écran à venir » et le ticket 09a.2 ; aucun chiffre dans les pages |
| CI | job **Frontend** ajouté (Node 22, `npm ci`, lint, typecheck, tests, build) |

Incident de build corrigé à la cause : un premier `next build` s'est terminé en
`Bus error` après une installation `npm` interrompue (deux installations concurrentes avaient
laissé `node_modules` incohérent). `node_modules` et `package-lock.json` supprimés puis
réinstallés proprement ; build vert, sans contournement.

## Lancer et rejouer

```bash
# API publique (depuis la racine)
uvicorn backend.api.app:app --port 8000

# Frontend
cd frontend
cp .env.example .env.local        # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm install
npm run dev                       # http://localhost:3000
npm run lint && npm run typecheck && npm test && npm run build
```

## Limites connues

- **Écrans métier non livrés** : `/estimer`, `/explorer` et `/comparer` annoncent leur ticket
  (09a.2 à 09a.4). Le client API est prêt mais aucun écran ne l'appelle encore.
- **Variables `NEXT_PUBLIC_*` inlinées au build** : changer l'URL de l'API impose de
  reconstruire le frontend.
- **Thème clair uniquement** : le mode sombre demanderait une palette complète et n'est pas au
  MVP.
- **Pas de bibliothèque de composants ni de graphiques** : ajoutées seulement si un écran
  l'exige ; le style des graphiques est déjà figé pour 09a.3.
- **Tests frontend volontairement limités** : le client API est testé unitairement ; les écrans
  sont vérifiés par le build, le rendu réel et des captures, sans moteur de test de composants
  (dépendance non justifiée à ce stade).
- **Pas de connexion à l'API depuis le socle** : les captures et le rendu ont été faits sans
  API démarrée, ce qui est l'état attendu tant qu'aucun écran ne consomme de données.

## Incréments suivants

| Ticket | Contenu |
|---|---|
| #56 | 09a.2 — écran estimation → résultat (formulaire 5 champs, fourchette, `N`, limites) |
| #57 | 09a.3 — écran explorer le marché (quartiers, types, seuil de publication) |
| #58 | 09a.4 — écran comparer (prix demandé, estimation, référence locale, écarts signés) |
| #68/#69 | 09b — interface d'administration, après les fondations 13.1 à 13.5 |
