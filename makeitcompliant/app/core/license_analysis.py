"""Full ML + dual Prolog analysis for uploaded license pairs."""

from __future__ import annotations

from dataclasses import dataclass, field

from makeitcompliant.app.core.license_models import define
from makeitcompliant.app.core.license_registry import atom_to_display
from makeitcompliant.app.ml.license_detector import LicenseDetector
from makeitcompliant.app.prolog.engine import PrologEngine, PrologEngineError
from makeitcompliant.app.prolog.facts_loader import write_runtime_facts
from makeitcompliant.app.prolog.reasoning_engine import (
    ComplianceReasoningEngine,
    ReasoningEngineError,
)
from makeitcompliant.app.prolog.runtime import check_prolog
from makeitcompliant.app.utils.logging_config import get_logger

logger = get_logger("core.license_analysis")


@dataclass
class LicenseSideAnalysis:
    display_name: str
    atom: str
    confidence: float
    detection_method: str
    permissions: list[str] = field(default_factory=list)
    distribution_conditions: list[str] = field(default_factory=list)
    modification_conditions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


@dataclass
class PairComplianceAnalysis:
    license_a: LicenseSideAnalysis
    license_b: LicenseSideAnalysis
    cross_compatible: bool | None
    cross_risk: str | None
    cross_explanation: str | None
    cross_conflict_reasons: list[str] = field(default_factory=list)
    obligations: list[str] = field(default_factory=list)
    prolog_available: bool = False
    prolog_message: str = ""


def _describe_list(atoms: list[str] | None) -> list[str]:
    if not atoms:
        return []
    out: list[str] = []
    for a in atoms:
        text = define(a)
        out.append(text if text else a)
    return out


def analyze_license_pair(text_a: str, text_b: str) -> PairComplianceAnalysis:
    """
    Maximize ML + Prolog usage:
    - LicenseDetector (SPDX + batch TF-IDF) for both texts
    - Legacy KB permissions via allLicenseFactsBaseCopy
    - New compliance KB via analyze_dependency / required_obligations
    """
    detector = LicenseDetector()
    ra = detector.detect(text_a, source="upload_a")
    rb = detector.detect(text_b, source="upload_b")

    legacy_a = atom_to_display(ra.license.identifier)
    legacy_b = atom_to_display(rb.license.identifier)
    write_runtime_facts(license_a=legacy_a, license_b=legacy_b)

    side_a = LicenseSideAnalysis(
        display_name=ra.license.display_name,
        atom=ra.license.identifier,
        confidence=ra.license.confidence,
        detection_method=ra.license.detection_method,
    )
    side_b = LicenseSideAnalysis(
        display_name=rb.license.display_name,
        atom=rb.license.identifier,
        confidence=rb.license.confidence,
        detection_method=rb.license.detection_method,
    )

    status = check_prolog()
    analysis = PairComplianceAnalysis(
        license_a=side_a,
        license_b=side_b,
        prolog_available=status.available,
        prolog_message=status.message,
    )

    if status.available:
        try:
            legacy = PrologEngine()
            side_a.permissions = _describe_list(legacy.permissions_for_a())
            side_b.permissions = _describe_list(legacy.permissions_for_b())
            side_a.distribution_conditions = _describe_list(legacy.conditions_distribution_a())
            side_b.distribution_conditions = _describe_list(legacy.conditions_distribution_b())
            side_a.modification_conditions = _describe_list(legacy.conditions_modification_a())
            side_b.modification_conditions = _describe_list(legacy.conditions_modification_b())
            side_a.limitations = _describe_list(legacy.limitations_a())
            side_b.limitations = _describe_list(legacy.limitations_b())
        except PrologEngineError as exc:
            logger.warning("Legacy Prolog KB: %s", exc)

        try:
            reasoner = ComplianceReasoningEngine()
            dep = reasoner.analyze_dependency(side_a.atom, side_b.atom)
            analysis.cross_compatible = dep.compatible
            analysis.cross_risk = dep.risk
            analysis.cross_conflict_reasons = dep.conflict_reasons
            analysis.cross_explanation = reasoner.explain_incompatibility(
                side_a.atom, side_b.atom
            )
            analysis.obligations = reasoner.required_obligations(
                side_a.atom, [side_b.atom]
            )
        except ReasoningEngineError as exc:
            logger.warning("Compliance Prolog KB: %s", exc)
            analysis.cross_explanation = str(exc)

    return analysis
