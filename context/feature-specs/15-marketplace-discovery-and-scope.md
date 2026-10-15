# Phase 15 — Marketplace : découverte et cadrage

Lire `context/product/camrent-product-realignment.md` (§3.4, §4.2) et
`context/architecture-context.md` (§Sous-systèmes fonctionnels, D) avant de commencer.

Objectif : la marketplace est **conservée dans le périmètre du produit** mais
**conditionnée** (décision 1) — cette spec est une **phase de décision** : cadrer et
mesurer l'intérêt avant toute implémentation.

> **Statut (2026-10-15)** : spec de cadrage créée après validation de la décision 1
> (« conservée, mais structurée »). **Aucune implémentation n'est engagée** ; la suite
> dépend d'une décision explicite du porteur du projet.

## Implementation (si l'intérêt est démontré et la décision prise)

1. **Cadrage d'abord** — définir comptes annonceurs, annonce, modération et contact ;
   mesurer l'intérêt (demandes reçues, interviews, usage) avant de coder.
2. **Recherche et filtres** d'annonces ; pages détaillées de logement.
3. **Comptes annonceurs** et gestion de leurs annonces.
4. **Photos, disponibilité déclarée** et historique des changements.
5. **Demandes de contact ou de visite.**
6. **Modération**, signalement, détection de doublons et d'annonces obsolètes.

## Invariant fondateur

Une **annonce publiée par un utilisateur** et une **observation importée d'une source
externe** restent des objets **distincts** (provenance, droits, cycle de vie), même si
un rapprochement est éventuellement proposé. Ne jamais nourrir le modèle ML avec des
annonces de marketplace sans la même traçabilité et les mêmes validations que
n'importe quelle source.

## Dependencies

- Services communs (E) : comptes, authentification, rôles, audit.
- Phases 08 (API) et 09 (interface) pour les parcours publics.

## Scope Limits

- À reporter : paiements intégrés, réservation, contrats numériques, gestion locative
  complète, commissions complexes, expansion multi-pays immédiate.
- Aucune implémentation avant cadrage validé et décision explicite.
- Le MVP vise Yaoundé et Douala ; **Conakry reste un chantier séparé** (décision 10).

## Check When Done

- Un document de cadrage (comptes, annonce, modération, contact, mesure d'intérêt) est
  validé par le porteur du projet.
- La décision explicite « bâtir / reporter » est prise et consignée dans
  `context/progress-tracker.md`.
- Si la décision est « bâtir » : une annonce publiée reste traçable comme objet
  distinct d'une observation importée, et aucun entraînement n'utilise d'annonces sans
  validation équivalente à celle d'une source.
