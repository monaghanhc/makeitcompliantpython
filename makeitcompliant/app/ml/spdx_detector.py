"""Fast SPDX identifier detection (first stage of license detection)."""

from __future__ import annotations

import re

from makeitcompliant.app.core.license_registry import extract_spdx_from_text, spdx_to_atom

_SPDX_LINE = re.compile(
    r"SPDX-License-Identifier:\s*([A-Za-z0-9.-]+)",
    re.IGNORECASE,
)
_LICENSE_LINE = re.compile(
    r"^License:\s*([A-Za-z0-9.\s-]+)$",
    re.IGNORECASE | re.MULTILINE,
)


def detect_spdx_in_text(text: str) -> tuple[str, str] | None:
    """
    Return (spdx_id, prolog_atom) if an SPDX identifier is found.
    """
    match = _SPDX_LINE.search(text)
    if match:
        spdx = match.group(1).strip()
        atom = spdx_to_atom(spdx)
        if atom:
            return spdx, atom
    atom = extract_spdx_from_text(text)
    if atom:
        return spdx_from_atom(atom), atom
    lic = _LICENSE_LINE.search(text)
    if lic:
        spdx = lic.group(1).strip()
        atom = spdx_to_atom(spdx.replace(" ", "-"))
        if atom:
            return spdx, atom
    return None


def spdx_from_atom(atom: str) -> str:
    mapping = {
        "mit": "MIT",
        "apache_2_0": "Apache-2.0",
        "gpl_2_0": "GPL-2.0-only",
        "gpl_3_0": "GPL-3.0-only",
        "lgpl_2_1": "LGPL-2.1-only",
        "lgpl_3_0": "LGPL-3.0-only",
        "agpl_3_0": "AGPL-3.0-only",
        "bsd_2_clause": "BSD-2-Clause",
        "bsd_3_clause": "BSD-3-Clause",
        "mpl_2_0": "MPL-2.0",
        "isc": "ISC",
        "unlicense": "Unlicense",
    }
    return mapping.get(atom, atom)
