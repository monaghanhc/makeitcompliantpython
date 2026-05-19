# Run unit tests from repository root
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

python -m pytest tests/ -v
