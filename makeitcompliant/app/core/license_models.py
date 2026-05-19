"""License identifiers and human-readable fact descriptions."""

from __future__ import annotations

# Map template filename stems (without .txt) to Prolog KB license names.
_TEMPLATE_TO_PROLOG: dict[str, str] = {
    "University of Illinios-NCSA Open Source License": (
        "University of Illinois-NCSA Open Source License"
    ),
    "CERN Open Hardware Licence Version 2 - Permissive": (
        "CERN Open Hardware License Version 2 - Permissive"
    ),
    "CERN Open Hardware Licence Version 2 - Strongly Reciprocal": (
        "CERN Open Hardware License Version 2 - Strongly Reciprocal"
    ),
    "CERN Open Hardware Licence Version 2 - Weakly Reciprocal": (
        "CERN Open Hardware License Version 2 - Weakly Reciprocal"
    ),
    "European Union Public Licence 1.1": "European Union Public License 1.1",
}

_FACT_DESCRIPTIONS: dict[str, str] = {
    "can_use_commercially": (
        "You can use the software licensed under this license commercially"
    ),
    "can_distribute": (
        "You can distribute the software licensed under this license "
        "without any additional conditions"
    ),
    "can_modify": (
        "You can modify the software licensed under this license "
        "without any additional conditions"
    ),
    "can_use_privately": (
        "You can use the software licensed under this license privately"
    ),
    "patent_use": (
        "You can use the patent of the software licensed under this license"
    ),
    "disclose_source_code": (
        "When distributing the software licensed under this license, "
        "you must disclose the source code"
    ),
    "copyright_license_with_source_code": (
        "You must include a copy of this license and copyright notice with the "
        "source code when distributing software licensed under this license"
    ),
    "copyright_license_with_binaries": (
        "You must include a copy of this license and copyright notice with the "
        "binaries when distributing software licensed under this license"
    ),
    "network_use_is_distribution": (
        "Users who interact with the licensed software over a network should be "
        "able to obtain a copy of the source code"
    ),
    "same_license": (
        "Any modifications of the licensed code must be distributed under the same "
        "license. With some licenses, a similar license is acceptable"
    ),
    "same_license_modded_files": (
        "Any modifications of existing files must be distributed under the same "
        "license. With some licenses, a similar license is acceptable"
    ),
    "same_license_library": (
        "Any modifications of the licensed code must be distributed under the same "
        "license. With some licenses, a similar license is acceptable, or may not "
        "apply for software that uses the licensed software as a library"
    ),
    "document_changes": (
        "You must document any changes you make to the licensed software"
    ),
    "liability": "The license includes a limitation of liability",
    "l_patent_use": (
        "You can't use the patent of the software licensed under this license"
    ),
    "warranty": "No warranty is provided",
    "trademark_use": (
        "You can't use the trademark of the software licensed under this license"
    ),
}


def template_stem(filename: str) -> str:
    name = filename
    if name.lower().endswith(".txt"):
        name = name[:-4]
    return name


def normalize_template_name_to_prolog(filename: str) -> str:
    stem = template_stem(filename)
    return _TEMPLATE_TO_PROLOG.get(stem, stem)


def describe_fact(prolog_fact_header: str) -> str | None:
    return _FACT_DESCRIPTIONS.get(prolog_fact_header)


# Backward-compatible alias used by legacy GUI imports
def define(prolog_fact_header: str) -> str | False:
    text = describe_fact(prolog_fact_header)
    return text if text is not None else False
