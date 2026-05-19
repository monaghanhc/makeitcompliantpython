from pathlib import Path
from unittest.mock import MagicMock, patch

from makeitcompliant.app.core.compliance_models import RiskLevel
from makeitcompliant.app.core.report_builder import build_compliance_report
from makeitcompliant.app.scanner.models import FindingKind, LicenseFinding


def test_report_unknown_project_and_incompatible_dep(tmp_path: Path) -> None:
    findings = [
        LicenseFinding(
            path="README",
            source_kind="file",
            license_atom="unknown",
            display_name="Unknown",
            confidence=0.2,
            evidence="?",
            kind=FindingKind.PROJECT_LICENSE,
        ),
        LicenseFinding(
            path="package.json",
            source_kind="manifest",
            license_atom="gpl_3_0",
            display_name="GPL-3",
            confidence=0.9,
            evidence="manifest",
            package_name="evil",
            kind=FindingKind.DEPENDENCY,
        ),
    ]
    dep_result = MagicMock(
        compatible=False,
        risk="high",
        conflict_reasons=["strong_copyleft_in_permissive_project"],
        dependency_license="gpl_3_0",
    )
    prolog_report = MagicMock(
        obligations=[],
        overall_risk="high",
        dependency_results=[dep_result],
    )
    with patch("makeitcompliant.app.core.report_builder.ProjectScanner") as sc:
        sc.return_value.scan.return_value = findings
        with patch("makeitcompliant.app.core.report_builder.ComplianceReasoningEngine") as eng:
            eng.return_value.analyze_project_licenses.return_value = prolog_report
            eng.return_value.explain_incompatibility.return_value = "GPL conflict"
            report = build_compliance_report(tmp_path)
    assert report.project_license
    assert report.issues
    assert report.overall_risk in (RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.CRITICAL, RiskLevel.UNKNOWN)
