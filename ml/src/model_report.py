"""Rendu markdown du rapport de modèles (Phase 6).

Comme pour la Phase 5, le rendu est **purement dérivé** de la structure produite
par `run_models.build_results` : les chiffres cités viennent tous du calcul, ce
qui permet de rejouer la phase sans réécrire le rapport.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import config
from .markdown import number, table

SPLIT_LABELS = {"train": "entraînement", "validation": "validation", "test": "test"}
SEGMENT_TITLES = (
    ("ville", "Ville"),
    ("type_de_logement", "Type de logement"),
    ("nombre_de_chambres", "Nombre de chambres"),
    ("niveau_de_prix", "Niveau de prix (quartiles d'entraînement)"),
    ("quartier", "Quartier (ville / quartier)"),
)


def _display_path(path: Any) -> str:
    """Chemin affiché relativement au dépôt (le rapport est versionné)."""
    try:
        return str(Path(path).resolve().relative_to(config.PROJECT_ROOT))
    except ValueError:
        return str(path)


def _candidate_table(selection: dict[str, Any]) -> list[str]:
    headers = [
        "Candidat",
        "Famille",
        "Cible",
        "MAE entraînement",
        "MAE validation",
        "MedAE validation",
        "MAE test",
        "Temps d'entraînement",
    ]
    rows = [
        [
            f"`{row['slug']}`",
            row["famille"],
            row["cible"],
            number(row["mae_train"]),
            number(row["mae_validation"]),
            number(row["medae_validation"]),
            number(row["mae_test"]),
            f"{number(row['entrainement_s'], decimals=2)} s",
        ]
        for row in selection["classement"]
    ]
    return table(headers, rows)


def _baseline_table(baselines: dict[str, Any], threshold: dict[str, Any]) -> list[str]:
    headers = [
        "Baseline",
        "Définition",
        "MAE validation",
        "MedAE validation",
        "MAE test",
        "IC 95 % MAE validation",
    ]
    rows = [
        [
            f"`{name}`",
            block["definition"],
            number(block["metriques"]["validation"]["mae"]),
            number(block["metriques"]["validation"]["medae"]),
            number(block["metriques"]["test"]["mae"]),
            (
                f"{number(block['ic_mae_validation']['mae_borne_basse'])} – "
                f"{number(block['ic_mae_validation']['mae_borne_haute'])}"
            ),
        ]
        for name, block in baselines.items()
    ]
    rows.append(
        [
            "**seuil à battre**",
            f"borne basse de l'IC de `{threshold['baseline']}`",
            number(threshold["mae_borne_basse_ic"]),
            "—",
            "—",
            "—",
        ]
    )
    return table(headers, rows)


def _robustness_table(robustness: dict[str, Any]) -> list[str]:
    headers = [
        "Candidat",
        "Graines évaluées",
        "MAE validation moyenne",
        "MAE validation min",
        "MAE validation max",
        "Gain médian vs baseline",
        "Gain moyen vs baseline",
        "Gain minimal",
        "Baseline battue sur",
        "Seuil battu sur",
    ]
    rows = [
        [
            f"`{slug}`",
            ", ".join(str(seed) for seed in block["graines"]),
            number(block["mae_validation_moyenne"]),
            number(block["mae_validation_min"]),
            number(block["mae_validation_max"]),
            f"**{number(block['gain_validation_median_pct'], decimals=2)} %**",
            f"{number(block['gain_validation_moyen_pct'], decimals=2)} %",
            f"{number(block['gain_validation_min_pct'], decimals=2)} %",
            f"{number(block['nb_graines_battant_la_baseline'])} / {number(block['nb_graines'])}",
            f"{number(block['nb_graines_battant_le_seuil'])} / {number(block['nb_graines'])}",
        ]
        for slug, block in robustness.items()
    ]
    return table(headers, rows)


def _segment_lines(segments: dict[str, Any], *, threshold_n: int) -> list[str]:
    lines: list[str] = []
    for family, title in SEGMENT_TITLES:
        limit = config.TOP_NEIGHBORHOODS if family == "quartier" else None
        for split_name in ("validation", "test"):
            records = segments[split_name][family]
            if limit is not None:
                records = records[:limit]
            lines.append(f"### {title} — {SPLIT_LABELS[split_name]}")
            lines.append("")
            rows: list[list[str]] = []
            has_small = False
            for record in records:
                label_column = next(iter(record))
                marker = " *" if record["sous_seuil_de_publication"] else ""
                has_small = has_small or record["sous_seuil_de_publication"]
                rows.append(
                    [
                        f"{record[label_column]}{marker}",
                        number(record["n"]),
                        number(record["mae"]),
                        number(record["medae"]),
                        number(record["r2"], decimals=3),
                    ]
                )
            lines += table(["Segment", "N", "MAE", "MedAE", "R²"], rows)
            if has_small:
                lines.append(f"`*` effectif < {number(threshold_n)} : à lire avec prudence.")
                lines.append("")
    return lines


def _interval_table(intervals: dict[str, Any]) -> list[str]:
    headers = [
        "Méthode",
        "Couverture validation",
        "Largeur médiane validation",
        "Largeur moyenne validation",
        "Couverture test",
        "Largeur médiane test",
        "Largeur moyenne test",
    ]
    rows = [
        [
            f"`{name}`",
            f"{number(block['validation']['couverture_pct'], decimals=1)} %",
            number(block["validation"]["largeur_mediane"]),
            number(block["validation"]["largeur_moyenne"]),
            f"{number(block['test']['couverture_pct'], decimals=1)} %",
            number(block["test"]["largeur_mediane"]),
            number(block["test"]["largeur_moyenne"]),
        ]
        for name, block in intervals["methodes"].items()
    ]
    return table(headers, rows)


def _importance_table(rows: list[dict[str, Any]]) -> list[str]:
    headers = [
        "Feature",
        "N",
        "Erreur médiane supplémentaire",
        "Écart-type",
        "Min",
        "Max",
    ]
    return table(
        headers,
        [
            [
                f"`{row['feature']}`",
                number(row["n"]),
                number(row["erreur_mediane_supplementaire_moyenne"]),
                number(row["erreur_mediane_supplementaire_ecart_type"]),
                number(row["erreur_mediane_supplementaire_min"]),
                number(row["erreur_mediane_supplementaire_max"]),
            ]
            for row in rows
        ],
    )


def _dependence_table(rows: list[dict[str, Any]]) -> list[str]:
    headers = ["Valeur", "N", "Prévision moyenne", "Prévision médiane"]
    return table(
        headers,
        [
            [
                number(row["valeur"], decimals=2),
                number(row["n"]),
                number(row["prediction_moyenne"]),
                number(row["prediction_mediane"]),
            ]
            for row in rows
        ],
    )


def render_report(results: dict[str, Any], *, generated_at: str) -> str:
    """Rend le rapport markdown complet de la Phase 6."""
    meta = results["meta"]
    quality = meta["qualite"]
    threshold = results["seuil_reference"]
    selection = results["selection"]
    retained = results["candidats"][selection["slug"]]
    errors = results["erreurs_test"]
    intervals = results["intervalles"]
    retained_interval = intervals["methodes"][intervals["methode_retenue"]]
    example = results["explicabilite"]["exemple"]
    dependence = results["explicabilite"]["dependance_partielle"]
    best_baseline = results["baselines"][threshold["baseline"]]

    lines: list[str] = [
        "# Phase 6 — Rapport des modèles (ML)",
        "",
        f"**Généré le :** {generated_at}",
        "",
        "Objectif : tester les familles de modèles dans l'ordre recommandé et retenir",
        "celui qui bat la baseline de la Phase 5 de façon **vérifiable**, en tenant",
        "compte de la précision, de la robustesse, de l'interprétabilité et du coût.",
        "",
        "## Protocole",
        "",
        f"- **Source :** `{meta['source']}` (Phases 4-5), cible `{meta['cible']}` en "
        f"{meta['devise']} ; {number(quality['n_observations'])} observations.",
        f"- **Séparation :** identique à la Phase 5 — 70 % / 15 % / 15 %, graine "
        f"`{meta['graine']}` (séparation chronologique impossible : `posted_at` vide, "
        "collecte sur une seule journée).",
        "- **Features :** "
        + ", ".join(f"`{feature}`" for feature in meta["features"])
        + ".",
        "- **Cible transformée :** chaque famille est testée sur la cible brute et sur",
        "  `log1p(cible)` : la distribution des loyers est très asymétrique (Phase 3),",
        "  l'effet de la transformation doit donc être mesuré, pas supposé.",
        "- **Échelle d'apprentissage :** la cible brute est apprise en **milliers de FCFA**",
        "  (sinon une pénalité `alpha` serait négligeable face à des loyers de l'ordre de",
        "  240 000 FCFA) ; prévisions et métriques sont reconverties en FCFA, donc la",
        "  comparaison avec la baseline reste directe.",
        "- **Hyperparamètres :** valeurs raisonnables **fixées**, aucune recherche — la",
        "  phase compare des familles, elle n'optimise pas.",
        "- **Métriques :** MAE (principale, en FCFA), RMSE, R², MedAE (robustesse),",
        "  temps d'entraînement, performance par segment (toujours avec son effectif).",
        "",
        "### Features écartées et pourquoi",
        "",
    ]
    lines += table(
        ["Feature", "Raison de l'exclusion"],
        [[f"`{name}`", reason] for name, reason in meta["features_ecartees"].items()],
    )

    lines += ["## Seuil de référence à battre (recalculé sur cette séparation)", ""]
    lines += _baseline_table(results["baselines"], threshold)
    lines += [
        "Règle héritée de la Phase 5 : battre la borne basse de l'intervalle de confiance",
        f"à 95 % de la MAE de la meilleure baseline, soit "
        f"**{number(threshold['mae_borne_basse_ic'])} FCFA** en validation "
        f"({number(threshold['gain_relatif_a_demontrer_pct'], decimals=2)} % de mieux que "
        f"`{threshold['baseline']}`).",
        "",
        "## Comparaison des candidats",
        "",
    ]
    lines += _candidate_table(selection)
    lines += [
        "Lecture : `brut` = cible brute, `log1p` = cible transformée. Le classement suit la",
        "MAE de validation (métrique de décision).",
        "",
        "## Modèle retenu",
        "",
        f"- **`{selection['slug']}`** — {retained['famille']}, "
        f"cible {retained['cible_transformee']}.",
        f"- Critère appliqué : {selection['critere_selection']}",
        "- Présélection (MAE de la graine de référence) : "
        + ", ".join(f"`{slug}`" for slug in selection["preselection"])
        + ".",
        f"- Rang du modèle retenu sur la graine de référence : "
        f"{number(selection['rang_graine_reference'])} (le classement d'une seule "
        "séparation ne décide pas).",
        f"- MAE validation **{number(selection['mae_validation'])} FCFA** "
        f"(MedAE {number(selection['medae_validation'])}) ; MAE test "
        f"{number(selection['mae_test'])} FCFA (MedAE {number(selection['medae_test'])}).",
        "- Gain face à la meilleure baseline : "
        f"**{number(selection['gain_vs_baseline_pct'], decimals=2)} %** en validation "
        f"(baseline `{threshold['baseline']}` : {number(threshold['mae_validation'])} FCFA).",
        f"- Seuil {'**battu**' if selection['bat_le_seuil_validation'] else '**NON battu**'} "
        f"sur la graine de référence ({number(threshold['mae_borne_basse_ic'])} FCFA).",
        f"- Baseline battue sur "
        f"**{number(selection['robustesse']['nb_graines_battant_la_baseline'])} / "
        f"{number(selection['robustesse']['nb_graines'])}** graines de robustesse "
        f"(seuil battu sur "
        f"{number(selection['robustesse']['nb_graines_battant_le_seuil'])} / "
        f"{number(selection['robustesse']['nb_graines'])}) — gain **médian** "
        f"{number(selection['robustesse']['gain_validation_median_pct'], decimals=2)} %, "
        f"gain moyen {number(selection['robustesse']['gain_validation_moyen_pct'], decimals=2)} %, "
        f"gain minimal {number(selection['robustesse']['gain_validation_min_pct'], decimals=2)} %.",
        "",
    ]
    lines += table(
        ["Ensemble", "N", "MAE", "RMSE", "R²", "MedAE", "p90 des erreurs"],
        [
            [
                SPLIT_LABELS[name],
                number(retained["metriques"][name]["n"]),
                number(retained["metriques"][name]["mae"]),
                number(retained["metriques"][name]["rmse"]),
                number(retained["metriques"][name]["r2"], decimals=3),
                number(retained["metriques"][name]["medae"]),
                number(retained["metriques"][name]["erreur_absolue_p90"]),
            ]
            for name in ("train", "validation", "test")
        ],
    )
    lines += [
        f"Lecture produit (test) : {number(errors['part_a_moins_de_20_pct'], decimals=1)} % des",
        "prévisions tombent à ±20 % du loyer observé.",
        "",
        "## Robustesse (autres séparations)",
        "",
        "La Phase 5 a montré que la MAE est instable sous cette distribution : le",
        "classement sur une seule séparation est donc du bruit. Les candidats",
        "présélectionnés sont réévalués sur "
        f"{number(len(results['meta']['graines_robustesse']))} graines ; le **gain médian** "
        "face à la baseline recalculée sur chaque graine décide.",
        "",
    ]
    lines += _robustness_table(results["robustesse"])
    lines += [
        "Le seuil est recalculé sur **chaque** graine : sans cela, on comparerait des",
        "découpages de données plutôt que des modèles.",
        "",
        f"- Meilleure baseline sur la graine de référence : "
        f"{number(best_baseline['metriques']['validation']['mae'])} FCFA en validation "
        f"({number(best_baseline['metriques']['test']['mae'])} en test).",
        "",
        "## Performance par segment (modèle retenu)",
        "",
        "Aucun segment n'est masqué : un `*` signale un effectif inférieur à "
        f"{number(meta['effectif_minimum_par_segment'])} observations "
        "(seuil de publication de la Phase 3).",
        "",
    ]
    lines += _segment_lines(
        results["segments"], threshold_n=meta["effectif_minimum_par_segment"]
    )

    lines += ["## Fourchette de prédiction", ""]
    lines += _interval_table(intervals)
    lines += [
        f"Niveau visé : **{number(intervals['niveau_vise_pct'])} %** "
        f"(alpha = {intervals['alpha']}). "
        f"Méthode retenue : `{intervals['methode_retenue']}`.",
        "",
        intervals["justification"],
        "",
        "- Couverture observée en test : "
        f"{number(retained_interval['test']['couverture_pct'], decimals=1)} % "
        "(validation : "
        f"{number(retained_interval['validation']['couverture_pct'], decimals=1)} %).",
        f"- Largeur moyenne en test : {number(retained_interval['test']['largeur_moyenne'])} FCFA "
        f"(médiane {number(retained_interval['test']['largeur_mediane'])} FCFA).",
        "",
        "## Explicabilité",
        "",
        "### Importance globale des facteurs (validation)",
        "",
        "Augmentation de l'**erreur médiane** lorsque la variable est permutée : plus la",
        "valeur est élevée, plus le modèle s'appuie sur la variable. Cette mesure",
        "remplace l'importance sur la MAE, qui devient instable — voire négative — dès",
        "que quelques loyers extrêmes conservés dominent l'erreur moyenne.",
        "",
    ]
    lines += _importance_table(results["explicabilite"]["importance_globale"])
    lines += [
        "### Effet du nombre de chambres (dépendance partielle, test)",
        "",
    ]
    lines += _dependence_table(dependence["bedrooms"])
    lines += [
        "### Effet du nombre de salles de bain (dépendance partielle, test)",
        "",
    ]
    lines += _dependence_table(dependence["bathrooms"])
    lines += [
        "### Exemple expliqué (« pourquoi ce prix ? »)",
        "",
        f"- Annonce : {example['caracteristiques']['quartier']} "
        f"({example['caracteristiques']['ville']}), "
        f"{example['caracteristiques']['type_de_logement']}, "
        f"{number(example['caracteristiques']['chambres'])} chambre(s), "
        f"{number(example['caracteristiques']['salles_de_bain'])} salle(s) de bain.",
        f"- Prévision : **{number(example['prevision'])} FCFA** (fourchette "
        f"{number(example['intervalle'][0])} – {number(example['intervalle'][1])} FCFA).",
        f"- Loyer observé dans l'annonce : {number(example['loyer_observe'])} FCFA.",
        f"- Marché local (entraînement) : médiane "
        f"**{number(example['marche_local']['mediane_quartier_type'])} FCFA** sur "
        f"{number(example['marche_local']['n_quartier_type'])} observation(s) de ce "
        f"(quartier, type) — publiée : "
        f"{'oui' if example['marche_local']['publiee'] else 'non (sous le seuil)'} ; "
        f"médiane ville {number(example['marche_local']['mediane_ville'])} FCFA "
        f"sur {number(example['marche_local']['n_ville'])} observations.",
        f"- Écart de la prévision à la médiane locale : "
        f"{number(example.get('ecart_vs_mediane_quartier_pct'), decimals=2)} %.",
        "",
        "## Compromis par famille",
        "",
    ]
    lines += table(
        [
            "Candidat",
            "Famille",
            "Complexité",
            "Interprétabilité",
            "MAE validation",
            "Temps d'entraînement",
        ],
        [
            [
                f"`{row['slug']}`",
                row["famille"],
                results["candidats"][row["slug"]]["complexite"],
                results["candidats"][row["slug"]]["interpretabilite"],
                number(row["mae_validation"]),
                f"{number(row['entrainement_s'], decimals=2)} s",
            ]
            for row in selection["classement"]
        ],
    )

    lines += [
        "## Limites du modèle",
        "",
        f"- **Cible approximative pour {number(quality['prix_borne'])} observations sur "
        f"{number(quality['n_observations'])}** : ces annonces ne donnent qu'une borne",
        "  inférieure de prix (« à partir de ») ; aucune méthode ne peut corriger cela.",
        f"- **Républications** : {number(quality['republications'])} observations signalées,",
        "  réparties aléatoirement — des annonces quasi identiques peuvent se retrouver",
        "  en entraînement et en test, ce qui rend l'évaluation optimiste.",
        f"- **Quartiers non reconnus** : {number(quality['quartiers_non_reconnus'])} observations",
        "  portent un libellé hors référentiel ; le modèle s'appuie alors sur la ville et le",
        "  type (profondeur de marché nulle pour ces quartiers).",
        "- **Features indisponibles** : surface, meublé, parking, barrière (vides dans le",
        "  Silver) et coordonnées géographiques (absentes) : la précision est plafonnée par",
        "  l'information collectée, pas par le choix du modèle.",
        "- **Hyperparamètres non optimisés** : une recherche systématique (et son suivi",
        "  MLflow) relève de la Phase 7.",
        "- **MAE instable** : la borne basse de l'IC bootstrap sert de seuil ; les décisions",
        "  produit ne doivent pas être prises sur une différence inférieure à cette marge.",
        "- Une estimation n'est jamais une valeur officielle du bien (invariant 9) et doit",
        "  toujours être présentée avec sa fourchette et le nombre d'observations local.",
        "",
        "## Reproductibilité",
        "",
        "```bash",
        "python -m pipelines silver --report docs/phase-2/cleaning-report.md",
        "python -m pipelines load",
        "cd dbt && dbt build && cd ..",
        "python -m ml.src baselines",
        "python -m ml.src models",
        "```",
        "",
        f"Versions : Python {meta['versions']['python']}, scikit-learn "
        f"{meta['versions']['scikit_learn']}, pandas {meta['versions']['pandas']}, "
        f"numpy {meta['versions']['numpy']}, "
        f"LightGBM {meta['versions'].get('lightgbm', 'absent')} ; graines de robustesse "
        f"{', '.join(str(seed) for seed in meta['graines_robustesse'])}.",
        "",
        "Artefacts (ignorés par git, régénérables) :",
        "",
    ]
    artifacts = results.get("artefacts", {})
    if artifacts:
        lines += table(
            ["Artefact", "Chemin"],
            [[name, f"`{_display_path(path)}`"] for name, path in artifacts.items()],
        )
    else:
        lines += ["- Aucun artefact de modèle écrit (exécution sans persistance).", ""]
    return "\n".join(lines)
