"""Configuration centrale de l'ingestion CamRent.

Aucun chemin ni identifiant n'est codé en dur ailleurs : tout passe par ce module
et, pour ce qui est sensible, par des variables d'environnement (AGENTS.md §9).

Le **registre des sources** (`SOURCES`) documente, pour chaque source, sa
catégorie de stockage, ses droits et la méthode de collecte. Les statuts de
droits déterminent si une confirmation légale explicite est exigée avant collecte
(invariant AGENTS.md : « aucune collecte automatisée sans vérification »).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Identité de collecte (User-Agent transparent). Surchargeable par variable d'env.
# ---------------------------------------------------------------------------
CONTACT_EMAIL: Final[str] = os.environ.get(
    "CAMRENT_CONTACT_EMAIL", "ibrahimtalla01@gmail.com"
)
USER_AGENT: Final[str] = (
    f"CamRentResearch/0.1 (data research; contact: {CONTACT_EMAIL})"
)

# ---------------------------------------------------------------------------
# Emplacements de sortie (le brut vit sous data/raw/, jamais écrasé)
# ---------------------------------------------------------------------------
DATA_ROOT: Final[Path] = Path(os.environ.get("CAMRENT_DATA_ROOT", PROJECT_ROOT / "data"))
RAW_ROOT: Final[Path] = DATA_ROOT / "raw"
SAMPLES_ROOT: Final[Path] = DATA_ROOT / "samples"

# ---------------------------------------------------------------------------
# Réseau / politesse
# ---------------------------------------------------------------------------
RATE_LIMIT_SECONDS: Final[float] = float(os.environ.get("CAMRENT_RATE_LIMIT", "2.0"))
REQUEST_TIMEOUT: Final[float] = float(os.environ.get("CAMRENT_REQUEST_TIMEOUT", "20.0"))
MAX_RETRIES: Final[int] = int(os.environ.get("CAMRENT_MAX_RETRIES", "3"))
RETRY_BACKOFF_SECONDS: Final[float] = 3.0

# Budget maximum de fetchs de DÉTAIL par page de listing : au-delà, les liens
# restants sont ignorés (débit borné, pas de charge excessive sur la source).
DETAIL_BUDGET_PER_PAGE: Final[int] = int(os.environ.get("CAMRENT_DETAIL_BUDGET", "20"))

# ---------------------------------------------------------------------------
# Catégories de stockage brut (spec Phase 1 §2)
# ---------------------------------------------------------------------------
CATEGORY_LISTINGS: Final[str] = "listings"
CATEGORY_REFERENCE: Final[str] = "reference_data"
CATEGORY_SUBMISSIONS: Final[str] = "user_submissions"
CATEGORY_METADATA: Final[str] = "metadata"

STORAGE_CATEGORIES: Final[tuple[str, ...]] = (
    CATEGORY_LISTINGS,
    CATEGORY_REFERENCE,
    CATEGORY_SUBMISSIONS,
)

# ---------------------------------------------------------------------------
# Statuts de droits
# ---------------------------------------------------------------------------
RIGHTS_VERIFIED: Final[str] = "verified"      # droits clairs, collecte directe
RIGHTS_UNCERTAIN: Final[str] = "uncertain"    # confirmation légale requise
RIGHTS_RESTRICTED: Final[str] = "restricted"  # collecte interdite/régulée

RIGHTS_HELP: Final[str] = (
    "Les sources 'uncertain' et 'restricted' exigent --confirm-legal après "
    "vérification des CGU/robots.txt ; les sources 'verified' et 'local' n'en exigent pas."
)

# Un document brut est considéré « frais » si sa collecte a moins de N jours.
FRESHNESS_MAX_DAYS: Final[int] = int(os.environ.get("CAMRENT_FRESHNESS_DAYS", "7"))

# Un lot est jugé anormalement petit (avertissement Bronze) sous ce seuil.
MIN_REASONABLE_RECORDS: Final[int] = int(os.environ.get("CAMRENT_MIN_RECORDS", "1"))


@dataclass(frozen=True)
class SourceSpec:
    """Description d'une source : catégorie de stockage, droits, méthode."""

    name: str
    category: str
    method: str
    rights: str
    rights_notice: str
    urls: tuple[str, ...]
    needs_network: bool = True
    enabled: bool = True

    @property
    def requires_confirm(self) -> bool:
        """Une confirmation légale est-elle exigée avant collecte ?"""
        return self.needs_network and self.rights not in (
            RIGHTS_VERIFIED,
            "local",
        )


# ---------------------------------------------------------------------------
# Registre des sources (vérifications légales : voir docs/phase-1/legal-review.md)
# ---------------------------------------------------------------------------
SOURCES: Final[dict[str, SourceSpec]] = {
    "geloka": SourceSpec(
        name="geloka",
        category=CATEGORY_REFERENCE,
        method="http_get_html_parse",
        rights=RIGHTS_UNCERTAIN,
        rights_notice=(
            "Baromètre agrégé : la page annonce une réutilisation « citation + lien », "
            "mais les CGU générales restreignent la copie/redistribution (usage personnel "
            "non commercial). N'utiliser que les agrégats, avec citation ; ne pas "
            "redistribuer le contenu."
        ),
        urls=("https://www.geloka.com/fr/rent-barometer",),
    ),
    "koutchoumi": SourceSpec(
        name="koutchoumi",
        category=CATEGORY_LISTINGS,
        method="http_get_html_parse",
        rights=RIGHTS_UNCERTAIN,
        rights_notice=(
            "Aucune CGU/ToS publiée (vérifié le 2026-10-09) ; robots.txt sans règle "
            "active (directives commentées). Collecte prudente : débit limité, aucune "
            "donnée personnelle, usage recherche, pas de redistribution brute."
        ),
        urls=("https://www.koutchoumi.com/en/main/showResults",),
    ),
    "reference_local": SourceSpec(
        name="reference_local",
        category=CATEGORY_REFERENCE,
        method="local_csv_read",
        rights="local",
        rights_notice=(
            "Jeu tiers `deegeorgie` sans licence déclarée : usage local uniquement, "
            "non redistribué (cf. docs/phase-0/legal-assessment.md)."
        ),
        urls=(),
        needs_network=False,
    ),
    "minfi_open_data": SourceSpec(
        name="minfi_open_data",
        category=CATEGORY_REFERENCE,
        method="http_get_raw_document",
        rights=RIGHTS_UNCERTAIN,
        rights_notice=(
            "Portail open data officiel (MINFI). Endpoints à valider au premier run ; "
            "on stocke le document brut sans le parser."
        ),
        urls=("https://mof-cameroon.opendataforafrica.org/",),
    ),
    "ins_cameroon": SourceSpec(
        name="ins_cameroon",
        category=CATEGORY_REFERENCE,
        method="http_get_raw_document",
        rights=RIGHTS_UNCERTAIN,
        rights_notice=(
            "Statistiques officielles INS ; accès détaillé sur demande. On stocke le "
            "document brut, sans parsing, en attendant un accès formel."
        ),
        urls=("https://statistics-cameroon.org/",),
    ),
}
