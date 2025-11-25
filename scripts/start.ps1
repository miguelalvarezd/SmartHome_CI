# Script de Inicio Rápido - Sistema Domótico
# ===========================================

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         🏠 SISTEMA DOMÓTICO - INICIO RÁPIDO 🏠         ║" -ForegroundColor Cyan
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

# Verificar que existe node_modules en home_simulator
if (-not (Test-Path "home_simulator\node_modules")) {
    Write-Host "❌ ERROR: Dependencias del simulador no encontradas" -ForegroundColor Red
    Write-Host "   Ejecuta primero: .\scripts\install.ps1" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host "🚀 Iniciando Sistema Domótico Completo..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Servicios que se iniciarán:" -ForegroundColor Cyan
Write-Host "  ✓ Servidor Python (Puertos 5000, 5001, 8080)" -ForegroundColor White
Write-Host "  ✓ Simulador 3D Vite (Puerto 3000)" -ForegroundColor White
Write-Host ""
Write-Host "────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host ""
Write-Host "📖 Acceso a servicios:" -ForegroundColor Yellow
Write-Host ""
Write-Host "🌐 Dashboard Web:" -ForegroundColor Cyan
Write-Host "   → Opción 1: Abre web\web_dashboard.html en tu navegador" -ForegroundColor Green
Write-Host "   → Opción 2: Ejecuta 'python web\web_server.py' (http://localhost:8000)" -ForegroundColor Green
Write-Host ""
Write-Host "🎮 Simulador 3D:" -ForegroundColor Cyan
Write-Host "   → URL: http://localhost:3000" -ForegroundColor Green
Write-Host "   → O usa la pestaña 'Simulador 3D' del dashboard" -ForegroundColor White
Write-Host ""
Write-Host "💻 Cliente CLI (opcional):" -ForegroundColor Cyan
Write-Host "   → Abre nueva terminal y ejecuta:" -ForegroundColor White
Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "     python client\client_console.py" -ForegroundColor Gray
Write-Host ""
Write-Host "📡 Telemetría UDP (opcional):" -ForegroundColor Cyan
Write-Host "   → Abre nueva terminal y ejecuta:" -ForegroundColor White
Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "     python client\udp_listener.py" -ForegroundColor Gray
Write-Host ""
Write-Host "────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  Para detener todos los servicios: Presiona Ctrl+C" -ForegroundColor Yellow
Write-Host ""
Write-Host "Iniciando servicios..." -ForegroundColor White
Write-Host ""

# Iniciar servidor Vite en background
Write-Host "🎮 Iniciando Simulador 3D (Vite)..." -ForegroundColor Cyan
$viteJob = Start-Job -ScriptBlock {
    param($simulatorPath)
    Set-Location $simulatorPath
    npm run dev
} -ArgumentList "$projectRoot\home_simulator"

Start-Sleep -Seconds 2

# Verificar que el job de Vite está corriendo
if ($viteJob.State -eq "Running") {
    Write-Host "  ✅ Simulador 3D iniciado en http://localhost:3000" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Advertencia: No se pudo iniciar el simulador 3D" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🐍 Iniciando Servidor Python..." -ForegroundColor Cyan

# Activar venv y ejecutar servidor
$activateScript = ".\venv\Scripts\Activate.ps1"
$pythonPath = ".\venv\Scripts\python.exe"

if (Test-Path $pythonPath) {
    try {
        & $pythonPath server\server_domotico.py
    } finally {
        # Detener el job de Vite al salir
        Write-Host ""
        Write-Host "🛑 Deteniendo servicios..." -ForegroundColor Yellow
        Stop-Job -Job $viteJob
        Remove-Job -Job $viteJob
        Write-Host "  ✅ Todos los servicios detenidos" -ForegroundColor Green
    }
} else {
    Write-Host "❌ ERROR: Python no encontrado en venv" -ForegroundColor Red
    Write-Host "   Ejecuta: .\scripts\install.ps1" -ForegroundColor Yellow
    Stop-Job -Job $viteJob
    Remove-Job -Job $viteJob
    Read-Host "Presiona Enter para salir"
    exit 1
}
