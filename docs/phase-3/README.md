# Phase 3 — Analyse exploratoire (EDA)

Objectif (spec : `context/feature-specs/03-eda.md`) : comprendre la donnée
Silver avant toute modélisation. Les rapports vivent dans `eda/` (convention
historique conservée) :

- `eda/univariate_analysis.md` — analyse univariée ;
- `eda/bivariate_analysis.md` — analyse bivariée ;
- `eda/insights.md` — enseignements et implications.

Le rendu est **purement dérivé** : `eda/generate_reports.py` lit
`eda/statistics.json` (ignoré par git), elle-même calculée par
`eda/compute_statistics.py` sur `data/processed/silver_listings.parquet`.
Aucune valeur en dur dans les rapports.

## Régénération

```bash
python eda/compute_statistics.py   # écrit eda/statistics.json
python eda/generate_reports.py     # rend les 3 rapports markdown
```

## Résultats (état courant, après l'enrichissement du référentiel — issue #20)

Voir `context/progress-tracker.md` (section Phase 3). En résumé, sur
2 992 lignes Silver : distribution très asymétrique (→ transformation `log1p`),
2 564 prix bornés, 2 001 républications, 17 aberrations conservées, 101 lignes
sur des quartiers non reconnus, couverture concentrée (Douala 2 811 /
Yaoundé 181), et features absentes du MVP (surface, date, meublé, parking).
Médianes de quartier non publiées sous 30 observations (décision de cette
phase, appliquée en Phase 4 via `min_publish_n`).
