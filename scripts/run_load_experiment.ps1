#!/usr/bin/env pwsh
# Drive the REAL stack under load for each scheduling algorithm and collect
# locust CSVs. Switches the algorithm at runtime via POST /api/scheduler/mode,
# so the same deployment is reused across algorithms (equal conditions).
#
# Prereq: frontend + scheduler(s) + workers already running (see start_*.ps1).
#
# Example:
#   ./scripts/run_load_experiment.ps1 `
#       -LoadBalancer http://10.0.0.20:8080 `
#       -SchedulerAdmin http://10.0.0.30:8000 `
#       -Users 100 -SpawnRate 10 -RunTime 5m -WorkerCount 4
#
# Note: mode is set on ONE scheduler's admin URL. If running multiple schedulers,
# set the mode on each (loop -SchedulerAdmin), or start them all in the same mode.

param(
    [string]$LoadBalancer = "http://localhost:8080",
    [string]$SchedulerAdmin = "http://localhost:8000",
    [string[]]$Algos = @("random", "round_robin", "queue_length", "queue_cost"),
    [int]$Users = 100,
    [int]$SpawnRate = 10,
    [string]$RunTime = "5m",
    [int]$WorkerCount = 4,
    [int]$Repeats = 1,
    [string]$ResultsDir = "results"
)

if (-not (Test-Path $ResultsDir)) { New-Item -ItemType Directory -Path $ResultsDir | Out-Null }
$locustfile = "tests/load/locustfile.py"

foreach ($algo in $Algos) {
    Write-Host "[MODE] Setting scheduler mode -> $algo" -ForegroundColor Cyan
    try {
        Invoke-RestMethod -Method Post -Uri "$SchedulerAdmin/api/scheduler/mode?mode=$algo" -ErrorAction Stop | Out-Null
    } catch {
        Write-Host "[WARN] Failed to set mode on $SchedulerAdmin ($_). Continuing." -ForegroundColor Yellow
    }
    Start-Sleep -Seconds 3  # let the change settle / warm up

    for ($r = 1; $r -le $Repeats; $r++) {
        $prefix = "$ResultsDir/real_${algo}_N${WorkerCount}_r${r}"
        Write-Host "[LOAD] $algo run $r/$Repeats -> $prefix" -ForegroundColor Green
        locust -f $locustfile --host $LoadBalancer `
            --users $Users --spawn-rate $SpawnRate --run-time $RunTime --headless `
            --csv $prefix --only-summary
    }
}

Write-Host "[DONE] CSVs written to $ResultsDir (real_<algo>_N<n>_r<rep>_stats.csv)" -ForegroundColor Cyan
Write-Host "       Analyze with: python -m evaluation.analyze_results $ResultsDir" -ForegroundColor Cyan
