"""SWI-Prolog rule-based compliance reasoning over project session facts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swiplserver import PrologMQI

from makeitcompliant.app.core.license_registry import (
    atom_to_display,
    conflict_reason_label,
    obligation_label,
)
from makeitcompliant.app.prolog.analysis_api import (
    DependencyAnalysisResult,
    ProjectAnalysisReport,
    parse_dependency_analysis,
    parse_explanation,
    parse_obligations,
    parse_project_report,
)
from makeitcompliant.app.prolog.session_facts import write_project_session
from makeitcompliant.app.utils.logging_config import get_logger
from makeitcompliant.app.utils.paths import (
    COMPLIANCE_KB_FILES,
    get_prolog_compliance_kb_dir,
    get_prolog_session_facts_path,
    prolog_path_for_consult,
)

logger = get_logger("prolog.reasoning")


class ReasoningEngineError(RuntimeError):
    pass


@dataclass
class DependencyVerdict:
    name: str
    license_atom: str
    license_display: str
    compatible: bool
    risk: str
    conflict_reasons: list[str] = field(default_factory=list)


@dataclass
class ReasoningResult:
    project_license_atom: str
    project_obligations: list[str]
    dependency_verdicts: list[DependencyVerdict]
    conflicts: list[tuple[str, str]]  # (dep_name, reason_atom)
    overall_risk: str
    requires_source_disclosure: bool
    requires_network_disclosure: bool
    requires_attribution: bool


class ComplianceReasoningEngine:
    """Load compliance KB + session facts and run structured queries."""

    def __init__(self) -> None:
        self._kb_dir = get_prolog_compliance_kb_dir()

    def _consult_kb(self, thread: Any, *, include_session: bool = False) -> None:
        if not self._kb_dir.is_dir():
            raise ReasoningEngineError(f"Compliance KB not found: {self._kb_dir}")
        for filename in COMPLIANCE_KB_FILES:
            path = prolog_path_for_consult(self._kb_dir / filename)
            thread.query(f'consult("{path}").')
        if include_session:
            session = prolog_path_for_consult(get_prolog_session_facts_path())
            thread.query(f'consult("{session}").')

    def _consult_all(self, thread: Any) -> None:
        self._consult_kb(thread, include_session=True)

    @staticmethod
    def _format_license_list(atoms: list[str]) -> str:
        if not atoms:
            return "[]"
        return "[" + ", ".join(atoms) + "]"

    def _run(self, goal: str, *, session: bool = False) -> list[dict[str, Any]] | False:
        try:
            with PrologMQI() as mqi:
                with mqi.create_thread() as thread:
                    self._consult_kb(thread, include_session=session)
                    return thread.query(goal)
        except ReasoningEngineError:
            raise
        except Exception as exc:
            logger.exception("Prolog query failed: %s", goal)
            raise ReasoningEngineError(str(exc)) from exc

    def analyze_dependency(
        self,
        project_license: str,
        dependency_license: str,
    ) -> DependencyAnalysisResult:
        """
        ``analyze_dependency(ProjectLicense, DependencyLicense, Result).``

        Result is ``result(Compatible, Risk, Conflicts)`` with ``Compatible`` in ``yes|no``.
        """
        goal = (
            f"analyze_dependency({project_license}, {dependency_license}, Result)."
        )
        rows = self._run(goal)
        if rows is False:
            raise ReasoningEngineError(
                f"analyze_dependency failed for {project_license}/{dependency_license}"
            )
        return parse_dependency_analysis(project_license, dependency_license, rows[0])

    def explain_incompatibility(
        self,
        project_license: str,
        dependency_license: str,
    ) -> str:
        """``explain_incompatibility(ProjectLicense, DependencyLicense, Explanation).``"""
        goal = (
            f"explain_incompatibility({project_license}, {dependency_license}, "
            f"Explanation)."
        )
        rows = self._run(goal)
        return parse_explanation(rows if rows is not False else False)

    def required_obligations(
        self,
        project_license: str,
        dependency_licenses: list[str],
    ) -> list[str]:
        """``required_obligations(ProjectLicense, DependencyLicenses, Obligations).``"""
        deps = self._format_license_list(dependency_licenses)
        goal = f"required_obligations({project_license}, {deps}, Obligations)."
        rows = self._run(goal)
        if rows is False:
            return []
        return parse_obligations(rows)

    def analyze_project_licenses(
        self,
        project_license: str,
        dependency_licenses: list[str],
    ) -> ProjectAnalysisReport:
        """
        ``analyze_project(ProjectLicense, DependencyLicenses, Report).``

        Report = ``report(Obligations, DependencyAnalyses, OverallRisk)``.
        """
        deps = self._format_license_list(dependency_licenses)
        goal = f"analyze_project({project_license}, {deps}, Report)."
        rows = self._run(goal)
        return parse_project_report(project_license, rows, dependency_licenses)

    def analyze(
        self,
        project_license_atom: str,
        dependencies: list[tuple[str, str]],
    ) -> ReasoningResult:
        """Session-based scan analysis; uses ``analyze_project/3`` when possible."""
        dep_atoms = [atom for _, atom in dependencies]
        write_project_session(project_license_atom, dependencies)

        try:
            report = self.analyze_project_licenses(project_license_atom, dep_atoms)
        except ReasoningEngineError:
            report = None

        try:
            with PrologMQI() as mqi:
                with mqi.create_thread() as thread:
                    self._consult_all(thread)
                    if report and report.dependency_results:
                        verdicts = self._verdicts_from_report(
                            dependencies, report.dependency_results
                        )
                        obligations = report.obligations
                        overall = report.overall_risk
                        conflicts = self._conflicts_from_report(
                            dependencies, report.dependency_results
                        )
                    else:
                        obligations = self._query_obligations(thread)
                        verdicts = self._query_dependency_verdicts(thread, dependencies)
                        conflicts = self._query_conflicts(thread)
                        overall = self._aggregate_risk(verdicts)

                    return ReasoningResult(
                        project_license_atom=project_license_atom,
                        project_obligations=obligations,
                        dependency_verdicts=verdicts,
                        conflicts=conflicts,
                        overall_risk=overall,
                        requires_source_disclosure=self._query_true(
                            thread, "project_requires_source_disclosure."
                        ),
                        requires_network_disclosure=self._query_true(
                            thread, "project_requires_network_disclosure."
                        ),
                        requires_attribution=self._query_true(
                            thread, "project_requires_attribution."
                        ),
                    )
        except ReasoningEngineError:
            raise
        except Exception as exc:
            logger.exception("Compliance reasoning failed")
            raise ReasoningEngineError(str(exc)) from exc

    @staticmethod
    def _verdicts_from_report(
        dependencies: list[tuple[str, str]],
        results: list[DependencyAnalysisResult],
    ) -> list[DependencyVerdict]:
        by_atom = {r.dependency_license: r for r in results}
        verdicts: list[DependencyVerdict] = []
        for name, atom in dependencies:
            r = by_atom.get(atom)
            if not r:
                continue
            verdicts.append(
                DependencyVerdict(
                    name=name,
                    license_atom=atom,
                    license_display=atom_to_display(atom),
                    compatible=r.compatible,
                    risk=r.risk,
                    conflict_reasons=r.conflict_reasons,
                )
            )
        return verdicts

    @staticmethod
    def _conflicts_from_report(
        dependencies: list[tuple[str, str]],
        results: list[DependencyAnalysisResult],
    ) -> list[tuple[str, str]]:
        by_atom = {r.dependency_license: r for r in results}
        out: list[tuple[str, str]] = []
        for name, atom in dependencies:
            r = by_atom.get(atom)
            if r and (not r.compatible or r.conflict_reasons):
                reason = (
                    r.conflict_reasons[0]
                    if r.conflict_reasons
                    else f"Risk level: {r.risk}"
                )
                out.append((name, reason))
        return out

    @staticmethod
    def _query_true(thread: Any, goal: str) -> bool:
        return thread.query(goal) is not False

    @staticmethod
    def _query_obligations(thread: Any) -> list[str]:
        result = thread.query("project_obligation(X).")
        if result is False:
            return []
        atoms = sorted({row["X"] for row in result})
        return [obligation_label(a) for a in atoms]

    def _query_dependency_verdicts(
        self,
        thread: Any,
        dependencies: list[tuple[str, str]],
    ) -> list[DependencyVerdict]:
        verdicts: list[DependencyVerdict] = []
        for dep_name, dep_atom in dependencies:
            risk = self._risk_for_dep(thread, dep_name)
            compatible = self._compatible_for_dep(thread, dep_name)
            reasons = self._conflicts_for_dep(thread, dep_name)
            verdicts.append(
                DependencyVerdict(
                    name=dep_name,
                    license_atom=dep_atom,
                    license_display=atom_to_display(dep_atom),
                    compatible=compatible,
                    risk=risk,
                    conflict_reasons=[conflict_reason_label(r) for r in reasons],
                )
            )
        return verdicts

    @staticmethod
    def _dep_goal_prefix(dep_name: str) -> str:
        escaped = dep_name.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    def _risk_for_dep(self, thread: Any, dep_name: str) -> str:
        dep = self._dep_goal_prefix(dep_name)
        goal = f"dependency_risk({dep}, R)."
        result = thread.query(goal)
        if result is False:
            return "medium"
        return result[0]["R"]

    def _compatible_for_dep(self, thread: Any, dep_name: str) -> bool:
        dep = self._dep_goal_prefix(dep_name)
        return thread.query(f"dependency_compatible({dep}).") is not False

    def _conflicts_for_dep(self, thread: Any, dep_name: str) -> list[str]:
        dep = self._dep_goal_prefix(dep_name)
        goal = f"dependency_conflict({dep}, R)."
        result = thread.query(goal)
        if result is False:
            return []
        return [row["R"] for row in result]

    @staticmethod
    def _query_conflicts(thread: Any) -> list[tuple[str, str]]:
        result = thread.query("dependency_conflict(N, R).")
        if result is False:
            return []
        return [(row["N"], row["R"]) for row in result]

    @staticmethod
    def _aggregate_risk(verdicts: list[DependencyVerdict]) -> str:
        order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        if not verdicts:
            return "low"
        worst = max(verdicts, key=lambda v: order.get(v.risk, 1))
        return worst.risk
