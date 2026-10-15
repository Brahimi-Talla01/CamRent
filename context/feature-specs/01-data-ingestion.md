# Phase 1 — Data ingestion

Lire `context/architecture-context.md` et `context/code-standards.md` avant de commencer.

Objectif : collecter les sources identifiées en Phase 0 et conserver les données brutes,
sans les altérer, avec leurs métadonnées et premières validations.

## Implementation

1. Construire les **scripts de collecte** dans `ingestion/` pour les sources retenues en Phase 0
   (priorité Koutchoumi + Geloka, complément Jumia / GitHub / contributions selon décision).

2. Stocker les données brutes dans `data/raw/`, organisées par date et par source :

   ```
   data/raw/
   ├── listings/
   │   ├── 2026-10-01/
   │   └── ...
   ├── user_submissions/
   ├── reference_data/
   └── metadata/
   ```

   Formats : JSON / CSV / Parquet. **Ne jamais modifier** un fichier raw après collecte.

3. Écrire les **métadonnées** de collecte par lot : source, URL, date de collecte, méthode,
   nombre d'enregistrements, format.

4. Ajouter les **premières validations** au niveau Bronze :

   - le fichier existe-t-il ?
   - le nombre de lignes est-il raisonnable ?
   - le JSON est-il valide ?
   - la dernière collecte est-elle récente (fraîcheur) ?

5. Rendre la collecte **idempotente** et rejouable : relancer une collecte ne doit pas corrompre
   les données existantes.

6. **Provenance renforcée** (extension issue de l'audit — plan §5/§7.7) : par lot, consigner la
   **version du connecteur**, une **empreinte de contenu** (hash), le statut de validation et
   l'historique des exécutions — matière première du module « Qualité » (Phase 13) et de
   l'observabilité (Phase 11).

## Dependencies

- Python (requests / httpx, parsing HTML ou JSON selon la source).
- Respecter strictement les contraintes d'usage documentées en Phase 0.

## Scope Limits

- Pas de nettoyage ni de normalisation à cette phase (c'est la Phase 2).
- Pas d'orchestration (Airflow) : scripts + exécution manuelle ou cron.
- Pas d'écriture en base analytique.
- Ne pas dépasser la fréquence de collecte autorisée par les sources.

## Check When Done

- Les données brutes d'au moins une collecte complète sont présentes dans `data/raw/`.
- Les métadonnées de collecte existent pour chaque lot.
- Les métadonnées permettent de retracer, par lot, l'empreinte de contenu et la version du
  connecteur (extension de provenance).
- Les validations Bronze passent (présence, volume, format, fraîcheur).
- Le Raw dataset v1 est produit et immuable.
- Aucune source sans vérification légale n'est collectée.
