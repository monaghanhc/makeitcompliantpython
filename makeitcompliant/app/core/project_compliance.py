"""Project compliance service (facade over report builder)."""

from __future__ import annotations

from pathlib import Path

from makeitcompliant.app.core.compliance_models import ComplianceReport, RiskLevel
from makeitcompliant.app.core.report_builder import (
    build_compliance_report,
    export_json,
    export_markdown,
)
from makeitcompliant.app.scanner.models import (
    LicenseConflict,
    LicenseFinding,
    ProjectComplianceReport,
)


def _to_legacy_report(report: ComplianceReport) -> ProjectComplianceReport:
    """Convert canonical report to legacy GUI model."""
    legacy = ProjectComplianceReport(
        project_path=report.project_path,
        obligations=report.obligations,
        risk_level=RiskLevel(report.overall_risk.value),
        recommended_actions=report.recommended_actions,
        scan_errors=report.scan_errors,
        files_scanned=report.files_scanned,
    )
    if report.project_license:
        pl = report.project_license
        legacy.project_license = LicenseFinding(
            path=pl.matched_text or "",
            source_kind=pl.source,
            license_atom=pl.identifier,
            display_name=pl.display_name,
            confidence=pl.confidence,
            evidence=pl.detection_method,
        )
    for dep in report.dependencies:
        if dep.declared_license is None:
            continue
        lic = dep.declared_license
        finding = LicenseFinding(
            path=dep.source_file,
            source_kind="dependency",
            license_atom=lic.identifier,
            display_name=lic.display_name,
            confidence=lic.confidence,
            evidence=lic.detection_method,
            package_name=dep.name,
        )
        if lic.identifier == "unknown":
            legacy.unknown_licenses.append(finding)
        else:
            legacy.dependency_licenses.append(finding)
    for issue in report.issues:
        if issue.rule_id.startswith("prolog"):
            legacy.conflicts.append(
                LicenseConflict(
                    dependency_name=issue.affected_items[0] if issue.affected_items else "?",
                    dependency_license=issue.title,
                    reason=issue.description,
                    severity=RiskLevel(issue.severity.value),
                )
            )
    return legacy


class ProjectComplianceService:
    def analyze(self, project_root: str | Path) -> ComplianceReport:
        return build_compliance_report(project_root)

    def analyze_project(self, project_root: str | Path) -> ProjectComplianceReport:
        return _to_legacy_report(self.analyze(project_root))

    def export_json(self, report: ComplianceReport, path: Path) -> None:
        export_json(report, path)

    def export_markdown(self, report: ComplianceReport, path: Path) -> None:
        export_markdown(report, path)
