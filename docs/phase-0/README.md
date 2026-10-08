# Phase 0 — Validation du problème

Livrables de validation : vérifier que suffisamment de données sont accessibles et que le problème
ML est suffisamment alimenté. Voir `context/feature-specs/00-validation-probleme.md` et l'issue #1.

## Contenu

| Fichier | Objet |
|---|---|
| `data-discovery-report.md` | Rapport consolidé : sources, volumes, variables, contraintes, faisabilité (10 points du Plan Technique §76) |
| `legal-assessment.md` | Évaluation CGU / `robots.txt` / licence par source |
| `feasibility.md` | Verdict de faisabilité ML + décision de stack |
| `profiling/missing_values_report.md` | Valeurs manquantes par colonne et par source |
| `profiling/duplicates_report.md` | Doublons et déduplication |
| `quality_report/data_quality_score.md` | Score qualité par source |
| `quality_report/recommendations.md` | Recommandations de collecte et de nettoyage |
| `eda/univariate_analysis.md` | Distributions univariées |
| `eda/bivariate_analysis.md` | Relations entre variables |
| `eda/insights.md` | Enseignements et implications |

## Reproduction

```bash
python docs/phase-0/scripts/profile_sample.py data/samples
```

L'échantillon brut n'est pas versionné (voir `data/samples/README.md`).
