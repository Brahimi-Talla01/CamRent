# `ml/` — code Machine Learning

Règle de la maison (`context/code-standards.md`) : **aucun modèle complexe tant
qu'une baseline mesurée n'est pas battue**. La Phase 5 mesure ces baselines ; la
Phase 6 n'ajoute un modèle que s'il démontre un gain vérifiable — c'est le cas
(`random_forest_log1p`, −22,31 % sur la MAE de validation).

## Structure

```
ml/
├── src/            # package importable `ml.src`
│   ├── config.py           # chemins, cible, features, graine, seuils
│   ├── data.py             # lecture de mart_ml_dataset + scénarios + qualité
│   ├── split.py            # train/validation/test reproductible
│   ├── baselines.py        # baseline_global, baseline_city, baseline_neighborhood
│   ├── evaluation.py       # MAE/RMSE/R²/MedAE, segments, IC bootstrap
│   ├── report.py           # rendu markdown des baselines (Phase 5)
│   ├── run_baselines.py    # orchestration Phase 5
│   ├── features.py         # features dérivées + imputation train-only (Phase 6)
│   ├── models.py           # zoo de candidats et pipelines (Phase 6)
│   ├── training.py         # comparaison, sélection multi-graines (Phase 6)
│   ├── uncertainty.py      # split-conformal vs régression quantile (Phase 6)
│   ├── interpretability.py # importance, dépendance, explication locale (Phase 6)
│   ├── persistence.py      # modèle retenu + métadonnées (Phase 6)
│   ├── model_report.py     # rendu markdown des modèles (Phase 6)
│   ├── markdown.py         # helpers de rendu partagés (Phases 5-6)
│   ├── run_models.py       # orchestration Phase 6
│   └── __main__.py         # CLI `python -m ml.src baselines|models`
├── artifacts/      # métriques JSON de la Phase 5 (ignoré par git)
├── evaluation/     # évaluation par segment (Phases 6-7)
├── models/         # artefacts de modèles (ignoré par git)
└── notebooks/      # exploration
```

## Utilisation

```bash
# Prérequis : le mart de la Phase 4 doit être en base
export DATABASE_URL=postgresql://camrent:change-me@localhost:5433/camrent
python -m ml.src baselines                      # Phase 5 : métriques + rapport
python -m ml.src baselines --report /tmp/r.md   # rapport ailleurs
python -m ml.src models                         # Phase 6 : comparaison + modèle retenu
python -m ml.src models --no-lightgbm           # ignorer la dépendance optionnelle
python -m ml.src models --no-persist            # sans écrire le modèle
python -m ml.src models --models-dir /tmp/models
```

Le rapport versionné est `docs/phase-5/baseline-report.md` (Phase 5) et
`docs/phase-6/model-report.md` (Phase 6) ; ils sont **entièrement dérivés** du
JSON de métriques (aucun chiffre en dur).

Rejeu : le JSON de la Phase 5 est strictement déterministe (pas d'horodatage, md5
identique). Celui de la Phase 6 l'est **hors durées mesurées** — entraînement et
prédiction varient d'un rejeu à l'autre, par nature ; toutes les métriques,
grilles de graines et fourchettes sont identiques.

Dépendances : `scikit-learn` (Phases 5-6) et `lightgbm` (Phase 6, **optionnelle** —
sans elle, la famille LightGBM est simplement retirée du zoo, l'installation est
recommandée pour pouvoir comparer). Installer via `pip install -e '.[ml]'`.

## Principes appliqués

- Aucune exclusion silencieuse : le scénario principal conserve toutes les
  observations ; les restrictions sont des scénarios étiquetés.
- Aucune statistique sans son nombre d'observations, y compris par segment ; les
  segments sous le seuil de publication sont marqués, pas masqués.
- Zéro data leakage : pas de `rent_per_m2`, quartiles de prix calculés sur
  l'entraînement uniquement, drapeaux de qualité jamais utilisés comme features.
- Reproductibilité : graine fixe, séparation déterministe, versions Python /
  pandas / numpy / scikit-learn consignées dans le rapport.

Détail des résultats : `docs/phase-5/README.md` (baselines) et
`docs/phase-6/README.md` (modèles).
