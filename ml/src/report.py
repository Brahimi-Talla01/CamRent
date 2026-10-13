"""Rendu markdown du rapport de baselines (Phase 5).

Le rendu est **purement dérivé** de la structure de métriques produite par
`run_baselines.build_metrics` : aucun chiffre n'est écrit en dur ici, ce qui
garantit que le rapport versionné reste rejouable (`python -m ml.src baselines`).
"""

from __future__ import annotations

from typing import Any

from . import config
from .markdown import gap_percent, number, relative_gap, table

SPLIT_LABELS = {"train": "entraînement", "validation": "validation", "test": "test"}
SEGMENT_FAMILIES = (
    ("ville", "Ville"),
    ("type_de_logement", "Type de logement"),
    ("nombre_de_chambres", "Nombre de chambres"),
    ("niveau_de_prix", "Niveau de prix (quartiles calculés sur l'entraînement)"),
    ("quartier", "Quartier (ville / quartier)"),
)
def _globaltable(blocks: dict[str, Any]) -> list[str]:
    """MAE / RMSE / R² par ensemble, pour chaque baseline."""
    headers = [
        "Baseline",
        "N entraînement",
        "MAE entraînement",
        "MAE validation",
        "MedAE validation",
        "RMSE validation",
        "R² validation",
        "MAE test",
        "MedAE test",
        "RMSE test",
        "R² test",
    ]
    rows: list[list[str]] = []
    for name, block in blocks.items():
        metrics = block["metriques"]
        rows.append(
            [
                f"`{name}`",
                number(metrics["train"]["n"]),
                number(metrics["train"]["mae"]),
                number(metrics["validation"]["mae"]),
                number(metrics["validation"]["medae"]),
                number(metrics["validation"]["rmse"]),
                number(metrics["validation"]["r2"], decimals=3),
                number(metrics["test"]["mae"]),
                number(metrics["test"]["medae"]),
                number(metrics["test"]["rmse"]),
                number(metrics["test"]["r2"], decimals=3),
            ]
        )
    return table(headers, rows)


def _robustnesstable(scenarios: dict[str, Any]) -> list[str]:
    """Écart validation → test de la MAE et de l'erreur médiane, par baseline."""
    headers = [
        "Scénario",
        "Baseline",
        "MAE validation",
        "MAE test",
        "Écart MAE",
        "MedAE validation",
        "MedAE test",
        "Écart MedAE",
    ]
    rows: list[list[str]] = []
    for scenario_name, scenario in scenarios.items():
        for name, block in scenario["baselines"].items():
            validation = block["metriques"]["validation"]
            test = block["metriques"]["test"]
            rows.append(
                [
                    f"`{scenario_name}`",
                    f"`{name}`",
                    number(validation["mae"]),
                    number(test["mae"]),
                    relative_gap(validation["mae"], test["mae"]),
                    number(validation["medae"]),
                    number(test["medae"]),
                    relative_gap(validation["medae"], test["medae"]),
                ]
            )
    return table(headers, rows)


def _segment_rows(
    blocks: dict[str, Any],
    split_name: str,
    family: str,
    *,
    limit: int | None = None,
) -> tuple[list[list[str]], bool]:
    """Lignes de segments : segment, N, MAE par baseline.

    Renvoie aussi si au moins un segment affiché est sous le seuil de
    publication (pour l'afficher en légende, jamais pour le masquer).
    """
    names = list(blocks)
    counts: dict[str, int] = {}
    below: set[str] = set()
    for name in names:
        for record in blocks[name]["segments"][split_name][family]:
            label_column = next(iter(record))
            label = str(record[label_column])
            counts[label] = int(record["n"])
            if record["sous_seuil_de_publication"]:
                below.add(label)

    ordered = sorted(counts, key=lambda label: (counts[label], label), reverse=True)
    if limit is not None:
        ordered = ordered[:limit]

    rows: list[list[str]] = []
    for label in ordered:
        marker = " *" if label in below else ""
        row = [f"{label}{marker}", number(counts[label])]
        for name in names:
            match = next(
                (
                    record
                    for record in blocks[name]["segments"][split_name][family]
                    if str(record[next(iter(record))]) == label
                ),
                None,
            )
            row.append(number(match["mae"]) if match else "—")
        rows.append(row)
    return rows, any(label in below for label in ordered)


def _leveltable(blocks: dict[str, Any], split_name: str) -> list[str]:
    """Quel niveau de prédiction (groupe ou repli) a servi pour chaque baseline."""
    names = list(blocks)
    levels: list[str] = []
    for name in names:
        for level in blocks[name]["niveaux_de_prediction"][split_name]:
            if level not in levels:
                levels.append(level)
    headers = ["Baseline", "N prédit", *levels]
    rows: list[list[str]] = []
    for name in names:
        counts = blocks[name]["niveaux_de_prediction"][split_name]
        rows.append(
            [
                f"`{name}`",
                number(sum(counts.values())),
                *[number(counts.get(level, 0)) for level in levels],
            ]
        )
    return table(headers, rows)


def _thresholdtable(scenarios: dict[str, Any]) -> list[str]:
    """Seuil de référence par scénario."""
    headers = [
        "Scénario",
        "N",
        "Meilleure baseline",
        "MAE validation",
        "IC 95 % MAE validation",
        "Seuil à battre",
        "Gain relatif exigé",
        "MAE test (référence)",
    ]
    rows: list[list[str]] = []
    for name, scenario in scenarios.items():
        threshold = scenario["seuil_reference_validation"]
        interval = (
            f"{number(threshold['mae_borne_basse_ic'])} – "
            f"{number(threshold['mae_borne_haute_ic'])}"
        )
        rows.append(
            [
                f"`{name}`",
                number(scenario["n_observations"]),
                f"`{threshold['baseline']}`",
                number(threshold["mae_validation"]),
                interval,
                number(threshold["mae_borne_basse_ic"]),
                f"{number(threshold['gain_relatif_a_demontrer_pct'], decimals=2)} %",
                number(threshold["mae_test"]),
            ]
        )
    return table(headers, rows)


def render_report(metrics: dict[str, Any], *, generated_at: str) -> str:
    """Rend le rapport markdown complet à partir des métriques."""
    meta = metrics["meta"]
    quality = meta["qualite"]
    chronology = meta["chronologie"]
    scenarios = metrics["scenarios"]
    primary_name = meta["scenario_principal"]
    primary = scenarios[primary_name]
    conclusion = metrics["conclusion"]
    threshold = conclusion["seuil_reference"]
    best = conclusion["meilleure_baseline"]
    best_block = primary["baselines"][best]
    validation_n = best_block["metriques"]["validation"]["n"]
    confidence = number((1 - meta["alpha_bootstrap"]) * 100)

    lines: list[str] = [
        "# Phase 5 — Rapport des baselines (ML)",
        "",
        f"**Généré le :** {generated_at}",
        "",
        "Baselines mesurées avant tout modèle : elles fixent le niveau à battre et",
        "répondent à une seule question — un modèle ML apporte-t-il un gain réel ?",
        "",
        "## Méthode",
        "",
        f"- **Source :** `{meta['source']}` (Phase 4), cible `{meta['cible']}` "
        f"en {meta['devise']}.",
        f"- **Observations :** {number(quality['n_observations'])}, "
        f"{number(quality['quartiers'])} quartiers distincts, "
        f"{number(quality['paires_ville_quartier_type'])} triplets (ville, quartier, type).",
        "- **Features d'entrée :** "
        + ", ".join(f"`{column}`" for column in meta["features"])
        + ".",
        "- **Drapeaux qualité (jamais des features) :** "
        + ", ".join(f"`{column}`" for column in meta["drapeaux_qualite"])
        + ".",
        "",
        "### Qualité des données (aucune exclusion silencieuse)",
        "",
    ]

    lines += table(
        ["Marqueur", "Observations"],
        [
            ["Prix borné (borne inférieure, « à partir de »)", number(quality["prix_borne"])],
            ["Républication", number(quality["republications"])],
            ["Aberration signalée (`outlier_flags`)", number(quality["aberrations"])],
            ["Quartier non reconnu", number(quality["quartiers_non_reconnus"])],
            ["Chambres manquantes", number(quality["chambres_manquantes"])],
            ["Salles de bain manquantes", number(quality["salles_de_bain_manquantes"])],
        ],
    )
    lines += [
        "Ces marqueurs ne filtrent rien dans le scénario principal : ils décrivent le",
        "dataset et alimentent les scénarios de sensibilité.",
        "",
        "### Séparation entraînement / validation / test",
        "",
        "- Proportions : "
        + ", ".join(
            f"{number(share * 100)} % {SPLIT_LABELS[name]}"
            for name, share in meta["proportions"].items()
        )
        + f" — graine fixe `{meta['graine']}` (reproductible).",
        "- Séparation **aléatoire**, pas chronologique : "
        f"`posted_at` renseigné sur {number(chronology.get('posted_at_renseignes', 0))} "
        f"observation(s) et `collected_at` couvrant "
        f"{number(chronology['jours_de_collecte_distincts'])} journée(s) de collecte — "
        "aucune information temporelle exploitable.",
        "",
    ]

    lines += table(
        [
            "Ensemble",
            "Observations",
            "Part",
            "Douala",
            "Yaoundé",
            "Républications",
            "Prix bornés",
            "Aberrations",
        ],
        [
            [
                SPLIT_LABELS[name],
                number(block["n_observations"]),
                f"{number(block['part'], decimals=1)} %",
                number(block["par_ville"].get("Douala", 0)),
                number(block["par_ville"].get("Yaoundé", 0)),
                number(block["republications"]),
                number(block["prix_borne"]),
                number(block["aberrations"]),
            ]
            for name, block in primary["taille_par_ensemble"].items()
        ],
    )

    lines += ["### Baselines", ""]
    lines += table(
        ["Baseline", "Définition", "Groupes appris", "Repli"],
        [
            [
                f"`{name}`",
                block["definition"],
                number(block["parametres"].get("groupes")),
                f"`{block['parametres']['repli']}`" if block["parametres"].get("repli") else "—",
            ]
            for name, block in primary["baselines"].items()
        ],
    )
    lines += [
        "Une baseline de groupe ne connaît pas les groupes absents de l'entraînement : la",
        "chaîne de repli est explicite (quartier+type → ville+type → ville → moyenne",
        "globale) et la table des niveaux de prédiction montre quel niveau a servi.",
        "",
        "### Scénarios d'évaluation",
        "",
    ]
    lines += table(
        ["Scénario", "Description", "Observations"],
        [
            [
                f"`{name}`",
                scenario["description"],
                number(scenario["n_observations"]),
            ]
            for name, scenario in scenarios.items()
        ],
    )

    lines += ["## Résultats globaux", ""]
    for name, scenario in scenarios.items():
        lines.append(f"### `{name}` — {number(scenario['n_observations'])} observations")
        lines.append("")
        lines += _globaltable(scenario["baselines"])
        lines.append("Niveaux de prédiction utilisés en validation :")
        lines.append("")
        lines += _leveltable(scenario["baselines"], "validation")

    lines += ["### Robustesse : la MAE dépend-elle de l'échantillon ?", ""]
    lines += [
        "Les prix sont très asymétriques et les valeurs extrêmes sont conservées",
        "(aucune suppression). La MAE est donc sensible à la composition de l'ensemble,",
        "contrairement à l'erreur absolue médiane (MedAE) :",
        "",
    ]
    lines += _robustnesstable(scenarios)
    validation_metrics = best_block["metriques"]["validation"]
    test_metrics = best_block["metriques"]["test"]
    mae_gap = abs(gap_percent(validation_metrics["mae"], test_metrics["mae"]) or 0)
    medae_gap = abs(gap_percent(validation_metrics["medae"], test_metrics["medae"]) or 0)
    lines += [
        f"Pour la meilleure baseline (`{best}`), la MAE passe de "
        f"{number(validation_metrics['mae'])} FCFA en validation à "
        f"{number(test_metrics['mae'])} FCFA en test "
        f"({number(mae_gap, decimals=1)} % d'écart), alors que l'erreur médiane varie de "
        f"{number(medae_gap, decimals=1)} %.",
        "Conséquence : le seuil de référence est défini sur la MAE (métrique demandée par",
        "la spec), mais la Phase 6 devra confirmer le gain sur la MedAE et sur plusieurs",
        "graines, faute de quoi le gain ne serait pas démontré.",
        "",
        f"À noter également : {number(quality['prix_borne'])} observations sur "
        f"{number(quality['n_observations'])} n'ont qu'une borne inférieure de prix",
        "(« à partir de ») — la cible est donc approximative pour la majorité du dataset,",
        "ce que les scénarios de sensibilité quantifient.",
        "",
    ]

    lines += ["## Performance par segment (scénario principal)", ""]
    threshold_n = meta["effectif_minimum_par_segment"]
    lines.append(
        "Aucun segment n'est masqué : chaque MAE est accompagnée de son effectif ; "
        f"un `*` signale un segment sous le seuil de publication de {number(threshold_n)} "
        "observations (décision Phase 3) dont la MAE n'est pas robuste. "
        "`—` : segment absent de l'ensemble ; quartiers limités aux "
        f"{number(config.TOP_NEIGHBORHOODS)} plus volumineux."
    )
    lines.append("")
    baseline_headers = list(primary["baselines"])
    for family, title in SEGMENT_FAMILIES:
        limit = config.TOP_NEIGHBORHOODS if family == "quartier" else None
        for split_name in ("validation", "test"):
            rows, has_small = _segment_rows(
                primary["baselines"], split_name, family, limit=limit
            )
            lines.append(f"### {title} — {SPLIT_LABELS[split_name]}")
            lines.append("")
            lines += table(
                ["Segment", "N", *[f"MAE `{name}`" for name in baseline_headers]],
                rows,
            )
            if has_small:
                lines.append(
                    f"`*` effectif < {number(threshold_n)} : MAE à lire avec prudence."
                )
                lines.append("")

    lines += ["## Seuil de référence à battre", ""]
    lines += _thresholdtable(scenarios)
    lines += [
        "Règle de décision (appliquée en Phase 6) : un modèle ML n'est retenu que s'il",
        "ramène la MAE de **validation** sous la borne basse de l'intervalle de confiance",
        f"bootstrap à {confidence} % de la meilleure baseline, soit sous "
        f"**{number(threshold['mae_borne_basse_ic'])} FCFA** pour le scénario principal — "
        f"un gain d'au moins {number(threshold['gain_absolu_a_demontrer_fcfa'])} FCFA "
        f"({number(threshold['gain_relatif_a_demontrer_pct'], decimals=2)} %), **et** que la",
        "réduction se confirme sur le test. Un gain inférieur à cet intervalle n'est pas",
        f"distinguable du bruit d'échantillonnage (N validation = {number(validation_n)}).",
        "",
        "## Conclusion",
        "",
        f"- Meilleure baseline : `{best}` — MAE validation "
        f"{number(best_block['metriques']['validation']['mae'])} FCFA, MAE test "
        f"{number(best_block['metriques']['test']['mae'])} FCFA.",
        f"- Seuil à battre : **{number(threshold['mae_borne_basse_ic'])} FCFA** en "
        "validation (gain minimal exigé : "
        f"{number(threshold['gain_relatif_a_demontrer_pct'], decimals=2)} %).",
        "- Aucun modèle ML n'est entraîné à cette phase (hors périmètre) : la Phase 6 doit",
        "  démontrer ce gain, sinon la baseline reste la référence du produit.",
        "",
        "Segments les plus difficiles pour la meilleure baseline (MAE décroissante) :",
        "",
    ]
    lines += table(
        ["Famille", "Segment", "N", "MAE"],
        [
            [row["famille"], row["segment"], number(row["n"]), number(row["mae"])]
            for row in conclusion["segments_les_plus_difficiles"]
        ],
    )

    lines += [
        "## Limites connues",
        "",
        f"- **Prix censurés** : {number(quality['prix_borne'])} observations sur "
        f"{number(quality['n_observations'])} ne donnent qu'une borne inférieure "
        "(« à partir de ») ; la cible est alors approximative.",
        f"- **Républications** : {number(quality['republications'])} observations signalées, "
        "réparties aléatoirement entre les ensembles ; des annonces très proches peuvent",
        "apparaître en entraînement et en test, ce qui rend l'évaluation légèrement optimiste.",
        f"- **Quartiers non reconnus** : {number(quality['quartiers_non_reconnus'])} observations "
        "portent un libellé absent du référentiel ; elles restent évaluées.",
        f"- **Petits segments** : les quartiers sous "
        f"{number(meta['effectif_minimum_par_segment'])} observations ne sont pas publiés "
        "(aucune fusion silencieuse).",
        "- **Features absentes** : `area_m2`, `furnished`, `parking`, `gated` sont vides",
        "  dans le Silver : les baselines n'exploitent que ville, quartier, type, chambres",
        "  et salles de bain.",
        "- Une estimation n'est jamais une valeur officielle du bien (invariant 9).",
        "",
        "## Reproductibilité",
        "",
        "```bash",
        "python -m pipelines silver --report docs/phase-2/cleaning-report.md",
        "python -m pipelines load",
        "cd dbt && dbt build && cd ..",
        "python -m ml.src baselines",
        "```",
        "",
        f"Versions : Python {meta['versions']['python']}, pandas {meta['versions']['pandas']}, "
        f"numpy {meta['versions']['numpy']}, scikit-learn {meta['versions']['scikit_learn']} ; "
        f"graine `{meta['graine']}`, bootstrap {number(meta['iterations_bootstrap'])} itérations.",
        "",
    ]
    return "\n".join(lines)
