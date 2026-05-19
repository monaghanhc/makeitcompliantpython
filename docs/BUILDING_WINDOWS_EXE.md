# Building the Windows Executable

## Prerequisites

- Python 3.10+
- `pip install -r requirements.txt pyinstaller`
- **SWI-Prolog** installed and on PATH (for full Prolog analysis at runtime)
- wxPython

## Build

```powershell
.\scripts\build_windows.ps1
```

Or manually:

```powershell
pyinstaller makeitcompliant.spec --noconfirm
```

Output: `dist\MakeItCompliant.exe`

## Bundled assets

The spec includes:

- `license_templates/`
- `prolog/kb/compliance/*.pl`
- `allLicenseFactsBaseCopy.pl` (legacy two-file analysis)
- `web/` (optional)

## Path resolution

`makeitcompliant.app.utils.paths.get_resource_root()` uses `sys._MEIPASS` when frozen.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Prolog queries fail | Install SWI-Prolog; verify `swipl` in PATH |
| Missing templates | Rebuild; check `datas` in `makeitcompliant.spec` |
| wx import error | `pip install wxPython` before build |
