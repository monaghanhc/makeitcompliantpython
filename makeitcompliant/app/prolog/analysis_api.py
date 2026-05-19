"""Parse SWI-Prolog results from analysis.pl predicates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from makeitcompliant.app.core.license_registry import (
    atom_to_display,
    conflict_reason_label,
    obligation_label,
)


@dataclass(frozen=True)
class DependencyAnalysisResult:
    project_license: str
    dependency_license: str
    compatible: bool
    risk: str
    conflict_reasons: list[str] = field(default_factory=list)

    @property
    def dependency_display(self) -> str:
        return atom_to_display(self.dependency_license)


@dataclass
class ProjectAnalysisReport:
    project_license: str
    obligations: list[str]
    dependency_results: list[DependencyAnalysisResult]
    overall_risk: str

    @property
    def project_display(self) -> str:
        return atom_to_display(self.project_license)


def _atom(value: Any) -> str:
    if isinstance(value, str):
        return value
    return str(value)


def _parse_result_compound(row: dict[str, Any]) -> DependencyAnalysisResult | None:
    """Parse Result from analyze_dependency/3 → result(Compat, Risk, Conflicts)."""
    result = row.get("Result") or row.get("result")
    if result is None:
        return None
    return _parse_result_term(result)


def _parse_result_term(result: Any) -> DependencyAnalysisResult | None:
    if isinstance(result, dict):
        # MQI compound: {'functor': 'result', 'args': ['yes', 'low', []]}
        if result.get("functor") == "result" and "args" in result:
            args = result["args"]
            if len(args) >= 3:
                compat = _atom(args[0]) == "yes"
                risk = _atom(args[1])
                conflicts_raw = args[2]
                conflicts = _parse_list_atoms(conflicts_raw)
                return DependencyAnalysisResult(
                    project_license="",
                    dependency_license="",
                    compatible=compat,
                    risk=risk,
                    conflict_reasons=[conflict_reason_label(c) for c in conflicts],
                )
    return None


def parse_dependency_analysis(
    project: str,
    dependency: str,
    row: dict[str, Any],
) -> DependencyAnalysisResult:
    parsed = _parse_result_compound(row)
    if parsed:
        return DependencyAnalysisResult(
            project_license=project,
            dependency_license=dependency,
            compatible=parsed.compatible,
            risk=parsed.risk,
            conflict_reasons=parsed.conflict_reasons,
        )
    compat = row.get("Compatible") == "yes" or row.get("Compat") == "yes"
    return DependencyAnalysisResult(
        project_license=project,
        dependency_license=dependency,
        compatible=compat,
        risk=_atom(row.get("Risk", "medium")),
        conflict_reasons=[],
    )


def _parse_list_atoms(value: Any) -> list[str]:
    if value is False or value is None:
        return []
    if isinstance(value, list):
        return [_atom(v) for v in value]
    if isinstance(value, dict) and value.get("functor") == ".":
        # Prolog list cell
        head = _atom(value.get("args", ["", ""])[0])
        tail = value.get("args", ["", ""])[1]
        return [head] + _parse_list_atoms(tail)
    if isinstance(value, str):
        return [value]
    return []


def parse_obligations(rows: list[dict[str, Any]] | False) -> list[str]:
    if rows is False:
        return []
    atoms: list[str] = []
    for row in rows:
        if "Obligations" in row:
            atoms.extend(_parse_list_atoms(row["Obligations"]))
        elif "X" in row:
            atoms.append(_atom(row["X"]))
        elif "Obl" in row:
            atoms.append(_atom(row["Obl"]))
    return [obligation_label(a) for a in sorted(set(atoms))]


def parse_explanation(row: dict[str, Any] | False) -> str:
    if row is False:
        return "No explanation available."
    if isinstance(row, list) and row:
        row = row[0]
    if not isinstance(row, dict):
        return str(row)
    exp = row.get("Explanation") or row.get("explanation")
    if exp is None:
        return "No explanation available."
    if isinstance(exp, str):
        return exp
    if isinstance(exp, list):
        return "".join(exp)
    return str(exp)


def parse_project_report(
    project: str,
    prolog_rows: list[dict[str, Any]] | False,
    dependency_licenses: list[str],
) -> ProjectAnalysisReport:
    """Parse analyze_project/3 → report(Obligations, Analyses, OverallRisk)."""
    obligations: list[str] = []
    analyses: list[DependencyAnalysisResult] = []
    overall = "low"

    if prolog_rows is False or not prolog_rows:
        return ProjectAnalysisReport(
            project_license=project,
            obligations=[],
            dependency_results=[],
            overall_risk="low",
        )

    report_term = prolog_rows[0].get("Report")
    if isinstance(report_term, dict) and report_term.get("functor") == "report":
        args = report_term.get("args", [])
        if len(args) >= 3:
            obligations = [obligation_label(a) for a in _parse_list_atoms(args[0])]
            analyses = _parse_dep_analyses(project, args[1])
            overall = _atom(args[2])

    if not analyses and dependency_licenses:
        # Fallback if compound parsing failed
        analyses = [
            DependencyAnalysisResult(
                project_license=project,
                dependency_license=d,
                compatible=True,
                risk="medium",
            )
            for d in dependency_licenses
        ]

    return ProjectAnalysisReport(
        project_license=project,
        obligations=obligations,
        dependency_results=analyses,
        overall_risk=overall,
    )


def _parse_dep_analyses(
    project: str,
    analyses_term: Any,
) -> list[DependencyAnalysisResult]:
    items = _parse_list_compounds(analyses_term)
    results: list[DependencyAnalysisResult] = []
    for item in items:
        if isinstance(item, dict) and item.get("functor") == "dep_analysis":
            args = item.get("args", [])
            if len(args) >= 2:
                dep = _atom(args[0])
                parsed = _parse_result_term(args[1])
                if parsed:
                    results.append(
                        DependencyAnalysisResult(
                            project_license=project,
                            dependency_license=dep,
                            compatible=parsed.compatible,
                            risk=parsed.risk,
                            conflict_reasons=parsed.conflict_reasons,
                        )
                    )
    return results


def _parse_list_compounds(value: Any) -> list[Any]:
    if value is None or value is False:
        return []
    if isinstance(value, list) and value and not isinstance(value[0], dict):
        return value
    if isinstance(value, dict) and value.get("functor") == ".":
        head = value["args"][0]
        tail = value["args"][1]
        return [head] + _parse_list_compounds(tail)
    if isinstance(value, list):
        out: list[Any] = []
        for v in value:
            out.extend(_parse_list_compounds(v))
        return out
    return [value]
