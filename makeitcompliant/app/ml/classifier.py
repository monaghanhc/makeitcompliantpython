"""Match license text — delegates to LicenseDetector pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from makeitcompliant.app.core.license_models import normalize_template_name_to_prolog
from makeitcompliant.app.ml.license_detector import LicenseDetector
from makeitcompliant.app.utils.paths import get_license_templates_dir


@dataclass(frozen=True)
class MatchResult:
    template_filename: str
    prolog_license_name: str
    confidence: float

    @property
    def confidence_percent(self) -> float:
        return round(self.confidence * 100.0, 2)


class LicenseClassifier:
    """Backward-compatible wrapper around :class:`LicenseDetector`."""

    def __init__(self, templates_dir: Path | None = None) -> None:
        self._detector = LicenseDetector()
        self._templates_dir = templates_dir or get_license_templates_dir()

    def list_templates(self) -> list[Path]:
        if not self._templates_dir.is_dir():
            raise FileNotFoundError(f"License templates not found: {self._templates_dir}")
        return sorted(p for p in self._templates_dir.iterdir() if p.is_file())

    def match(self, license_text: str, *, min_confidence: float | None = None) -> MatchResult:
        result = self._detector.detect(license_text)
        lic = result.license
        if min_confidence is not None and lic.confidence < min_confidence:
            pass
        if result.template_filename:
            prolog_name = normalize_template_name_to_prolog(result.template_filename)
        else:
            from makeitcompliant.app.core.license_registry import atom_to_display

            prolog_name = atom_to_display(lic.identifier)
        return MatchResult(
            template_filename=result.template_filename or f"{lic.identifier}.txt",
            prolog_license_name=prolog_name,
            confidence=lic.confidence,
        )
