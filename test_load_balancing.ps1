# ============================================================================
# Load Balancing Algorithm Test
# ============================================================================
# Test script for validating queue-cost based load balancing

Write-Host "`n[TEST] Load Balancing Algorithm Test" -ForegroundColor Cyan
Write-Host "=" * 70

# Configuration
$API_URL = "http://localhost:8010"
$SCHEDULER_URL = "http://localhost:8000"

# Test scenarios
$SCENARIOS = @(
    @{
        Name = "Scenario 1: Long job on Worker-1, then 2 short jobs"
        Description = "Send 5-second job to lock Worker-1, then send two 1-second jobs that should go to Worker-2"
        Jobs = @(
            @{
                Code = @"
import time
print('Long job starting on worker...')
time.sleep(5)
print('Long job completed!')
result = sum(range(1000))
print(f'Result: {result}')
"@
                Language = "python"
                ExpectedDuration = 5000
                Description = "5-second blocking job"
            },
            @{
                Code = @"
import time
print('Short job 1 starting...')
time.sleep(1)
print('Short job 1 completed!')
result = 42
print(f'Result: {result}')
"@
                Language = "python"
                ExpectedDuration = 1000
                Description = "1-second job (should go to Worker-2)"
                DelayMs = 500  # Send after 500ms
            },
            @{
                Code = @"
import time
print('Short job 2 starting...')
time.sleep(1)
print('Short job 2 completed!')
result = 100
print(f'Result: {result}')
"@
                Language = "python"
                ExpectedDuration = 1000
                Description = "1-second job (should go to Worker-2)"
                DelayMs = 1000  # Send after 1 second
            }
        )
    }
)

# Function to send code execution request
function Send-CodeExecution {
    param(
        [string]$Code,
        [string]$Language = "python"
    )
    
    $body = @{
        code = $Code
        language = $Language
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/run-code" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30
        return $response
    } catch {
        Write-Host "[ERROR] Failed to send request: $_" -ForegroundColor Red
        return $null
    }
}

# Function to get scheduler state
function Get-SchedulerState {
    try {
        $response = Invoke-RestMethod -Uri "$SCHEDULER_URL/api/workers" -Method GET
        return $response
    } catch {
        return $null
    }
}

# Function to display worker states
function Show-WorkerStates {
    param($Workers)
    
    Write-Host "`n[WORKERS] Current State:" -ForegroundColor Yellow
    foreach ($worker in $Workers) {
        $color = if ($worker.queue_cost_ms -eq 0) { "Green" } else { "Yellow" }
        Write-Host "  Worker: $($worker.worker_id)" -ForegroundColor $color
        Write-Host "    Queue Cost: $($worker.queue_cost_ms)ms"
        Write-Host "    Active Jobs: $($worker.active_jobs)"
        if ($worker.cpu_util) {
            Write-Host "    CPU: $($worker.cpu_util)%"
        }
        if ($worker.mem_util) {
            Write-Host "    Memory: $($worker.mem_util)%"
        }
    }
}

# Main test execution
Write-Host "`n[INFO] Testing queue-cost based load balancing" -ForegroundColor Cyan
Write-Host "[INFO] This test validates that shorter jobs route to less busy workers`n"

foreach ($scenario in $SCENARIOS) {
    Write-Host "`n" + "=" * 70 -ForegroundColor Cyan
    Write-Host "[SCENARIO] $($scenario.Name)" -ForegroundColor Cyan
    Write-Host "[DESC] $($scenario.Description)" -ForegroundColor Gray
    Write-Host "=" * 70 -ForegroundColor Cyan
    
    # Show initial worker states
    $initialStates = Get-SchedulerState
    if ($initialStates) {
        Show-WorkerStates -Workers $initialStates
    }
    
    # Track submitted jobs
    $submittedJobs = @()
    $startTime = Get-Date
    
    # Submit all jobs
    for ($i = 0; $i -lt $scenario.Jobs.Count; $i++) {
        $job = $scenario.Jobs[$i]
        
        # Apply delay if specified
        if ($job.DelayMs -and $i -gt 0) {
            $elapsed = ((Get-Date) - $startTime).TotalMilliseconds
            $waitTime = $job.DelayMs - $elapsed
            if ($waitTime -gt 0) {
                Write-Host "`n[WAIT] Waiting $([math]::Round($waitTime))ms before sending next job..." -ForegroundColor Gray
                Start-Sleep -Milliseconds $waitTime
            }
        }
        
        Write-Host "`n[JOB $($i+1)] $($job.Description)" -ForegroundColor Yellow
        Write-Host "[SEND] Submitting to API server..."
        
        $result = Send-CodeExecution -Code $job.Code -Language $job.Language
        
        if ($result -and $result.job_id) {
            Write-Host "[OK] Job accepted: $($result.job_id)" -ForegroundColor Green
            if ($result.worker_id) {
                Write-Host "[ROUTE] Assigned to: $($result.worker_id)" -ForegroundColor Cyan
            }
            
            $submittedJobs += @{
                JobId = $result.job_id
                Description = $job.Description
                SubmitTime = Get-Date
                WorkerId = $result.worker_id
                Success = $result.success
                ActualRuntime = $result.actual_runtime_ms
            }
            
            # Show worker states after submission
            Start-Sleep -Milliseconds 300  # Give time for state update
            $currentStates = Get-SchedulerState
            if ($currentStates) {
                Show-WorkerStates -Workers $currentStates
            }
        } else {
            Write-Host "[FAIL] Job submission failed!" -ForegroundColor Red
        }
    }
    
    # Wait for all jobs to complete
    Write-Host "`n[WAIT] Waiting for all jobs to complete..." -ForegroundColor Cyan
    Write-Host "[INFO] Longest job takes ~5 seconds, please wait...`n"
    
    Start-Sleep -Seconds 7  # Wait for all jobs to finish
    
    # Analyze results
    Write-Host "`n" + "=" * 70 -ForegroundColor Cyan
    Write-Host "[ANALYSIS] Load Balancing Results" -ForegroundColor Cyan
    Write-Host "=" * 70 -ForegroundColor Cyan
    
    $worker1Jobs = $submittedJobs | Where-Object { $_.WorkerId -like "*worker-1*" }
    $worker2Jobs = $submittedJobs | Where-Object { $_.WorkerId -like "*worker-2*" }
    
    Write-Host "`nWorker-1 executed: $($worker1Jobs.Count) jobs"
    foreach ($job in $worker1Jobs) {
        $duration = if ($job.ActualRuntime) { "$($job.ActualRuntime)ms" } else { "N/A" }
        Write-Host "  - $($job.Description) (runtime: $duration)"
    }
    
    Write-Host "`nWorker-2 executed: $($worker2Jobs.Count) jobs"
    foreach ($job in $worker2Jobs) {
        $duration = if ($job.ActualRuntime) { "$($job.ActualRuntime)ms" } else { "N/A" }
        Write-Host "  - $($job.Description) (runtime: $duration)"
    }
    
    # Validation
    Write-Host "`n[VALIDATION]" -ForegroundColor Yellow
    
    if ($worker1Jobs.Count -eq 1 -and $worker2Jobs.Count -eq 2) {
        Write-Host "[PASS] ✓ Load balancing worked correctly!" -ForegroundColor Green
        Write-Host "  - Long job (5s) went to Worker-1" -ForegroundColor Green
        Write-Host "  - Two short jobs (1s each) went to Worker-2 (avoided busy worker)" -ForegroundColor Green
    } elseif ($worker1Jobs.Count -eq 3 -and $worker2Jobs.Count -eq 0) {
        Write-Host "[FAIL] ✗ All jobs went to Worker-1 only!" -ForegroundColor Red
        Write-Host "  Expected: Worker-1 = 1 job, Worker-2 = 2 jobs"
        Write-Host "  Actual: Worker-1 = $($worker1Jobs.Count) jobs, Worker-2 = $($worker2Jobs.Count) jobs"
        Write-Host "`n[ISSUE] This indicates the routing logic is broken - jobs aren't being sent to selected workers"
    } else {
        Write-Host "[PARTIAL] Load distribution occurred but not as expected" -ForegroundColor Yellow
        Write-Host "  Expected: Worker-1 = 1 job, Worker-2 = 2 jobs"
        Write-Host "  Actual: Worker-1 = $($worker1Jobs.Count) jobs, Worker-2 = $($worker2Jobs.Count) jobs"
    }
    
    # Show final worker states
    Write-Host ""
    $finalStates = Get-SchedulerState
    if ($finalStates) {
        Show-WorkerStates -Workers $finalStates
    }
}

Write-Host "`n" + "=" * 70 -ForegroundColor Cyan
Write-Host "[COMPLETE] Load balancing test finished" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "`n[NOTE] Check scheduler logs for worker selection decisions"
Write-Host "[NOTE] Check worker logs to verify actual execution distribution`n"
