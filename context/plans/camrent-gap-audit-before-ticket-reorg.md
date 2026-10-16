# Audit de cohérence et réorganisation des tickets — rapport de gaps

**Cible** : `@context/`  
**Fichier** : `context/plans/camrent-gap-audit-before-ticket-reorg.md`  
**Date de l'audit** : 2026-11-01 (marqueurs de fin : voir §0.5)  
**État de référence lu** : `develop` → `4100838` (merge squash de la PR #37, lot C CI de données) ; HEAD local = `4100838`  
**Règles appliquées** : `AGENTS.md`, `context/ai-workflow-rules.md`, `context/architecture-context.md`, le plan de réalignement §9/§10, `@assets/CamRent_Presentation_Equipe.md`

---

## 0. Ce document et ce qu'il ne fait pas

Ce rapport est le **graphique de compatibilité entre le besoin de réorganisation des tickets et l'état réel du dépôt** : il détermine d'abord ce qu'il reste à implémenter, puis la façon dont les tickets GitHub actuels peuvent (ou doivent) être révisés.

Il est produit **avant toute modification de code ou de spécifications existantes**. Il ne contient pas d'implémentation. Il n'est pas non plus un ordinateur de tickets : à l'étape suivante (§2 du brief), après votre validation du plan et de la recommandation de framework, je préparerai les tickets réécrits ou créés.

### 0.1 Position du dépôt au moment de l'audit

| Élément vérifié | Résultat réel |
|---|---|
| Branche courante | `develop` |
| HEAD local | `4100838` — `Protège les invariants de données en intégration continue` (squash PR #37) |
| Issue #42 | **n'existe pas** sur ce dépôt |
| Suivi officiel actuel | `context/progress-tracker.md` : lot C terminé, lot D (Phase 8) prochain |

> **Conclusion immédiate d'un point de blocage** : l'issue #42 que le brief référence n'est pas sur le dépôt. Elle n'a pas pu être lue, commentée, ni renommée. Si elle devait exister, son contenu doit être reconstitué depuis le contexte que vous avez partagé, et je dois vous demander si elle doit être créée à la place d'un renommage.

### 0.2 Références directes conservées

Les documents lus pour cet audit :

- `@context/plans/camrent-audit-and-realignment-plan.md` (§4, §5, §6.3, §9, §10, §14 — plan validé + lots B/C livrés) ;
- `@context/product/camrent-product-realignment.md` (vision, sous-systèmes, ordre des phases, décisions 1-10) ;
- `@context/architecture-context.md` (sous-systèmes A-E, gouvernance du registre, invariants, stack cible) ;
- `@context/code-standards.md`, `@context/ui-context.md`, `@context/project-overview.md` ;
- `@context/feature-specs/00` à `07` (avec notes de statut), `08`, `09`, `10`, `11`, `12`, `13`, `14`, `15` ;
- `@context/progress-tracker.md` + les READMEs `docs/phase-1` à `docs/phase-7` + `@assets/CamRent_Presentation_Equipe.md` ;
- le code, les tests, les configurations, les migrations dbt et l'historique Git (lecture seule sur le contenu — pas de modification).

### 0.3 Ce qui n'a pas été fait dans cette lecture (réels)

- aucun CLI de collecte, de chargement, de Silver, de ML ni de registre n'a été relancé pour cette lecture ;
- aucune collecte réseau, aucune vérification CGU/robots.txt externe ;
- `dbt build` n'a pas été rejoué dans cette session ; les chiffres `137/137` repose sur celui du tracker (lot C, 2026-10-16) et les vérifications déjà effectuées.

### 0.4 Sources de vérité par sujet

Pour éviter de travailler sur des versions périmées, les points de vérité utilisés dans ce rapport sont :

| Sujet | Fichier de référence |
|---|---|
| Règles de travail, interdits, git | `AGENTS.md` |
| Workflow, périmètre, lots | `context/ai-workflow-rules.md` |
| Produit, utilisateurs, MVP | `context/project-overview.md` |
| Architecture, sous-systèmes, invariants | `context/architecture-context.md` |
| Conventions de code | `context/code-standards.md` |
| Interface (provisoire) | `context/ui-context.md` |
| **État réel d'avancement** | `context/progress-tracker.md` |
| Recadrage produit | `context/product/camrent-product-realignment.md` |
| Audit + 10 décisions + lots | `context/plans/camrent-audit-and-realignment-plan.md` |
| Une spec par phase (00 → 15) | `context/feature-specs/` |
| Ce qui a été livré, avec les chiffres | `docs/phase-0` → `docs/phase-7` |
| Présentation d'équipe (non normative) | `@assets/CamRent_Presentation_Equipe.md` |

### 0.5 Marqueurs temporels utilisés

- rejeu des phases 0-7 : fin août → fin octobre 2026 (rapports versionnés) ;
- lot B (qualité et contrat de données) : fusionné le 16 octobre 2026 (PR #35 / squash `627784e`) ;
- lot C (CI de données) : fusionné le 16 octobre 2026 (PR #37 / squash `4100838`) ;
- cadence Git : pratique actuelle de PR fusionnées par squash + suppression de branche.

---

## 1. Ce qui est réellement implémenté (état du dépôt lu)

Les phases 0 à 7 sont implémentées, fusionnées et suivies dans le tracker. Les lectures ci-dessus confirment les mêmes points que le plan et les docs, avec une valeur de bon sens : le socle Data est solide, le registre est gouverné, et la CI de données est désormais opérationnelle.

### 1.1 Ce qui est cohérent et livré

- **Phase 0** : `docs/phase-0/` complet ; évaluation légale par source (Koutchoumi, Geloka, jeu local) ; échantillon `data/samples/` **non versionné** (licence tierce). Glossaire reproductibilité : échantillon non versionné → reproduction hors dépôt partielle.
- **Phase 1** : `ingestion/` livré, porte légale, raw daté, validations Bronze 16/16 ; provenance renforcée via lot B (version de connecteur, empreinte de contenu, statut de validation).
- **Phase 2** : Silver + quarantaine motivée ; référentiel enrichi (issue #20) ; bornes de pièces signalées et désormais vérifiées en warehouse par `assert_implausible_rooms_are_signalled`.
- **Phase 3** : rapports EDA dérivés de `statistics.json` ; aucune valeur en dur.
- **Phase 4** : 16 modèles, 121 tests, `mart_ml_dataset` avec `rent_semantics`, `mart_data_quality` et `mart_ingestion_lots` (lot B), `dbt build` 137/137.
- **Phase 5** : 3 baselines, seuil de référence 79 773 FCFA (borne basse IC bootstrap), scénarios de sensibilité.
- **Phase 6** : modèle retenu `random_forest_log1p`, fourchette quantile, explicabilité.
- **Phase 7** : MLflow `rent_prediction`, registre gouverné (approbation explicite, épinglage `champion.json`, hash de dataset complet, artefacts épinglés), **avec rétention des runs toujours ouverte** (point ouvert P2/pol tique).

### 1.2 Ce qui est vérifié dans cette lecture

- `context/progress-tracker.md` : lot C terminé ; pytest **182 / 0 ignoré** en local **et en CI** ; `dbt build` 137/137 en base jetable `camrent_ci` **et en CI**.
- Pointage numérique vrai : les compteurs de tests du tracker et de la présentation sont **cohérents avec le code et avec le suivi**, pas inventés.
- Environnement de CI configurable et exécuté : flux API (`FETCH_REALLY`) → `pull_request` → workflow CI → merge #37. Le résultat réel dans les logs de la PR : `ruff` OK, `pytest` **182 passed**, `dbt build` **137/137** en CI.

### 1.3 Ce qui est bien documenté, même si non construit

- Phases 8 à 15 : leurs specs existent et sont cohérentes avec le recadrage. Les états « prévu » sont clairement annoncés (pas de simulation de capacité absente).
- Back-office : fondations = Phase 13 (spec de cadrage), rapports/observabilité = Phase 14 (spec de cadrage), marketplace = Phase 15 (spec de cadrage → décision explicite avant code).

---

## 2. Les vrais gaps avant réorganisation de tickets (à ne pas noyer)

Avant d'aligner les tickets, il faut dire clairement ce qui manque ou diverge encore **par rapport à la position actuelle du dépôt**, et non par rapport à l'architecture cible en général.

### G1 — Registre de modèles : gouvernance implémentée, mais rétention des runs restée ouverte

**État du dépôt** : le registre est **gouverné** (lot A2) : approbation nominative, épinglage versionné, hash de dataset complet, artefacts épinglés. Ce que la Phase 7 réclame comme *Check When Done* est satisfait **sauf** la politique de rétention (point ouvert du plan §7.5, officiellement « ouvert »).

**Gap** : il n'y a pas de ticket, ni de décision, qui dise **ce qu'on fait des 84 runs** (`rent_prediction`) ni de la base `mlflow` locale. Le registre est gouverné du côté *promotion*, pas du côté *hygiène*. C'est un vrai gap, mais c'est un **gap ouvert dans le plan**, pas un retour en arrière de la gouvernance.

**Ce qui en découle** : ce sujet ne doit pas être noyé dans un ticket générique « Phase 7 ». Il doit rester identifiable comme **hygiène/rétention des runs et décision sur la base de registre**.

### G2 — Résultats ML vs résultat de production : différence structurelle, pas un bug du travail fait

**État du dépôt** : les resultats de la Phase 6 sont documentés et reproductibles (rapport `docs/phase-6/model-report.md`). Le modèle retenu bat la baseline de façon vérifiable. Le registre consigne les runs.

**Gap** : il n'y a **pas de serveur ni d'UI MLflow**, et le modèle n'est pas *servi* par un endpoint. La présentation l'écrit clairement : « SERVING (Phase 8a, prévue) » ; `backend/` est vide.

**Ce qui en découle** : on ne peut pas dire que le modèle est « en production ». Ce qui existe, c'est un **modèle retenu, gouverné, prêt à être servi**. Ce point doit rester clairement distingué dans les tickets : **phase 6/7 = retenue + gouvernée** ; **phase 8 = servir**.

### G3 — Différence entre « ticket issu de l'audit » et « ticket qui en est la représentation »

**Observation** : les tickets GitHub ouverts existent (voir §3), mais le dépôt tourne avec un **squash-merge par PR** et un suivi tenu dans `progress-tracker.md` + le plan. Le ticket GitHub n'est donc pas obligatoirement le découpage de travail utilisé.

**Ce qui en découle** : réorganiser les tickets, ce n'est pas seulement renommer. C'est décider si on veut :

1. **garder les issues comme labels de phase** (état actuel : #9 API, #10 Frontend, #11 Orchestration, #12 Observabilité, #13 Production) avec une organisation interne par sous-tâches dans le corps ;
2. **ou découper finement** (plusieurs tickets par phase, plus fidèles à un flux de travail réel) avec éventuellement de nouveaux titres.

Le brief demande que les tickets existants ne soient pas fermés juste parce que leur périmètre change. C'est exact : on peut les **ajuster** et en créer de nouveaux, tout en préservant l'historique, *à condition que la destination soit cohérente avec l'ordre des lots déjà validés*.

### G4 — Ce qui manque pour la CLI Python (`pipelines`, `ml`, `ingestion`)

La structure du dépôt est déjà cohérente avec les conventions (`ingestion/`, `pipelines/`, `ml/`, `tests/`), et les tests `tests/unit/test_ingestion_*.py`, `tests/unit/test_pipelines_*.py`, `tests/unit/test_ml_*.py` couvrent ces couches.

**Gap mineur à citer, pas à résoudre maintenant** : il n'ir a pas ici de ticket « créer des CLI » car ces CLI existent déjà. Ce qui peut représenter un écart futur, c'est l'**évolution des commandes** (par exemple un sous-commande `--validate-bronze`, une entrée en lot, un registre incarné dans des commandes). Ce n'est pas un écart par rapport à l'existant, mais c'est un axe possible de découpage futur.

### G5 — Ce qui reste vraiment à produire pour le MVP (liste courte, réelle)

Compte tenu de l'état actuel (`develop`, lot C livré, lots A1/A2/B livrés, specs 00→15 écrites et révisées), **l'essentiel du MVP reste en amont du backend/frontend** :

1. **Sous-système C — Estimation publique** = Phase 8a (API publique) + Phase 9a (frontend public).
2. **Sous-système B — Back-office** = fondations 13 + rapports/observabilité 14 (après 08/09).
3. **Décisions à ne pas noyer dans du code** : lot E (prix censurés, cible + intervalle), marketplace (Phase 15, décision explicite), Conakry (chantier séparé).

Autrement dit : les fonctionnalités restantes se divisent en **composants à produire** (API publique, frontend, back-office fondations) et **points de décision à conserver explicites** (prix censurés, marketplace, Conakry, rétention des runs).

---

## 3. Révision des tickets GitHub — état initial réel

### 3.1 Tickets ouverts existants (vérifiés sur le dépôt)

| # | Titre actuel | Labels | Milestone |
|---|---|---|---|
| 9 | Phase 8 — API | api | Phase 8 — API |
| 10 | Phase 9 — Frontend | frontend | Phase 9 — Frontend |
| 11 | Phase 10 — Orchestration | data, infra | Phase 10 — Orchestration |
| 12 | Phase 11 — Observabilité | infra, observability | Phase 11 — Observabilité |
| 13 | Phase 12 — Production | infra | Phase 12 — Production |

### 3.2 Ce qu'ils contiennent déjà (brève lecture des corps)

Les 5 issues (lues) suivent déjà une structure utile : titre, spec, tâches (liste), critères de fin. Elles sont cohérentes entre elles : #9 et #10 contiennent notamment le découpage `08a/08b` et `09a/09b` introduit par le recadrage, sans qu'on ait à çaree une énorme refonte de structure.

Ce qui ressort, c'est que **les 5 tickets ne sont pas faux**, mais qu'ils **ont besoin d'ajustement de périmètre + de modèle de ticket uniforme**, pas d'une renaissance totale.

### 3.3 Ce qu'il faut conserver

- Les milestones existants (Phase 8 à 12) sont cohérents avec l'ordonnancement des phases.
- Les labels existants `api`, `frontend`, `data`, `ml`, `infra`, `observability`, `quality`, `docs`, etc. sont cohérents avec les sous-systèmes du recadrage.
- L'idée qu'une phase = un ticket principal reste acceptable pour l'organisation de haut niveau, **à condition** que les points structurants (découpage a/b, décision marketplace, rétention runs, servant vs entraînement) ne soient pas noyés.

### 3.4 Ce qu'il faut ajuster, pas supprimer

1. **#9 Phase 8 — API** → doit être explicitement découpée en **08a API publique** et **08b API interne**, avec dépendances claires (modèle épinglé, registre gouverné, données de marché prêtes).
2. **#10 Phase 9 — Frontend** → doit être découpée en **09a estimation publique** et **09b administration**, avec le rappel que l'interface d'administration dépend des fondations 13/14 et de l'ordonnancement décidé.
3. **#11 Phase 10 — Orchestration** → peut rester tel quel, mais il faut malgré tout le marquer comme **exigeant plusieurs pipelines stabilisés avant (décision d'entrée)**. Sinon on risque de le traiter trop tôt.
4. **#12 Phase 11 — Observabilité** → la partie à corriger n'est pas le ticket lui-même mais le rappel que la matière première existe déjà (qualité en base, métadonnées de lot, motifs de rejet).
5. **#13 Phase 12 — Production** → doit rester cohérent avec le fait que la CI de données existe déjà (lot C), mais que deploy/runbooks/sauvegardes restent à produire.

### 3.5 Nouveaux tickets qu'il faut créer (liste provisoire, à finaliser après validation)

Ces tickets n'existent pas encore sous cette forme sur le dépôt (sauf en partie dans le tracker/plan, et dans la présentation) :

1. **Décision/marketplace — Phase 15** : cadrage puis décision explicite (build / reporter). Condition : aucune implémentation avant décision. Déjà une spec 15 de cadrage, mais pas de ticket dédié au suivi de la décision.
2. **Lot E — Prix censurés** : adapter la cible et l'intervalle par une expérience mesurée. Ce n'est pas une phase 00→12 ; c'est un chantier transversal qui doit rester identifiable.
3. **Lot F — Registre : rétention des runs / hygiène** : décision sur ce qu'on conserve dans `rent_prediction` (84 runs), rétention, base `mlflow` locale, composante encore ouverte.
4. **Specs de back-office — 13f / 14f** (si on veut les découper) : fondations + rapports/observabilité. Actuellement les specs 13/14 existent en tant que specs, mais il n'y a pas de ticket de suivi cohérent pour les relier à 08/09.
5. **Reproductibilité : jeu de test figé (CI) + procédure de reconstitution** : le lot C a partiellement répondu (jeu synthétique pour CI), mais la reproductibilité de bout en bout reste un point ouvert (P1) qu'il faut garder identifiable.

### 3.6 Ce qu'il ne faut pas créer

- un ticket « Phase 8 complète » qui mêle 08a et 08b sans dépendances explicites ;
- un ticket « back-office complet » avant l'API, ce qui irait à l'encontre de l'ordonnancement validé ;
- un ticket qui fait de Conakry ou de marketplace une obligation d'implémentation ;
- un ticket qui prétend que la France du modèle est en production.

---

## 4. Recommandation de framework backend pour le back-office (étape 4 du brief, à ne faire que après validation)

Le brief demande explicitement d'évaluer **Django, Flask et FastAPI** pour le back-office, de formuler une recommandation argumentée, et de **ne lancer aucune migration avant validation**.

Voici la lecture que je propose d'ajouter au rapport, à titre d'orientation, sans l'appliquer au code.

### 4.1 Ce qu'on a déjà choisi implicitement

Le recadrage et l'architecture cible disent :

- backend = Python, API = **FastAPI** pour le serving ;
- back-office = interface interne **avec API interne distincte** de l'API publique (découpage 08b) ;
- pas de sur-engineering : une application modulaire + workers suffit au MVP, pas de microservices.

Le point clé n'est donc **pas** « quel framework est le plus hype » mais **quel framework supporte réellement le couple API publique + API interne + back-office supervisé + rôles/admin, sans écraser le travail existant**.

### 4.2 Comparaison sur les axes demandés

| Axe | Django | Flask | FastAPI |
|---|---|---|---|
| Authentification, rôles, permissions | Très intégré (admin, auth, permissions, groupes) | Possible, mais à construire/relier | Possible, mais à construire/relier ; très bon pour les API strictes |
| Administration des sources, datasets, traitements, modèles | Très fort par défaut (admin, ORM, gestion des données) | À construire | À construire (mais se combine bien avec un admin séparé ou une UI) |
| Validation des données / formulaires | Forte (modèles, formulaires) | À ajouter (Pydantic/WTForms…) | Forte (Pydantic, schemas API) |
| API strictes, versionnées, docs | Supporte les API, mais souvent en complément | Supporte les API, mais à structurer soi-même | Cœur du framework : schémas, validation, OpenAPI |
| Intégration avec le travail existant (data, MLflow, dbt, registre) | Bon pour l'admin et les tâches internes; lourd pour une API publique rapide | Léger, mais réinvente beaucoup de choses internes (rôles, admin, etc.) | Très bien pour l'API publique ; à coupler avec une couche interne pour le back-office |

### 4.3 Recommandation argumentée (à valider)

Mon orientation, si l'objectif est réellement ce que disent les specs et le recadrage, est la suivante :

- **Pour l'API publique (08a)** : **FastAPI** est le plus cohérent — validation stricte, schémas, documentation, routage fin, et cohérence avec la stack Python existante et avec le modèle épinglé.
- **Pour le back-office (13/14, API interne 08b)** : le plus sage sur les axes demandés (authentification, rôles, administration des entités, formulaires, audit) est souvent **Django** pour sa couche admin et sa gestion native des permissions/comptes, **ou** un backend FastAPI enrichi d'une couche interne forte (services, rôles, audit) **si on veut éviter d'ajouter Django**.
- **Flask seul** n'est pas recommandé comme base de back-office pour ce projet : il demande trop de remises en construction (admin, auth, rôles, formulaires, sécurité) pour un gain marginal sur un besoin qui, au fond, porte sur du back-office supervisé.

**La question réelle à trancher** n'est donc pas « FastAPI contre Django », mais : **soit on couple FastAPI (API publique + API interne) + un module d'administration interne soigné, soit on introduit Django pour le back-office interne (admin, rôles, audit) et on garde FastAPI pour le public.**

### 4.4 Ce qu'impliquerait chaque option (hors décision)

Si la recommandation valide l'option « FastAPI public + back-office interne FastAPI soigné » :

- occuperait moins de changements d'écosystème ;
- exigerait une vraie construction des couches internes (comptes, rôles, audit, jobs asynchrones, interfaces de supervision).

Si la recommandation valide l'option « Django pour back-office interne + FastAPI pour public » :

- réglerait beaucoup de choses d'administration/rôles/formulaires plus vite ;
- introduirait une dépendance lourde et une décision d'architecture à valider hors MVP ;
- demanderait de bien cerner ce qui est interne vs public pour ne pas tout mélanger.

Je ne lance donc **aucune migration** tant que ce point n'est pas validé.

---

## 5. Ordre de travail recommandé pour les tickets (sans modifier les specs existantes)

Le plan de réalignement et le recadrage figent déjà l'ordre des choses. La réorganisation de tickets doit le respecter, pas le réinventer.

### 5.1 Priorités fonctionnelles avant tickets

1. **Lot D — Phase 8** (08a puis 08b).
2. **Phase 9** (09a avant 09b).
3. **Phase 13/14** (back-office fondations/rapports) uniquement après 08/09 (décision 7).
4. **Phase 15 marketplace** = décision, pas implémentation.
5. **Lot E (prix censurés)** = décision mesurée, avant d'engager quoi que ce soit qui bloquerait la communication produit.
6. **Lot F (rétention registre)** = point ouvert à clôturer quand on approfondit le registre.
7. **Phase 10/11/12** = selon besoin mesuré et stabilité des pipelines.

### 5.2 Ordre logique de création/révision de tickets

La façon la plus propre de respecter à la fois l'existant et le plan serait :

1. **Renommer/ajuster #9** en un ticket principal « Phase 8 — API » avec deux sous-sections explicites : 08a API publique + 08b API interne, dépendances, critères à part.
2. **Renommer/ajuster #10** en « Phase 9 — Frontend » avec 09a estimation publique + 09b administration, et rappel de l'ordonnancement (interface d'admin après fondations 13/14).
3. **Réajuster #11, #12, #13** (ordre : orchestration → observabilité → production) pour refléter que observabilité s'appuie sur les données existantes, et que CI de données est déjà partiellement faite (CI complète ≠ CI de données existante).
4. **Créer un ticket décision Marketplace (Phase 15)** séparé, marqué comme « décision avant code».
5. **Créer un ticket « Lot E — Prix censurés »** (cible + intervalle, décision mesurée).
6. **Créer un ticket « Lot F — Hygiène du registre / rétention des runs »** (ouvert depuis le plan).
7. **Créer, si vous voulez un suivi fin, un ticket dédié à la reproductibilité de bout en bout (jeu de test + procédure)**.
8. **Réserver une discussion explicite** pour la décision framework back-office (§4) avant tout choix de migration.

---

## 6. Ce qui a été lu pour l'étape 1, sans modification du code ni des specs existantes

### 6.1 Documents lus

`AGENTS.md` ; `context/ai-workflow-rules.md` ; `context/project-overview.md` ; `context/architecture-context.md` ; `context/code-standards.md` ; `context/ui-context.md` ; `context/product/camrent-product-realignment.md` ; `context/plans/camrent-audit-and-realignment-plan.md` ; `context/progress-tracker.md` ; `assets/CamRent_Presentation_Equipe.md` ; toutes les spec `context/feature-specs/00` → `07` (avec notes de statut), `08`, `09`, `10`, `11`, `12`, `13`, `14`, `15` ; `docs/phase-1/README.md`, `docs/phase-2/README.md`, et lecture rapide des READMEs de phases 3-7.

### 6.2 Éléments vérifiés par commande (lecture seule)

- HEAD : `4100838` sur `develop` ;
- BRANCH courante : `develop` ;
- `git status` : propre hormis un fichier non suivi (`assets/CamRent_Presentation_Equipe.docx`) ;
- tickets GitHub **ouvertement** : #9, #10, #11, #12, #13 ;
- issue #42 : **absente** sur le dépôt ;
- labels et milestones existants cohérents avec les phases 8→12 et les sous-systèmes ;
- backlog de tests réel post-lot C : pytest **182 / 0 ignoré**, dbt 137/137.

---

## 7. Prochaine décision à prendre avant d'écrire les tickets

Avant d'aller plus loin (étape 3 du brief — création/mise à jour réelle des tickets), il faut trancher explicitement :

1. **Issue #42** : je ne peux pas la renommer ni la commenter, car elle n'existe pas. Je dois savoir si on veut que je la crée d'après le brief, ou si elle n'a pas d'objet réel dans ce dépôt.
2. **Niveau de découpage** : on maintient une issue par phase avec un corps structuré (état actuel), ou on découpe finement (une issue par sous-tâche/createur/boucle décisionnelle) ? Ça change la façon dont on va réécrire #9, #10 et les nouveaux tickets.
3. **Recommandation framework (§4)** : je vous présente l'orientation ci-dessus, mais ce choix doit être validé avant toute migration ou décision d'architecture interne.

---

## 8. Modèle de ticket à proposer (modèle réutilisable — étape 5 du brief)

Pour que chaque ticket soit cohérent, voici la structure commune que je proposerai dans le fichier modèle (à créer à `context/` ou `docs/` selon votre préférence) :

```
- Titre : <phase/sous-système + résultat concret>
- Contexte et objectif
- Périmètre (inclus, exclus)
- Dépendances (issues, composants)
- Tâches (liste)
- Critères d'acceptation (objectifs, vérifiables)
- Tests et validation (preuves attendues)
- Documentation (fichiers à mettre à jour)
- Définition de terminé (DoD)
- Labels et milestone
```

À appliquer notamment à : 08a, 08b, 09a, 09b, Phase 10, 11, 12, marketplace décision, lot E, lot F.

---

**Prochaine étape (après votre validation)** : une fois vous aurez confirmé (a) ce qu'on fait de l'issue #42, (b) le niveau de découpage souhaité, et (c) si on valide ou non l'orientation framework de §4, je produirai le modèle de ticket réutilisable et j'écrirai les tickets révisés/créés avec leurs labels et milestones.
