# Make It Compliant — Upgrade Plan

| # | Area | Status | Notes |
|---|------|--------|-------|
| 1 | Audit | Done | `docs/ARCHITECTURE.md` |
| 2 | Python package | Done | `makeitcompliant/app/` |
| 3 | Prolog KB | Done | `prolog/kb/compliance/`, `analysis.pl`, `tests.pl` |
| 4 | ML detection | Done | SPDX → TF-IDF, `LicenseDetector`, tiers |
| 5 | Project scanner | Done | Manifests, headers, NOTICE, limits |
| 6 | Risk + reports | Done | `ComplianceReport`, export JSON/MD |
| 7 | UI | Done | Tabbed scanner, export, risk badge |
| 8 | Tests | Done | pytest + plunit file |
| 9 | Windows exe | Done | `makeitcompliant.spec`, `build_windows.ps1` |
| 10 | GitHub Pages | Done | `web/index.html`, deploy workflow |
| 11 | Docs | Done | ML, reports, building, pages |

## Architecture principle

**ML detects and scores. Prolog reasons and explains.**

## Prolog API

```prolog
analyze_dependency/3
analyze_project/3
explain_incompatibility/3
required_obligations/3
```

## Run locally

```powershell
pip install -r requirements-dev.txt
python -m makeitcompliant.app.main
python -m pytest tests/ -q
```

## plunit (optional)

```bash
cd prolog/kb/compliance
swipl -g run_tests,halt -t halt tests.pl
```
