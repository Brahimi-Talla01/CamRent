# Phase 11 — Observabilité

Lire `context/architecture-context.md` (§Principes directeurs, §Invariants) avant de commencer.

Objectif : savoir en continu si les pipelines fonctionnent, si la qualité des données se dégrade,
et si le modèle perd en performance.

## Implementation

1. **Observabilité des pipelines** — suivre :

   - *Pipeline health* : success, failed, duration, retries ;
   - *Data freshness* : `last_successful_ingestion` ;
   - *Data volume* : rows_ingested, rows_valid, rows_rejected ;
   - *Data quality* : null_rate, duplicate_rate, invalid_rate.

2. **Logs structurés** pour chaque pipeline, par exemple :

   ```
   pipeline = daily_rent_pipeline
   run_id   = 2026-10-08-001
   stage    = transform_listings
   input_rows = 12543
   output_rows = 11782
   rejected_rows = 761
   duration = 42s
   status = success
   ```

3. **Tests de dérive des données** — détecter les variations brutales :

   - exemple : prix médian Douala ≈ 180 000 pendant des mois, puis ≈ 450 000 ;
   - distinguer vraie évolution / changement de source / erreur de parsing / erreur d'unité.

4. **Observabilité du modèle** :

   - distribution des features ;
   - distribution des prédictions ;
   - erreurs lorsque le feedback est disponible ;
   - performance par segment ;
   - **data drift**, **prediction drift**, **model performance drift**.

5. **Alertes** : fraîcheur, volume, qualité, dérive.

6. Outils : dbt tests + Pandera ou Great Expectations (choix définitif selon l'implémentation).

7. **Qualité des données en continu** — consommer la table de qualité du lot B (motifs de
   rejet, quarantaine, volumes) : taux de rejet par source et par motif, comparaison aux lots
   précédents.

8. **Observabilité des jobs ML** — statut, durée et issue des entraînements (Phase 8b / Phase 13) ;
   comparaison des métriques entre deux entraînements.

9. **Audit** — les actions sensibles (promotion de modèle, lancement de job, activation de
   source) sont journalisées et consultables (services communs E, Phase 13/14).

## Dependencies

- Pipelines (Phases 1-4) et modèle en production (Phases 6-8).
- Airflow (Phase 10) pour l'exécution planifiée.

## Scope Limits

- Pas d'outil d'observabilité lourd non justifié (Soda, plateformes ML managées) sans besoin réel.
- Ne pas alerter sur du bruit : les seuils doivent être adaptés au contexte métier.

## Check When Done

- Les métriques de pipeline (health, freshness, volume, quality) sont collectées et consultables.
- Les logs structurés existent pour chaque étape.
- La détection de dérive des données fonctionne et distingue les causes possibles.
- Le suivi du modèle (features, prédictions, performance par segment, drift) est en place.
- Les alertes sont configurées avec des seuils justifiés.
- Les taux de rejet et leurs motifs sont suivis dans le temps (table de qualité du lot B).
- Les actions sensibles sont journalisées et consultables.
