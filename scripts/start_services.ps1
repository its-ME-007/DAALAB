# Start both microservices for the DAALAB platform

Write-Host "🚀 Starting DAALAB Platform Microservices..." -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ Error: .env file not found!" -ForegroundColor Red
    Write-Host "Please create a .env file with your configuration." -ForegroundColor Yellow
    Write-Host "See .env.example for template" -ForegroundColor Yellow
    exit 1
}

# Check if required packages are installed
Write-Host "📦 Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import fastapi, langchain, openai, supabase" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Missing dependencies. Installing..." -ForegroundColor Red
        pip install -r requirements.txt
    } else {
        Write-Host "✅ Dependencies OK" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Could not verify dependencies" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting services..." -ForegroundColor Cyan
Write-Host "  • Main API Service: http://localhost:8000" -ForegroundColor White
Write-Host "  • AI Helper Service: http://localhost:8001" -ForegroundColor White
Write-Host ""

# Start Main API Service
Write-Host "🔵 Starting Main API Service (Port 8000)..." -ForegroundColor Blue
$mainService = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Write-Host '🔵 Main API Service Running' -ForegroundColor Blue; python api_server.py"
) -PassThru -WindowStyle Normal

Start-Sleep -Seconds 2

# Start AI Helper Service
Write-Host "🤖 Starting AI Helper Service (Port 8001)..." -ForegroundColor Magenta
$aiService = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Write-Host '🤖 AI Helper Service Running' -ForegroundColor Magenta; python -m helper_agent.agent_service"
) -PassThru -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "✅ All services started successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Service URLs:" -ForegroundColor Cyan
Write-Host "  Main API:       http://localhost:8000" -ForegroundColor White
Write-Host "  AI Service:     http://localhost:8001" -ForegroundColor White
Write-Host "  Health Check:   http://localhost:8000/api/health" -ForegroundColor White
Write-Host "  AI Health:      http://localhost:8001/health" -ForegroundColor White
Write-Host ""
Write-Host "📖 Documentation: See AI_SERVICE_README.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to stop all services..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Cleanup - Stop services
Write-Host ""
Write-Host "🛑 Stopping services..." -ForegroundColor Red
try {
    Stop-Process -Id $mainService.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $aiService.Id -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Services stopped" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Some services may still be running" -ForegroundColor Yellow
}
