# IT Support Chatbot - Windows Service Installation
# Run as Administrator!
# Usage: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#        .\install_service.ps1

param(
    [string]$ServiceName = "ChatbotService",
    [string]$DisplayName = "IT Support Chatbot",
    [string]$BackendPath = "D:\IT_Support_Chatbot\backend"
)

# Check if running as Administrator
$isAdmin = [Security.Principal.WindowsIdentity]::GetCurrent().Groups -contains "S-1-5-32-544"
if (-not $isAdmin) {
    Write-Host "ERROR: This script must run as Administrator!" -ForegroundColor Red
    exit 1
}

Write-Host "=== IT Support Chatbot Service Installation ===" -ForegroundColor Cyan
Write-Host "Service Name: $ServiceName"
Write-Host "Backend Path: $BackendPath"
Write-Host ""

# Step 1: Create batch file for service startup
Write-Host "Creating startup batch file..." -ForegroundColor Yellow
$batchContent = @"
@echo off
REM IT Support Chatbot Startup Script
cd /d "$BackendPath"
call venv\Scripts\activate.bat
python run.py
"@

$batchPath = "$BackendPath\start_service.bat"
Set-Content -Path $batchPath -Value $batchContent -Encoding ASCII
Write-Host "✓ Created: $batchPath"

# Step 2: Check if service already exists
Write-Host ""
Write-Host "Checking for existing service..." -ForegroundColor Yellow
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if ($existingService) {
    Write-Host "Service already exists. Removing old service..." -ForegroundColor Yellow

    if ($existingService.Status -eq 'Running') {
        Stop-Service -Name $ServiceName -Force
        Write-Host "✓ Stopped service"
    }

    Remove-Item "HKLM:\SYSTEM\CurrentControlSet\Services\$ServiceName" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "✓ Removed old service"
}

# Step 3: Create new service using sc.exe (built-in Windows tool)
Write-Host ""
Write-Host "Creating new Windows Service..." -ForegroundColor Yellow

$serviceDisplayName = "$DisplayName (Port 8001)"
$servicePath = "cmd.exe"
$serviceArgs = "/c `"$batchPath`""

# Use sc.exe to create service (no external tools needed)
& sc.exe create $ServiceName binPath= "$servicePath $serviceArgs" DisplayName= "$serviceDisplayName" start= auto

$LASTEXITCODE_create = $LASTEXITCODE
if ($LASTEXITCODE_create -eq 0) {
    Write-Host "✓ Service created successfully"
} else {
    Write-Host "✗ Error creating service. Exit code: $LASTEXITCODE_create" -ForegroundColor Red
    exit 1
}

# Step 4: Configure service to restart on failure
Write-Host ""
Write-Host "Configuring auto-restart on failure..." -ForegroundColor Yellow
& sc.exe failure $ServiceName reset= 300 actions= "restart/5000/restart/10000/run/C:\Windows\System32\cmd.exe /c echo Service failed > `"$BackendPath\logs\service_crash.log`""
Write-Host "✓ Configured restart behavior"

# Step 5: Start service
Write-Host ""
Write-Host "Starting service..." -ForegroundColor Yellow
Start-Service -Name $ServiceName -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

# Step 6: Verify service is running
Write-Host ""
Write-Host "Verifying service status..." -ForegroundColor Yellow
$service = Get-Service -Name $ServiceName
$service | Format-List Name, DisplayName, Status, StartType

if ($service.Status -eq 'Running') {
    Write-Host ""
    Write-Host "✓✓✓ Service installed and running successfully! ✓✓✓" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access the chatbot at: http://localhost:8001/frontend/" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "⚠ Service created but not running. Check logs:" -ForegroundColor Yellow
    Write-Host "  PowerShell: Get-EventLog -LogName System -Source $ServiceName -Newest 10"
}

# Step 7: Show management commands
Write-Host ""
Write-Host "=== Service Management Commands ===" -ForegroundColor Cyan
Write-Host "Start service:   Start-Service -Name $ServiceName"
Write-Host "Stop service:    Stop-Service -Name $ServiceName"
Write-Host "Restart service: Restart-Service -Name $ServiceName"
Write-Host "View status:     Get-Service -Name $ServiceName"
Write-Host "Remove service:  & sc.exe delete $ServiceName"
Write-Host ""
Write-Host "View logs:"
Write-Host "  Get-EventLog -LogName System -Source $ServiceName -Newest 20"
Write-Host ""
