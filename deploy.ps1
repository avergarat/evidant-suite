# ============================================================
#  deploy.ps1  —  Commit + Push a GitHub -> Streamlit Cloud
#  Uso: .\deploy.ps1            (mensaje automatico)
#       .\deploy.ps1 "mi nota"  (mensaje personalizado)
# ============================================================

param(
    [string]$Mensaje = ""
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  EVIDANT SUITE -- Deploy a Streamlit   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar cambios
$status = git status --short
if (-not $status) {
    Write-Host "OK  Sin cambios pendientes. Nada que subir." -ForegroundColor Green
    exit 0
}

Write-Host "Archivos modificados:" -ForegroundColor Yellow
git status --short
Write-Host ""

# 2. Mensaje de commit
if (-not $Mensaje) {
    $fecha    = Get-Date -Format "yyyy-MM-dd HH:mm"
    $archivos = (git diff --name-only 2>$null) | ForEach-Object { Split-Path $_ -Leaf }
    $resumen  = ($archivos | Select-Object -Unique -First 3) -join ", "
    if (-not $resumen) { $resumen = "varios archivos" }
    $Mensaje  = "update: $resumen -- $fecha"
}

Write-Host "Commit: $Mensaje" -ForegroundColor Cyan
Write-Host ""

# 3. Stage + Commit + Push
try {
    git add -A
    git commit -m $Mensaje
    Write-Host ""
    Write-Host "Subiendo a GitHub..." -ForegroundColor Yellow
    git push origin main
    Write-Host ""
    Write-Host "Push completado OK" -ForegroundColor Green
}
catch {
    Write-Host ""
    Write-Host "ERROR durante git: $_" -ForegroundColor Red
    exit 1
}

# 4. Info
Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor DarkCyan
Write-Host " Streamlit Cloud se actualiza al recibir" -ForegroundColor DarkCyan
Write-Host " el commit. Espera ~30 seg en la app."    -ForegroundColor DarkCyan
Write-Host ""
Write-Host " https://evidant-suite-grrnubdwsjqikhyokozzos.streamlit.app" -ForegroundColor White
Write-Host "----------------------------------------" -ForegroundColor DarkCyan
Write-Host ""
