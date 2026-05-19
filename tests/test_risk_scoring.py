from makeitcompliant.app.core.compliance_models import (
    ComplianceIssue,
    ComplianceReport,
    ConfidenceTier,
    DetectedLicense,
    RiskLevel,
)
from makeitcompliant.app.core.risk_scoring import (
    elevate_risk,
    finalize_overall_risk,
    issues_from_low_confidence,
    risk_from_prolog,
)


def test_elevate_risk() -> None:
    assert elevate_risk(RiskLevel.LOW, RiskLevel.HIGH) == RiskLevel.HIGH
    assert elevate_risk(RiskLevel.HIGH, RiskLevel.LOW) == RiskLevel.HIGH


def test_risk_from_prolog_bad_value() -> None:
    assert risk_from_prolog("not-a-level") == RiskLevel.MEDIUM


def test_issues_from_low_confidence() -> None:
    lic = DetectedLicense(
        identifier="unknown",
        source="LICENSE",
        confidence=0.5,
        detection_method="tfidf",
        confidence_tier=ConfidenceTier.LOW,
    )
    issues = issues_from_low_confidence(lic, [])
    assert issues and "confidence" in issues[0].title.lower()
    missing = issues_from_low_confidence(None, [])
    assert any("Missing project license" in i.title for i in missing)


def test_finalize_overall_risk() -> None:
    report = ComplianceReport(
        project_path="/p",
        project_license=None,
        overall_risk=RiskLevel.MEDIUM,
        issues=[
            ComplianceIssue(
                severity=RiskLevel.HIGH,
                title="x",
                description="d",
                rule_id="r",
                recommendation="a",
            )
        ],
    )
    assert finalize_overall_risk(report) == RiskLevel.HIGH
