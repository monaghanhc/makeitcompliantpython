from makeitcompliant.app.core.license_registry import (
    atom_to_display,
    conflict_reason_label,
    display_name_to_atom,
    extract_spdx_from_text,
    manifest_value_to_atom,
    normalize_spdx,
    obligation_label,
    spdx_to_atom,
)


def test_spdx_and_display_mappings() -> None:
    assert spdx_to_atom("MIT") == "mit"
    assert spdx_to_atom("GPL-3.0-only") == "gpl_3_0"
    assert display_name_to_atom("MIT License") == "mit"
    assert atom_to_display("apache_2_0") == "Apache License 2.0"
    assert normalize_spdx("apache 2.0") == "APACHE-2.0"


def test_manifest_value_variants() -> None:
    assert manifest_value_to_atom("MIT") == "mit"
    assert manifest_value_to_atom("SEE LICENSE IN LICENSE") is None
    assert manifest_value_to_atom("proprietary") == "proprietary"
    assert manifest_value_to_atom("unlicensed") == "proprietary"


def test_extract_spdx_from_text() -> None:
    text = "SPDX-License-Identifier: Apache-2.0\n"
    assert extract_spdx_from_text(text) == "apache_2_0"


def test_labels() -> None:
    assert "copyright" in obligation_label("include_copyright_notice").lower()
    assert "copyleft" in conflict_reason_label("strong_copyleft_in_permissive_project").lower()
    assert "other" in conflict_reason_label("other_reason").lower()
