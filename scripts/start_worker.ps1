#!/usr/bin/env pwsh
# Start a single WORKER role (one per VM for real per-worker CPU isolation).
#
# Example (on a worker VM):
#   ./scripts/start_worker.ps1 -WorkerId worker-1 -Port 8001 -MaxConcurrentJobs 1
#
# Bind is 0.0.0.0 so the scheduler VM can reach it via this VM's IP:Port.

param(
    [string]$WorkerId = "worker-1",
    [int]$Port = 8001,
    [int]$MaxConcurrentJobs = 10,
    [string]$ResourceMonitoring = "true",
    [string]$LogDir = "logs"
)

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

$env:WORKER_ID = $WorkerId
$env:WORKER_PORT = "$Port"
$env:WORKER_HOST = "0.0.0.0"
$env:MAX_CONCURRENT_JOBS = "$MaxConcurrentJobs"          # swept concurrency knob
$env:ENABLE_RESOURCE_MONITORING = $ResourceMonitoring

Write-Host "[WORKER] $WorkerId on 0.0.0.0:$Port  (MAX_CONCURRENT_JOBS=$MaxConcurrentJobs)" -ForegroundColor Green
python -m worker.worker_server 2>&1 | Tee-Object -FilePath "$LogDir/$WorkerId.log"
