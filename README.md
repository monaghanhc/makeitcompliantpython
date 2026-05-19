# Make It Compliant

**Free & open source (MIT)** — software license compliance for project folders: **ML license detection**, **SWI-Prolog rule reasoning**, and **explainable reports**. No subscription, no cloud required for the desktop engine.

- **Live site (demo):** [https://monaghanhc.github.io/makeitcompliantpython/](https://monaghanhc.github.io/makeitcompliantpython/)
- **Repository:** [github.com/monaghanhc/makeitcompliantpython](https://github.com/monaghanhc/makeitcompliantpython)

## Features

- **Project scanner** — LICENSE, README, manifests (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, …), source headers, NOTICE files
- **License detection** — SPDX first, then TF-IDF vs template corpus; confidence tiers (high / medium / unknown)
- **Prolog engine** — families, obligations, compatibility, `risk_level/3`, `analyze_project/3`, `explain_incompatibility/3`
- **Reports** — issues with recommendations; export **JSON** and **Markdown**
- **Desktop UI** (wxPython) — upload/compare licenses, project scan, Prolog console
- **GitHub Pages** — live landing + SPDX/heuristic browser demo (full ML + Prolog is desktop-only)
- **CI** — pytest + optional SWI-Prolog plunit on every push to `main`

## Quick start

```powershell
pip install -r requirements.txt
# Install SWI-Prolog: https://www.swi-prolog.org/download/stable

python -m makeitcompliant.app.main
```

Legacy entry points still work:

```powershell
python ComplianceSystemForSoftwareLicensingGui.py
```

## Project scan (API)

```python
from makeitcompliant.app.core.report_builder import build_compliance_report

report = build_compliance_report("C:/path/to/your/repo")
print(report.summary())
```

## Tests

```powershell
pip install -r requirements-dev.txt
.\scripts\test.ps1
```

## Windows executable

```powershell
.\scripts\build_windows.ps1
```

See [docs/BUILDING_WINDOWS_EXE.md](docs/BUILDING_WINDOWS_EXE.md).

## Documentation

| Doc | Topic |
|-----|--------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System overview |
| [PROLOG_RULES.md](docs/PROLOG_RULES.md) | Prolog predicates |
| [ML_LICENSE_DETECTION.md](docs/ML_LICENSE_DETECTION.md) | Detection pipeline |
| [COMPLIANCE_REPORTS.md](docs/COMPLIANCE_REPORTS.md) | Report model & export |
| [COMPLIANCE_ENGINE.md](docs/COMPLIANCE_ENGINE.md) | Scanner + reasoning |
| [GITHUB_PAGES.md](docs/GITHUB_PAGES.md) | Static site limits |
| [UPGRADE_PLAN.md](docs/UPGRADE_PLAN.md) | Implementation status |

## Disclaimer

Automated analysis only — **not legal advice**. Verify results with qualified counsel before distribution.
