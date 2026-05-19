"""Build ComplianceReport and export JSON / Markdown."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from makeitcompliant.app.core.compliance_models import (
    ComplianceIssue,
    ComplianceReport,
    DependencyInfo,
    DetectedLicense,
    RiskLevel,
)
from makeitcompliant.app.core.risk_scoring import (
    elevate_risk,
    finalize_overall_risk,
    issues_from_low_confidence,
    risk_from_prolog,
)
from makeitcompliant.app.prolog.reasoning_engine import (
    ComplianceReasoningEngine,
    ReasoningEngineError,
)
from makeitcompliant.app.scanner.models import FindingKind, LicenseFinding
from makeitcompliant.app.scanner.project_scanner import ProjectScanner
from makeitcompliant.app.utils.logging_config import get_logger

logger = get_logger("core.report_builder")


def _finding_to_detected(f: LicenseFinding) -> DetectedLicense:
    atom = f.license_atom or "unknown"
    return DetectedLicense(
        identifier=atom,
        source=f.source_kind,
        confidence=f.confidence,
        detection_method=f.evidence[:40] if f.evidence else "scan",
        display_name=f.display_name,
        matched_text=f.path,
    )


def build_compliance_report(project_root: str | Path) -> ComplianceReport:
    root = Path(project_root).resolve()
    report = ComplianceReport(project_path=str(root))
    scanner = ProjectScanner()
    reasoner = ComplianceReasoningEngine()

    try:
        findings = scanner.scan(root)
    except Exception as exc:
        report.scan_errors.append(str(exc))
        report.overall_risk = RiskLevel.UNKNOWN
        report.recommended_actions.append("Fix scan errors and re-run analysis.")
        return report

    report.files_scanned = len(findings)

    project_candidates = [
        f for f in findings if f.kind == FindingKind.PROJECT_LICENSE and f.is_known
    ]
    if project_candidates:
        best = max(project_candidates, key=lambda f: f.confidence)
        report.project_license = _finding_to_detected(best)
    elif any(f.kind == FindingKind.PROJECT_LICENSE for f in findings):
        report.project_license = _finding_to_detected(
            next(f for f in findings if f.kind == FindingKind.PROJECT_LICENSE)
        )

    deps_map: dict[str, LicenseFinding] = {}
    for f in findings:
        if f.package_name and f.kind in (FindingKind.DEPENDENCY, FindingKind.UNKNOWN):
            prev = deps_map.get(f.package_name)
            if prev is None or f.confidence > prev.confidence:
                deps_map[f.package_name] = f

    for name, f in sorted(deps_map.items()):
        lic = _finding_to_detected(f) if f.is_known else DetectedLicense(
            identifier="unknown",
            source=f.source_kind,
            confidence=0.0,
            detection_method="manifest",
            display_name="Unknown",
            matched_text=f.evidence,
        )
        report.dependencies.append(
            DependencyInfo(
                name=name,
                version=None,
                source_file=f.path,
                declared_license=lic,
            )
        )

    report.issues.extend(issues_from_low_confidence(report.project_license, report.dependencies))

    project_atom = report.project_license.identifier if report.project_license else "unknown"
    dep_atoms = [
        (d.name, d.declared_license.identifier)
        for d in report.dependencies
        if d.declared_license
    ]

    try:
        prolog = reasoner.analyze_project_licenses(
            project_atom,
            [a for _, a in dep_atoms],
        )
        report.obligations = prolog.obligations
        report.overall_risk = risk_from_prolog(prolog.overall_risk)
        report.prolog_reasoning_summary = (
            f"Prolog overall risk: {prolog.overall_risk}; "
            f"{len(prolog.dependency_results)} dependencies analyzed."
        )

        for i, dep_result in enumerate(prolog.dependency_results):
            dep_name = dep_atoms[i][0] if i < len(dep_atoms) else dep_result.dependency_license
            if not dep_result.compatible or dep_result.conflict_reasons:
                for reason in dep_result.conflict_reasons or [f"Risk: {dep_result.risk}"]:
                    explanation = ""
                    try:
                        explanation = reasoner.explain_incompatibility(
                            project_atom, dep_result.dependency_license
                        )
                    except ReasoningEngineError:
                        pass
                    report.issues.append(
                        ComplianceIssue(
                            severity=risk_from_prolog(dep_result.risk),
                            title=f"Incompatible or risky dependency: {dep_name}",
                            description=reason,
                            rule_id=f"prolog_{dep_result.dependency_license}",
                            recommendation=explanation
                            or "Review dependency license compatibility.",
                            affected_items=[dep_name],
                            prolog_explanation=explanation,
                        )
                    )
                    report.overall_risk = elevate_risk(
                        report.overall_risk, risk_from_prolog(dep_result.risk)
                    )
    except ReasoningEngineError as exc:
        report.scan_errors.append(f"Prolog reasoning: {exc}")
        report.recommended_actions.append(
            "Install SWI-Prolog on PATH for full rule-based analysis."
        )

    report.overall_risk = finalize_overall_risk(report)
    report.recommended_actions = _build_actions(report)
    return report


def _build_actions(report: ComplianceReport) -> list[str]:
    actions: list[str] = []
    if report.project_license is None or report.project_license.identifier == "unknown":
        actions.append("Add a LICENSE file with an SPDX-License-Identifier line.")
    unknown = [
        d
        for d in report.dependencies
        if d.declared_license and d.declared_license.identifier == "unknown"
    ]
    if unknown:
        actions.append(
            f"Resolve {len(unknown)} unknown dependency license(s) "
            "(audit or lockfile metadata)."
        )
    if report.obligations:
        actions.append("Satisfy project obligations: " + "; ".join(report.obligations[:3]))
    if report.issues:
        actions.append(f"Review {len(report.issues)} compliance issue(s) before release.")
    if not actions:
        actions.append("No critical issues detected. Keep NOTICE files and attributions current.")
    return actions


def _json_default(obj: object) -> object:
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(f"Not serializable: {type(obj)}")


def export_json(report: ComplianceReport, path: Path) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report": asdict(report),
    }
    path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")


def export_markdown(report: ComplianceReport, path: Path) -> None:
    lines = [
        "# Make It Compliant — Project Report",
        "",
        f"**Project:** `{report.project_path}`",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Overall risk:** {report.overall_risk.value.upper()}",
        "",
        "## Project license",
        "",
    ]
    if report.project_license:
        pl = report.project_license
        lines += [
            f"- **{pl.display_name}** ({pl.identifier})",
            f"- Confidence: {pl.confidence:.0%} ({pl.confidence_tier.value})",
            f"- Method: {pl.detection_method}",
            "",
        ]
    else:
        lines.append("*Not detected*\n")

    lines += [
        "## Dependencies",
        "",
        "| Package | License | Confidence |",
        "|---------|---------|------------|",
    ]
    for d in report.dependencies:
        lic = d.declared_license
        if lic:
            lines.append(
                f"| {d.name} | {lic.display_name} | {lic.confidence:.0%} |"
            )
        else:
            lines.append(f"| {d.name} | Unknown | — |")
    lines.append("")

    if report.obligations:
        lines += ["## Obligations", ""]
        for o in report.obligations:
            lines.append(f"- {o}")
        lines.append("")

    if report.issues:
        lines += ["## Issues", ""]
        for issue in report.issues:
            lines.append(f"### [{issue.severity.value.upper()}] {issue.title}")
            lines.append("")
            lines.append(issue.description)
            lines.append("")
            lines.append(f"**Recommendation:** {issue.recommendation}")
            if issue.prolog_explanation:
                lines.append("")
                lines.append(f"> {issue.prolog_explanation}")
            lines.append("")

    if report.recommended_actions:
        lines += ["## Recommended actions", ""]
        for a in report.recommended_actions:
            lines.append(f"1. {a}")
        lines.append("")

    lines.append("---")
    lines.append("*Automated analysis only — not legal advice.*")
    path.write_text("\n".join(lines), encoding="utf-8")
