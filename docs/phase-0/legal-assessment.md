# Évaluation légale et d'usage des sources

**Phase :** 0 — Validation du problème
**Date :** 8 octobre 2026

Règle projet (AGENTS.md) : **aucune collecte automatisée sans vérification préalable des CGU, de
`robots.txt` et des droits sur les données.**

## Vérifications effectuées

| Source | `robots.txt` | Vérifié le | Constat |
|---|---|---|---|
| **Koutchoumi** | `https://www.koutchoumi.com/robots.txt` | 2026-10-08 | Directives **commentées** (`#User-agent: *` / `#Disallow: `) → aucune restriction explicite |
| **Geloka** | `https://www.geloka.com/robots.txt` | 2026-10-08 | `User-agent: * / Allow: /` → exploration autorisée |

## Statut par source

| Source | Type | Droits / licence | Statut | Décision |
|---|---|---|---|---|
| **Geloka** | Baromètre agrégé | CGU non lues | `robots.txt` permissif | Utilisable **sous réserve** de vérifier les CGU (citation requise selon le Data Discovery Report) |
| **Koutchoumi** | Portail d'annonces | CGU non lues | Pas d'interdiction `robots.txt` explicite | **Prudence** : lire les CGU avant toute collecte |
| **Jumia House** | Portail d'annonces | Non vérifié | Incertain | **Ne pas collecter** tant que non vérifié |
| **Lewambi** | Portail d'annonces | Non vérifié | Incertain | **Ne pas collecter** |
| **Facebook (Marketplace / groupes)** | Annonces utilisateurs | CGU Facebook | Interdit hors API officielle | **Ne pas collecter** |
| **MINHAB / INS** | Données officielles | Accès formel | Accès sur demande | **Demande formelle** à initier |
| **GitHub `deegeorgie`** | Dataset public tiers | **Aucune licence déclarée** (`license: null`) | Réutilisation non autorisée par défaut | **Usage local pour analyse uniquement**, non redistribué |

## Décision sur l'échantillon GitHub

Le dépôt `deegeorgie/Predicting-house-prices-in-Cameroon` est public mais **sans licence**. En droit,
l'absence de licence signifie « tous droits réservés » : sa redistribution n'est pas autorisée.

Conséquences appliquées :

- les fichiers `koutchoumi1.csv` et `jumia.csv` sont conservés **localement** dans `data/samples/`
  mais **exclus du versionnement** (`.gitignore`) ;
- seuls les **résultats dérivés** (rapports, statistiques) et le **script** sont publiés ;
- ce dataset ne doit pas être présenté comme une source pérenne de production.

## Données personnelles

Les deux échantillons analysés ne contiennent **aucune donnée personnelle** (pas de téléphone,
e-mail ni nom). Les futures collectes devront exclure explicitement ces champs.

## À faire avant toute collecte

1. Lire et archiver les CGU de la source.
2. Revérifier `robots.txt` au moment de la collecte.
3. Limiter le débit de requêtes (pas de charge excessive).
4. Documenter la source, la date et la méthode de chaque lot collecté.

## Mise à jour Phase 1 (9 octobre 2026)

Vérification complémentaire effectuée au démarrage de la **Phase 1** :

- **Geloka** — CGU lues (`/fr/terms-and-conditions`, maj 2025-06-22). Elles
  restreignent la copie/redistribution et limitent l'usage aux besoins
  personnels et non commerciaux : plus restrictives que la mention « citation +
  lien » du baromètre. Décision : baromètre utilisé comme **repère agrégé** avec
  citation, sans redistribution, collecte soumise à confirmation.
- **Koutchoumi** — **aucune CGU/ToS publiée** (toutes les URL candidates renvoient
  une page générique) ; `robots.txt` sans règle active. Décision : collecte en
  usage recherche, prudente, sans données personnelles, soumise à confirmation.

Détail : `docs/phase-1/legal-review.md`. Aucune source n'est classée `verified`
à ce stade : toutes les collectes réseaux exigent `--confirm-legal`.
