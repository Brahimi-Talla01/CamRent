# `ml/` — code Machine Learning

Règle de la maison (`context/code-standards.md`) : **aucun modèle complexe tant
qu'une baseline mesurée n'est pas battue**. La Phase 5 mesure ces baselines ; la
Phase 6 n'ajoutera un modèle que s'il démontre un gain vérifiable.

## Structure

```
ml/
├── src/            # baselines (Phase 5) — package importable `ml.src`
│   ├── config.py        # chemins, cible, features, graine, seuils
│   ├── data.py          # lecture de mart_ml_dataset + scénarios + qualité
│   ├── split.py         # train/validation/test reproductible
│   ├── baselines.py     # baseline_global, baseline_city, baseline_neighborhood
│   ├── evaluation.py    # MAE/RMSE/R²/MedAE, segments, IC bootstrap
│   ├── report.py        # rendu markdown dérivé des métriques
│   ├── run_baselines.py # orchestration
│   └── __main__.py      # CLI `python -m ml.src baselines`
├── artifacts/      # métriques JSON régénérables (ignoré par git)
├── evaluation/     # évaluation par segment (Phases 6-7)
├── models/         # artefacts de modèles (ignoré par git)
└── notebooks/      # exploration
```

## Utilisation

```bash
# Prérequis : le mart de la Phase 4 doit être en base
export DATABASE_URL=postgresql://camrent:change-me@localhost:5433/camrent
python -m ml.src baselines                      # métriques + rapport
python -m ml.src baselines --report /tmp/r.md   # rapport ailleurs
python -m ml.src baselines --artifacts-dir /tmp # JSON ailleurs
```

Le rapport versionné est `docs/phase-5/baseline-report.md` ; il est **entièrement
dérivé** du JSON de métriques (aucun chiffre en dur), et le JSON est déterministe
(pas d'horodatage) pour permettre la comparaison de rejeu.

## Principes appliqués

- Aucune exclusion silencieuse : le scénario principal conserve toutes les
  observations ; les restrictions sont des scénarios étiquetés.
- Aucune statistique sans son nombre d'observations, y compris par segment ; les
  segments sous le seuil de publication sont marqués, pas masqués.
- Zéro data leakage : pas de `rent_per_m2`, quartiles de prix calculés sur
  l'entraînement uniquement, drapeaux de qualité jamais utilisés comme features.
- Reproductibilité : graine fixe, séparation déterministe, versions Python /
  pandas / numpy / scikit-learn consignées dans le rapport.

Détail des résultats : `docs/phase-5/README.md`.
