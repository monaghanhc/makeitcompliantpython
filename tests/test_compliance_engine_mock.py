from unittest.mock import MagicMock, patch

import pytest

from makeitcompliant.app.core.compliance_engine import ComplianceEngine, PairAnalysis
from makeitcompliant.app.ml.classifier import MatchResult


def _match(name: str, conf: float = 0.9) -> MatchResult:
    return MatchResult(
        template_filename="MIT License.txt",
        prolog_license_name=name,
        confidence=conf,
    )


def test_classify_and_pair() -> None:
    clf = MagicMock()
    clf.match.return_value = _match("MIT License")
    prolog = MagicMock()
    prolog.permissions_for_a.return_value = ["can_use_commercially"]
    prolog.permissions_for_b.return_value = ["can_use_commercially"]
    prolog.conditions_distribution_a.return_value = []
    prolog.conditions_distribution_b.return_value = []
    prolog.conditions_modification_a.return_value = []
    prolog.conditions_modification_b.return_value = []
    prolog.limitations_a.return_value = []
    prolog.limitations_b.return_value = []

    engine = ComplianceEngine(classifier=clf, prolog=prolog)
    m = engine.classify("text")
    assert m.prolog_license_name == "MIT License"
    a, b = engine.classify_pair("a", "b")
    assert a.prolog_license_name == "MIT License"
    analysis = engine.analyze_pair("a", "b")
    assert isinstance(analysis, PairAnalysis)
    assert analysis.permissions_a == ["can_use_commercially"]


def test_file_comparison_facade(mit_text: str) -> None:
    with patch("makeitcompliant.app.core.file_comparison._engine") as eng:
        eng.classify_pair.return_value = (_match("MIT License"), _match("MIT License"))
        eng.classify.return_value = _match("MIT License")
        from makeitcompliant.app.core import file_comparison as fc

        names = fc.classify_two_files(mit_text, mit_text)
        assert names[0] == "MIT License"
        assert fc.classify(mit_text) == "MIT License"
        assert fc.cosine_similarity(mit_text, mit_text) == pytest.approx(1.0)
        with patch("makeitcompliant.app.core.file_comparison.PrologEngine") as pe:
            pe.return_value.permissions_for_a.return_value = ["x"]
            pe.return_value.permissions_for_b.return_value = []
            pe.return_value.conditions_distribution_a.return_value = []
            pe.return_value.conditions_distribution_b.return_value = []
            pe.return_value.conditions_modification_a.return_value = []
            pe.return_value.conditions_modification_b.return_value = []
            pe.return_value.limitations_a.return_value = []
            pe.return_value.limitations_b.return_value = []
            pe.return_value.query.return_value = [{"X": "mit"}]
            assert fc.get_permissions()[0] == ["x"]
            assert fc.query("true") == [{"X": "mit"}]
