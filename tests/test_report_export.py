from pathlib import Path

from makeitcompliant.app.core.compliance_models import (
    ComplianceIssue,
    ComplianceReport,
    DependencyInfo,
    DetectedLicense,
    RiskLevel,
)
from makeitcompliant.app.core.report_builder import export_json, export_markdown


def test_export_roundtrip(tmp_path: Path) -> None:
    report = ComplianceReport(
        project_path=str(tmp_path),
        project_license=DetectedLicense(
            identifier="mit",
            source="LICENSE",
            confidence=0.95,
            detection_method="spdx",
        ),
        dependencies=[
            DependencyInfo(
                name="lodash",
                version="4.0.0",
                source_file="package.json",
                declared_license=DetectedLicense(
                    identifier="mit",
                    source="lockfile",
                    confidence=0.9,
                    detection_method="manifest",
                ),
            )
        ],
        issues=[
            ComplianceIssue(
                severity=RiskLevel.LOW,
                title="Test",
                description="Desc",
                rule_id="test",
                recommendation="OK",
            )
        ],
        overall_risk=RiskLevel.LOW,
    )
    jp = tmp_path / "r.json"
    md = tmp_path / "r.md"
    export_json(report, jp)
    export_markdown(report, md)
    assert jp.read_text(encoding="utf-8").find("mit") >= 0
    assert md.read_text(encoding="utf-8").find("Make It Compliant") >= 0
