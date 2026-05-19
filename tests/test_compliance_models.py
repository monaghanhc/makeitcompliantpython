from makeitcompliant.app.core.compliance_models import (
    ComplianceIssue,
    ComplianceReport,
    ConfidenceTier,
    DependencyInfo,
    DetectedLicense,
    RiskLevel,
    confidence_tier_for,
)


def test_confidence_tiers() -> None:
    assert confidence_tier_for(0.95) == ConfidenceTier.HIGH
    assert confidence_tier_for(0.8) == ConfidenceTier.MEDIUM
    assert confidence_tier_for(0.5) == ConfidenceTier.LOW
    assert confidence_tier_for(0.0) == ConfidenceTier.UNKNOWN


def test_detected_license_post_init() -> None:
    lic = DetectedLicense(
        identifier="mit",
        source="test",
        confidence=0.99,
        detection_method="spdx",
    )
    assert lic.display_name == "MIT License"
    assert lic.confidence_tier == ConfidenceTier.HIGH


def test_report_summary() -> None:
    report = ComplianceReport(
        project_path="/tmp/p",
        project_license=DetectedLicense(
            identifier="mit",
            source="LICENSE",
            confidence=0.9,
            detection_method="spdx",
        ),
        dependencies=[
            DependencyInfo("pkg", "1.0", "package.json", DetectedLicense(
                identifier="mit", source="lock", confidence=0.8, detection_method="manifest",
            )),
            DependencyInfo("unk", None, "package.json", DetectedLicense(
                identifier="unknown", source="lock", confidence=0.0, detection_method="none",
            )),
        ],
        issues=[
            ComplianceIssue(
                severity=RiskLevel.LOW,
                title="t",
                description="d",
                rule_id="r",
                recommendation="ok",
            )
        ],
        overall_risk=RiskLevel.LOW,
    )
    s = report.summary()
    assert "MIT" in s
    assert "1 known" in s
