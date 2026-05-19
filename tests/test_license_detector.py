from makeitcompliant.app.core.compliance_models import ConfidenceTier
from makeitcompliant.app.ml.features import normalize_license_text
from makeitcompliant.app.ml.license_detector import LicenseDetector
from makeitcompliant.app.ml.spdx_detector import detect_spdx_in_text


def test_normalize_collapses_whitespace() -> None:
    assert normalize_license_text("a  \n  b") == "a b"


def test_spdx_detection() -> None:
    text = "SPDX-License-Identifier: MIT\n"
    hit = detect_spdx_in_text(text)
    assert hit is not None
    assert hit[1] == "mit"


def test_detector_spdx_fast_path() -> None:
    det = LicenseDetector()
    r = det.detect("SPDX-License-Identifier: Apache-2.0\n")
    assert r.license.identifier == "apache_2_0"
    assert r.license.detection_method == "spdx"
    assert r.license.confidence_tier == ConfidenceTier.HIGH


def test_detector_low_confidence_unknown() -> None:
    det = LicenseDetector()
    r = det.detect("totally unrelated random text xyz")
    assert r.license.identifier == "unknown" or r.license.confidence < 0.7
