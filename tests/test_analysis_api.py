"""Tests for analysis.pl API (requires SWI-Prolog on PATH)."""

from __future__ import annotations

import shutil

import pytest

from makeitcompliant.app.prolog.analysis_api import (
    parse_dependency_analysis,
    parse_explanation,
)


def test_parse_dependency_result_compound() -> None:
    row = {
        "Result": {
            "functor": "result",
            "args": ["no", "critical", ["unknown_dependency_requires_review"]],
        }
    }
    r = parse_dependency_analysis("mit", "unknown", row)
    assert r.compatible is False
    assert r.risk == "critical"
    assert r.conflict_reasons


def test_parse_explanation_string() -> None:
    assert "compatible" in parse_explanation({"Explanation": "Licenses are compatible"}).lower()


@pytest.mark.skipif(not shutil.which("swipl"), reason="SWI-Prolog not on PATH")
def test_analyze_dependency_mit_gpl3() -> None:
    pytest.importorskip("swiplserver")
    from makeitcompliant.app.prolog.reasoning_engine import ComplianceReasoningEngine

    engine = ComplianceReasoningEngine()
    result = engine.analyze_dependency("mit", "gpl_3_0")
    assert result.compatible is False
    assert result.risk in ("high", "critical", "medium")
    explanation = engine.explain_incompatibility("mit", "gpl_3_0")
    assert len(explanation) > 20


@pytest.mark.skipif(not shutil.which("swipl"), reason="SWI-Prolog not on PATH")
def test_required_obligations_and_analyze_project() -> None:
    pytest.importorskip("swiplserver")
    from makeitcompliant.app.prolog.reasoning_engine import ComplianceReasoningEngine

    engine = ComplianceReasoningEngine()
    obligations = engine.required_obligations("mit", ["apache_2_0"])
    assert obligations

    report = engine.analyze_project_licenses("mit", ["mit", "unknown"])
    assert report.overall_risk in ("low", "medium", "high", "critical")
    assert len(report.dependency_results) >= 1
