# Start StockTrade Locally

Write-Host "Starting StockTrade Platform Locally..." -ForegroundColor Green

$RootDir = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }

# Set up and start Backend
Write-Host "Setting up Backend..." -ForegroundColor Cyan
Start-Process powershell -WorkingDirectory "$RootDir\backend_api" -ArgumentList "-NoExit", "-Command", "Set-Location '$RootDir\backend_api'; if (Test-Path .\venv\Scripts\Activate.ps1) { .\venv\Scripts\Activate.ps1 }; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

# Set up and start Frontend
Write-Host "Setting up Frontend..." -ForegroundColor Cyan
Start-Process powershell -WorkingDirectory "$RootDir\frontend" -ArgumentList "-NoExit", "-Command", "Set-Location '$RootDir\frontend'; `$env:NODE_OPTIONS = '--max-old-space-size=4096'; npm run dev"

Write-Host "Both services are starting up in separate terminal windows." -ForegroundColor Green
Write-Host "Backend API: http://localhost:8000"
Write-Host "Frontend App: http://localhost:3000"
Write-Host "API Docs: http://localhost:8000/docs"
