"""Helpers de rendu markdown partagés par les rapports (Phases 5 et 6).

Aucune valeur n'est écrite en dur dans les rapports : ils ne font que mettre en
forme les structures de métriques produites par les modules de calcul.
"""

from __future__ import annotations

from typing import Any

SEPARATOR = "\u202f"  # espace insécable fine (séparateur de milliers)


def number(value: Any, *, decimals: int = 0) -> str:
    """Formate un nombre (séparateur de milliers) ; `None` devient `—`."""
    if value is None:
        return "—"
    if decimals == 0:
        return f"{round(float(value)):,}".replace(",", SEPARATOR)
    return f"{float(value):,.{decimals}f}".replace(",", SEPARATOR)


def table(headers: list[str], rows: list[list[str]]) -> list[str]:
    """Table markdown simple (liste de lignes, terminée par une ligne vide)."""
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    lines.append("")
    return lines


def gap_percent(reference: Any, other: Any) -> float | None:
    """Écart relatif de `reference` vers `other`, en pourcentage signé."""
    if reference in (None, 0):
        return None
    return 100.0 * (float(other) - float(reference)) / float(reference)


def relative_gap(reference: Any, other: Any) -> str:
    """Écart relatif formaté (ou `—`)."""
    gap = gap_percent(reference, other)
    if gap is None:
        return "—"
    return f"{'+' if gap >= 0 else '−'}{number(abs(gap), decimals=1)} %"
