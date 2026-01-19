#!/usr/bin/env pwsh
# Quick test script for scheduler-worker architecture

Write-Host "🧪 Testing DAALAB Scheduler-Worker Architecture" -ForegroundColor Cyan
Write-Host "=" * 70
Write-Host ""

$BaseURL = "http://localhost:8000"

# Test 1: Health Check
Write-Host "[1/5] Health Check..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$BaseURL/api/health" -Method Get
    Write-Host "  ✅ Scheduler: $($health.status)" -ForegroundColor Green
    Write-Host "  📊 Workers available: $($health.details.workers_available)" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Scheduler not responding" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Submit Simple Code (O(1))
Write-Host "[2/5] Testing O(1) code execution..." -ForegroundColor Yellow
$code1 = @{
    code = "print('Hello from scheduler-worker architecture!')"
    language = "python"
    algorithm_name = "hello_world"
    input_size = 1
} | ConvertTo-Json

try {
    $result1 = Invoke-RestMethod -Uri "$BaseURL/api/run-code" -Method Post -Body $code1 -ContentType "application/json"
    Write-Host "  ✅ Success: $($result1.success)" -ForegroundColor Green
    Write-Host "  ⏱️  Runtime: $($result1.runtime)s" -ForegroundColor Green
    Write-Host "  📝 Output: $($result1.output.Trim())" -ForegroundColor Cyan
} catch {
    Write-Host "  ❌ Failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 3: Submit Linear Code (O(n))
Write-Host "[3/5] Testing O(n) code execution..." -ForegroundColor Yellow
$code2 = @{
    code = @"
def sum_array(n):
    total = 0
    for i in range(n):
        total += i
    return total

result = sum_array(1000)
print(f'Sum: {result}')
"@
    language = "python"
    algorithm_name = "linear_sum"
    input_size = 1000
} | ConvertTo-Json

try {
    $result2 = Invoke-RestMethod -Uri "$BaseURL/api/run-code" -Method Post -Body $code2 -ContentType "application/json"
    Write-Host "  ✅ Success: $($result2.success)" -ForegroundColor Green
    Write-Host "  ⏱️  Runtime: $($result2.runtime)s" -ForegroundColor Green
    Write-Host "  📝 Output: $($result2.output.Trim())" -ForegroundColor Cyan
} catch {
    Write-Host "  ❌ Failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 4: Check Scheduling Mode
Write-Host "[4/5] Checking scheduling mode..." -ForegroundColor Yellow
try {
    $mode = Invoke-RestMethod -Uri "$BaseURL/api/scheduler/mode" -Method Get
    Write-Host "  📊 Current mode: $($mode.mode)" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Could not fetch mode" -ForegroundColor Yellow
}

Write-Host ""

# Test 5: Submit Quadratic Code (O(n²))
Write-Host "[5/5] Testing O(n²) code execution..." -ForegroundColor Yellow
$code3 = @{
    code = @"
def count_pairs(n):
    count = 0
    for i in range(n):
        for j in range(n):
            count += 1
    return count

result = count_pairs(50)
print(f'Total pairs: {result}')
"@
    language = "python"
    algorithm_name = "quadratic_pairs"
    input_size = 50
} | ConvertTo-Json

try {
    $result3 = Invoke-RestMethod -Uri "$BaseURL/api/run-code" -Method Post -Body $code3 -ContentType "application/json"
    Write-Host "  ✅ Success: $($result3.success)" -ForegroundColor Green
    Write-Host "  ⏱️  Runtime: $($result3.runtime)s" -ForegroundColor Green
    Write-Host "  📝 Output: $($result3.output.Trim())" -ForegroundColor Cyan
} catch {
    Write-Host "  ❌ Failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=" * 70
Write-Host "✅ All tests completed!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Run unit tests:   pytest tests/unit/ -v" -ForegroundColor White
Write-Host "  2. Run load tests:   locust -f tests/load/locustfile.py" -ForegroundColor White
Write-Host "  3. Compare modes:    Switch between 'queue_length' and 'queue_cost'" -ForegroundColor White
Write-Host ""
Write-Host "📖 Full documentation: SCHEDULER_WORKER_README.md" -ForegroundColor White
Write-Host "=" * 70
