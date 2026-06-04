#!/usr/bin/env pwsh
# Start the FRONTEND roles on one VM: complexity service + load balancer + API.
# The load balancer round-robins over all schedulers listed in -SchedulerUrls,
# which is how you add a second scheduler to test the scheduler bottleneck.
#
# Example:
#   ./scripts/start_frontend.ps1 `
#       -SchedulerUrls "http://10.0.0.30:8000,http://10.0.0.31:8000"
#
# Then point load tests at the load balancer (default :8080).

param(
    [Parameter(Mandatory = $true)][string]$SchedulerUrls,
    [int]$ComplexityPort = 5000,
    [int]$LoadBalancerPort = 8080,
    [int]$ApiPort = 8010,
    [string]$LogDir = "logs"
)

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

# 1) Complexity Analysis Service (static-first; runs offline if no GROQ key)
Write-Host "[FRONTEND] Complexity service on :$ComplexityPort" -ForegroundColor Green
Start-Process pwsh -ArgumentList @(
    "-NoExit", "-Command",
    "`$env:AI_SERVICE_PORT='$ComplexityPort'; python -m code_assist.complexity_service 2>&1 | Tee-Object -FilePath $LogDir/complexity-service.log"
) -WindowStyle Normal
Start-Sleep -Seconds 2

# 2) Load Balancer (round-robins over all schedulers)
Write-Host "[FRONTEND] Load balancer on :$LoadBalancerPort -> $SchedulerUrls" -ForegroundColor Green
Start-Process pwsh -ArgumentList @(
    "-NoExit", "-Command",
    "`$env:SCHEDULER_URLS='$SchedulerUrls'; `$env:LOAD_BALANCER_PORT='$LoadBalancerPort'; python -m load_balancer.balancer 2>&1 | Tee-Object -FilePath $LogDir/load-balancer.log"
) -WindowStyle Normal
Start-Sleep -Seconds 2

# 3) API Server / Frontend gateway
Write-Host "[FRONTEND] API server on :$ApiPort -> LB :$LoadBalancerPort" -ForegroundColor Green
Start-Process pwsh -ArgumentList @(
    "-NoExit", "-Command",
    "`$env:LOAD_BALANCER_URL='http://localhost:$LoadBalancerPort'; python api_server.py 2>&1 | Tee-Object -FilePath $LogDir/api-server.log"
) -WindowStyle Normal

Write-Host "[FRONTEND] Started. Point load tests at http://<this-vm>:$LoadBalancerPort" -ForegroundColor Cyan
