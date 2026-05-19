from makeitcompliant.app.ml import normalizer
from makeitcompliant.app.ml.features import normalize_license_text, preprocess_tokens
from makeitcompliant.app.ml.spdx_detector import detect_spdx_in_text, spdx_from_atom


def test_normalizer_reexports() -> None:
    assert normalizer.normalize_license_text is normalize_license_text
    assert normalizer.preprocess_tokens is preprocess_tokens


def test_detect_spdx_mit(mit_text: str) -> None:
    hit = detect_spdx_in_text(mit_text)
    assert hit is not None
    assert hit[0] == "MIT"
    assert hit[1] == "mit"


def test_detect_spdx_license_line() -> None:
    hit = detect_spdx_in_text("License: MIT\n")
    assert hit is not None


def test_spdx_from_atom_unknown() -> None:
    assert spdx_from_atom("custom_atom") == "custom_atom"
