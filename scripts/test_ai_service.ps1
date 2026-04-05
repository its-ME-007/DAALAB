# ============================================================================
# AI Service Health Check Script
# ============================================================================
# Tests Complexity Analysis Service (port 5000) used by the scheduler
# This is separate from the main AI code assistant service

Write-Host "[TEST] Complexity Analysis Service Health Check" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan
Write-Host "[INFO] This service provides fast complexity estimation for the scheduler" -ForegroundColor Gray
Write-Host "[INFO] Main AI agent (chat/analysis) is on a different port`n" -ForegroundColor Gray

# Test 1: Check if port 5000 is listening
Write-Host "[1] Checking if port 5000 is listening..." -ForegroundColor Yellow
try {
    $tcpConnection = Test-NetConnection -ComputerName localhost -Port 5000 -WarningAction SilentlyContinue
    if ($tcpConnection.TcpTestSucceeded) {
        Write-Host "[OK] Port 5000 is OPEN" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Port 5000 is CLOSED - Complexity service not running!" -ForegroundColor Red
        Write-Host "`n[FIX] Start the complexity service with:" -ForegroundColor Yellow
        Write-Host "  python -m code_assist.complexity_service" -ForegroundColor White
        Write-Host "`n  OR run the full system:" -ForegroundColor Yellow
        Write-Host "  .\start_all.ps1" -ForegroundColor White
        exit 1
    }
} catch {
    Write-Host "[ERROR] Failed to test port: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Check health endpoint
Write-Host "`n[2] Testing /health endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/health" -Method Get -TimeoutSec 5
    Write-Host "[OK] Health endpoint responded: $($response | ConvertTo-Json -Compress)" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Health endpoint failed: $_" -ForegroundColor Red
}

# Test 3: Test complexity analysis endpoint
Write-Host "`n[3] Testing /analyze_complexity endpoint..." -ForegroundColor Yellow

$testCode = @"
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
"@

$body = @{
    code = $testCode
    language = "python"
} | ConvertTo-Json

try {
    Write-Host "[INFO] Sending test code to complexity service..." -ForegroundColor Cyan
    $response = Invoke-RestMethod -Uri "http://localhost:5000/analyze_complexity" `
        -Method Post `
        -Body $body `
        -ContentType "application/json" `
        -TimeoutSec 30
    
    Write-Host "[OK] Complexity analysis succeeded!" -ForegroundColor Green
    Write-Host "`n[RESPONSE]" -ForegroundColor Cyan
    Write-Host ($response | ConvertTo-Json -Depth 5) -ForegroundColor White
    
    if ($response.estimated_time_ms) {
        Write-Host "`n[SUCCESS] Complexity service is working!" -ForegroundColor Green
        Write-Host "  Time Complexity: $($response.time_complexity)" -ForegroundColor White
        Write-Host "  Space Complexity: $($response.space_complexity)" -ForegroundColor White
        Write-Host "  Estimated Time: $($response.estimated_time_ms)ms" -ForegroundColor White
        Write-Host "  Confidence: $([math]::Round($response.confidence * 100))%" -ForegroundColor White
    } else {
        Write-Host "`n[WARNING] Response doesn't contain estimated_time_ms" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[ERROR] Complexity analysis failed!" -ForegroundColor Red
    Write-Host "[ERROR] $_" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        $responseBody = $reader.ReadToEnd()
        Write-Host "[ERROR] Response body: $responseBody" -ForegroundColor Red
    }
}

# Test 4: Check service info
Write-Host "`n[4] Checking service info..." -ForegroundColor Yellow
try {
    $info = Invoke-RestMethod -Uri "http://localhost:5000/" -Method Get
    Write-Host "[OK] Service info retrieved" -ForegroundColor Green
    Write-Host "  Service: $($info.service)" -ForegroundColor White
    Write-Host "  Version: $($info.version)" -ForegroundColor White
    Write-Host "  Description: $($info.description)" -ForegroundColor White
} catch {
    Write-Host "[WARNING] Could not retrieve service info" -ForegroundColor Yellow
}

# Test 5: Check if GROQ_API_KEY is set
Write-Host "`n[4] Checking environment variables..." -ForegroundColor Yellow
if ($env:GROQ_API_KEY) {
    Write-Host "[OK] GROQ_API_KEY is set" -ForegroundColor Green
} else {
    Write-Host "[WARNING] GROQ_API_KEY not found in environment!" -ForegroundColor Yellow
    Write-Host "[INFO] Checking .env file..." -ForegroundColor Cyan
    if (Test-Path ".env") {
        $envContent = Get-Content ".env" | Select-String "GROQ_API_KEY"
        if ($envContent) {
            Write-Host "[OK] GROQ_API_KEY found in .env file" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] GROQ_API_KEY not in .env file!" -ForegroundColor Red
        }
    } else {
        Write-Host "[ERROR] .env file not found!" -ForegroundColor Red
    }
}

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "[DONE] Complexity Analysis Service health check complete" -ForegroundColor Cyan
Write-Host "`n[NOTE] This is the scheduler's complexity estimation service" -ForegroundColor Gray
Write-Host "[NOTE] For interactive code analysis, use the main AI agent" -ForegroundColor Gray
