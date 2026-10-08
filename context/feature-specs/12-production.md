# Phase 12 — Production

Lire `context/architecture-context.md` avant de commencer.

Objectif : rendre CamRent déployable, testé, sécurisé et maintenable.

## Implementation

1. **Environnements** — trois environnements :

   ```
   development   → tests locaux
   staging       → validation avant production
   production    → données réelles
   ```

2. **Docker** — standardiser l'environnement local via `docker-compose.yml` :

   ```
   postgres
   minio        (object storage local, si utilisé)
   airflow      (si Phase 10 activée)
   redis        (seulement si besoin réel)
   backend
   frontend
   ```

   Principe : **n'ajouter un service que lorsqu'il répond à un besoin réel**.

3. **CI/CD** (GitHub Actions / GitLab CI) :

   ```
   Lint → Unit tests → Data tests → Integration tests → Build → Deploy
   ```

   Le modèle et les transformations sont validés avant déploiement.

4. **Tests** — quatre niveaux :

   - *Unit* : parsing, normalisation, feature engineering, services API ;
   - *Integration* : API → DB, API → Model, Pipeline → DB ;
   - *Data* : nulls, types, ranges, unicité, fraîcheur, distribution ;
   - *End-to-end* : Utilisateur → Frontend → API → Model → Prediction → Response.

5. **Déploiement** :

   ```
   Frontend → Backend → PostgreSQL → Object Storage → ML Model
   ```

6. **Sécurité et confidentialité** :

   - minimisation des données ; pas de collecte inutile de données personnelles ;
   - contrôle des accès ;
   - secrets dans des variables d'environnement ;
   - chiffrement en transit (HTTPS) ;
   - sauvegardes ;
   - logs sans informations sensibles.

## Dependencies

- Docker / docker-compose.
- Toutes les phases précédentes.
- Un fournisseur d'hébergement et un object storage (à choisir selon budget et besoins).

## Scope Limits

- Pas de Kubernetes sauf nécessité réelle.
- Pas de migration vers un Data Warehouse ni vers du streaming à cette phase.
- Ne pas exposer de données personnelles dans les logs.

## Check When Done

- Les trois environnements sont définis et fonctionnels.
- `docker-compose.yml` démarre la stack locale nécessaire.
- La CI exécute lint, tests unitaires, tests de données, tests d'intégration, build.
- Le déploiement frontend / backend / base / storage / modèle fonctionne.
- HTTPS, secrets, sauvegardes et logs non sensibles sont en place.
- La documentation permet à un autre développeur de comprendre et relancer le système.
