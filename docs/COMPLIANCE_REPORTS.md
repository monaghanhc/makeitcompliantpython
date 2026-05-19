# Compliance Reports

## Canonical model

`ComplianceReport` in `core/compliance_models.py`:

- `project_license`: `DetectedLicense`
- `dependencies`: `DependencyInfo` list
- `issues`: `ComplianceIssue` list (severity, rule_id, recommendation, prolog_explanation)
- `overall_risk`: `low` | `medium` | `high` | `critical` | `unknown`
- `obligations`, `recommended_actions`, `prolog_reasoning_summary`

## Building a report

```python
from makeitcompliant.app.core.report_builder import build_compliance_report

report = build_compliance_report("/path/to/project")
```

## Export

```python
from pathlib import Path
from makeitcompliant.app.core.report_builder import export_json, export_markdown

export_json(report, Path("report.json"))
export_markdown(report, Path("report.md"))
```

Desktop UI: **Project Scanner → Export JSON / Export Markdown**.

## Issue structure

Each `ComplianceIssue` includes:

- **detected item** (`affected_items`)
- **rule** (`rule_id`, often `prolog_*` or `ml_low_confidence_*`)
- **human explanation** (`description`, `prolog_explanation`)
- **recommended action**

## Sample Markdown sections

1. Project license  
2. Dependency table  
3. Obligations  
4. Issues (severity-tagged)  
5. Recommended actions  
