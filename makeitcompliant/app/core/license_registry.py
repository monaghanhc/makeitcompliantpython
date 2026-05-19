"""Map SPDX strings, manifest values, and classifier names to Prolog license atoms."""

from __future__ import annotations

import re

# Prolog atom -> human display name
LICENSE_DISPLAY: dict[str, str] = {
    "mit": "MIT License",
    "apache_2_0": "Apache License 2.0",
    "bsd_2_clause": "BSD 2-Clause Simplified License",
    "bsd_3_clause": "BSD 3-Clause New or Revised License",
    "gpl_2_0": "GNU General Public License v2.0",
    "gpl_3_0": "GNU General Public License v3.0",
    "lgpl_2_1": "GNU Lesser General Public License v2.1",
    "lgpl_3_0": "GNU Lesser General Public License v3.0",
    "agpl_3_0": "GNU Affero General Public License v3.0",
    "mpl_2_0": "Mozilla Public License 2.0",
    "eclipse_2_0": "Eclipse Public License 2.0",
    "unlicense": "The Unlicense",
    "isc": "ISC License",
    "postgresql": "PostgreSQL License",
    "zlib": "zlib License",
    "proprietary": "Proprietary",
    "unknown": "Unknown",
}

# Classifier / template display name -> atom
_DISPLAY_TO_ATOM: dict[str, str] = {
    v.lower(): k for k, v in LICENSE_DISPLAY.items()
}
_DISPLAY_TO_ATOM.update(
    {
        "mit license": "mit",
        "apache license 2.0": "apache_2_0",
        "bsd 2-clause simplified license": "bsd_2_clause",
        "bsd 3-clause new or revised license": "bsd_3_clause",
        "gnu general public license v2.0": "gpl_2_0",
        "gnu general public license v3.0": "gpl_3_0",
        "gnu lesser general public license v2.1": "lgpl_2_1",
        "gnu lesser general public license v3.0": "lgpl_3_0",
        "gnu affero general public license v3.0": "agpl_3_0",
        "mozilla public license 2.0": "mpl_2_0",
        "eclipse public license 2.0": "eclipse_2_0",
        "the unlicense": "unlicense",
        "isc license": "isc",
        "postgresql license": "postgresql",
        "zlib license": "zlib",
    }
)

_SPDX_TO_ATOM: dict[str, str] = {
    "mit": "mit",
    "apache-2.0": "apache_2_0",
    "apache-2": "apache_2_0",
    "bsd-2-clause": "bsd_2_clause",
    "bsd-3-clause": "bsd_3_clause",
    "gpl-2.0": "gpl_2_0",
    "gpl-2.0-only": "gpl_2_0",
    "gpl-2.0-or-later": "gpl_2_0",
    "gpl-3.0": "gpl_3_0",
    "gpl-3.0-only": "gpl_3_0",
    "gpl-3.0-or-later": "gpl_3_0",
    "lgpl-2.1": "lgpl_2_1",
    "lgpl-2.1-only": "lgpl_2_1",
    "lgpl-3.0": "lgpl_3_0",
    "lgpl-3.0-only": "lgpl_3_0",
    "agpl-3.0": "agpl_3_0",
    "agpl-3.0-only": "agpl_3_0",
    "mpl-2.0": "mpl_2_0",
    "epl-2.0": "eclipse_2_0",
    "unlicense": "unlicense",
    "isc": "isc",
    "postgresql": "postgresql",
    "zlib": "zlib",
    "proprietary": "proprietary",
}

_SPDX_RE = re.compile(
    r"SPDX-License-Identifier:\s*([A-Za-z0-9.-]+)",
    re.IGNORECASE,
)

_OBLIGATION_LABELS: dict[str, str] = {
    "include_copyright_notice": "Include copyright and permission notice",
    "include_license_text": "Include a copy of the license text",
    "preserve_notice": "Preserve legal notices in source distributions",
    "state_changes": "Document modifications you make",
    "patent_grant_notice": "Include patent grant / retaliation notice (Apache 2.0)",
    "disclose_source_on_distribution": "Disclose source when distributing binaries",
    "same_license_for_derivatives": "License derivatives under the same license",
    "disclose_source_for_lgpl_components": "Provide LGPL component source",
    "allow_library_relinking": "Allow user to relink LGPL library",
    "network_use_triggers_source_offer": "Offer source to network users (AGPL)",
    "weak_copyleft_file_scope": "Share modifications to MPL-covered files",
    "weak_copyleft_module_scope": "Comply with Eclipse copyleft module rules",
    "no_redistribution_without_permission": "No redistribution without permission",
    "commercial_license_required": "Obtain a commercial license",
    "manual_license_review_required": "Manually review unknown license",
    "patent_retaliation_clause": "Comply with patent retaliation terms",
}


def normalize_spdx(value: str) -> str:
    return value.strip().replace(" ", "-").upper()


def spdx_to_atom(spdx: str) -> str | None:
    key = spdx.strip().lower()
    return _SPDX_TO_ATOM.get(key)


def display_name_to_atom(name: str) -> str | None:
    key = name.strip().lower()
    if key in _DISPLAY_TO_ATOM:
        return _DISPLAY_TO_ATOM[key]
    return spdx_to_atom(key)


def manifest_value_to_atom(value: str) -> str | None:
    """Parse package.json / pyproject license fields."""
    raw = value.strip()
    if not raw:
        return None
    if raw.upper().startswith("SEE LICENSE"):
        return None
    if raw.lower() in ("proprietary", "unlicensed"):
        return "proprietary"
    atom = spdx_to_atom(raw) or display_name_to_atom(raw)
    if atom:
        return atom
    # MIT, Apache-2.0 without normalization
    return spdx_to_atom(normalize_spdx(raw).lower()) or display_name_to_atom(raw)


def extract_spdx_from_text(text: str) -> str | None:
    match = _SPDX_RE.search(text)
    if match:
        return spdx_to_atom(match.group(1))
    return None


def atom_to_display(atom: str) -> str:
    return LICENSE_DISPLAY.get(atom, atom.replace("_", " ").title())


def obligation_label(atom: str) -> str:
    return _OBLIGATION_LABELS.get(atom, atom.replace("_", " ").capitalize())


def conflict_reason_label(reason: str) -> str:
    labels = {
        "strong_copyleft_in_permissive_project": (
            "Strong copyleft dependency in a permissive-licensed project "
            "may infect distribution if combined into one work."
        ),
        "permissive_in_strong_copyleft_violation": (
            "Combining permissive-only dependency terms with a GPL-family "
            "project may fail GPL compliance for the combined work."
        ),
        "agpl_network_obligation_conflict": (
            "AGPL dependency may require offering source to network users."
        ),
        "proprietary_dependency_blocked": (
            "Proprietary dependency cannot be used in an open-source project "
            "without explicit permission."
        ),
        "unknown_dependency_requires_review": (
            "Dependency license is unknown — manual review required."
        ),
        "proprietary_project_blocks_copyleft": (
            "Copyleft dependency conflicts with proprietary project licensing."
        ),
    }
    return labels.get(reason, reason.replace("_", " "))
