# Script de Instalación - Sistema Domótico con Entorno Virtual
# =============================================================

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║    🏠 SISTEMA DOMÓTICO - INSTALACIÓN CON VENV 🏠      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Navegar al directorio raíz del proyecto
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host "📁 Directorio del proyecto: $projectRoot" -ForegroundColor White
Write-Host ""

# [1/5] Verificar Python
Write-Host "[1/5] Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✅ $pythonVersion encontrado" -ForegroundColor Green
} catch {
    Write-Host "  ❌ ERROR: Python no está instalado o no está en PATH" -ForegroundColor Red
    Write-Host "  Descarga Python desde: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

# [2/5] Crear entorno virtual
Write-Host ""
Write-Host "[2/5] Creando entorno virtual..." -ForegroundColor Yellow

if (Test-Path "venv") {
    Write-Host "  ⚠️  El entorno virtual ya existe" -ForegroundColor Yellow
    $respuesta = Read-Host "  ¿Deseas recrearlo? (S/N)"
    
    if ($respuesta -eq "S" -or $respuesta -eq "s") {
        Write-Host "  🗑️  Eliminando venv antiguo..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force venv
        Write-Host "  📦 Creando nuevo entorno virtual..." -ForegroundColor Cyan
        python -m venv venv
    } else {
        Write-Host "  ℹ️  Usando venv existente" -ForegroundColor Cyan
    }
} else {
    Write-Host "  📦 Creando entorno virtual..." -ForegroundColor Cyan
    python -m venv venv
}

if (Test-Path "venv") {
    Write-Host "  ✅ Entorno virtual creado en: $projectRoot\venv" -ForegroundColor Green
} else {
    Write-Host "  ❌ ERROR: No se pudo crear el entorno virtual" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

# [3/5] Actualizar pip
Write-Host ""
Write-Host "[3/5] Actualizando pip en venv..." -ForegroundColor Yellow

$pipPath = "$projectRoot\venv\Scripts\pip.exe"

if (Test-Path $pipPath) {
    & $pipPath install --upgrade pip | Out-Null
    Write-Host "  ✅ pip actualizado" -ForegroundColor Green
}

# [4/5] Instalar dependencias
Write-Host ""
Write-Host "[4/5] Instalando dependencias..." -ForegroundColor Yellow
Write-Host "    - Flask 3.0.0 (Framework web)" -ForegroundColor Cyan
Write-Host "    - flask-cors 4.0.0 (CORS para API)" -ForegroundColor Cyan
Write-Host "    - Werkzeug 3.0.1 (Utilidades WSGI)" -ForegroundColor Cyan
Write-Host "    - requests 2.31.0 (HTTP para tests)" -ForegroundColor Cyan
Write-Host ""

& $pipPath install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Dependencias instaladas correctamente" -ForegroundColor Green
} else {
    Write-Host "  ❌ ERROR al instalar dependencias" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

# [5/5] Verificar instalación
Write-Host ""
Write-Host "[5/5] Verificando instalación..." -ForegroundColor Yellow

$packagesToCheck = @("flask", "flask-cors", "werkzeug", "requests")
$allInstalled = $true

foreach ($package in $packagesToCheck) {
    $result = & $pipPath show $package 2>&1 | Select-String "Version"
    if ($result) {
        Write-Host "  ✅ $package - $result" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $package NO instalado" -ForegroundColor Red
        $allInstalled = $false
    }
}

# Resumen final
Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
if ($allInstalled) {
    Write-Host "           ✅ INSTALACIÓN COMPLETADA ✅" -ForegroundColor Green
} else {
    Write-Host "      ⚠️  INSTALACIÓN COMPLETADA CON ADVERTENCIAS" -ForegroundColor Yellow
}
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📁 Estructura del proyecto:" -ForegroundColor Yellow
Write-Host "   ✓ venv/                  Entorno virtual Python" -ForegroundColor White
Write-Host "   ✓ server/                Servidor central" -ForegroundColor White
Write-Host "   ✓ client/                Clientes (CLI + UDP)" -ForegroundColor White
Write-Host "   ✓ web/                   Gemelo digital HTML" -ForegroundColor White
Write-Host "   ✓ scripts/               Automatización y tests" -ForegroundColor White
Write-Host "   ✓ docs/                  Documentación técnica" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Para iniciar el sistema:" -ForegroundColor Yellow
Write-Host "   .\scripts\start.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "📖 Más información:" -ForegroundColor Yellow
Write-Host "   README.md            - Manual de usuario" -ForegroundColor White
Write-Host "   docs\ARQUITECTURA.md - Documentación técnica" -ForegroundColor White
Write-Host ""

Read-Host "Presiona Enter para continuar"
