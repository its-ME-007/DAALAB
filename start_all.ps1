#!/usr/bin/env pwsh
# Start all services for scheduler-worker architecture testing

Write-Host "[START] Starting DAALAB Scheduler-Worker Architecture" -ForegroundColor Cyan
Write-Host "=" * 70

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Check if Docker is running
try {
    docker ps | Out-Null
} catch {
    Write-Host "[WARNING] Docker is not running. Starting Docker..." -ForegroundColor Yellow
    Start-Process "Docker Desktop"
    Start-Sleep -Seconds 5
}

# Create log directory
$LogDir = "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

Write-Host ""
Write-Host "[INFO] Starting services (logs in ./logs/)..." -ForegroundColor Yellow

# Start Worker 1
Write-Host "  [2/6] Starting Worker 1 (Port 8001)..." -ForegroundColor Green
Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "`$env:WORKER_ID='worker-1'; `$env:WORKER_PORT='8001'; `$env:ENABLE_RESOURCE_MONITORING='true'; python -m worker.worker_server 2>&1 | Tee-Object -FilePath logs/worker-1.log"
) -WindowStyle Normal

Start-Sleep -Seconds 2

# Start Worker 2
Write-Host "  [3/6] Starting Worker 2 (Port 8002)..." -ForegroundColor Green
Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "`$env:WORKER_ID='worker-2'; `$env:WORKER_PORT='8002'; `$env:ENABLE_RESOURCE_MONITORING='true'; python -m worker.worker_server 2>&1 | Tee-Object -FilePath logs/worker-2.log"
) -WindowStyle Normal

Start-Sleep -Seconds 3

# Start Scheduler
Write-Host "  [4/6] Starting Scheduler (Port 8000)..." -ForegroundColor Green
Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "`$env:WORKER_URLS='http://localhost:8001,http://localhost:8002'; `$env:SCHEDULING_MODE='queue_cost'; python -m scheduler.scheduler_server 2>&1 | Tee-Object -FilePath logs/scheduler.log"
) -WindowStyle Normal

Start-Sleep -Seconds 3

# Start Load Balancer
Write-Host "  [5/6] Starting Load Balancer (Port 8080)..." -ForegroundColor Green
Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "`$env:SCHEDULER_URLS='http://localhost:8000'; python -m load_balancer.balancer 2>&1 | Tee-Object -FilePath logs/load-balancer.log"
) -WindowStyle Normal

Start-Sleep -Seconds 3

# Start API Server (Frontend Gateway)
Write-Host "  [6/6] Starting API Server/Frontend Gateway (Port 8010)..." -ForegroundColor Green
Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "`$env:LOAD_BALANCER_URL='http://localhost:8080'; python api_server.py 2>&1 | Tee-Object -FilePath logs/api-server.log"
) -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "[SUCCESS] All services started!" -ForegroundColor Green
Write-Host "=" * 70
Write-Host ""

# Health checks
Write-Host "[HEALTH] Performing health checks..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

$services = @(
    @{Name="Worker 1"; URL="http://localhost:8001/health"},
    @{Name="Worker 2"; URL="http://localhost:8002/health"},
    @{Name="Scheduler"; URL="http://localhost:8000/api/health"},
    @{Name="Load Balancer"; URL="http://localhost:8080/lb/health"},
    @{Name="API Server"; URL="http://localhost:8010/api/auth/health"}
)

foreach ($service in $services) {
    try {
        $response = Invoke-RestMethod -Uri $service.URL -Method Get -ErrorAction Stop
        Write-Host "  [OK] $($service.Name) - Healthy" -ForegroundColor Green
    } catch {
        Write-Host "  [WARNING] $($service.Name) - Not ready yet" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[SERVICES] Service URLs:" -ForegroundColor Cyan
Write-Host "  Frontend:      http://localhost:8010 (API Server + UI)" -ForegroundColor White
Write-Host "  Load Balancer: http://localhost:8080" -ForegroundColor White
Write-Host "  Scheduler:     http://localhost:8000" -ForegroundColor White
Write-Host "  Worker 1:      http://localhost:8001" -ForegroundColor White
Write-Host "  Worker 2:      http://localhost:8002" -ForegroundColor White
Write-Host ""
Write-Host "[DOCS] Documentation:" -ForegroundColor Cyan
Write-Host "  README:        SCHEDULER_WORKER_README.md" -ForegroundColor White
Write-Host "  API Docs:      http://localhost:8010/docs" -ForegroundColor White
Write-Host "  Scheduler Docs: SCHEDULER_WORKER_README.md" -ForegroundColor White
Write-Host "  API Docs:      http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "[TEST] Testing:" -ForegroundColor Cyan
Write-Host "  Unit tests:    pytest tests/unit/ -v" -ForegroundColor White
Write-Host "  Load test:     locust -f tests/load/locustfile.py --host=http://localhost:8080" -ForegroundColor White
Write-Host ""
Write-Host "[STOP] To stop all services, close the PowerShell windows or press Ctrl+C" -ForegroundColor Yellow
Write-Host "=" * 70
