"""Structured compliance scan results."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class FindingKind(str, Enum):
    PROJECT_LICENSE = "project_license"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"


@dataclass
class LicenseFinding:
    path: str
    source_kind: str
    license_atom: str | None
    display_name: str
    confidence: float
    evidence: str
    package_name: str | None = None
    kind: FindingKind = FindingKind.UNKNOWN

    @property
    def is_known(self) -> bool:
        return self.license_atom is not None and self.license_atom != "unknown"


@dataclass
class LicenseConflict:
    dependency_name: str
    dependency_license: str
    reason: str
    severity: RiskLevel = RiskLevel.HIGH


@dataclass
class ProjectComplianceReport:
    project_path: str
    project_license: LicenseFinding | None
    dependency_licenses: list[LicenseFinding] = field(default_factory=list)
    unknown_licenses: list[LicenseFinding] = field(default_factory=list)
    conflicts: list[LicenseConflict] = field(default_factory=list)
    obligations: list[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.UNKNOWN
    recommended_actions: list[str] = field(default_factory=list)
    scan_errors: list[str] = field(default_factory=list)
    files_scanned: int = 0

    def summary(self) -> str:
        proj = self.project_license.display_name if self.project_license else "Not detected"
        return (
            f"Project: {Path(self.project_path).name}\n"
            f"License: {proj}\n"
            f"Dependencies: {len(self.dependency_licenses)} known, "
            f"{len(self.unknown_licenses)} unknown\n"
            f"Conflicts: {len(self.conflicts)}\n"
            f"Risk: {self.risk_level.value}\n"
        )
