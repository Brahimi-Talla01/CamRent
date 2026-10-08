# AGENTS.md - Règles de travail pour les agents

Ce fichier définit les règles à respecter par **tout agent** (IA ou humain) qui travaille sur le dépôt
CamRent. **Il prime sur les habitudes ou conventions par défaut de l'outil.** En cas de conflit entre
ce fichier et un réglage par défaut, c'est ce fichier qui s'applique.

---

## 1. Avant de commencer une tâche - checklist obligatoire

Ne jamais commencer à coder avant d'avoir fait ces étapes, dans cet ordre :

1. **Lire ce fichier** (`AGENTS.md`).
2. Lire `context/ai-workflow-rules.md` — règles de workflow et de périmètre.
3. Lire `context/project-overview.md` et `context/architecture-context.md` — produit, architecture, invariants.
4. Lire `context/code-standards.md` (+ `context/ui-context.md` si la tâche touche l'interface).
5. Lire la **spec de la phase concernée** dans `context/feature-specs/` (00 → 12).
6. Lire `context/progress-tracker.md` — état **réel** d'avancement et points ouverts.
7. Vérifier que la tâche ne viole aucun **invariant** de `architecture-context.md`.
8. Si l'exigence est ambiguë ou absente → la résoudre d'abord dans le fichier de contexte concerné,
   ou l'inscrire comme point ouvert dans `progress-tracker.md`. **Ne jamais inventer de comportement.**
9. **Afficher le plan** avant de modifier (voir §4).

## 2. Périmètre et ordre des phases

- Travailler sur **une phase à la fois**, dans l'ordre `00 → 12`.
- Préférer de **petits incréments vérifiables** à de grands changements spéculatifs.
- Ne pas mélanger plusieurs responsabilités dans une même étape (UI + pipeline, data + API…).
- Si un changement ne peut pas être vérifié de bout en bout rapidement, **découper**.
- Ne pas sauter à une phase suivante tant que la phase courante n'est pas terminée et vérifiée.

## 3. Ce qu'il ne faut jamais faire

- Introduire une technologie non prévue par la phase courante (Airflow, MongoDB, Redis, Kafka, Spark,
  Kubernetes, Data Warehouse…) — voir `architecture-context.md` §Pas de sur-engineering.
- Modifier les données de `data/raw/` après collecte (elles sont **immuables**).
- Supprimer automatiquement des valeurs aberrantes : les isoler en **quarantine**.
- Introduire une feature à **data leakage** (dépendant de la cible, ex. `rent_per_m2`).
- Afficher une statistique de marché **sans son nombre d'observations**.
- Afficher un **niveau de confiance** non justifié statistiquement.
- Présenter une estimation comme une **valeur officielle** du bien.
- Lancer une **collecte automatisée** sans vérifier CGU / `robots.txt` / droits sur les données.
- Modifier du **code généré**, des **migrations appliquées** ou des **composants de fondation tiers**
  sans instruction explicite.
- Mettre un **secret** dans le code, un log ou un commit.

## 4. Avant de modifier

- Pour toute tâche non triviale (architecture, plusieurs fichiers, choix structurant), **afficher le
  plan et les fichiers concernés** et attendre validation.
- Annoncer le périmètre exact : ce qui sera modifié, ce qui ne le sera pas.
- Ne pas élargir le périmètre au-delà de la demande.

## 5. Règles Data (invariants projet)

- `RAW → CLEAN → TRANSFORMED → ANALYTICAL` : la donnée brute n'est jamais écrasée.
- Philosophie **ELT**, avec ETL ciblé uniquement dans l'ingestion.
- Reproductibilité : mêmes données + même code → mêmes résultats.
- La **qualité des données est une fonctionnalité**, pas une tâche ponctuelle.
- Cible du modèle : `rent_price` (prix **demandé** dans les annonces — à ne pas confondre avec le prix payé).

## 6. Qualité et vérification

- Tout changement non trivial doit être **vérifié** : exécuter les tests, le typecheck ou le build pertinents.
- Une phase est terminée quand les critères **« Check When Done »** de sa spec sont satisfaits.
- Corriger la **cause racine**, pas empiler des contournements.
- Ne pas annoncer une tâche terminée si elle n'a pas été vérifiée.

## 7. Tenir la documentation à jour

- Mettre à jour le fichier de contexte concerné dès qu'un changement affecte l'architecture, le
  stockage, les conventions ou le périmètre.
- Mettre à jour `context/progress-tracker.md` pour refléter l'état **réel** (pas l'état souhaité).
- Les specs `feature-specs/` sont la référence : ne pas les contredire silencieusement.

## 8. Git et commits

- **Un commit = un changement cohérent.** Ne pas mélanger des changements sans rapport.
- Message **clair, concis, à l'impératif, en français**, orienté sur le **pourquoi** plutôt que le _quoi_.
- **Interdiction absolue de co-auteur et de trailer de génération.** Aucun commit ne doit contenir :
  - `Co-Authored-By:` ;
  - `Generated with …`, `🤖`, ou toute mention d'un outil / agent.
    Le commit n'attribue que le(s) auteur(s) humain(s) du dépôt.
- Ne **jamais** `git push` sans demande explicite.
- Ne **jamais** `git commit`, `git rebase`, `git reset` ou toute opération destructive sans demande explicite.
- Ne pas commiter de secrets (`.env` est ignoré) ni de données brutes/traitées.

Exemple de message attendu :

```
Ajoute le pipeline d'ingestion des annonces Koutchoumi

Les scripts de collecte écrivent les données brutes par date afin de garantir
un raw immuable et de permettre le rejeu des transformations.
```

## 9. Sécurité et confidentialité

- Secrets uniquement via variables d'environnement (`.env`, non versionné).
- Minimisation des données : ne pas collecter de données personnelles inutiles.
- Logs sans information sensible.

## 10. Références

| Fichier                           | Contenu                                    |
| --------------------------------- | ------------------------------------------ |
| `context/project-overview.md`     | Produit, utilisateurs, MVP, hors périmètre |
| `context/architecture-context.md` | Stack, frontières, stockage, invariants    |
| `context/code-standards.md`       | Conventions de code                        |
| `context/ui-context.md`           | Contexte interface (provisoire)            |
| `context/feature-specs/`          | Une spec par phase (00 → 12)               |
| `context/progress-tracker.md`     | État d'avancement réel                     |
