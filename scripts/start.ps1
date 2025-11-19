# Script de Inicio Rápido - Sistema Domótico
# ===========================================

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         🏠 SISTEMA DOMÓTICO - INICIO RÁPIDO 🏠        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Navegar al directorio raíz del proyecto
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Verificar que existe el servidor
if (-not (Test-Path "server\server_domotico.py")) {
    Write-Host "❌ ERROR: No se encuentra server\server_domotico.py" -ForegroundColor Red
    Write-Host "   Asegúrate de estar en el directorio correcto" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Verificar que existe el venv
if (-not (Test-Path "venv")) {
    Write-Host "❌ ERROR: Entorno virtual no encontrado" -ForegroundColor Red
    Write-Host "   Ejecuta primero: .\scripts\install.ps1" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host "🚀 Iniciando servidor domótico..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Servicios que se iniciarán:" -ForegroundColor Cyan
Write-Host "  ✓ TCP Socket (Puerto 5000) - Comandos de control" -ForegroundColor White
Write-Host "  ✓ UDP Broadcast (Puerto 5001) - Telemetría cada 2s" -ForegroundColor White
Write-Host "  ✓ API REST (Puerto 8080) - Gemelo digital web" -ForegroundColor White
Write-Host ""
Write-Host "────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host ""
Write-Host "📖 Instrucciones:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1️⃣  Para usar el cliente CLI:" -ForegroundColor Cyan
Write-Host "   Abre otra terminal PowerShell y ejecuta:" -ForegroundColor White
Write-Host "   → .\venv\Scripts\Activate.ps1" -ForegroundColor Green
Write-Host "   → python client\client_console.py" -ForegroundColor Green
Write-Host ""
Write-Host "2️⃣  Para ver el gemelo digital web:" -ForegroundColor Cyan
Write-Host "   Abre web\web_dashboard.html en tu navegador" -ForegroundColor White
Write-Host ""
Write-Host "3️⃣  Para escuchar telemetría UDP:" -ForegroundColor Cyan
Write-Host "   Abre otra terminal y ejecuta:" -ForegroundColor White
Write-Host "   → .\venv\Scripts\Activate.ps1" -ForegroundColor Green
Write-Host "   → python client\udp_listener.py" -ForegroundColor Green
Write-Host ""
Write-Host "────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  Para detener el servidor: Presiona Ctrl+C" -ForegroundColor Yellow
Write-Host ""
Write-Host "Activando entorno virtual e iniciando servidor..." -ForegroundColor White
Write-Host ""

# Activar venv y ejecutar servidor
$activateScript = ".\venv\Scripts\Activate.ps1"
$pythonPath = ".\venv\Scripts\python.exe"

if (Test-Path $pythonPath) {
    & $pythonPath server\server_domotico.py
} else {
    Write-Host "❌ ERROR: Python no encontrado en venv" -ForegroundColor Red
    Write-Host "   Ejecuta: .\scripts\install.ps1" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}
