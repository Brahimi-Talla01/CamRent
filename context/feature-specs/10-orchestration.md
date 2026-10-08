# Phase 10 — Orchestration

Lire `context/architecture-context.md` (§Pas de sur-engineering) avant de commencer.

Objectif : automatiser les pipelines une fois qu'ils sont **stabilisés** — pas avant.

> **Condition d'entrée** : n'introduire Airflow que lorsque plusieurs pipelines existent, que les
> dépendances deviennent complexes, ou que la planification manuelle devient un problème. Sinon,
> rester sur Python + scripts + cron.

## Implementation

1. Construire le DAG quotidien :

   ```
   DAG daily_rent_pipeline
   extract
      ↓
   load_raw
      ↓
   quality_raw
      ↓
   transform
      ↓
   quality_silver
      ↓
   build_gold
      ↓
   build_ml_dataset
   ```

2. Configurer : planification, dépendances entre tâches, retries, logs, monitoring, historique des exécutions.

3. **Gestion des erreurs** :

   - retry automatique ;
   - isolation des données invalides (quarantine) ;
   - **ne jamais** supprimer les données précédentes ;
   - signaler les erreurs et permettre la reprise.

   ```
   Raw → Transform → ERROR → Pipeline failed → le Gold précédent reste disponible
   ```

4. Rejouer un run passé doit produire le même résultat (reproductibilité).

5. Garder la possibilité de lancer le pipeline manuellement (hors ordonnanceur) pendant la transition.

## Dependencies

- Apache Airflow (Docker).
- Pipelines des Phases 1-4 stabilisés.

## Scope Limits

- Ne pas ajouter de streaming (Kafka / Redpanda) : le batch suffit au MVP.
- Ne pas automatiser le **réentraînement** du modèle sans justification (il pourra être ajouté ensuite).
- Ne pas remplacer un dataset Gold valide par un dataset vide en cas d'échec de collecte.

## Check When Done

- Le DAG quotidien s'exécute de bout en bout.
- Dépendances, retries, logs et historique fonctionnent.
- Un échec d'étape n'écrase pas les données valides et les données invalides partent en quarantine.
- Le pipeline est rejouable à l'identique.
- L'exécution peut être déclenchée manuellement.
