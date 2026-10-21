# Phase 9a — Frontend public : socle Next.js et thème figé (09a.1)

Objectif (spec : `context/feature-specs/09-frontend.md`) : rendre l'estimation et le marché
compréhensibles par des non-techniciens. La phase 9 est livrée en **deux temps** — **09a
estimation publique** puis **09b administration** (plan §10, lot 5) — et 09a se découpe en
quatre tickets (#55 à #58).

Ce document couvre les **trois premiers incréments** : **09a.1 (ticket #55)** — figer le
thème, poser le socle Next.js, la mise en page et le client d'API —, **09a.2 (ticket
#56)** — l'écran d'estimation, branché sur l'API réelle — et **09a.3 (ticket #57)** —
l'exploration du marché. La comparaison arrive ensuite (09a.4).

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
/estimer    écran 09a.2 (livré) : formulaire 5 champs → estimation + fourchette + contexte
/explorer   écran 09a.3 (livré) : filtres URL, synthèse par quartier, détail type × chambres
/comparer   écran 09a.4 — idem
*           404 au thème, avec retour à l'accueil
```

### Écran d'estimation (09a.2, ticket #56)

- **Cinq champs exactement** : ville (Douala / Yaoundé), quartier (liste des marts
  via `GET /api/v1/market/neighborhoods?city=…`, saisie libre conservée), type
  (`apartment`/`studio`/`room`/`house`), chambres et salles de bain (0–10).
  La superficie, le mobilier ou le parking ne sont pas demandés : le modèle ne
  les prend pas en compte (décision 6).
- **Résultat** : loyer estimé, fourchette 5 % / 95 %, version du modèle épinglé
  (`POST /api/v1/predictions`), contexte de marché du groupe
  (`GET /api/v1/market/prices`) : N obligatoire, moyenne, médiane si et seulement
  si elle est publiée (sinon « Non publiée (moins de <N_seuil> observations) »),
  étendue p10–p90.
- **Erreurs reprises comme des phrases** : quartier jamais observé → 404
  expliqué (le modèle ne l'a jamais vu, vérifiez la liste) ; 422 affiché
  champ par champ depuis le détail de l'enveloppe d'erreur ; réseau/délai :
  message stable, aucune trace technique.
- **CORS opt-in** : `CORS_ALLOWED_ORIGINS=http://localhost:3000` sur l'API
  (middleware ajouté côté backend, défaut strict : aucune en-tête CORS sans
  déclaration, testé par 2 tests dédiés).
- Un écran non livré **le dit** (« Écran à venir », ticket concerné) au lieu
  d'afficher un formulaire inerte ou un chiffre inventé : aucune capacité n'est
  simulée.

### Écran d'exploration (09a.3, ticket #57)

- **Filtres dans l'URL** : `?city=…&neighborhood=…&property_type=…&bedrooms=…`.
  Chaque combinaison est partageable et vérifiable dans un navigateur réel
  (quartier publié, groupe sous le seuil, filtre vide). Les paramètres hors
  contrat (ville inconnue, type inconnu, chambres hors 0–10, quartier
  démesuré) sont ignorés — l'écran ne relaie jamais une requête invalide.
- **Deux grains, jamais mélangés** : `/market/neighborhoods` fournit la synthèse
  par quartier (N, moyenne, minimum–maximum, nombre de groupes) ; le détail
  quartier × type × chambres vient de `/market/prices` (N, moyenne, médiane si
  publiée, p10–p90). Les médianes ne sont **jamais agrégées** : la table par
  quartier l'explique et renvoie au détail.
- **Seuil de publication** : la médiane n'apparaît que si `median_published` est
  vrai **et** N ≥ `min_publish_n`. Le seuil est revérifié côté écran
  (`lib/explorer.ts::medianDisplay`), pour qu'une réponse incohérente ne rende
  pas visible une médiane non publiable. Sinon : « Non publiée (< 30 obs.) »,
  avec le rappel que N et moyenne restent affichés.
- **Limites de la donnée** : au niveau de la ville, seuls les biais non nuls
  sont listés avec leur volume et leur part (prix « à partir de »,
  republications, quartiers non reconnus), puis la période observée et le seuil
  de publication. Les prix **demandés** sont rappelés sur l'écran.
- **États** : filtre sans résultat → phrase explicite (« Aucune observation
  collectée pour … ») et bouton de retrait des filtres, aucun chiffre approché ;
  échec de l'API → table vidée et message stable, jamais de valeurs périmées.
- **Ce que l'écran exclut** (rappelé sous la table) : classement de quartiers,
  recherche par budget, cartographie fine, statistiques calculées côté
  frontend.

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
| `npm test` | **49 tests réussis** (client API, formatage, helpers marché et exploration, erreurs d'estimation) |
| `npm run build` | **succès** — routes prérendues : `/`, `/estimer`, `/explorer`, `/comparer`, `/_not-found` |
| `npm run lint` / `npm run typecheck` | 0 erreur (ESLint 9 + `tsc --noEmit` strict) |
| serveur réel (`next start`, port 3000) | `/` 200, `/estimer` 200, `/explorer` 200, `/comparer` 200, `/inconnu` **404** |
### Vérifications bout en bout de 09a.2 (2026-10-20)

| Contrôle | Résultat |
|---|---|
| API réelle (`uvicorn` + CORS opt-in) | preflight admis 200 pour `http://localhost:3000`, 400 par défaut pour toute autre origine |
| estimation réelle | `Makepe × apartment × 2ch × 1 sdb` → **78 299 FCFA** (bornes 60 000–100 000, `rent-model-v4`) ; groupe de marché **N = 632**, moyenne 98 498, médiane 90 000 publiée |
| hydration réelle (Chrome headless, 12 s de budget virtuel) | le hint du quartier passe à « **88 quartiers observés dans les données pour Douala** » : le fetch client part bien du navigateur vers les marts, le composant hydrate |
| `/estimer` SSR | formulaire servi dans le HTML initial (aucun contenu client-only) ; `NEXT_PUBLIC_API_BASE_URL` inlineé dans le bundle |
| captures responsive | 1280×1600 et 390×1600 de `/estimer` |
| suites locales | frontend lint 0, typecheck 0, 28 tests ; Python ruff 0, 359 unitaires |
| thème centralisé | CSS servi (7,0 Ko) : tokens `--color-primary`, `--color-bg`, `--text-4xl`, media queries 1024 px, `prefers-reduced-motion` présents |
| accessibilité de base | lien d'évitement, `nav aria-label`, `aria-hidden` sur les décorations, cibles de 44 px, contrastes documentés |
| rendu responsive | captures Chrome headless **1280×1600** et **390×1600** de l'accueil (vérification visuelle des breakpoints) |
| aucune donnée simulée | `/estimer` affiche « Écran à venir » et le ticket 09a.2 ; aucun chiffre dans les pages |
| CI | job **Frontend** ajouté (Node 22, `npm ci`, lint, typecheck, tests, build) — exécuté et vert depuis la PR #88 |

### Vérifications bout en bout de 09a.3 (2026-10-21)

| Contrôle | Résultat |
|---|---|
| cohérence écran ↔ API ↔ marts | Douala / Makepe / appartement / 2 ch. : écran, API et `mart_neighborhood_prices` donnent **N = 632, moyenne 98 498, médiane 90 000, p10–p90 70 000–150 000** |
| zone sous le seuil | Douala / Bonapriso / appartement / 1 ch. : **N = 25**, moyenne 269 000, médiane « Non publiée (< 30 obs.) », p10–p90 150 000–500 000 — aucune médiane affichée |
| filtre sans résultat | Yaoundé / Bastos / maison / 9 ch. : « Aucune observation collectée pour … », aucun chiffre de marché approché |
| paramètres forgés | `?city=Conakry&property_type=villa&bedrooms=99` → repli sur Douala (88 quartiers, 2 811 observations), aucune valeur hors contrat envoyée |
| filtres interactifs (CDP, Chrome réel) | ville Douala → Yaoundé : 89 → 54 options et 88 → 53 lignes ; quartier Bastos : 6 groupes, médiane non publiée ; « Retirer les filtres » → retour aux 53 quartiers |
| limites agrégées | Douala : prix bornés 2 508 obs. (89 %), republications 1 984 obs. (71 %), quartiers non reconnus 64 obs. (2 %), période du 9 octobre 2026 |
| responsive | captures 1280×1600 et 390×1600 ; à 390 et 500 px la page ne déborde pas, la table (1 156 px) défile dans son conteneur (451 px) |

Incident de build corrigé à la cause : un premier `next build` s'est terminé en
`Bus error` après une installation `npm` interrompue (deux installations concurrentes avaient
laissé `node_modules` incohérent). `node_modules` et `package-lock.json` supprimés puis
réinstallés proprement ; build vert, sans contournement.

## Lancer et rejouer

```bash
# API publique (depuis la racine) — l'origine du frontend doit y être déclarée
CORS_ALLOWED_ORIGINS=http://localhost:3000 uvicorn backend.api.app:app --port 8000

# Frontend
cd frontend
cp .env.example .env.local        # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm install
npm run dev                       # http://localhost:3000
npm run lint && npm run typecheck && npm test && npm run build
```

## Limites connues

- **Écran d'estimation non piloté par un test automatisé** : la soumission complète du
  formulaire est vérifiée par les endpoints réels (`curl`), l'hydration réelle en Chrome
  headless (hint des quartiers mis à jour après fetch) et les tests backend, sans moteur de
  test de composants (aucune dépendance installée pour cela à ce stade).
- **Écran 09a.4 non livré** : `/comparer` annonce encore son ticket.
- **Filtres d'exploration pilotés par URL** : le rendu de chaque état (quartier
  publié, groupe sous le seuil, filtre vide, paramètres forgés) est vérifié
  après hydration ; le passage d'un filtre à l'autre est vérifié par CDP
  (changement de ville, choix d'un quartier, retrait des filtres) — sans moteur
  de test de composants installé.
- **Tableaux étroits** : sur mobile, les tableaux défilent horizontalement dans
  leur conteneur ; la page elle-même ne déborde pas (vérifié à 390 et 500 px).
- **Variables `NEXT_PUBLIC_*` inlinées au build** : changer l'URL de l'API impose de
  reconstruire le frontend.
- **Thème clair uniquement** : le mode sombre demanderait une palette complète et n'est pas au
  MVP.
- **Pas de bibliothèque de composants ni de graphiques** : ajoutées seulement si un écran
  l'exige ; le style des graphiques est déjà figé pour 09a.3.
- **Tests frontend volontairement limités** : la logique pure (client API, formatage,
  marché, erreurs) est testée unitairement ; les écrans sont vérifiés par le build, le
  rendu réel et des captures, sans moteur de test de composants.
- **Pas de connexion à l'API depuis le socle** : les captures et le rendu ont été faits sans
  API démarrée, ce qui est l'état attendu tant qu'aucun écran ne consomme de données.

## Incréments suivants

| Ticket | Contenu |
|---|---|
| #58 | 09a.4 — écran comparer (prix demandé, estimation, référence locale, écarts signés) |
| #68/#69 | 09b — interface d'administration, après les fondations 13.1 à 13.5 |
