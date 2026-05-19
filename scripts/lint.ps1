# Lint Python sources
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

python -m ruff check makeitcompliant tests
