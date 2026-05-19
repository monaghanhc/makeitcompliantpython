"""Canonical compliance analysis data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ConfidenceTier(str, Enum):
    HIGH = "high"  # >= 0.90
    MEDIUM = "medium"  # 0.70 - 0.89
    LOW = "low"  # < 0.70
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class DetectedLicense:
    identifier: str  # Prolog atom e.g. mit, apache_2_0
    source: str
    confidence: float
    detection_method: str
    display_name: str = ""
    spdx_id: str | None = None
    matched_text: str | None = None
    confidence_tier: ConfidenceTier = ConfidenceTier.UNKNOWN

    def __post_init__(self) -> None:
        if not self.display_name:
            from makeitcompliant.app.core.license_registry import atom_to_display

            self.display_name = atom_to_display(self.identifier)
        self.confidence_tier = confidence_tier_for(self.confidence)


def confidence_tier_for(score: float) -> ConfidenceTier:
    if score >= 0.90:
        return ConfidenceTier.HIGH
    if score >= 0.70:
        return ConfidenceTier.MEDIUM
    if score > 0.0:
        return ConfidenceTier.LOW
    return ConfidenceTier.UNKNOWN


@dataclass
class DependencyInfo:
    name: str
    version: str | None
    source_file: str
    declared_license: DetectedLicense | None = None


@dataclass
class ComplianceIssue:
    severity: RiskLevel
    title: str
    description: str
    rule_id: str
    recommendation: str
    affected_items: list[str] = field(default_factory=list)
    confidence: float | None = None
    prolog_explanation: str | None = None


@dataclass
class ComplianceReport:
    project_path: str
    project_license: DetectedLicense | None
    dependencies: list[DependencyInfo] = field(default_factory=list)
    obligations: list[str] = field(default_factory=list)
    issues: list[ComplianceIssue] = field(default_factory=list)
    overall_risk: RiskLevel = RiskLevel.UNKNOWN
    recommended_actions: list[str] = field(default_factory=list)
    scan_errors: list[str] = field(default_factory=list)
    files_scanned: int = 0
    prolog_reasoning_summary: str = ""

    def summary(self) -> str:
        proj = self.project_license.display_name if self.project_license else "Not detected"
        known = sum(
            1
            for d in self.dependencies
            if d.declared_license and d.declared_license.identifier != "unknown"
        )
        unknown = len(self.dependencies) - known
        return (
            f"Project license: {proj}\n"
            f"Dependencies: {known} known, {unknown} unknown\n"
            f"Issues: {len(self.issues)}\n"
            f"Overall risk: {self.overall_risk.value}\n"
        )
