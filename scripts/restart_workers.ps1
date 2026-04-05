# ============================================================================
# Restart Workers Script
# ============================================================================
# Stops and restarts only the worker services to apply code fixes

Write-Host "[RESTART] Restarting Worker Services" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Step 1: Stop existing worker processes
Write-Host "[1] Stopping existing worker processes..." -ForegroundColor Yellow

$workerProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*worker.worker_server*"
}

if ($workerProcesses) {
    $workerProcesses | ForEach-Object {
        Write-Host "  Stopping process $($_.Id)..." -ForegroundColor Gray
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
    Write-Host "[OK] Old worker processes stopped" -ForegroundColor Green
} else {
    Write-Host "[INFO] No worker processes found to stop" -ForegroundColor Gray
}

# Step 2: Start Worker 1
Write-Host "`n[2] Starting Worker 1 (Port 8001)..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "`$env:WORKER_ID='worker-1'; `$env:WORKER_PORT='8001'; `$env:ENABLE_RESOURCE_MONITORING='true'; python -m worker.worker_server 2>&1 | Tee-Object -FilePath logs/worker-1.log"
) -WindowStyle Normal

Start-Sleep -Seconds 3

# Step 3: Start Worker 2
Write-Host "[3] Starting Worker 2 (Port 8002)..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-Command",
    "`$env:WORKER_ID='worker-2'; `$env:WORKER_PORT='8002'; `$env:ENABLE_RESOURCE_MONITORING='true'; python -m worker.worker_server 2>&1 | Tee-Object -FilePath logs/worker-2.log"
) -WindowStyle Normal

Start-Sleep -Seconds 3

# Step 4: Health check
Write-Host "`n[4] Performing health checks..." -ForegroundColor Yellow

try {
    $worker1 = Invoke-RestMethod -Uri "http://localhost:8001/health" -Method Get -TimeoutSec 5
    Write-Host "[OK] Worker 1 - Healthy" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Worker 1 - Not responding" -ForegroundColor Red
}

try {
    $worker2 = Invoke-RestMethod -Uri "http://localhost:8002/health" -Method Get -TimeoutSec 5
    Write-Host "[OK] Worker 2 - Healthy" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Worker 2 - Not responding" -ForegroundColor Red
}

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "[DONE] Workers restarted with updated code" -ForegroundColor Cyan
Write-Host "`n[NOTE] The fix for 'decrement_active_jobs' is now active" -ForegroundColor Green
Write-Host "[TEST] Run: .\test_end_to_end.ps1" -ForegroundColor Yellow
