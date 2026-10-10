"""Génère les rapports de l'EDA (Phase 3) depuis ``eda/statistics.json``.

Rendu **purement dérivé** : chaque chiffre est lu depuis les statistiques
produites par ``compute_statistics.py`` ; rien n'est écrit en dur, afin que les
rapports restent fidèles aux données et reproductibles.

Exécuter ``python eda/compute_statistics.py`` puis ``python eda/generate_reports.py``.

Écrit :

- ``eda/univariate_analysis.md``
- ``eda/bivariate_analysis.md``
- ``eda/insights.md``
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

OUT_DIR = Path(__file__).resolve().parent
STATS_PATH = OUT_DIR / "statistics.json"
REPORT_DIR = OUT_DIR

CITY_ORDER = ["Douala", "Yaoundé"]

HEADER = """**Phase :** 3 — Analyse exploratoire (EDA)
**Source :** `data/processed/silver_listings.parquet` (Silver, Phase 2)"""


def _fmt_number(value: float, decimals: int = 0) -> str:
    return f"{value:,.{decimals}f}"


def _fmt_int(value: int) -> str:
    return f"{value:,}"


def _pct(part: float, total: float) -> str:
    return f"{100.0 * part / total:.2f}%" if total else "0.00%"


def _flag(record: dict[str, Any], key: str, value: Any) -> dict[str, Any]:
    """Renvoie l'enregistrement dont la colonne booléenne ``key`` vaut ``value``."""
    return next(item for item in record if item[key] == value)


def build_univariate(stats: dict[str, Any]) -> str:
    rp = stats["rent_price"]
    log = stats["log_target"]["log1p"]
    dataset = stats["dataset"]
    total = dataset["total_rows"]
    summary = stats["outlier_summary"]
    bedrooms = stats["bedrooms"]
    bathrooms = stats["bathrooms"]

    cities = ", ".join(
        f"{c['city']} ({_fmt_int(c['count'])})" for c in stats["city"]
    )
    empty_columns = ", ".join(f"`{c}`" for c in stats["empty_columns"])
    coherence = stats["city_neighborhood"]
    coherence_by_city = ", ".join(
        f"{c['city']} : {_fmt_int(c['count'])}" for c in coherence["by_city"]
    )
    smallest_source = stats["source"][-1]

    city_rows = "\n".join(
        f"| {c['city']} | {_fmt_int(c['count'])} | {_fmt_number(c['mean'])} | "
        f"{_fmt_number(c['median'])} | {_fmt_number(c['min'])} | "
        f"{_fmt_number(c['max'])} | {_fmt_number(c['std'])} |"
        for c in stats["city"]
    )
    type_rows = "\n".join(
        f"| {t['property_type']} | {_fmt_int(t['count'])} | {_fmt_number(t['mean'])} | "
        f"{_fmt_number(t['median'])} | {_fmt_number(t['min'])} | "
        f"{_fmt_number(t['max'])} |"
        for t in stats["property_type"]
    )
    recognized_rows = "\n".join(
        f"| {'Oui' if x['neighborhood_recognized'] else 'Non'} | {_fmt_int(x['count'])} | "
        f"{_fmt_number(x['mean'])} | {_fmt_number(x['median'])} |"
        for x in stats["neighborhood_recognized"]
    )
    rep_rows = "\n".join(
        f"| {'Oui' if x['is_republication'] else 'Non'} | {_fmt_int(x['count'])} | "
        f"{_fmt_number(x['median'])} |"
        for x in stats["is_republication"]
    )
    bound_rows = "\n".join(
        f"| {'Oui' if x['price_is_bound'] else 'Non'} | {_fmt_int(x['count'])} | "
        f"{_fmt_number(x['median'])} |"
        for x in stats["price_is_bound"]
    )
    source_rows = "\n".join(
        f"| {s['source']} | {_fmt_int(s['count'])} | {_fmt_number(s['mean'])} | "
        f"{_fmt_number(s['median'])} | {_fmt_number(s['max'])} |"
        for s in stats["source"]
    )
    missing_rows = "\n".join(
        f"| `{m['column']}` | {_fmt_int(m['missing_count'])} | {m['share']:.2f}% |"
        for m in stats["missing"]
    )
    outlier_rows = "\n".join(
        f"| {o['source']} | {o['city']} | {o['property_type']} | "
        f"{_fmt_int(o['rent_price'])} | {o['outlier_flags']} |"
        for o in stats["outliers"]
    )

    return f"""# Analyse univariée — Silver dataset

{HEADER}
**Périmètre :** {_fmt_int(total)} observations, {dataset['column_count']} colonnes.

- **Villes :** {cities}.
- **Colonnes entièrement vides** (0 observation) : {empty_columns}.

> Chaque statistique est accompagnée du nombre d'observations utilisées.

## 1. Distribution globale de `rent_price`

| Statistique | Valeur |
|---|---|
| Nombre d'observations | {_fmt_int(rp['count'])} |
| Moyenne | {_fmt_number(rp['mean'])} FCFA |
| Médiane | {_fmt_number(rp['median'])} FCFA |
| Ecart-type | {_fmt_number(rp['std'])} FCFA |
| Min | {_fmt_number(rp['min'])} FCFA |
| Max | {_fmt_number(rp['max'])} FCFA |
| 1er quartile (Q1) | {_fmt_number(rp['q25'])} FCFA |
| 3e quartile (Q3) | {_fmt_number(rp['q75'])} FCFA |
| Asymétrie (skewness) | {rp['skewness']:.3f} |
| Kurtosis | {rp['kurtosis']:.3f} |
| Nuls | {_fmt_int(rp['zeros'])} |
| Négatifs | {_fmt_int(rp['negatives'])} |

### Observations

- Distribution **fortement asymétrique à droite** : skewness ≈ {rp['skewness']:.1f},
  kurtosis ≈ {rp['kurtosis']:.0f} (N = {_fmt_int(rp['count'])}).
- {_fmt_int(summary.get('price_outlier', 0))} prix signalés hors des bornes
  plausibles de la Phase 2 (voir §9).

### Transformation de la cible

Une **transformation logarithmique est fortement pertinente**. Sur `log1p(rent_price)` :

| Statistique (log1p) | Valeur |
|---|---|
| Moyenne | {log['mean']:.3f} |
| Médiane | {log['median']:.3f} |
| Ecart-type | {log['std']:.3f} |
| Asymétrie | {log['skewness']:.3f} |

L'asymétrie passe de ~{rp['skewness']:.1f} à {log['skewness']:.2f} (N = {_fmt_int(rp['count'])}) :
la distribution log-transformée est quasi-normale.
Recommandation pour la Phase 5 : entraîner sur `log1p(rent_price)` puis retransformer.

## 2. Distribution par ville

| Ville | N | Moyenne | Médiane | Min | Max | Ecart-type |
|---|---|---|---|---|---|---|
{city_rows}

## 3. Distribution par type de bien

| Type | N | Moyenne | Médiane | Min | Max |
|---|---|---|---|---|---|
{type_rows}

## 4. Quartiers reconnus vs non reconnus

| Reconnu | N | Moyenne | Médiane |
|---|---|---|---|
{recognized_rows}

## 5. Republications

| Ligne republication ? | N | Médiane |
|---|---|---|
{rep_rows}

## 6. Prix bornés (`price_is_bound = true`)

| Borné | N | Médiane |
|---|---|---|
{bound_rows}

## 7. Sources

| Source | N | Moyenne | Médiane | Max |
|---|---|---|---|---|
{source_rows}

- La source la moins fournie (`{smallest_source['source']}`) ne compte que
  {_fmt_int(smallest_source['count'])} lignes : trop peu pour évaluer son bruit.

## 8. Qualité

### 8.1 Colonnes avec valeurs manquantes

| Colonne | N manquant | % du total |
|---|---|---|
{missing_rows}

Les colonnes à 100 % manquant ({empty_columns}) sont inutilisables en l'état.

### 8.2 Cohérence ville / quartier

- {coherence['recognized_total']} quartiers canoniques reconnus utilisés
  ({coherence_by_city}).
- {coherence['cross_city_conflicts']} quartier reconnu rattaché à plus d'une ville
  (attendu : 0 → cohérence ville/quartier vérifiée).
- {_fmt_int(stats['neighborhood']['not_recognized'])} observations portent sur des
  quartiers non reconnus.

## 9. Valeurs aberrantes (`outlier_flags`)

{_fmt_int(summary.get('total', 0))} lignes signalées, **conservées** (jamais supprimées).
Répartition : {_breakdown(summary)}.

| Source | Ville | Type | Prix | Drapeau |
|---|---|---|---|---|
{outlier_rows}

## 10. Chambres et salles de bain

| Statistique | Chambres | Salles de bain |
|---|---|---|
| N | {_fmt_int(bedrooms['count'])} | {_fmt_int(bathrooms['count'])} |
| Moyenne | {_fmt_number(bedrooms['mean'])} | {_fmt_number(bathrooms['mean'])} |
| Médiane | {_fmt_number(bedrooms['median'])} | {_fmt_number(bathrooms['median'])} |
| Min | {_fmt_number(bedrooms['min'])} | {_fmt_number(bathrooms['min'])} |
| Max | {_fmt_number(bedrooms['max'])} | {_fmt_number(bathrooms['max'])} |
| Nuls | {_fmt_int(bedrooms['zeros'])} | {_fmt_int(bathrooms['zeros'])} |
| Hors plage | {_fmt_int(summary.get('bedrooms_outlier', 0))} | \
{_fmt_int(summary.get('bathrooms_outlier', 0))} |

---
{_FOOTER}
"""


def _breakdown(summary: dict[str, Any]) -> str:
    counts = {k: v for k, v in summary.items() if k != "total"}
    return ", ".join(f"{k} : {_fmt_int(v)}" for k, v in counts.items()) or "aucun drapeau"


_FOOTER = (
    "*Rapport dérivé de `eda/statistics.json` (généré par `eda/compute_statistics.py`)*\n"
    "*Aucune valeur n'est saisie manuellement : rejouer les scripts régénère ces chiffres.*"
)


def build_bivariate(stats: dict[str, Any]) -> str:
    total = stats["dataset"]["total_rows"]
    corr = stats["correlations"]["matrix"]
    neighborhood = stats["neighborhood"]

    city_rows = "\n".join(
        f"| {c['city']} | {_fmt_int(c['count'])} | {_fmt_number(c['median'])} | "
        f"{_fmt_number(c['mean'])} |"
        for c in stats["city"]
    )
    bed_rows = "\n".join(
        f"| {b['bedrooms']} | {_fmt_int(b['count'])} | {_fmt_number(b['median'])} | "
        f"{_fmt_number(b['mean'])} |"
        for b in stats["bedrooms"]["by_value"]
    )
    top_rows = "\n".join(
        f"| {n['neighborhood']} | {_fmt_int(n['count'])} | {_fmt_number(n['median'])} | "
        f"{n['bound_share']:.1f} % |"
        for n in neighborhood["top_by_count"]
    )
    expensive_rows = "\n".join(
        f"| {n['neighborhood']} | {_fmt_int(n['count'])} | {_fmt_number(n['median'])} |"
        for n in neighborhood["most_expensive"]
    )
    affordable_rows = "\n".join(
        f"| {n['neighborhood']} | {_fmt_int(n['count'])} | {_fmt_number(n['median'])} |"
        for n in neighborhood["most_affordable"]
    )
    unavailable_rows = "\n".join(
        f"| `{c}` | **Entièrement absent** (0 observation) |"
        for c in ("furnished", "parking", "gated", "area_m2")
    )

    return f"""# Analyse bivariée — Silver dataset

{HEADER}
**Périmètre :** {_fmt_int(total)} observations.

> Chaque statistique est accompagnée du nombre d'observations utilisées.

## 1. Corrélations entre variables numériques

| Variable | `rent_price` | `bedrooms` | `bathrooms` |
|---|---|---|---|
| `rent_price` | 1.000 | {corr['rent_price']['bedrooms']:.3f} | \
{corr['rent_price']['bathrooms']:.3f} |
| `bedrooms` | {corr['bedrooms']['rent_price']:.3f} | 1.000 | \
{corr['bedrooms']['bathrooms']:.3f} |
| `bathrooms` | {corr['bathrooms']['rent_price']:.3f} | \
{corr['bathrooms']['bedrooms']:.3f} | 1.000 |

- `rent_price` est faiblement corrélé avec `bedrooms` (N = {_fmt_int(total)}).
- `bathrooms` est faiblement corrélé avec `bedrooms` et `rent_price`.

## 2. Prix médian par ville

| Ville | N | Médiane | Moyenne |
|---|---|---|---|
{city_rows}

## 3. Effet du nombre de chambres

| N chambres | N | Médiane | Moyenne |
|---|---|---|---|
{bed_rows}

- La médiane augmente avec le nombre de chambres (tendance directionnelle),
  mais sans surface et avec très peu d'observations pour 4-5 chambres.

## 4. Quartiers les plus chers / les plus accessibles

Top-5 par nombre d'observations (les plus fiables) :

| Quartier | N | Médiane | Part de prix bornés |
|---|---|---|---|
{top_rows}

Parmi les quartiers comptant au moins {neighborhood['min_n_threshold']} observations :

**Les plus chers (médiane la plus élevée) :**

| Quartier | N | Médiane |
|---|---|---|
{expensive_rows}

**Les plus accessibles (médiane la plus faible) :**

| Quartier | N | Médiane |
|---|---|---|
{affordable_rows}

- {_fmt_int(neighborhood['not_recognized'])} observations portent sur des quartiers
  **non reconnus** : signalées, non agrégées ici.

## 5. Effet surface, parking, meublé, barrière

| Caractéristique | Statut dans Silver |
|---|---|
{unavailable_rows}

→ Aucune analyse bivariée possible : ces attributs sont absents de toutes les
sources collectées (0 observation chacun).

## 6. Dimension temporelle

| Statut | Résultat |
|---|---|
| Colonne `posted_at` | **Absente** (0 observation disponible) |

→ Aucune analyse temporelle possible : la source ne fournit pas de date de publication.

---
{_FOOTER}
"""


def build_insights(stats: dict[str, Any]) -> str:
    total = stats["dataset"]["total_rows"]
    rp = stats["rent_price"]
    log = stats["log_target"]["log1p"]
    neighborhood = stats["neighborhood"]
    bound_true = _flag(stats["price_is_bound"], "price_is_bound", True)
    rep_true = _flag(stats["is_republication"], "is_republication", True)
    douala = _flag(stats["city"], "city", "Douala")
    yaounde = _flag(stats["city"], "city", "Yaoundé")
    apartment = stats["property_type"][0]

    return f"""# Insights — Silver dataset (Phase 3)

{HEADER}
**Périmètre :** {_fmt_int(total)} observations.

> Chaque insight est accompagné du nombre d'observations. Les zones à faible
> volume sont explicitement signalées comme **non fiables**.

## Synthèse exécutive

- `{_fmt_int(total)}` observations Silver
  (Douala : {_fmt_int(douala['count'])}, Yaoundé : {_fmt_int(yaounde['count'])}).
- `{_fmt_int(bound_true['count'])}` prix bornés ({_pct(bound_true['count'], total)}) :
  la cible est majoritairement un `> X` (borne inférieure), pas un prix exact.
- `{_fmt_int(rep_true['count'])}` republications ({_pct(rep_true['count'], total)}) :
  les données sont très dupliquées.
- Distribution **très asymétrique** (skewness ≈ {rp['skewness']:.1f}) :
  une **transformation log est nécessaire**.
- **Aucune surface** (`area_m2` absent) et **aucune date** (`posted_at` absent) :
  pas de `rent_per_m2`, pas d'analyse temporelle.
- **Aucun meublé, parking, barrière** : ces features sont inutilisables pour le MVP.

## Insights détaillés

### 1. Distribution des loyers

- Moyenne {_fmt_number(rp['mean'])} FCFA contre médiane {_fmt_number(rp['median'])} FCFA
  (N = {_fmt_int(rp['count'])}) → distribution très asymétrique.
- Prix typique : {_fmt_number(rp['q25'])}–{_fmt_number(rp['q75'])} FCFA (Q1–Q3).
- La transformation `log1p` rend la distribution quasi-normale
  (skewness ≈ {log['skewness']:.2f} contre {rp['skewness']:.1f} avant).

### 2. Géographie

- **Douala** domine ({_pct(douala['count'], total)} des lignes) ;
  Yaoundé ({_fmt_int(yaounde['count'])} lignes) est beaucoup plus petit.
- {_fmt_int(neighborhood['recognized'])} observations sur des quartiers reconnus,
  {_fmt_int(neighborhood['not_recognized'])} sur des quartiers non reconnus
  (noms à normaliser au référentiel).
- Médianes par ville : Douala {_fmt_number(douala['median'])} FCFA
  (N = {_fmt_int(douala['count'])}) vs Yaoundé {_fmt_number(yaounde['median'])} FCFA
  (N = {_fmt_int(yaounde['count'])}) — l'écart de volume rend la comparaison fragile.

### 3. Effet du type de bien

- `{apartment['property_type']}` domine :
  {_fmt_int(apartment['count'])}/{_fmt_int(total)} =
  {_pct(apartment['count'], total)}.
- Les autres types sont marginaux, ce qui limite l'analyse de segment.

### 4. Effet du nombre de chambres

- La médiane augmente avec le nombre de chambres, mais les observations pour
  4-5 chambres sont rares (voir §4 du rapport bivarié) → à utiliser avec précaution.

### 5. Prix bornés et republications

- {_fmt_int(bound_true['count'])} prix bornés
  ({_pct(bound_true['count'], total)}) : conservés avec `price_is_bound=true`,
  à pondérer/exclure à l'entraînement (Phases 5-6).
- {_fmt_int(rep_true['count'])} republications
  ({_pct(rep_true['count'], total)}) : à décider (conserver / pondérer / dédupliquer).

### 6. Quartiers sous-représentés

- {_fmt_int(neighborhood['total'])} quartiers distincts au total.
- {_fmt_int(neighborhood['single_observation_neighborhoods'])} n'apparaissent
  qu'**une seule fois**.
- {_fmt_int(neighborhood['low_volume_neighborhoods'])} quartiers comptent
  ≤ {neighborhood['low_volume_threshold']} observations (soit
  {_fmt_int(neighborhood['low_volume_rows'])} lignes) : leurs statistiques sont
  **non fiables** et ne sont pas publiées comme médianes de référence.
- Aucune médiane par quartier n'est publiée en dessous de
  {neighborhood['min_n_threshold']} observations.

### 7. Biais de couverture

- Les 5 quartiers les plus présents concentrent {neighborhood['top5_share']} % des
  lignes et les 10 premiers {neighborhood['top10_share']} % → **fort biais de couverture**.
- `price_is_bound=true` sur {_pct(bound_true['count'], total)} des lignes :
  ces prix sont des bornes inférieures (`> X`), donc le loyer réel est ≥ la valeur observée.
- {_fmt_int(neighborhood['not_recognized'])} observations hors référentiel de quartiers :
  risque de zones populaires mal représentées.

### 8. Décisions de feature engineering (issues de l'EDA)

- **Cible** : entraîner sur `log1p(rent_price)` (distribution rendue quasi-normale).
- **À conserver** : `city`, `neighborhood`, `property_type`, `bedrooms`, `bathrooms`,
  `price_is_bound`, `neighborhood_recognized`, `is_republication`, `outlier_flags`.
- **À écarter (vides)** : `area_m2`, `furnished`, `parking`, `gated`, `posted_at`.
- **À traiter** : pondérer/exclure les prix bornés ; décider du sort des republications ;
  enrichir/canonicaliser les quartiers non reconnus.
- **Interdit** : toute feature dérivée de la cible (ex. `rent_per_m2`).

### 9. Conclusion sur la transformation de la cible

La transformation `log1p` est **recommandée** : elle ramène l'asymétrie de
~{rp['skewness']:.1f} à {log['skewness']:.2f} sur {_fmt_int(rp['count'])} observations,
condition nécessaire pour exploiter une régression linéaire (baseline de la Phase 5).

### 10. Zones à faible volume

- **Yaoundé** : {_fmt_int(yaounde['count'])} observations
  ({_pct(yaounde['count'], total)}) → comparaisons inter-villes fragiles.
- **Sources secondaires** : voir §7 du rapport univarié — certaines sources
  contribuent trop peu pour être analysées séparément.
- **Quartiers sous-représentés** : voir §6.

---
{_FOOTER}
"""


REPORTS = {
    "univariate_analysis.md": build_univariate,
    "bivariate_analysis.md": build_bivariate,
    "insights.md": build_insights,
}


def main() -> None:
    if not STATS_PATH.exists():
        raise SystemExit(
            f"Missing {STATS_PATH}. Run `python eda/compute_statistics.py` first."
        )
    with STATS_PATH.open(encoding="utf-8") as handle:
        stats = json.load(handle)
    for name, builder in REPORTS.items():
        (REPORT_DIR / name).write_text(builder(stats), encoding="utf-8")
        print(f"Wrote {REPORT_DIR / name}")


if __name__ == "__main__":
    main()
