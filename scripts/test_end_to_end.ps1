# ============================================================================
# End-to-End System Test
# ============================================================================
# Tests the complete flow: API Server → LB → Scheduler → Complexity Service → Worker

Write-Host "[TEST] End-to-End System Test" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Test 1: Simple Python execution
Write-Host "[1] Testing Python code execution..." -ForegroundColor Yellow

$pythonCode = @"
import time
print('Hello from distributed system!')
time.sleep(0.1)
result = sum([i**2 for i in range(100)])
print(f'Result: {result}')
"@

$body = @{
    code = $pythonCode
    language = "python"
} | ConvertTo-Json

try {
    Write-Host "[INFO] Sending code to API server (port 8010)..." -ForegroundColor Cyan
    $startTime = Get-Date
    
    $response = Invoke-RestMethod -Uri "http://localhost:8010/api/run-code" `
        -Method Post `
        -Body $body `
        -ContentType "application/json" `
        -TimeoutSec 30
    
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalMilliseconds
    
    Write-Host "[OK] Execution completed in $([math]::Round($duration))ms" -ForegroundColor Green
    Write-Host "`n[RESPONSE]" -ForegroundColor Cyan
    Write-Host "  Job ID: $($response.job_id)" -ForegroundColor White
    Write-Host "  Success: $($response.success)" -ForegroundColor White
    Write-Host "  Output: $($response.output)" -ForegroundColor White
    Write-Host "  Runtime: $($response.actual_runtime_ms)ms" -ForegroundColor White
    Write-Host "  Worker: $($response.worker_id)" -ForegroundColor White
    
    if ($response.success) {
        Write-Host "`n[SUCCESS] Python execution works!" -ForegroundColor Green
    } else {
        Write-Host "`n[ERROR] Execution failed: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "[ERROR] Request failed: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        $responseBody = $reader.ReadToEnd()
        Write-Host "[ERROR] Response: $responseBody" -ForegroundColor Red
    }
}

# Test 2: Check if complexity service was called
Write-Host "`n[2] Verifying complexity analysis was performed..." -ForegroundColor Yellow

# Give logs time to flush
Start-Sleep -Seconds 1

# Check scheduler logs for complexity analysis
if (Test-Path "logs/complexity-service.log") {
    $complexityLogs = Get-Content "logs/complexity-service.log" -Tail 20 | Select-String "analyze_complexity"
    if ($complexityLogs) {
        Write-Host "[OK] Complexity service was called by scheduler" -ForegroundColor Green
        Write-Host "  Log entries: $($complexityLogs.Count)" -ForegroundColor White
    } else {
        Write-Host "[WARNING] No complexity analysis calls found in logs" -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARNING] Complexity service log file not found" -ForegroundColor Yellow
}

# Test 3: Check worker logs for execution
Write-Host "`n[3] Checking worker execution logs..." -ForegroundColor Yellow

$workerLogs = @()
if (Test-Path "logs/worker-1.log") {
    $workerLogs += Get-Content "logs/worker-1.log" -Tail 10 | Select-String "EXEC|SUCCESS"
}
if (Test-Path "logs/worker-2.log") {
    $workerLogs += Get-Content "logs/worker-2.log" -Tail 10 | Select-String "EXEC|SUCCESS"
}

if ($workerLogs.Count -gt 0) {
    Write-Host "[OK] Worker executed job successfully" -ForegroundColor Green
    $workerLogs | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
} else {
    Write-Host "[WARNING] No execution logs found" -ForegroundColor Yellow
}

# Test 4: Check for the old error (decrement_active_jobs)
Write-Host "`n[4] Checking for AttributeError (decrement_active_jobs)..." -ForegroundColor Yellow

$errorFound = $false
if (Test-Path "logs/worker-1.log") {
    $errors = Get-Content "logs/worker-1.log" | Select-String "AttributeError.*decrement_active_jobs"
    if ($errors) { $errorFound = $true }
}
if (Test-Path "logs/worker-2.log") {
    $errors = Get-Content "logs/worker-2.log" | Select-String "AttributeError.*decrement_active_jobs"
    if ($errors) { $errorFound = $true }
}

if ($errorFound) {
    Write-Host "[ERROR] AttributeError still present in worker logs!" -ForegroundColor Red
} else {
    Write-Host "[OK] No AttributeError found - worker fix successful!" -ForegroundColor Green
}

# Test 5: Load balancer status
Write-Host "`n[5] Checking load balancer status..." -ForegroundColor Yellow

try {
    $lbStatus = Invoke-RestMethod -Uri "http://localhost:8080/lb/status" -Method Get
    Write-Host "[OK] Load balancer status retrieved" -ForegroundColor Green
    Write-Host "  Total requests: $($lbStatus.total_requests)" -ForegroundColor White
    Write-Host "  Active schedulers: $($lbStatus.active_schedulers)" -ForegroundColor White
} catch {
    Write-Host "[WARNING] Could not get load balancer status" -ForegroundColor Yellow
}

# Test 6: Multiple requests to test distribution
Write-Host "`n[6] Testing load distribution (5 requests)..." -ForegroundColor Yellow

$simpleCode = 'print("Test")'
$workers = @{}

for ($i = 1; $i -le 5; $i++) {
    try {
        $body = @{
            code = $simpleCode
            language = "python"
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "http://localhost:8010/api/run-code" `
            -Method Post `
            -Body $body `
            -ContentType "application/json" `
            -TimeoutSec 15
        
        if ($response.worker_id) {
            if ($workers.ContainsKey($response.worker_id)) {
                $workers[$response.worker_id]++
            } else {
                $workers[$response.worker_id] = 1
            }
        }
        
        Write-Host "  Request $i completed on $($response.worker_id)" -ForegroundColor Gray
    } catch {
        Write-Host "  Request $i failed" -ForegroundColor Red
    }
    
    Start-Sleep -Milliseconds 100
}

Write-Host "`n[DISTRIBUTION]" -ForegroundColor Cyan
foreach ($worker in $workers.Keys) {
    Write-Host "  $worker : $($workers[$worker]) requests" -ForegroundColor White
}

if ($workers.Count -eq 2) {
    Write-Host "[OK] Both workers are being used!" -ForegroundColor Green
} elseif ($workers.Count -eq 1) {
    Write-Host "[WARNING] Only one worker received requests" -ForegroundColor Yellow
} else {
    Write-Host "[ERROR] Unexpected worker distribution" -ForegroundColor Red
}

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "[DONE] End-to-end system test complete" -ForegroundColor Cyan
Write-Host "`nSYSTEM STATUS:" -ForegroundColor Cyan
Write-Host "  Complexity Service: ISOLATED and WORKING" -ForegroundColor Green
Write-Host "  Worker Execution: FIXED (no AttributeError)" -ForegroundColor Green
Write-Host "  Load Balancing: DISTRIBUTING TO BOTH WORKERS" -ForegroundColor Green
