# CamRent — Recadrage produit, architecture fonctionnelle et plan de réalignement

**Statut :** proposition à relire et valider avant toute modification du dépôt
**Version :** 1.0
**Date :** 2026-10-14

## 1. Objet

Ce document recadre CamRent à partir de son objectif initial — estimer les loyers observés à Yaoundé et Douala — et des besoins apparus pendant le développement : gérer les sources de données, inspecter et préparer les datasets, entraîner et évaluer les modèles, produire des rapports, administrer la plateforme et envisager une fonctionnalité de recherche de logements avec mise en relation.

Ce document **n'autorise pas une réécriture immédiate du dépôt**. Il définit une cible raisonnable et une méthode de réalignement. Le dépôt contient déjà les phases 00 à 07 et le développement s'est arrêté à la phase 07 (`model-registry`). L'agent IA doit donc auditer l'existant plutôt que supposer que les fonctionnalités prévues sont toutes implémentées ou testées.

Objectifs :

1. Préserver le travail utile déjà réalisé.
2. Vérifier la cohérence des phases 00–07.
3. Corriger les écarts avérés sans réécriture massive par défaut.
4. Définir les produits/sous-systèmes CamRent et leurs frontières.
5. Faire apparaître le back-office progressivement.
6. Garder la marketplace comme extension soumise à validation.
7. Replanifier les phases 08–12 selon les dépendances réelles.
8. Encadrer l'agent IA avec un processus auditable et par étapes.

## 2. Vision produit retenue

### 2.1 Produit initial

CamRent vise initialement à fournir une estimation indicative des **loyers mensuels affichés sur le marché** pour des logements résidentiels à Yaoundé et Douala, à partir des caractéristiques disponibles et des observations collectées.

Tant que le dataset repose principalement sur des annonces, le produit ne doit pas prétendre prédire avec certitude le loyer réellement payé ni présenter le résultat comme un « prix juste » universel. L'interface devra préciser la date des observations, le périmètre couvert et les limites de l'estimation.

### 2.2 Proposition de valeur

> Aider les utilisateurs à mieux comprendre les loyers demandés sur le marché immobilier, grâce à des données contrôlées, des estimations documentées et, si cette extension est validée, des annonces permettant de rechercher un logement et d'entrer en contact avec son annonceur.

### 2.3 Marché de départ

- **Périmètre initial :** Yaoundé et Douala, au Cameroun.
- **Devise de référence :** XAF.
- **Cible initiale :** logements résidentiels proposés à la location mensuelle.
- **À exclure du périmètre ML initial :** ventes immobilières, locations journalières/touristiques, bureaux et commerces, sauf expérience séparée avec un besoin et un dataset adéquats.
- **Extension géographique :** Conakry ou d'autres marchés nécessitent une décision explicite, un audit des sources, des référentiels géographiques, une gestion des devises et une validation locale.

## 3. Produits et sous-systèmes CamRent

CamRent doit être pensé comme un écosystème modulaire. Ces sous-systèmes peuvent partager une base technique et une identité de marque, mais doivent conserver des responsabilités, permissions et cycles de vie clairs. Cette séparation fonctionnelle **n'impose pas des microservices**.

### 3.1 A — CamRent Data Platform

**But :** collecter, conserver, tracer, contrôler et préparer les données pour l'analyse et le ML.

Responsabilités :

- catalogue des sources et métadonnées de collecte ;
- connecteurs contrôlés et exécutions de collecte ;
- conservation des données brutes et de leur provenance ;
- validation, normalisation, déduplication et gestion des rejets ;
- versionnement des datasets et traçabilité des transformations ;
- contrôles de qualité et mesures de couverture ;
- transformations dbt et tables prêtes pour l'analyse et le ML.

Garde-fous :

- ne pas confondre données brutes et données transformées ;
- ne pas écraser silencieusement l'historique des observations ;
- ne pas considérer un dataset importé comme fiable sans validation ;
- respecter les droits d'accès et conditions d'utilisation des sources.

### 3.2 B — CamRent Back-office

**But :** interface interne permettant à l'équipe autorisée de superviser et piloter les capacités existantes.

Modules visés :

1. **Vue d'ensemble :** état des collectes, qualité, exécutions dbt, jobs ML, modèle actif et incidents.
2. **Sources :** registre, paramètres contrôlés, activation/désactivation, collecte manuelle, historique, erreurs et prévisualisation.
3. **Datasets :** exploration paginée, profilage, import validé, exports autorisés et suivi des versions.
4. **Qualité :** règles de validation versionnées, résultats des tests, lignes rejetées et motifs.
5. **Expériences ML :** choix d'un dataset versionné, lancement d'un job asynchrone, logs, métriques et comparaisons.
6. **Registre des modèles :** versions, provenance, statut, approbation, déploiement et retrait.
7. **Rapports :** qualité et marché en interne ; rapports publics seulement après validation de leur méthodologie.
8. **Utilisateurs et permissions :** comptes internes, rôles et autorisations minimales.
9. **Paramètres :** configuration fonctionnelle autorisée, référentiels et devise de référence.
10. **Audit et supervision :** journal des actions sensibles, erreurs techniques et alertes.

Le back-office se développe progressivement avec les fonctions qu'il pilote. Une page ne doit pas simuler une capacité inexistante dans le backend.

### 3.3 C — CamRent Estimation

**But :** exposer une estimation indicative du loyer mensuel demandé pour un logement décrit par des caractéristiques prises en charge.

Fonctions :

- saisie et validation des caractéristiques ;
- estimation via un modèle approuvé ou une méthode de secours documentée ;
- présentation des limites, de la fraîcheur des données et de la couverture ;
- comparaison avec des observations similaires si cela est suffisamment fiable ;
- conservation de la version du modèle utilisée.

Ne pas afficher de « confiance de 95 % » arbitraire. Une éventuelle fourchette doit provenir d'une méthode statistique documentée ; la couverture des données peut être présentée séparément.

### 3.4 D — CamRent Marketplace

**But :** Possibilité pour un locataire et un bailleur d'entrer en contact.

Si l'intérêt est démontré :

- recherche et filtres d'annonces ;
- pages détaillées de logement ;
- comptes annonceurs et gestion de leurs annonces (Locataires) ;
- photos, disponibilité déclarée et historique des changements ;
- demandes de contact ou de visite ;
- modération, signalement, détection de doublons et annonces obsolètes.

À reporter : paiements intégrés, réservation, contrats numériques, gestion locative complète, commissions complexes et expansion multi-pays immédiate.

Une annonce publiée par un utilisateur (Locataire) et une observation importée depuis une source externe doivent rester des objets distincts, éventuellement rapprochés, afin de préserver la provenance, les droits et la gestion des mises à jour.

### 3.5 E — Services communs

- authentification et autorisation ;
- rôles et permissions ;
- audit des opérations sensibles ;
- tâches asynchrones et suivi de statut ;
- configuration et gestion des secrets ;
- observabilité, alertes, sauvegardes et récupération ;
- API interne et API publique avec autorisations distinctes.

Ces sous-systèmes n'impliquent pas plusieurs déploiements ou bases. Pour le MVP, préférer une application modulaire et des workers pour les tâches longues. Séparer des services uniquement si un besoin mesuré le justifie.

## 4. Périmètre et priorités

### 4.1 Obligatoire pour le MVP Data/ML

- ingestion reproductible de quelques sources autorisées ;
- conservation du brut avec source, identifiant/URL quand disponible, date de collecte et empreinte de contenu ;
- normalisation et déduplication traçables ;
- suivi des rejets et de leurs raisons ;
- profilage et couverture par ville, quartier et type de logement ;
- modèles dbt documentés et testés ;
- baseline ML comparée à des méthodes simples ;
- évaluation sans fuite de données, avec analyse par segment ;
- registre simple des expériences et modèles ;
- API d'estimation et interface minimale ;
- back-office initial pour sources, imports, qualité, jobs et modèles ;
- rôles, audit et logs essentiels ;
- procédures de configuration, tests, sauvegarde et déploiement.

### 4.2 À réaliser seulement si le besoin est confirmé

- marketplace complète ;
- Conakry ou d'autres marchés ;
- orchestration avancée ;
- règles de nettoyage définies librement par du code utilisateur ;
- facturation et abonnements ;
- rapports PDF avancés ;
- notifications complexes ;
- microservices ;
- streaming événementiel/Kafka.

### 4.3 À ne pas construire maintenant

- éditeur graphique généraliste de pipelines ;
- exécution de scripts arbitraires depuis le navigateur ;
- entraînement synchrone dans une requête HTTP ;
- suppression automatique de valeurs atypiques uniquement parce qu'elles sont rares ;
- score de confiance non calibré ;
- architecture distribuée sans justification.

## 5. Principes Data/ML

### 5.1 Sémantique de la cible

La cible initiale doit être explicite, par exemple `monthly_rent_xaf`, et représenter le loyer mensuel affiché après normalisation. Chaque observation doit conserver une sémantique :

- `asking_rent` : loyer demandé ;
- `actual_rent` : loyer réellement payé, si obtenu de manière fiable ;
- `unknown` : sémantique non établie.

Ne pas mélanger ces catégories dans la même cible sans analyse et justification.

### 5.2 Provenance et historique

Conserver autant que possible :

- source et identifiant source ;
- URL source, sous réserve des règles applicables ;
- date de publication si connue ;
- date de collecte ;
- empreinte de contenu ;
- version du connecteur/parser ;
- statut de validation et raison de rejet ;
- dates d'observation et changements de prix.

Une nouvelle collecte ne doit pas écraser l'historique sans conserver les changements pertinents.

### 5.3 Qualité

- Distinguer `false`, `true` et `unknown`.
- Normaliser villes, quartiers, types de logement, devises et périodicités.
- Conserver la valeur originale lorsque nécessaire à l'audit.
- Séparer anomalie détectée et décision de rejet.
- Tester schémas, contraintes métier et transformations.
- Mesurer la couverture avant d'autoriser une estimation.

### 5.4 Rôle de dbt

dbt intervient sur les données disponibles dans la base analytique après l'ingestion et le chargement. Il transforme et teste les données SQL, documente les modèles et construit des tables réutilisables. Il ne remplace ni les connecteurs, ni le stockage brut, ni l'entraînement ML, ni le registre des modèles.

Les modèles dbt actuels doivent être audités avant modification. Ne pas imposer des noms de tables ou de schémas qui entrent en conflit avec l'existant sans inspection.

### 5.5 Validation ML

- établir une baseline ;
- choisir un découpage train/validation/test adapté au temps et aux dépendances entre annonces ;
- éviter qu'un même logement ou des doublons quasi identiques apparaissent dans train et test ;
- rapporter MAE en XAF, RMSE et erreurs relatives pertinentes ;
- comparer les résultats par ville, quartier et type de bien ;
- éviter les fuites de cible ;
- documenter les limites et segments sous-représentés ;
- déployer uniquement un modèle approuvé avec possibilité de retour arrière.

## 6. Principes d'architecture technique

Ces orientations ne doivent pas provoquer une migration automatique.

### Stockage

- stockage objet ou fichiers versionnés pour les snapshots bruts, si disponible et adapté ;
- PostgreSQL pour les données applicatives et structurées ;
- PostGIS si les besoins géographiques le justifient ;
- `JSONB` pour les attributs variables lorsque cela simplifie l'ingestion ;
- tables analytiques construites par SQL/dbt.

MongoDB n'est pas une exigence. Ne l'ajouter que si l'audit démontre un besoin concret que le stockage objet et PostgreSQL/JSONB ne servent pas correctement.

### Transformations et qualité

- dbt pour les transformations SQL analytiques, tests et documentation ;
- Python pour les connecteurs, traitements non SQL, profilage et ML selon l'architecture existante ;
- rapports de validation et de rejets conservés.

### Orchestration

Commencer par des tâches reproductibles et un mécanisme simple de planification. Ajouter un orchestrateur dédié lorsque dépendances, reprises, planification ou volumes le justifient. Kafka/streaming n'est pas requis pour un MVP de loyers mensuels.

### ML

Un registre simple et traçable suffit si le volume d'expériences est faible. MLflow peut être retenu si l'audit confirme son intérêt. Ne pas ajouter un registre parallèle qui duplique l'information.

### Sécurité et tâches asynchrones

Collectes, transformations coûteuses et entraînements doivent s'exécuter hors des requêtes HTTP. L'API enregistre la demande et retourne un identifiant de job ; un worker exécute le traitement et le back-office suit son statut.

Ne jamais exposer les secrets dans les logs ou réponses API. Valider les imports et les protéger contre les fichiers malveillants ou excessivement volumineux.

## 7. Révision proposée des phases existantes

Ne pas supprimer ou renommer automatiquement les fichiers. Auditer leur contenu, le code, les tests et l'historique Git avant de proposer des changements.

| Phase                       | Décision proposée              | Vérifications ou ajouts                                                             |
| --------------------------- | ------------------------------ | ----------------------------------------------------------------------------------- |
| `00-validation-probleme.md` | Réviser si nécessaire          | Cible, utilisateurs, hypothèses, périmètre et marketplace conditionnelle.           |
| `01-data-ingestion.md`      | Conserver et compléter         | Registre des sources, provenance, snapshots, exécutions, erreurs, prévisualisation. |
| `02-data-cleaning.md`       | Conserver et compléter         | Règles versionnées, quarantaine, inconnues, rejets et imports.                      |
| `03-eda.md`                 | Conserver et compléter         | Profilage, couverture, représentativité et critères de décision.                    |
| `04-data-marts.md`          | Auditer attentivement          | Modèles dbt, tests, documentation, tables analytiques et dataset ML.                |
| `05-baseline-ml.md`         | Auditer attentivement          | Baseline, validation, métriques et prévention des fuites.                           |
| `06-modeles-ml.md`          | Conserver et compléter         | Comparaison des modèles et erreurs par segment.                                     |
| `07-model-registry.md`      | Point de reprise prioritaire   | Implémentation réelle, provenance des artefacts, statuts et transitions.            |
| `08-api.md`                 | Réviser après audit            | API publique, API admin, permissions, jobs asynchrones, erreurs.                    |
| `09-frontend.md`            | Réviser et décomposer si utile | Estimation publique et back-office ; pas de marketplace complète par défaut.        |
| `10-orchestration.md`       | Conserver et proportionner     | Dépendances, reprises et planification sans sur-ingénierie.                         |
| `11-observabilite.md`       | Compléter                      | Qualité, jobs, erreurs, fraîcheur, logs, audit et alertes.                          |
| `12-production.md`          | Compléter                      | Secrets, sauvegardes, CI, sécurité, retour arrière et runbooks.                     |

Nouvelles spécifications proposées, après validation du plan :

- `context/feature-specs/13-backoffice-foundations.md`
- `context/feature-specs/14-backoffice-reporting-observability.md`
- `context/feature-specs/15-marketplace-discovery-and-scope.md`

La phase 15 est d'abord une phase de discovery et de décision, pas une obligation d'implémenter la marketplace. Si la décision est positive, créer ensuite une spécification d'implémentation distincte.

Les fondations du back-office sont transversales : leur réalisation doit être planifiée au moment où les premières fonctions en ont besoin, pas nécessairement après la phase 12.

## 8. Plan de réalignement pour l'agent IA local

L'agent ne doit pas effectuer toutes les modifications en une seule opération. Il travaille par étapes avec des livrables examinables et des validations humaines.

### Étape 0 — Audit en lecture seule

Lire au minimum :

- `context/architecture-context.md`
- `context/ai-workflow-rules.md`
- `context/code-standards.md`
- `context/project-overview.md`
- `context/progress-tracker.md`
- `context/ui-context.md`
- tous les fichiers `context/feature-specs/00` à `07`
- les documents dans `assets/`
- le code, les tests, scripts, dépendances, migrations et l'historique Git disponible.

Déterminer :

- ce qui est implémenté, partiel, prévu ou absent ;
- ce qui est testé et ce qui n'est pas vérifié ;
- les écarts entre spécifications, tracker, architecture et code ;
- les dépendances réelles ;
- les risques de régression et les décisions déjà prises.

Ne pas déclarer une phase terminée uniquement parce qu'un fichier de suivi la marque comme terminée.

**Livrable :** `context/plans/camrent-audit-and-realignment-plan.md`.

Cette étape est en lecture seule, sauf autorisation explicite pour une correction urgente séparée.

### Étape 1 — Plan de réalignement

À partir de l'audit, préparer :

- tableau des écarts ;
- fichiers à modifier et raisons ;
- phases 00–07 à corriger éventuellement ;
- phases 08–12 à réviser ;
- nouvelles spécifications proposées ;
- migrations éventuelles ;
- tests de non-régression ;
- ordre recommandé et critères d'acceptation par lot ;
- décisions nécessitant l'accord du porteur du projet.

Ne pas modifier le code applicatif à cette étape.

### Étape 2 — Mise à jour documentaire contrôlée

Après validation humaine du plan :

1. mettre à jour `project-overview.md` et `architecture-context.md` ;
2. mettre à jour `progress-tracker.md` sans inventer de progrès ;
3. ajuster `ui-context.md` si la séparation public/back-office le nécessite ;
4. ajuster les phases 00–12 sans effacer les décisions encore valides ;
5. créer uniquement les spécifications approuvées ;
6. synchroniser les références entre fichiers ;
7. signaler les contradictions restantes au lieu de les résoudre par supposition.

Fournir un diff lisible et une synthèse des décisions.

### Étape 3 — Implémentation par lots

Après validation documentaire :

- choisir un lot à la fois ;
- définir fichiers et modules concernés ;
- mettre à jour les tests ;
- implémenter une capacité verticale complète ;
- exécuter les tests et contrôles pertinents ;
- mettre à jour le tracker après vérification ;
- fournir commandes exécutées, résultats, limites et diff.

Ne pas démarrer la marketplace pendant la mise à jour des fondations Data/ML, sauf décision explicite.

### Étape 4 — Revue de chaque lot

Un lot n'est terminé que si :

- ses critères d'acceptation sont satisfaits ;
- les tests passent ou les échecs sont expliqués ;
- les spécifications reflètent le comportement réel ;
- les documents de suivi sont à jour ;
- les risques restants sont documentés ;
- l'utilisateur peut examiner les changements.

## 9. Règles impératives pour l'agent IA

1. Inspecter avant de modifier. Ne pas inventer code, tables, endpoints ou résultats.
2. Préserver les implémentations, décisions et historiques valides.
3. Ne pas marquer une phase terminée sans preuve.
4. Ne pas élargir le périmètre sans autorisation : marketplace, multi-pays, paiements et facturation restent conditionnels.
5. Ne pas ajouter une technologie uniquement parce qu'elle est populaire ; justifier son besoin.
6. Ne pas faire de migration destructive sans sauvegarde, plan de retour arrière et accord explicite.
7. Ne pas exécuter de commandes supprimant des données ou réécrivant l'historique Git sans autorisation.
8. Si le code contredit un document, signaler le conflit et proposer une résolution.
9. Séparer faits observés, hypothèses et recommandations.
10. Ne pas afficher de faux indicateurs ; une capacité absente doit être marquée comme prévue ou indisponible.
11. Ne pas copier les secrets dans la documentation, les commits, captures ou logs.
12. Demander une validation humaine pour les décisions structurantes, changements de portée, migrations risquées et implémentation de la marketplace.

## 10. Critères d'acceptation du réalignement documentaire

- La vision produit est cohérente dans les documents de référence.
- Chaque sous-système possède un objectif, des responsabilités et des frontières.
- La marketplace est explicitement conditionnelle.
- Les phases 00–07 reflètent le code réel, y compris les travaux partiels et les tests manquants.
- Les phases 08–12 suivent des dépendances réalistes.
- Les fonctions du back-office sont rattachées aux capacités qu'elles pilotent.
- Les décisions techniques sont justifiées sans complexité inutile.
- Les critères d'acceptation sont vérifiables.
- `progress-tracker.md` ne contient pas de statut non vérifié.
- Les documents ne se contredisent pas.
- Un plan d'implémentation par lots est fourni avant les modifications applicatives.

## 11. Décisions ouvertes

L'agent ne doit pas décider seul :

1. si la marketplace est officiellement retenue ou reste une piste ;
2. quel segment utilisateur est prioritaire ;
3. quelles sources peuvent être collectées et quelles données redistribuées ;
4. quels rôles internes sont nécessaires au départ ;
5. quels rapports seront publics ou réservés à l'équipe ;
6. quel registre de modèles ou orchestrateur est réellement nécessaire ;
7. si la collaboration avec l'ami de Conakry porte sur des données, du code, un produit existant, la commercialisation ou un partenariat plus large.

L'agent peut documenter les options et conséquences, mais ces décisions restent soumises à validation.

## 12. Prochaine action

1. Placer ce document dans `context/product/camrent-product-realignment.md`.
2. Le lire et le valider.
3. Une fois validé, demander à l'agent IA local d'effectuer **uniquement les étapes 0 et 1** : audit en lecture seule puis plan de réalignement.
4. Examiner et approuver le plan.
5. Laisser l'agent mettre à jour la documentation par lots.
6. Reprendre l'implémentation applicative après validation de la documentation révisée et de l'ordre des phases.

Le but n'est pas d'ajouter de la documentation pour elle-même, mais d'éviter de construire des écrans et services dont les responsabilités, les données ou les dépendances ne sont pas suffisamment définies.
