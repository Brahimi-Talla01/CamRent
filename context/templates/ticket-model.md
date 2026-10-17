# Modèle de ticket — CamRent

Ce modèle est réutilisable pour tous les tickets (nouveaux ou révisés). Chaque ticket doit être
cohérent avec les documents de référence lus :

- règles de travail : `AGENTS.md`
- workflow, périmètre, lots : `context/ai-workflow-rules.md`
- produit, utilisateurs, MVP : `context/project-overview.md`
- architecture, sous-systèmes, invariants : `context/architecture-context.md`
- conventions de code : `context/code-standards.md`
- **état réel d'avancement** : `context/progress-tracker.md`
- recadrage produit : `context/product/camrent-product-realignment.md`
- audit + 10 décisions + ordre des lots : `context/plans/camrent-audit-and-realignment-plan.md`
- une spec par phase (00 → 15) : `context/feature-specs/`

---

## Titre

<préfixe de phase + résultat concret d'**un seul** module>

Un ticket couvre **un module**, pas une phase entière : si le périmètre commence à ressembler à
« API publique : prédiction, marché, comparaison », il faut le découper (3 à 5 tickets par phase,
voir `context/ai-workflow-rules.md` §Suivi des tickets).

Exemples :
- `08a.2 — Endpoint de prédiction (modèle épinglé, fourchette, model_version)`
- `13.4 — Jobs ML asynchrones`

## Contexte et objectif

<Ce que le ticket apporte, et pourquoi il existe maintenant.>

## Périmètre

### Inclus

<liste concise>

### Exclus

<liste concise — notamment ce qu'il ne doit pas faire, même implicitement>

## Dépendances

<issues, phases, composants, données, décisions préalables.>

## Tâches

- [ ] <tâche 1>
- [ ] <tâche 2>
- [ ] <tâche 3>

## Critères d'acceptation

<conditions précises, objectives, vérifiables. Pas de formulation vague comme « implémenter l'API».>

## Tests et validation

<tests attendus et preuves de réussite.>

## Documentation

<fichiers à mettre à jour, le cas échéant.>

## Définition de terminé (DoD)

<code, tests, documentation et contrôles requis pour clôturer.>

## Labels

<labels existants uniquement>

## Milestone

<sous-système uniquement : `Data Platform`, `Estimation`, `Back-office` ou `Marketplace` — voir
`context/ai-workflow-rules.md` §Suivi des tickets. Les milestones de phase ne sont plus utilisés :
la phase se porte par le préfixe du titre (`08a.2`, `13.4`).>
