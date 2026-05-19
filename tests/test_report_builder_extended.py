from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from makeitcompliant.app.core.compliance_models import ComplianceReport, DetectedLicense, RiskLevel
from makeitcompliant.app.core.report_builder import (
    _build_actions,
    _finding_to_detected,
    _json_default,
    build_compliance_report,
    export_json,
    export_markdown,
)
from makeitcompliant.app.prolog.reasoning_engine import ReasoningEngineError
from makeitcompliant.app.scanner.models import FindingKind, LicenseFinding


def test_json_default_enum_and_path(tmp_path: Path) -> None:
    assert _json_default(RiskLevel.LOW) == "low"
    assert _json_default(tmp_path) == str(tmp_path)
    with pytest.raises(TypeError):
        _json_default(object())


def test_finding_to_detected() -> None:
    f = LicenseFinding(
        path="LICENSE",
        source_kind="file",
        license_atom="mit",
        display_name="MIT",
        confidence=0.9,
        evidence="SPDX",
        kind=FindingKind.PROJECT_LICENSE,
    )
    d = _finding_to_detected(f)
    assert d.identifier == "mit"


def test_build_actions_variants() -> None:
    empty = ComplianceReport(project_path="/p", project_license=None)
    assert "LICENSE" in _build_actions(empty)[0]
    with_dep = ComplianceReport(
        project_path="/p",
        project_license=DetectedLicense("mit", "L", 0.9, "spdx"),
        dependencies=[],
        obligations=["obl1"],
        issues=[MagicMock()],
    )
    actions = _build_actions(with_dep)
    assert any("obligation" in a.lower() for a in actions)


def test_build_compliance_report_scan_error(tmp_path: Path) -> None:
    with patch("makeitcompliant.app.core.report_builder.ProjectScanner") as sc:
        sc.return_value.scan.side_effect = RuntimeError("scan failed")
        report = build_compliance_report(tmp_path)
    assert report.scan_errors
    assert report.overall_risk == RiskLevel.UNKNOWN


def test_build_compliance_report_with_prolog(tmp_path: Path) -> None:
    findings = [
        LicenseFinding(
            path="LICENSE",
            source_kind="file",
            license_atom="mit",
            display_name="MIT",
            confidence=0.95,
            evidence="SPDX",
            kind=FindingKind.PROJECT_LICENSE,
        ),
        LicenseFinding(
            path="package.json",
            source_kind="manifest",
            license_atom="mit",
            display_name="MIT",
            confidence=0.8,
            evidence="manifest",
            package_name="lodash",
            kind=FindingKind.DEPENDENCY,
        ),
    ]
    prolog_report = MagicMock(
        obligations=["include_copyright_notice"],
        overall_risk="low",
        dependency_results=[
            MagicMock(
                compatible=True,
                risk="low",
                conflict_reasons=[],
                dependency_license="mit",
            )
        ],
    )
    with patch("makeitcompliant.app.core.report_builder.ProjectScanner") as sc:
        sc.return_value.scan.return_value = findings
        with patch("makeitcompliant.app.core.report_builder.ComplianceReasoningEngine") as eng:
            eng.return_value.analyze_project_licenses.return_value = prolog_report
            report = build_compliance_report(tmp_path)
    assert report.project_license
    assert report.dependencies


def test_build_compliance_report_prolog_failure(tmp_path: Path) -> None:
    findings = [
        LicenseFinding(
            path="LICENSE",
            source_kind="file",
            license_atom="mit",
            display_name="MIT",
            confidence=0.95,
            evidence="SPDX",
            kind=FindingKind.PROJECT_LICENSE,
        ),
    ]
    with patch("makeitcompliant.app.core.report_builder.ProjectScanner") as sc:
        sc.return_value.scan.return_value = findings
        with patch("makeitcompliant.app.core.report_builder.ComplianceReasoningEngine") as eng:
            eng.return_value.analyze_project_licenses.side_effect = ReasoningEngineError("no prolog")
            report = build_compliance_report(tmp_path)
    assert any("Prolog" in e for e in report.scan_errors)


def test_export_paths(tmp_path: Path) -> None:
    report = ComplianceReport(project_path=str(tmp_path), project_license=None)
    export_json(report, tmp_path / "out.json")
    export_markdown(report, tmp_path / "out.md")
    assert (tmp_path / "out.json").exists()
    assert "Make It Compliant" in (tmp_path / "out.md").read_text(encoding="utf-8")
