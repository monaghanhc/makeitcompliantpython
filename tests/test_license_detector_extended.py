from makeitcompliant.app.ml.license_detector import LicenseDetector


def test_detector_empty_text() -> None:
    r = LicenseDetector().detect("   ")
    assert r.license.identifier == "unknown"


def test_detector_rank(mit_text: str) -> None:
    ranked = LicenseDetector().rank(mit_text, top_n=3)
    assert len(ranked) >= 1
    assert ranked[0].license.confidence > 0
