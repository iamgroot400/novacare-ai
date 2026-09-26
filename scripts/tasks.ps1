<#
  NovaCare AI — Windows task runner (PowerShell equivalent of the Makefile)
  Usage:  ./scripts/tasks.ps1 <task>
  Tasks:  env setup seed test up down logs models smoke clean
#>
param([Parameter(Mandatory = $true)][string]$Task)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

switch ($Task) {
  "env" {
    if (-not (Test-Path .env)) { Copy-Item .env.example .env; Write-Host "Created .env" }
  }
  "setup" {
    & $PSScriptRoot/tasks.ps1 env
    python -m venv backend/.venv
    backend/.venv/Scripts/pip install -U pip
    backend/.venv/Scripts/pip install -r backend/requirements.txt
    Push-Location frontend; npm install; Pop-Location
  }
  "seed"  { python scripts/seed.py }
  "test"  {
    Push-Location backend
    backend/.venv/Scripts/python -m pytest -q tests/test_store_service.py tests/test_api.py
    Pop-Location
  }
  "up"    { docker compose up -d; Write-Host "Now run: ./scripts/tasks.ps1 models" }
  "down"  { docker compose down }
  "logs"  { docker compose logs -f --tail=100 }
  "models" {
    docker compose exec -T backend python -c "from app.rag import get_rag; print(get_rag().reindex(force=True))"
  }
  "smoke" { python scripts/smoke_test.py }
  "clean" { docker compose down -v }
  default { Write-Host "Unknown task: $Task" }
}
