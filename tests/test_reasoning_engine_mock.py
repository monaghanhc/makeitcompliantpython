from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from makeitcompliant.app.prolog.reasoning_engine import (
    ComplianceReasoningEngine,
    ReasoningEngineError,
)


def test_consult_kb_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "makeitcompliant.app.prolog.reasoning_engine.get_prolog_compliance_kb_dir",
        lambda: tmp_path / "nope",
    )
    engine = ComplianceReasoningEngine()
    with pytest.raises(ReasoningEngineError):
        engine._consult_kb(MagicMock())


def test_analyze_dependency_success(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = ComplianceReasoningEngine()
    row = {"Result": {"functor": "result", "args": ["no", "high", []]}}
    with patch.object(engine, "_run", return_value=[row]):
        r = engine.analyze_dependency("mit", "gpl_3_0")
    assert r.compatible is False


def test_analyze_dependency_false(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = ComplianceReasoningEngine()
    with patch.object(engine, "_run", return_value=False):
        with pytest.raises(ReasoningEngineError):
            engine.analyze_dependency("mit", "gpl_3_0")


def test_format_license_list() -> None:
    assert ComplianceReasoningEngine._format_license_list([]) == "[]"
    assert "mit" in ComplianceReasoningEngine._format_license_list(["mit", "apache_2_0"])


def test_analyze_project_licenses(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = ComplianceReasoningEngine()
    report_row = {
        "Report": {
            "functor": "report",
            "args": [["include_copyright_notice"], [], "low"],
        }
    }
    with patch.object(engine, "_run", return_value=[report_row]):
        rep = engine.analyze_project_licenses("mit", ["apache_2_0"])
    assert rep.overall_risk == "low"


def test_analyze_method(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = ComplianceReasoningEngine()
    thread = MagicMock()
    thread.query.return_value = False
    mqi = MagicMock()
    mqi.create_thread.return_value.__enter__ = MagicMock(return_value=thread)
    mqi.create_thread.return_value.__exit__ = MagicMock(return_value=False)
    mqi.__enter__ = MagicMock(return_value=mqi)
    mqi.__exit__ = MagicMock(return_value=False)
    with patch("makeitcompliant.app.prolog.reasoning_engine.write_project_session"):
        with patch.object(engine, "analyze_project_licenses") as ap:
            ap.return_value = MagicMock(
                obligations=["o"],
                overall_risk="medium",
                dependency_results=[
                    MagicMock(
                        dependency_license="apache_2_0",
                        compatible=False,
                        risk="high",
                        conflict_reasons=["strong_copyleft_in_permissive_project"],
                    )
                ],
            )
            with patch("makeitcompliant.app.prolog.reasoning_engine.PrologMQI", return_value=mqi):
                with patch.object(engine, "_consult_all"):
                    result = engine.analyze("mit", [("pkg", "apache_2_0")])
    assert result.overall_risk == "medium"
    assert result.dependency_verdicts
