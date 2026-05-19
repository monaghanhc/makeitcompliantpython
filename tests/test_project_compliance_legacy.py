from pathlib import Path

from makeitcompliant.app.core.compliance_models import (
    ComplianceReport,
    DependencyInfo,
    DetectedLicense,
)
from makeitcompliant.app.core.project_compliance import _to_legacy_report


def test_to_legacy_report_all_branches(tmp_path: Path) -> None:
    report = ComplianceReport(
        project_path=str(tmp_path),
        project_license=DetectedLicense("mit", "LICENSE", 0.9, "spdx"),
        dependencies=[
            DependencyInfo(
                "known",
                "1.0",
                "package.json",
                DetectedLicense("mit", "lock", 0.9, "manifest"),
            ),
            DependencyInfo(
                "unk",
                None,
                "package.json",
                DetectedLicense("unknown", "lock", 0.0, "none"),
            ),
        ],
        files_scanned=2,
    )
    legacy = _to_legacy_report(report)
    assert legacy.project_license is not None
    assert len(legacy.dependency_licenses) == 1
    assert len(legacy.unknown_licenses) == 1
