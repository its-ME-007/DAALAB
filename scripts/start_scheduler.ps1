#!/usr/bin/env pwsh
# Start a single SCHEDULER role. Run >=2 of these (on separate VMs/ports) behind
# the load balancer to test the single-scheduler bottleneck threat to validity.
#
# Example (on a scheduler VM, pointing at worker VMs):
#   ./scripts/start_scheduler.ps1 `
#       -WorkerUrls "http://10.0.0.11:8001,http://10.0.0.12:8001" `
#       -ComplexityServiceUrl "http://10.0.0.20:5000" `
#       -SchedulingMode queue_cost -Port 8000
#
# SchedulingMode is also switchable at runtime via POST /api/scheduler/mode,
# which is what run_load_experiment.ps1 uses to sweep algorithms.

param(
    [Parameter(Mandatory = $true)][string]$WorkerUrls,
    [string]$ComplexityServiceUrl = "http://localhost:5000",
    [ValidateSet("queue_length", "queue_cost", "random", "round_robin")]
    [string]$SchedulingMode = "queue_cost",
    [int]$Port = 8000,
    [string]$LogDir = "logs"
)

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

$env:WORKER_URLS = $WorkerUrls
$env:COMPLEXITY_SERVICE_URL = $ComplexityServiceUrl
$env:SCHEDULING_MODE = $SchedulingMode
$env:SCHEDULER_PORT = "$Port"
$env:SCHEDULER_HOST = "0.0.0.0"

Write-Host "[SCHEDULER] mode=$SchedulingMode on 0.0.0.0:$Port" -ForegroundColor Green
Write-Host "  workers=$WorkerUrls" -ForegroundColor Gray
Write-Host "  complexity=$ComplexityServiceUrl" -ForegroundColor Gray
python -m scheduler.scheduler_server 2>&1 | Tee-Object -FilePath "$LogDir/scheduler-$Port.log"
