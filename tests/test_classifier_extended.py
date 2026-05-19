from pathlib import Path

import pytest

from makeitcompliant.app.ml.classifier import LicenseClassifier


def test_list_templates_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        LicenseClassifier(templates_dir=tmp_path / "nope").list_templates()


def test_match_spdx_without_template_file(mit_text: str) -> None:
    m = LicenseClassifier().match(mit_text)
    assert m.confidence > 0.5
    assert m.prolog_license_name
