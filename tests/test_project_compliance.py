from pathlib import Path
from unittest.mock import patch

from makeitcompliant.app.core.compliance_models import (
    ComplianceIssue,
    ComplianceReport,
    DetectedLicense,
    RiskLevel,
)
from makeitcompliant.app.core.project_compliance import ProjectComplianceService


def test_service_export_and_legacy(tmp_path: Path) -> None:
    report = ComplianceReport(
        project_path=str(tmp_path),
        project_license=DetectedLicense("mit", "LICENSE", 0.9, "spdx"),
        dependencies=[],
        issues=[
            ComplianceIssue(
                severity=RiskLevel.HIGH,
                title="Incompatible",
                description="d",
                rule_id="prolog_gpl",
                recommendation="fix",
                affected_items=["pkg"],
            )
        ],
        overall_risk=RiskLevel.HIGH,
        recommended_actions=["review"],
        files_scanned=3,
    )
    svc = ProjectComplianceService()
    with patch.object(svc, "analyze", return_value=report):
        legacy = svc.analyze_project(tmp_path)
    assert legacy.project_license is not None
    assert legacy.conflicts
    jp = tmp_path / "out.json"
    md = tmp_path / "out.md"
    svc.export_json(report, jp)
    svc.export_markdown(report, md)
    assert jp.exists()
