# Prolog Compliance Rules

## License atoms

Identifiers such as `mit`, `apache_2_0`, `gpl_3_0`, `agpl_3_0`, `unknown` are used in rules. Python maps SPDX strings and classifier output via `license_registry.py`.

## Families

| Family | Examples | Meaning (simplified) |
|--------|----------|----------------------|
| `permissive` | MIT, Apache-2.0, BSD | Relatively few reciprocal duties |
| `weak_copyleft` | LGPL, MPL, EPL | File/module-level sharing duties |
| `strong_copyleft` | GPL, AGPL | Strong reciprocal duties on combined works |
| `proprietary` | — | Restricted redistribution |
| `unknown` | — | Requires manual review |

## Core predicates

```prolog
license(mit).                           % declared in licenses.pl
license_family(mit, permissive).
obligation(mit, include_copyright_notice).
compatible(Project, Dependency).
incompatible(Project, Dependency, Reason).
risk_level(Project, Dependency, Risk).  % low | medium | high | critical
requires_source_disclosure(gpl_3_0).
requires_network_source_disclosure(agpl_3_0).
requires_attribution(mit).
```

## Session facts (generated)

```prolog
project_license(mit).
dependency("lodash", mit).
dependency("unknown-lib", unknown).
```

## High-level analysis API (`analysis.pl`)

These predicates work on **license atoms** directly (no session file required):

### `analyze_dependency(ProjectLicense, DependencyLicense, Result)`

```prolog
?- analyze_dependency(mit, gpl_3_0, R).
R = result(no, high, [strong_copyleft_in_permissive_project]).
```

- `Result = result(Compatible, Risk, Conflicts)`
- `Compatible`: `yes` | `no`
- `Risk`: `low` | `medium` | `high` | `critical`
- `Conflicts`: list of reason atoms (empty when compatible)

### `analyze_project(ProjectLicense, DependencyLicenses, Report)`

```prolog
?- analyze_project(mit, [apache_2_0, unknown], R).
```

- `Report = report(Obligations, DependencyAnalyses, OverallRisk)`
- `DependencyAnalyses`: list of `dep_analysis(License, Result)`

### `explain_incompatibility(ProjectLicense, DependencyLicense, Explanation)`

Returns a human-readable explanation string (or compatibility message when no conflict).

### `required_obligations(ProjectLicense, DependencyLicenses, Obligations)`

Sorted list of unique obligation atoms for the project license and all dependency licenses.

### Python

```python
from makeitcompliant.app.prolog.reasoning_engine import ComplianceReasoningEngine

engine = ComplianceReasoningEngine()
engine.analyze_dependency("mit", "gpl_3_0")
engine.explain_incompatibility("mit", "gpl_3_0")
engine.required_obligations("mit", ["apache_2_0", "unknown"])
engine.analyze_project_licenses("mit", ["apache_2_0", "unknown"])
```

## Session-scoped queries (`queries.pl`)

| Goal | Meaning |
|------|---------|
| `project_obligation(O)` | Obligations on the project license |
| `dependency_conflict(Name, Reason)` | Incompatible dependency |
| `dependency_risk(Name, Risk)` | Risk level for one dependency |
| `dependency_compatible(Name)` | Compatible with project license |
| `project_requires_source_disclosure` | Project triggers source disclosure duties |

## Example incompatibilities

- Permissive **project** + **GPL** dependency → `strong_copyleft_in_permissive_project` (high/critical risk).
- Permissive project + **AGPL** dependency → network obligation conflict.
- Open project + **proprietary** dependency → blocked.
- Any project + **unknown** dependency → review required.

## Extending rules

1. Add atom to `licenses.pl` and family in `families.pl`.
2. Add obligations in `obligations.pl` and flags in `requirements.pl`.
3. Adjust `compatibility.pl` if pairing behavior changes.
4. Add Python mapping in `license_registry.py`.
5. Run tests: `pytest tests/test_project_scanner.py` (with SWI-Prolog on PATH).
