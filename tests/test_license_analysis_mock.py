from unittest.mock import MagicMock, patch

from makeitcompliant.app.core.compliance_models import ConfidenceTier, DetectedLicense
from makeitcompliant.app.core.license_analysis import analyze_license_pair
from makeitcompliant.app.ml.license_detector import DetectionResult


def _det(atom: str, conf: float = 0.95) -> DetectionResult:
    return DetectionResult(
        license=DetectedLicense(
            identifier=atom,
            source="t",
            confidence=conf,
            detection_method="spdx",
            confidence_tier=ConfidenceTier.HIGH,
        )
    )


def test_analyze_license_pair_without_prolog(mit_text: str, gpl3_text: str) -> None:
    with patch("makeitcompliant.app.core.license_analysis.LicenseDetector") as det:
        det.return_value.detect.side_effect = [_det("mit"), _det("gpl_3_0")]
        with patch("makeitcompliant.app.core.license_analysis.check_prolog") as st:
            st.return_value = MagicMock(available=False, message="no swipl")
            with patch("makeitcompliant.app.core.license_analysis.write_runtime_facts"):
                out = analyze_license_pair(mit_text, gpl3_text)
    assert out.license_a.atom == "mit"
    assert not out.prolog_available


def test_analyze_license_pair_with_prolog(mit_text: str, gpl3_text: str) -> None:
    with patch("makeitcompliant.app.core.license_analysis.LicenseDetector") as det:
        det.return_value.detect.side_effect = [_det("mit"), _det("gpl_3_0")]
        with patch("makeitcompliant.app.core.license_analysis.check_prolog") as st:
            st.return_value = MagicMock(available=True, message="ok")
            with patch("makeitcompliant.app.core.license_analysis.write_runtime_facts"):
                legacy = MagicMock()
                legacy.permissions_for_a.return_value = ["can_use_commercially"]
                legacy.permissions_for_b.return_value = []
                legacy.conditions_distribution_a.return_value = []
                legacy.conditions_distribution_b.return_value = []
                legacy.conditions_modification_a.return_value = []
                legacy.conditions_modification_b.return_value = []
                legacy.limitations_a.return_value = []
                legacy.limitations_b.return_value = []
                reasoner = MagicMock()
                dep = MagicMock(compatible=False, risk="high", conflict_reasons=["r"])
                reasoner.analyze_dependency.return_value = dep
                reasoner.explain_incompatibility.return_value = "explain"
                reasoner.required_obligations.return_value = ["include_copyright_notice"]
                with patch("makeitcompliant.app.core.license_analysis.PrologEngine", return_value=legacy):
                    with patch(
                        "makeitcompliant.app.core.license_analysis.ComplianceReasoningEngine",
                        return_value=reasoner,
                    ):
                        out = analyze_license_pair(mit_text, gpl3_text)
    assert out.cross_compatible is False
    assert out.obligations
