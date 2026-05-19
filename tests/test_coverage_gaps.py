"""Targeted tests for remaining uncovered branches."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from makeitcompliant.app.core import file_comparison as fc
from makeitcompliant.app.core.license_analysis import analyze_license_pair
from makeitcompliant.app.ml import model_cache
from makeitcompliant.app.ml.classifier import LicenseClassifier
from makeitcompliant.app.ml.features import _ensure_nltk_punkt
from makeitcompliant.app.ml.license_detector import LicenseDetector
from makeitcompliant.app.prolog import facts_loader
from makeitcompliant.app.prolog.analysis_api import (
    ProjectAnalysisReport,
    _atom,
    parse_explanation,
    parse_project_report,
)
from makeitcompliant.app.prolog.engine import PrologEngine, PrologEngineError
from makeitcompliant.app.prolog.reasoning_engine import (
    ComplianceReasoningEngine,
    ReasoningEngineError,
)
from makeitcompliant.app.scanner.models import LicenseFinding, ProjectComplianceReport


def test_file_to_string(mit_license_file: Path) -> None:
    text = fc.file_to_string(mit_license_file)
    assert "MIT" in text


def test_model_cache_missing_dir(tmp_path: Path) -> None:
    model_cache.clear_template_cache()
    entries = model_cache.load_template_cache(str(tmp_path / "missing"))
    assert entries == ()


def test_model_cache_skip_unreadable(tmp_path: Path) -> None:
    model_cache.clear_template_cache()
    bad = tmp_path / "bad.txt"
    bad.write_text("ok", encoding="utf-8")

    real_read = Path.read_text

    def _read(self, *a, **k):
        if self.name == "bad.txt":
            raise OSError("denied")
        return real_read(self, *a, **k)

    with patch.object(Path, "read_text", _read):
        entries = model_cache.load_template_cache(str(tmp_path))
    assert len(entries) == 0


def test_read_base_kb_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        facts_loader.read_base_kb(tmp_path / "nope.pl")


def test_ensure_nltk_downloads() -> None:
    with patch("makeitcompliant.app.ml.features.nltk.data.find", side_effect=LookupError):
        with patch("makeitcompliant.app.ml.features.nltk.download") as dl:
            _ensure_nltk_punkt()
            assert dl.called


def test_paths_cwd_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from makeitcompliant.app.utils import paths

    (tmp_path / "license_templates").mkdir()
    monkeypatch.chdir(tmp_path)
    paths.get_resource_root.cache_clear()
    root = paths.get_resource_root()
    assert (root / "license_templates").is_dir()
    paths.get_resource_root.cache_clear()


def test_engine_query_failure(tmp_path: Path) -> None:
    kb = tmp_path / "k.pl"
    kb.write_text("%\n", encoding="utf-8")
    with patch("makeitcompliant.app.prolog.engine.get_prolog_runtime_kb_path", return_value=kb):
        with patch("makeitcompliant.app.prolog.engine.PrologMQI", side_effect=RuntimeError("x")):
            with pytest.raises(PrologEngineError):
                PrologEngine().query("true")


def test_analysis_api_atom_and_parse() -> None:
    assert _atom(42) == "42"
    assert parse_explanation({"bad": 1}) == "No explanation available."
    rep = parse_project_report("mit", [{"Report": "x"}], ["apache_2_0"])
    assert isinstance(rep, ProjectAnalysisReport)


def test_license_analysis_legacy_and_reasoner_errors(mit_text: str, gpl3_text: str) -> None:
    with patch("makeitcompliant.app.core.license_analysis.LicenseDetector") as det:
        lic = MagicMock()
        lic.license.identifier = "mit"
        lic.license.display_name = "MIT"
        lic.license.confidence = 0.9
        lic.license.detection_method = "spdx"
        det.return_value.detect.return_value = MagicMock(license=lic.license)
        with patch("makeitcompliant.app.core.license_analysis.check_prolog") as st:
            st.return_value = MagicMock(available=True, message="ok")
            with patch("makeitcompliant.app.core.license_analysis.write_runtime_facts"):
                with patch(
                    "makeitcompliant.app.core.license_analysis.PrologEngine",
                    side_effect=__import__(
                        "makeitcompliant.app.prolog.engine", fromlist=["PrologEngineError"]
                    ).PrologEngineError("legacy"),
                ):
                    with patch(
                        "makeitcompliant.app.core.license_analysis.ComplianceReasoningEngine",
                        side_effect=__import__(
                            "makeitcompliant.app.prolog.reasoning_engine",
                            fromlist=["ReasoningEngineError"],
                        ).ReasoningEngineError("reasoner"),
                    ):
                        out = analyze_license_pair(mit_text, gpl3_text)
    assert out.cross_explanation


def test_classifier_min_confidence(mit_text: str) -> None:
    LicenseClassifier().match(mit_text, min_confidence=0.01)


def test_detector_lazy_templates(mit_text: str) -> None:
    d = LicenseDetector()
    assert d.templates
    d.detect(mit_text)


def test_scanner_legacy_summary() -> None:
    r = ProjectComplianceReport(project_path="/p")
    assert "Project" in r.summary()


def test_reasoning_analyze_without_report(mit_text: str) -> None:
    engine = ComplianceReasoningEngine()
    thread = MagicMock()
    thread.query.return_value = False
    mqi = MagicMock()
    mqi.create_thread.return_value.__enter__ = MagicMock(return_value=thread)
    mqi.create_thread.return_value.__exit__ = MagicMock(return_value=False)
    mqi.__enter__ = MagicMock(return_value=mqi)
    mqi.__exit__ = MagicMock(return_value=False)
    with patch("makeitcompliant.app.prolog.reasoning_engine.write_project_session"):
        with patch.object(engine, "analyze_project_licenses", side_effect=ReasoningEngineError("x")):
            with patch("makeitcompliant.app.prolog.reasoning_engine.PrologMQI", return_value=mqi):
                with patch.object(engine, "_consult_all"):
                    with patch.object(engine, "_query_obligations", return_value=["o"]):
                        with patch.object(engine, "_query_dependency_verdicts", return_value=[]):
                            with patch.object(engine, "_query_conflicts", return_value=[]):
                                with patch.object(engine, "_aggregate_risk", return_value="low"):
                                    result = engine.analyze("mit", [("pkg", "mit")])
    assert result.overall_risk == "low"


def test_license_finding_is_known() -> None:
    f = LicenseFinding(
        path="x",
        source_kind="f",
        license_atom="mit",
        display_name="MIT",
        confidence=1.0,
        evidence="e",
    )
    assert f.is_known
    u = LicenseFinding("x", "f", "unknown", "U", 0.0, "e")
    assert not u.is_known
