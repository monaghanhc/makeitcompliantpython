import shutil

import pytest

from makeitcompliant.app.core.license_analysis import analyze_license_pair


@pytest.mark.skipif(not shutil.which("swipl"), reason="SWI-Prolog not on PATH")
def test_analyze_mit_gpl_pair(mit_text: str, gpl3_text: str) -> None:
    pytest.importorskip("swiplserver")
    result = analyze_license_pair(mit_text, gpl3_text)
    assert result.prolog_available
    assert result.license_a.atom == "mit"
    assert result.cross_compatible is False or result.cross_risk in ("high", "critical", "medium")
