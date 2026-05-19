from unittest.mock import MagicMock, patch

import pytest

from makeitcompliant.app.prolog.analysis_api import DependencyAnalysisResult
from makeitcompliant.app.prolog.reasoning_engine import (
    ComplianceReasoningEngine,
    ReasoningEngineError,
)


def test_run_raises_wrapped() -> None:
    engine = ComplianceReasoningEngine()
    with patch("makeitcompliant.app.prolog.reasoning_engine.PrologMQI", side_effect=RuntimeError("fail")):
        with pytest.raises(ReasoningEngineError):
            engine._run("true")


def test_explain_and_obligations() -> None:
    engine = ComplianceReasoningEngine()
    with patch.object(engine, "_run", return_value=[{"Explanation": "Because"}]):
        assert "Because" in engine.explain_incompatibility("mit", "gpl_3_0")
    with patch.object(engine, "_run", return_value=[{"X": "include_copyright_notice"}]):
        obs = engine.required_obligations("mit", ["apache_2_0"])
        assert obs
    with patch.object(engine, "_run", return_value=False):
        assert engine.required_obligations("mit", []) == []


def test_verdict_helpers() -> None:
    engine = ComplianceReasoningEngine()
    deps = [("pkg", "apache_2_0")]
    results = [
        DependencyAnalysisResult(
            "mit", "apache_2_0", False, "high", conflict_reasons=["strong_copyleft_in_permissive_project"]
        )
    ]
    verdicts = engine._verdicts_from_report(deps, results)
    assert verdicts[0].name == "pkg"
    conflicts = engine._conflicts_from_report(deps, results)
    assert conflicts
    assert engine._aggregate_risk(verdicts) == "high"
    assert engine._aggregate_risk([]) == "low"


def test_query_helpers() -> None:
    engine = ComplianceReasoningEngine()
    thread = MagicMock()
    thread.query.side_effect = lambda goal: (
        [{"X": "include_copyright_notice"}]
        if "project_obligation" in goal
        else [{"R": "high"}]
        if "dependency_risk" in goal
        else True
        if "dependency_compatible" in goal
        else [{"R": "strong_copyleft_in_permissive_project"}]
        if "dependency_conflict" in goal and "N" not in goal
        else [{"N": "pkg", "R": "strong_copyleft_in_permissive_project"}]
    )
    assert engine._query_obligations(thread)
    assert engine._risk_for_dep(thread, "pkg") == "high"
    assert engine._compatible_for_dep(thread, "pkg") is True
    assert engine._conflicts_for_dep(thread, "pkg")
    assert engine._query_conflicts(thread)
    assert engine._query_true(thread, "goal.") is True
