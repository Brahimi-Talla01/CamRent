"""Rendu markdown du rapport du registre (Phase 7).

Comme les rapports des Phases 5 et 6, le rendu est **purement dérivé** du résumé
produit par `run_registry.build_summary` : aucun chiffre n'est écrit en dur, le
rapport est donc régénérable à l'identique (hors horodatage).
"""

from __future__ import annotations

from typing import Any

from .markdown import number, table


def render_report(summary: dict[str, Any], *, generated_at: str) -> str:
    """Assemble le rapport markdown du registre de modèles."""
    meta = summary["meta"]
    dataset = summary["dataset"]
    code = summary["code"]
    tracking = summary["tracking"]
    decision = summary["promotion"]
    registered = summary.get("registered")

    lines: list[str] = [
        "# Phase 7 — Rapport du registre de modèles (MLflow)",
        "",
        f"**Généré le :** {generated_at}",
        "",
        "Objectif : tracer chaque expérience et versionner le modèle retenu, pour "
        "ne pas choisir un modèle « sur la base d'une impression » — et n'en "
        "déployer aucun qui ne soit enregistré (spec "
        "`context/feature-specs/07-model-registry.md`).",
        "",
        "## Protocole",
        "",
        f"- **Expérience :** `{tracking['experiment']}` (identifiant "
        f"`{tracking['experiment_id']}`).",
        f"- **URI de suivi :** `{tracking['uri']}`.",
        f"- **Runs journalisés :** {len(summary['runs'])} candidats de la Phase 6 "
        "(chaque famille × transformation de cible).",
        f"- **Dataset :** `{dataset['source']}` — {number(dataset['n_observations'])} "
        f"observations, version `{dataset['version']}` (hash du contenu).",
        "- **Version du code :** consignée dans chaque run (SHA Git + versions "
        f"logicielles, ex. Python {code['logiciel']['python']}, "
        f"scikit-learn {code['logiciel']['scikit_learn']}).",
        f"- **Cible :** `{meta['cible']}` en {meta['devise']}, graine `{meta['graine']}`.",
        "",
        "## Runs journalisés",
        "",
    ]

    ranking = summary["selection"]["classement"]
    rows = [
        [
            f"`{item['slug']}`",
            item["famille"],
            item["cible"],
            number(item["mae_train"]),
            number(item["mae_validation"]),
            number(item["mae_test"]),
            f"`{summary['runs'].get(item['slug'], '—')[:8]}`",
        ]
        for item in ranking
    ]
    lines += table(
        ["Candidat", "Famille", "Cible", "MAE entraînement", "MAE validation", "MAE test", "Run"],
        rows,
    )

    lines += [
        "## Modèle enregistré",
        "",
    ]
    if registered:
        lines += [
            f"- **Étiquette :** `{registered['etiquette']}` "
            f"(nom `{registered['name']}`, version {registered['version']}).",
            "- **Alias :** "
            + (f"`{registered['alias']}`" if registered["alias"] else "aucun (non promu)"),
            f"- **Run source :** `{registered['run_id']}`.",
            f"- **Promu :** {registered['promotion']}.",
            "",
        ]
    else:
        lines += ["Aucun modèle enregistré (exécution en mode `--no-register`).", ""]

    lines += [
        "## Règle de promotion",
        "",
        "Un modèle est promu (alias `champion`) uniquement si **toutes** les "
        "conditions suivantes sont satisfaites :",
        "",
    ]
    for condition in decision["conditions"]:
        marker = "✅" if condition["satisfait"] else "❌"
        lines.append(f"- {marker} **{condition['id']}** — {condition['detail']}.")
    lines += [
        "",
        f"**Décision :** {'promu' if decision['promotion'] else 'non promu'}.",
        "",
        decision["regle"]["portee"],
        "",
        "## Reproductibilité",
        "",
        "Chaque run conserve la version du dataset (hash), la version du code, les "
        "features, les hyperparamètres et les métriques des trois ensembles : le "
        "modèle enregistré est rejouable à partir de son run.",
        "",
        "```bash",
        "# identifiants locaux du docker-compose (voir ml/README.md) :",
        "export DATABASE_URL=postgresql://camrent:<mot-de-passe>@localhost:5433/camrent",
        "# base de registre dédiée (une fois) :",
        "#   createdb -h localhost -p 5433 -U camrent mlflow",
        "python -m ml.src registry",
        "```",
        "",
    ]
    return "\n".join(lines)
