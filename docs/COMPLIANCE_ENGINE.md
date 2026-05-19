# Compliance Engine

Make It Compliant combines **project scanning**, **ML license detection**, and **SWI-Prolog rule-based reasoning**.

## Project scanner

`ProjectScanner` walks a repository (skipping `node_modules`, `.git`, `venv`, etc.) and detects:

| Source | Examples |
|--------|----------|
| License files | `LICENSE`, `COPYING`, `NOTICE` |
| README | SPDX lines, license mentions |
| Manifests | `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `Gemfile`, `.csproj`, `requirements.txt` |
| Lockfiles | `package-lock.json` (dependency `license` fields) |
| Source headers | SPDX / GPL-family hints in first 40 lines |

Dependency licenses are **known** when declared in lockfiles or manifests; otherwise they are marked **unknown** for manual review.

## Rule engine (Prolog)

KB location: `prolog/kb/compliance/`

| File | Role |
|------|------|
| `licenses.pl` | Canonical license atoms |
| `families.pl` | permissive / weak_copyleft / strong_copyleft |
| `obligations.pl` | `obligation(License, Atom)` |
| `requirements.pl` | `requires_source_disclosure/1`, etc. |
| `compatibility.pl` | `compatible/2`, `incompatible/3`, `risk_level/3` |
| `queries.pl` | Session queries over `project_license/1` and `dependency/2` |

Python writes `compliance_session.pl` with facts, then consults the KB via **SWI-Prolog MQI**.

## Report

`ProjectComplianceService.analyze_project(path)` returns:

- `project_license` — best detected project license
- `dependency_licenses` / `unknown_licenses`
- `conflicts` — from `incompatible/3` and high `risk_level/3`
- `obligations` — project-level obligations
- `risk_level` — `low` | `medium` | `high` | `critical`
- `recommended_actions` — human-readable next steps

## Desktop UI

**Analyze → Scan Project Folder…** or **View → Project Scanner**

## Limitations

- Not legal advice; rules are simplified compatibility heuristics.
- Many ecosystems do not embed dependency licenses in manifests (use lockfiles or external audit tools).
- Legacy `allLicenseFactsBaseCopy.pl` remains for two-file license comparison; project scan uses the new KB.
