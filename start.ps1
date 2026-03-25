# Script para iniciar el sistema completo
# Backend Flask + Frontend React

Write-Host "`n" -NoNewline
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " SISTEMA DE VALIDACION DE ALLOCATIONS - INICIO " -ForegroundColor White
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "api\app.py")) {
    Write-Host "[ERROR] No se encuentra api\app.py" -ForegroundColor Red
    Write-Host "Asegurate de ejecutar este script desde la raiz del proyecto" -ForegroundColor Yellow
    exit 1
}

# Función para verificar si un puerto está en uso
function Test-Port {
    param([int]$Port)
    $res = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return [bool]$res
}

# Función para detener un proceso que ocupa un puerto
function Stop-PortProcess {
    param([int]$Port)
    $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid in $processes) {
        if ($pid) {
            Write-Host "      [FIX] Cerrando proceso en puerto $Port (PID: $pid)..." -ForegroundColor Cyan
            try {
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            } catch {}
        }
    }
    # Esperar un momento para que el sistema libere el puerto
    Start-Sleep -Milliseconds 1500
}

# Verificar puertos
Write-Host "[CHECK] Verificando puertos..." -ForegroundColor Yellow
if (Test-Port 5000) {
    Write-Host "[WARNING] Puerto 5000 ya esta en uso (Backend)" -ForegroundColor Yellow
    Stop-PortProcess 5000
}

if (Test-Port 5173) {
    Write-Host "[WARNING] Puerto 5173 ya esta en uso (Frontend)" -ForegroundColor Yellow
    Stop-PortProcess 5173
}

# Iniciar Backend (Flask)
Write-Host ""
Write-Host "[1/2] Iniciando Backend (Flask API)..." -ForegroundColor Green
Write-Host "      Puerto: 5000" -ForegroundColor Gray

# Activar venv y ejecutar Flask en background
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & ".\venv\Scripts\Activate.ps1"
    & python api\app.py
}

Start-Sleep -Seconds 3

# Verificar que el backend inició correctamente
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -Method Get -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "      [OK] Backend iniciado correctamente" -ForegroundColor Green
    }
} catch {
    Write-Host "      [WARNING] Backend puede no haber iniciado correctamente" -ForegroundColor Yellow
    Write-Host "      Verifica los logs mas abajo" -ForegroundColor Gray
}

# Iniciar Frontend (React + Vite)
Write-Host ""
Write-Host "[2/2] Iniciando Frontend (React + Vite)..." -ForegroundColor Green
Write-Host "      Puerto: 5173" -ForegroundColor Gray

$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Set-Location dashboard-financiero
    & npx vite --port 5173 --strictPort
}

Start-Sleep -Seconds 5

Write-Host "      [OK] Frontend iniciandose..." -ForegroundColor Green

# Resumen
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " SISTEMA INICIADO " -ForegroundColor White -NoNewline
Write-Host "OK" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Backend (API Flask):   http://localhost:5000" -ForegroundColor White
Write-Host "  Frontend (React):      http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "  Job IDs:" -ForegroundColor Gray
Write-Host "    Backend:  $($backendJob.Id)" -ForegroundColor Gray
Write-Host "    Frontend: $($frontendJob.Id)" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para detener los servidores, ejecuta:" -ForegroundColor Yellow
Write-Host "  Stop-Job $($backendJob.Id), $($frontendJob.Id); Remove-Job $($backendJob.Id), $($frontendJob.Id)" -ForegroundColor Gray
Write-Host ""
Write-Host "O simplemente cierra esta terminal" -ForegroundColor Gray
Write-Host ""
Write-Host "Presiona Ctrl+C para ver logs en tiempo real..." -ForegroundColor Cyan

# Mantener la terminal abierta y mostrar logs
try {
    while ($true) {
        Write-Host "`n--- Backend Logs ---" -ForegroundColor Yellow
        Receive-Job -Job $backendJob | Select-Object -Last 10
        
        Write-Host "`n--- Frontend Logs ---" -ForegroundColor Yellow
        Receive-Job -Job $frontendJob | Select-Object -Last 10
        
        Start-Sleep -Seconds 5
    }
} finally {
    # Limpiar al salir
    Write-Host "`nDeteniendo servidores..." -ForegroundColor Yellow
    Stop-Job $backendJob, $frontendJob
    Remove-Job $backendJob, $frontendJob
    Write-Host "Servidores detenidos" -ForegroundColor Green
}
