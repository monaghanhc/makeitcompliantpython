"""Orchestrates classification, Prolog fact generation, and KB queries."""

from __future__ import annotations

from dataclasses import dataclass

from makeitcompliant.app.ml.classifier import LicenseClassifier, MatchResult
from makeitcompliant.app.ml.features import cosine_similarity, jaccard_similarity
from makeitcompliant.app.prolog.engine import PrologEngine
from makeitcompliant.app.prolog.facts_loader import write_runtime_facts
from makeitcompliant.app.utils.logging_config import get_logger

logger = get_logger("core.compliance_engine")


@dataclass
class PairAnalysis:
    match_a: MatchResult
    match_b: MatchResult
    cosine_between_uploads: float
    jaccard_between_uploads: float
    permissions_a: list[str] | None
    permissions_b: list[str] | None
    conditions_distribution_a: list[str] | None
    conditions_distribution_b: list[str] | None
    conditions_modification_a: list[str] | None
    conditions_modification_b: list[str] | None
    limitations_a: list[str] | None
    limitations_b: list[str] | None


class ComplianceEngine:
    def __init__(
        self,
        classifier: LicenseClassifier | None = None,
        prolog: PrologEngine | None = None,
    ) -> None:
        self._classifier = classifier or LicenseClassifier()
        self._prolog = prolog or PrologEngine()

    def classify(self, license_text: str, *, min_confidence: float | None = None) -> MatchResult:
        match = self._classifier.match(license_text, min_confidence=min_confidence)
        write_runtime_facts(license_a=match.prolog_license_name)
        return match

    def classify_pair(self, text_a: str, text_b: str) -> tuple[MatchResult, MatchResult]:
        match_a = self._classifier.match(text_a)
        match_b = self._classifier.match(text_b)
        write_runtime_facts(
            license_a=match_a.prolog_license_name,
            license_b=match_b.prolog_license_name,
        )
        logger.info(
            "Classified licenses: %s (%.2f%%), %s (%.2f%%)",
            match_a.prolog_license_name,
            match_a.confidence_percent,
            match_b.prolog_license_name,
            match_b.confidence_percent,
        )
        return match_a, match_b

    def analyze_pair(self, text_a: str, text_b: str) -> PairAnalysis:
        match_a, match_b = self.classify_pair(text_a, text_b)
        return PairAnalysis(
            match_a=match_a,
            match_b=match_b,
            cosine_between_uploads=cosine_similarity(text_a, text_b),
            jaccard_between_uploads=jaccard_similarity(text_a, text_b),
            permissions_a=self._prolog.permissions_for_a(),
            permissions_b=self._prolog.permissions_for_b(),
            conditions_distribution_a=self._prolog.conditions_distribution_a(),
            conditions_distribution_b=self._prolog.conditions_distribution_b(),
            conditions_modification_a=self._prolog.conditions_modification_a(),
            conditions_modification_b=self._prolog.conditions_modification_b(),
            limitations_a=self._prolog.limitations_a(),
            limitations_b=self._prolog.limitations_b(),
        )
