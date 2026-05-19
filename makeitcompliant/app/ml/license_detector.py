"""Unified local license detection: SPDX → TF-IDF templates → unknown."""

from __future__ import annotations

from dataclasses import dataclass

from makeitcompliant.app.core.compliance_models import (
    ConfidenceTier,
    DetectedLicense,
    confidence_tier_for,
)
from makeitcompliant.app.core.license_registry import atom_to_display
from makeitcompliant.app.ml.features import normalize_license_text
from makeitcompliant.app.ml.model_cache import TemplateEntry, load_template_cache
from makeitcompliant.app.ml.similarity import best_template_score, rank_templates
from makeitcompliant.app.ml.spdx_detector import detect_spdx_in_text
from makeitcompliant.app.utils.logging_config import get_logger

logger = get_logger("ml.license_detector")

HIGH_THRESHOLD = 0.90
MEDIUM_THRESHOLD = 0.70
UNKNOWN_ATOM = "unknown"


@dataclass(frozen=True)
class DetectionResult:
    license: DetectedLicense
    template_filename: str | None = None


class LicenseDetector:
    """
    Efficient pipeline:
    1. SPDX / metadata heuristics (fastest)
    2. TF-IDF cosine vs cached templates
  3. Mark unknown if confidence < 0.70
    """

    def __init__(self, *, medium_threshold: float = MEDIUM_THRESHOLD) -> None:
        self._medium_threshold = medium_threshold
        self._templates: tuple[TemplateEntry, ...] | None = None

    @property
    def templates(self) -> tuple[TemplateEntry, ...]:
        if self._templates is None:
            self._templates = load_template_cache()
        return self._templates

    def detect(
        self,
        text: str,
        *,
        source: str = "text",
        max_chars: int = 500_000,
    ) -> DetectionResult:
        snippet = text[:max_chars]
        normalized = normalize_license_text(snippet)

        spdx_hit = detect_spdx_in_text(snippet)
        if spdx_hit:
            spdx_id, atom = spdx_hit
            return DetectionResult(
                license=DetectedLicense(
                    identifier=atom,
                    spdx_id=spdx_id,
                    source=source,
                    confidence=0.98,
                    detection_method="spdx",
                    matched_text=spdx_id,
                    confidence_tier=ConfidenceTier.HIGH,
                    display_name=atom_to_display(atom),
                )
            )

        if not normalized.strip():
            return self._unknown(source, "Empty license text")

        best = best_template_score(normalized)
        if best is None:
            return self._unknown(source, "No templates loaded")

        entry = best.entry
        best_score = best.score
        tier = confidence_tier_for(best_score)
        if best_score < self._medium_threshold:
            return DetectionResult(
                license=DetectedLicense(
                    identifier=UNKNOWN_ATOM,
                    source=source,
                    confidence=best_score,
                    detection_method="tfidf_low_confidence",
                    matched_text=entry.filename,
                    confidence_tier=ConfidenceTier.UNKNOWN,
                    display_name="Unknown (needs review)",
                ),
                template_filename=entry.filename,
            )

        return DetectionResult(
            license=DetectedLicense(
                identifier=entry.prolog_atom,
                source=source,
                confidence=best_score,
                detection_method="tfidf",
                matched_text=entry.filename,
                confidence_tier=tier,
                display_name=atom_to_display(entry.prolog_atom),
            ),
            template_filename=entry.filename,
        )

    def rank(self, text: str, top_n: int = 5) -> list[DetectionResult]:
        """Return top-N template matches (explainability / review UI)."""
        normalized = normalize_license_text(text[:500_000])
        results: list[DetectionResult] = []
        for scored in rank_templates(normalized, top_n=top_n):
            results.append(
                DetectionResult(
                    license=DetectedLicense(
                        identifier=scored.entry.prolog_atom,
                        source="rank",
                        confidence=scored.score,
                        detection_method="tfidf_rank",
                        matched_text=scored.entry.filename,
                        confidence_tier=confidence_tier_for(scored.score),
                        display_name=atom_to_display(scored.entry.prolog_atom),
                    ),
                    template_filename=scored.entry.filename,
                )
            )
        return results

    def _unknown(self, source: str, reason: str) -> DetectionResult:
        return DetectionResult(
            license=DetectedLicense(
                identifier=UNKNOWN_ATOM,
                source=source,
                confidence=0.0,
                detection_method="none",
                matched_text=reason,
                confidence_tier=ConfidenceTier.UNKNOWN,
                display_name="Unknown",
            )
        )
