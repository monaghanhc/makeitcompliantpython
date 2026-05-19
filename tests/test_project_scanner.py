from pathlib import Path

import pytest

from makeitcompliant.app.core.license_registry import display_name_to_atom, manifest_value_to_atom
from makeitcompliant.app.scanner.models import FindingKind
from makeitcompliant.app.scanner.project_scanner import ProjectScanner

FIXTURE = Path(__file__).parent / "fixtures" / "sample_node_project"


def test_manifest_value_mit() -> None:
    assert manifest_value_to_atom("MIT") == "mit"


def test_display_name_gpl3() -> None:
    assert display_name_to_atom("GNU General Public License v3.0") == "gpl_3_0"


def test_scan_sample_node_project() -> None:
    if not FIXTURE.is_dir():
        pytest.skip("fixture missing")
    findings = ProjectScanner().scan(FIXTURE)
    project = [f for f in findings if f.kind == FindingKind.PROJECT_LICENSE]
    assert any(f.license_atom == "mit" for f in project)
    deps = [f for f in findings if f.package_name]
    assert len(deps) >= 2


def test_prolog_reasoning_mit_with_unknown_dep() -> None:
    import shutil

    if not shutil.which("swipl"):
        pytest.skip("SWI-Prolog not on PATH")
    pytest.importorskip("swiplserver")
    from makeitcompliant.app.prolog.reasoning_engine import ComplianceReasoningEngine

    engine = ComplianceReasoningEngine()
    result = engine.analyze("mit", [("lodash", "mit"), ("mystery-pkg", "unknown")])
    assert result.overall_risk in ("medium", "high", "critical")
    assert any(v.name == "mystery-pkg" for v in result.dependency_verdicts)
