# Build Windows executable with PyInstaller
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

pip install pyinstaller wxPython nltk scikit-learn swiplserver eel

python -m PyInstaller makeitcompliant.spec --noconfirm

Write-Host "Output: dist\MakeItCompliant.exe"
Write-Host "Note: SWI-Prolog must be installed on the target machine unless bundled separately."
