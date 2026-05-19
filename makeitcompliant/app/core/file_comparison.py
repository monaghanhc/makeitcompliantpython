"""
Backward-compatible facade for legacy ``FileComparison`` module API.

New code should use :class:`~makeitcompliant.app.core.compliance_engine.ComplianceEngine`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from makeitcompliant.app.core.compliance_engine import ComplianceEngine
from makeitcompliant.app.core.license_models import define, describe_fact
from makeitcompliant.app.ml.features import (
    cosine_similarity,
    jaccard_similarity,
    normalize_license_text,
)
from makeitcompliant.app.prolog.engine import PrologEngine
from makeitcompliant.app.prolog.facts_loader import write_runtime_facts

_engine = ComplianceEngine()


def file_to_string(filename: str | Path) -> str:
    return Path(filename).read_text(encoding="utf-8")


def classify(file_string: str) -> str:
    match = _engine.classify(file_string)
    return match.prolog_license_name


def classify_two_files(file_a_string: str, file_b_string: str) -> list[str]:
    match_a, match_b = _engine.classify_pair(file_a_string, file_b_string)
    return [match_a.prolog_license_name, match_b.prolog_license_name]


def get_permissions() -> list[list[str] | None]:
    p = PrologEngine()
    return [p.permissions_for_a(), p.permissions_for_b()]


def get_conditions_for_distribution() -> list[list[str] | None]:
    p = PrologEngine()
    return [p.conditions_distribution_a(), p.conditions_distribution_b()]


def get_conditions_for_modification() -> list[list[str] | None]:
    p = PrologEngine()
    return [p.conditions_modification_a(), p.conditions_modification_b()]


def get_limitations() -> list[list[str] | None]:
    p = PrologEngine()
    return [p.limitations_a(), p.limitations_b()]


def query(goal: str) -> list[dict[str, Any]] | False:
    return PrologEngine().query(goal)


__all__ = [
    "cosine_similarity",
    "jaccard_similarity",
    "normalize_license_text",
    "file_to_string",
    "classify",
    "classify_two_files",
    "get_permissions",
    "get_conditions_for_distribution",
    "get_conditions_for_modification",
    "get_limitations",
    "query",
    "define",
    "describe_fact",
    "write_runtime_facts",
]
