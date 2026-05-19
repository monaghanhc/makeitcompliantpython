"""Aggregate ML confidence and Prolog risk into report-level scoring."""

from __future__ import annotations

from makeitcompliant.app.core.compliance_models import (
    ComplianceIssue,
    ComplianceReport,
    ConfidenceTier,
    DetectedLicense,
    RiskLevel,
)


def elevate_risk(current: RiskLevel, new: RiskLevel) -> RiskLevel:
    order = {
        RiskLevel.LOW: 0,
        RiskLevel.MEDIUM: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.CRITICAL: 3,
        RiskLevel.UNKNOWN: 4,
    }
    return current if order[current] >= order[new] else new


def risk_from_prolog(prolog_risk: str) -> RiskLevel:
    try:
        return RiskLevel(prolog_risk.lower())
    except ValueError:
        return RiskLevel.MEDIUM


def issues_from_low_confidence(
    project_license: DetectedLicense | None,
    dependencies: list,
) -> list[ComplianceIssue]:
    issues: list[ComplianceIssue] = []
    if project_license and project_license.confidence_tier in (
        ConfidenceTier.LOW,
        ConfidenceTier.UNKNOWN,
    ):
        issues.append(
            ComplianceIssue(
                severity=RiskLevel.MEDIUM,
                title="Low confidence project license",
                description=(
                    f"Project license detected as {project_license.display_name} "
                    f"with {project_license.confidence:.0%} confidence "
                    f"({project_license.detection_method})."
                ),
                rule_id="ml_low_confidence_project",
                recommendation="Verify the project LICENSE file and SPDX identifier manually.",
                affected_items=[project_license.source],
                confidence=project_license.confidence,
            )
        )
    if project_license is None:
        issues.append(
            ComplianceIssue(
                severity=RiskLevel.HIGH,
                title="Missing project license",
                description="No LICENSE file or package metadata license was detected.",
                rule_id="missing_project_license",
                recommendation=(
                    "Add a LICENSE file to the project root with a clear SPDX identifier."
                ),
                affected_items=["project root"],
            )
        )
    return issues


def finalize_overall_risk(report: ComplianceReport) -> RiskLevel:
    risk = RiskLevel.LOW
    for issue in report.issues:
        risk = elevate_risk(risk, issue.severity)
    if report.overall_risk != RiskLevel.UNKNOWN:
        risk = elevate_risk(risk, report.overall_risk)
    return risk
