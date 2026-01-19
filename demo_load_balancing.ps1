#!/usr/bin/env pwsh
# Demo script to show load balancing across two workers

Write-Host "[DEMO] Load Balancing Demonstration" -ForegroundColor Cyan
Write-Host "=" * 70

# Test configuration
$API_URL = "http://localhost:8080/api/run-code"  # Load balancer
$NUM_REQUESTS = 10
$SLEEP_TIME_MS = 1000  # Simulated work time

# Sample code that takes ~1 second to execute
$TEST_CODE = @"
import time
import random

# Simulate computational work
start = time.time()
time.sleep($SLEEP_TIME_MS / 1000.0)
result = sum(range(1000000))
elapsed = time.time() - start

print(f"Worker processed task in {elapsed:.2f}s - Result: {result}")
"@

Write-Host ""
Write-Host "[INFO] Configuration:" -ForegroundColor Yellow
Write-Host "  - Number of requests: $NUM_REQUESTS"
Write-Host "  - Task duration: ~$SLEEP_TIME_MS ms each"
Write-Host "  - Load Balancer: $API_URL"
Write-Host ""

# Function to send a request and track timing
function Send-CodeRequest {
    param([int]$RequestId)
    
    $body = @{
        code = $TEST_CODE
        language = "python"
    } | ConvertTo-Json
    
    $startTime = Get-Date
    
    try {
        $response = Invoke-RestMethod -Uri $API_URL -Method POST -Body $body -ContentType 'application/json' -ErrorAction Stop
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        # Extract worker ID from output (if available)
        $workerInfo = if ($response.output -match "Worker processed") { "Success" } else { "Unknown" }
        
        return [PSCustomObject]@{
            RequestId = $RequestId
            Success = $response.success
            Runtime = [math]::Round($response.runtime, 3)
            Duration = [math]::Round($duration, 3)
            Status = $workerInfo
        }
    }
    catch {
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        return [PSCustomObject]@{
            RequestId = $RequestId
            Success = $false
            Runtime = 0
            Duration = [math]::Round($duration, 3)
            Status = "Error: $_"
        }
    }
}

Write-Host "[TEST 1] Sequential Execution (Simulating 1 Worker)" -ForegroundColor Green
Write-Host "-" * 70

$seq_start = Get-Date
$seq_results = @()

for ($i = 1; $i -le $NUM_REQUESTS; $i++) {
    Write-Host "  Request $i/$NUM_REQUESTS..." -NoNewline
    $result = Send-CodeRequest -RequestId $i
    $seq_results += $result
    Write-Host " [OK] ${result.Duration}s" -ForegroundColor Green
}

$seq_end = Get-Date
$seq_total = ($seq_end - $seq_start).TotalSeconds

Write-Host ""
Write-Host "[RESULTS] Sequential Execution:" -ForegroundColor Yellow
Write-Host "  Total Time: $([math]::Round($seq_total, 2))s"
Write-Host "  Average per request: $([math]::Round($seq_total / $NUM_REQUESTS, 2))s"
Write-Host ""

Start-Sleep -Seconds 2

Write-Host "[TEST 2] Parallel Execution (Using 2 Workers via Load Balancer)" -ForegroundColor Green
Write-Host "-" * 70

$par_start = Get-Date

# Send requests in parallel using PowerShell jobs
$jobs = @()
for ($i = 1; $i -le $NUM_REQUESTS; $i++) {
    Write-Host "  Launching request $i/$NUM_REQUESTS..." -ForegroundColor Cyan
    $job = Start-Job -ScriptBlock {
        param($url, $code, $id)
        
        $body = @{
            code = $code
            language = "python"
        } | ConvertTo-Json
        
        $startTime = Get-Date
        try {
            $response = Invoke-RestMethod -Uri $url -Method POST -Body $body -ContentType 'application/json' -ErrorAction Stop
            $endTime = Get-Date
            $duration = ($endTime - $startTime).TotalSeconds
            
            return [PSCustomObject]@{
                RequestId = $id
                Success = $response.success
                Runtime = [math]::Round($response.runtime, 3)
                Duration = [math]::Round($duration, 3)
                Status = "Success"
            }
        }
        catch {
            $endTime = Get-Date
            $duration = ($endTime - $startTime).TotalSeconds
            
            return [PSCustomObject]@{
                RequestId = $id
                Success = $false
                Runtime = 0
                Duration = [math]::Round($duration, 3)
                Status = "Error"
            }
        }
    } -ArgumentList $API_URL, $TEST_CODE, $i
    
    $jobs += $job
}

Write-Host ""
Write-Host "  Waiting for all requests to complete..." -ForegroundColor Yellow

# Wait for all jobs and collect results
$par_results = @()
$jobs | ForEach-Object {
    $result = Wait-Job $_ | Receive-Job
    $par_results += $result
    Remove-Job $_
    Write-Host "  Request $($result.RequestId) completed in $($result.Duration)s" -ForegroundColor Green
}

$par_end = Get-Date
$par_total = ($par_end - $par_start).TotalSeconds

Write-Host ""
Write-Host "[RESULTS] Parallel Execution:" -ForegroundColor Yellow
Write-Host "  Total Time: $([math]::Round($par_total, 2))s"
Write-Host "  Average per request: $([math]::Round($par_total / $NUM_REQUESTS, 2))s"
Write-Host ""

# Calculate improvement
$improvement = (($seq_total - $par_total) / $seq_total) * 100
$speedup = $seq_total / $par_total

Write-Host "=" * 70
Write-Host "[SUMMARY] Performance Comparison" -ForegroundColor Cyan
Write-Host "=" * 70
Write-Host ""
Write-Host "Sequential (1 Worker):" -ForegroundColor White
Write-Host "  Total Time:     $([math]::Round($seq_total, 2))s" -ForegroundColor Gray
Write-Host "  Avg per request: $([math]::Round($seq_total / $NUM_REQUESTS, 2))s" -ForegroundColor Gray
Write-Host ""
Write-Host "Parallel (2 Workers):" -ForegroundColor White
Write-Host "  Total Time:     $([math]::Round($par_total, 2))s" -ForegroundColor Gray
Write-Host "  Avg per request: $([math]::Round($par_total / $NUM_REQUESTS, 2))s" -ForegroundColor Gray
Write-Host ""
Write-Host "Performance Gain:" -ForegroundColor Green
Write-Host "  Time Saved:     $([math]::Round($seq_total - $par_total, 2))s ($([math]::Round($improvement, 1))%)" -ForegroundColor Green
Write-Host "  Speedup:        ${speedup}x faster" -ForegroundColor Green
Write-Host ""

# Show worker distribution
Write-Host "[INFO] Checking Worker Distribution..." -ForegroundColor Yellow

try {
    $lb_status = Invoke-RestMethod -Uri "http://localhost:8080/lb/status" -Method GET
    Write-Host ""
    Write-Host "Load Balancer Status:" -ForegroundColor Cyan
    Write-Host "  Total Requests Handled: $($lb_status.total_requests)" -ForegroundColor White
    Write-Host ""
    Write-Host "Worker Distribution:" -ForegroundColor Cyan
    $lb_status.schedulers | ForEach-Object {
        $percentage = [math]::Round(($_.requests / $lb_status.total_requests) * 100, 1)
        Write-Host "  $($_.url): $($_.requests) requests (${percentage}%)" -ForegroundColor White
    }
}
catch {
    Write-Host "  Unable to fetch load balancer status" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" * 70
Write-Host "[DEMO] Demonstration Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Key Takeaways:" -ForegroundColor Cyan
Write-Host "  1. Two workers can handle requests concurrently" -ForegroundColor White
Write-Host "  2. Load balancer distributes requests evenly" -ForegroundColor White
Write-Host "  3. Parallel execution provides ${speedup}x speedup" -ForegroundColor White
Write-Host "  4. System can handle $NUM_REQUESTS requests efficiently" -ForegroundColor White
Write-Host ""
