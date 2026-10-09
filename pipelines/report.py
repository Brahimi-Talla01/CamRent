"""Génération du **rapport de nettoyage** (markdown).

Documente chaque règle appliquée et son **volume d'impact**, comme exigé par les
critères « Check When Done » de la Phase 2.
"""

from __future__ import annotations

import datetime as dt

from .silver import CleanResult

REASON_LABELS: dict[str, str] = {
    "doublon_technique": "Doublon technique (même `source` + `source_listing_id`) — supprimé",
    "republication": "Même logement republié — conservé et marqué `is_republication`",
    "city_inconnue": "Ville absente ou hors périmètre — quarantine",
    "quartier_manquant": "Quartier absent — quarantine",
    "type_inconnu": "Type de bien non reconnu — quarantine",
    "prix_manquant": "Prix absent — quarantine",
    "prix_invalide": "Prix ≤ 0 — quarantine",
    "bedrooms_invalide": "Chambres < 0 — quarantine",
    "bathrooms_invalide": "Salles de bain < 0 — quarantine",
    "surface_invalide": "Surface ≤ 0 — quarantine",
}


def _table(counts: dict[str, int], header: str) -> str:
    if not counts:
        return f"_{header} : aucune._\n"
    lines = [f"| {header} | Volume |", "|---|---|"]
    lines += [f"| {key} | {value} |" for key, value in counts.items()]
    return "\n".join(lines) + "\n"


def render_report(result: CleanResult) -> str:
    stats = result.stats
    reasons = stats.get("reasons", {})

    rules_lines = ["| Règle | Volume |", "|---|---|"]
    for reason, count in reasons.items():
        rules_lines.append(f"| {REASON_LABELS.get(reason, reason)} | {count} |")
    rules = "\n".join(rules_lines) + "\n"

    now = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC")
    outliers = stats.get("outliers", 0)
    price_bound = stats.get("price_bound", 0)
    unrecognized = stats.get("neighborhood_unrecognized", 0)
    return f"""# Rapport de nettoyage — Silver dataset

**Phase :** 2 — Data cleaning
**Généré le :** {now}
**Source :** Raw immuable (`data/raw/`) → ne sont jamais modifiés.

## Récapitulatif

| Étape | Volume |
|---|---|
| Observations brutes lues | {stats.get('records_read', 0)} |
| Observations adaptées (source gérée) | {stats.get('adapted', 0)} |
| **Lignes Silver** | **{stats.get('silver_rows', 0)}** |
| **Lignes en quarantine** | **{stats.get('quarantine_rows', 0)}** |

## Règles appliquées et impact

{rules}
- **Aberrations signalées** (gardées, `outlier_flags`) : {outliers}
- **Prix bornés** (minimums, `price_is_bound`) : {price_bound}
- **Quartiers non reconnus** (`neighborhood_recognized=false`) : {unrecognized}

## Répartition par source

{_table(stats.get('by_source', {}), 'Source')}
## Répartition par ville

{_table(stats.get('by_city', {}), 'Ville')}
## Rappel des invariants

- `data/raw/` n'est **jamais** modifié.
- Aucune valeur aberrante n'est supprimée : elles sont signalées (`outlier_flags`).
- Les observations invalides vont en **quarantine**, jamais dans le vide.
- Aucune imputation permissive n'est appliquée.
"""


def write_report(result: CleanResult, path) -> None:  # type: ignore[no-untyped-def]
    from pathlib import Path

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_report(result), encoding="utf-8")
