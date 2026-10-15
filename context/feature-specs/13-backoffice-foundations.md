# Phase 13 — Back-office : fondations

Lire `context/architecture-context.md` (§Sous-systèmes fonctionnels, §Gouvernance du
registre de modèles) et `context/product/camrent-product-realignment.md` (§3.2) avant
de commencer.

Objectif : donner à l'équipe autorisée des capacités **gouvernées et interrogeables**
pour superviser la Data Platform, les jobs ML et le registre des modèles — les
fondations sur lesquelles s'appuiera l'interface d'administration (Phase 9b).

> **Statut (2026-10-15)** : spec de cadrage créée après l'audit et le recadrage.
> **Implémentation après les phases 08 et 09** (décision 7) : le back-office se
> construit avec les fonctions qu'il pilote, et une page ne doit jamais simuler une
> capacité absente du backend. Les capacités gouvernées qu'il supervise (registre
> approuvé, qualité en base, CI de données) sont livrées par les lots B et C du plan
> de réalignement.

## Implementation

1. **Accès et rôles** — API interne distincte de l'API publique (découpage 08b),
   autorisation minimale par action, premier rôle : `admin` ; toute action sensible
   est journalisée (qui, quoi, quand).
2. **Sources** — registre des sources (lecture depuis `ingestion/config.py`),
   activation/désactivation, déclenchement manuel d'une collecte, historique des
   exécutions et erreurs (métadonnées de lots, lot B).
3. **Datasets** — exploration paginée du Silver et des marts, profilage (volumes,
   colonnes, valeurs manquantes), suivi des versions ; imports validés uniquement.
4. **Qualité** — consultation de la table de qualité (quarantaine, motifs de rejet
   agrégés, drapeaux) produite par le lot B ; règles de validation versionnées (tests
   dbt) et leurs résultats.
5. **Jobs ML** — lancement **asynchrone** d'un entraînement sur un dataset versionné,
   logs, statut, métriques ; aucun entraînement synchrone dans une requête HTTP.
6. **Registre des modèles** — versions, provenance (run, dataset, code), statut
   d'approbation, version servie épinglée ; toute promotion suit la voie approuvée de
   la Phase 7, sans contournement possible par l'interface.
7. **Utilisateurs et permissions** — comptes internes, rôles, autorisations minimales.

## Dependencies

- Phases 08 (API interne 08b) et 09 (interface) ; lots B (qualité en base) et
  C (CI de données) du plan de réalignement.
- Services communs (E) : authentification, rôles, audit, tâches asynchrones.

## Scope Limits

- Aucune page qui simule une capacité absente du backend.
- Pas d'exécution de scripts arbitraires depuis l'interface.
- Pas de rôles complexes au départ : `admin` d'abord, extensions seulement si besoin
  mesuré.
- Ne pas dupliquer les garde-fous du registre : l'approbation de promotion reste
  nominative et tracée, quel que soit le point d'entrée.

## Check When Done

- Un compte `admin` authentifié peut consulter sources, exécutions, qualité, jobs et
  registre via l'API interne.
- Chaque action sensible est journalisée.
- La promotion d'un modèle via le back-office exige la même approbation nominative
  qu'en CLI.
- Aucune capacité affichée sans exécution réelle derrière.
