# Phase 1 — Revue légale et d'usage des sources

**Phase :** 1 — Data ingestion
**Date de vérification :** 9 octobre 2026

Règle projet (AGENTS.md) : **aucune collecte automatisée sans vérification
préalable des CGU, de `robots.txt` et des droits sur les données.** Complète
`docs/phase-0/legal-assessment.md`.

## Vérifications effectuées

| Source | `robots.txt` | CGU / ToS | Statut retenu |
|---|---|---|---|
| **Geloka** | `Allow: /` (vérifié 2026-10-08) | **lues** le 2026-10-09 (`/fr/terms-and-conditions`, maj 2025-06-22) | `uncertain` — collecte possible sous conditions |
| **Koutchoumi** | directives **commentées** → aucune règle active | **aucune CGU/ToS publiée** (toutes les URL candidates renvoient une page générique) | `uncertain` — collecte prudente |
| **MINFI Open Data** | n/a (portail) | portail open data officiel | `uncertain` — document brut |
| **INS Cameroun** | n/a | accès détaillé **sur demande** | `uncertain` — document brut |
| **`deegeorgie`** (local) | n/a | **aucune licence** déclarée | `local` — usage local, non redistribué |

## Geloka — points saillants des CGU

- **§9 Propriété intellectuelle** : le contenu des Services appartient à Geloka ;
  la licence accordée est « **limitée, non exclusive, non transférable et
  révocable** […] uniquement pour vos besoins **personnels et non commerciaux** ».
- **§9 Restrictions** : « Vous ne devez pas **copier, modifier, distribuer,
  vendre ou louer** toute partie des Services ou du contenu sans l'autorisation
  écrite préalable de Geloka. »

Ces clauses sont **plus restrictives** que la mention, sur la page du baromètre,
d'une réutilisation « libre sous réserve de citation + lien ». En cas de tension,
la lecture prudente s'applique.

**Décision :** n'utiliser le baromètre que comme **repère agrégé**, avec
**citation + lien obligatoires**, sans redistribution du contenu ni usage
commercial. Les fichiers brut restent **locaux** (`data/raw/`, non versionné).
La collecte est soumise à `--confirm-legal`.

## Koutchoumi — absence de CGU

Aucune page de conditions d'utilisation n'est publiée (les URL candidates
`/en/terms`, `/fr/cgu`, `/conditions-generales…` renvoient la page générique du
site). Le `robots.txt` ne contient que des directives **commentées**
(`#User-agent: *` / `#Disallow:`) : aucune interdiction explicite, mais **aucune
autorisation explicite** non plus.

**Décision :** collecte en **usage recherche**, avec les garde-fous suivants —
`robots.txt` respecté dynamiquement, débit limité (1 requête / 2 s), User-Agent
transparent identifiant la recherche et un contact, **aucune donnée personnelle
stockée**, pas de redistribution du brut. La collecte est soumise à
`--confirm-legal`.

## Données personnelles

Les pages de détail Koutchoumi exposent des **téléphones, e-mails et noms
d'annonceurs**. Conformément à AGENTS.md §9 (minimisation) et aux recommandations
de la Phase 0, le **texte brut n'est pas conservé** pour cette source : seuls
l'URL, le slug (ville/quartier/type/pièces/prix) et les champs structurés non
personnels sont enregistrés. Les échantillons locaux (`deegeorgie`) ne
contiennent pas de données personnelles.

## À refaire à chaque collecte

1. Re-vérifier `robots.txt` (fait automatiquement par `HttpClient`).
2. Respecter le débit et le User-Agent transparent.
3. Ne jamais stocker de données personnelles.
4. Documenter source, date et méthode dans les **métadonnées de lot**.
