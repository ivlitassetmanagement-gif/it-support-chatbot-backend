# IT Support Chatbot - Health Monitor
# Run this periodically to check system health
# Usage: .\monitor_chatbot.ps1

param(
    [string]$ApiUrl = "http://localhost:8001",
    [string]$LogPath = "D:\IT_Support_Chatbot\backend\logs\health_check.log"
)

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$healthStatus = @()

Write-Host "=== IT Support Chatbot Health Monitor ===" -ForegroundColor Cyan
Write-Host "Time: $timestamp"
Write-Host ""

# Ensure logs directory exists
$logDir = Split-Path -Parent $LogPath
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Log-Message {
    param([string]$Message, [string]$Level = "INFO")
    $msg = "[$timestamp] [$Level] $Message"
    Write-Host $msg
    Add-Content -Path $LogPath -Value $msg
}

# ==================== TEST 1: Health Endpoint ====================
Write-Host "Test 1: Health Endpoint" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$ApiUrl/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Health endpoint: OK" -ForegroundColor Green
        Log-Message "Health endpoint: OK (Status: 200)" "SUCCESS"
        $healthStatus += $true
    } else {
        Write-Host "✗ Health endpoint: Status $($response.StatusCode)" -ForegroundColor Red
        Log-Message "Health endpoint: FAILED (Status: $($response.StatusCode))" "ERROR"
        $healthStatus += $false
    }
} catch {
    Write-Host "✗ Health endpoint: Connection failed" -ForegroundColor Red
    Log-Message "Health endpoint: FAILED - $_" "ERROR"
    $healthStatus += $false
}

# ==================== TEST 2: Service Status ====================
Write-Host ""
Write-Host "Test 2: Service Status" -ForegroundColor Yellow
try {
    $service = Get-Service -Name "ChatbotService" -ErrorAction SilentlyContinue
    if ($service) {
        if ($service.Status -eq 'Running') {
            Write-Host "✓ Service Status: Running" -ForegroundColor Green
            Log-Message "Service Status: Running" "SUCCESS"
            $healthStatus += $true
        } else {
            Write-Host "✗ Service Status: $($service.Status)" -ForegroundColor Red
            Log-Message "Service Status: $($service.Status)" "WARNING"
            $healthStatus += $false
        }
    } else {
        Write-Host "⚠ Service not installed" -ForegroundColor Yellow
        Log-Message "Service not installed" "WARNING"
        $healthStatus += $null
    }
} catch {
    Write-Host "✗ Error checking service: $_" -ForegroundColor Red
    Log-Message "Service check failed: $_" "ERROR"
    $healthStatus += $false
}

# ==================== TEST 3: Authentication ====================
Write-Host ""
Write-Host "Test 3: Authentication" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$ApiUrl/auth/token" `
        -Method Post `
        -Headers @{"X-API-Key" = "sk_live_test"} `
        -UseBasicParsing `
        -TimeoutSec 5

    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Authentication: OK" -ForegroundColor Green
        Log-Message "Authentication endpoint: OK" "SUCCESS"
        $healthStatus += $true
    }
} catch {
    Write-Host "✗ Authentication failed: $_" -ForegroundColor Red
    Log-Message "Authentication failed: $_" "ERROR"
    $healthStatus += $false
}

# ==================== TEST 4: Process Memory ====================
Write-Host ""
Write-Host "Test 4: Process Memory" -ForegroundColor Yellow
try {
    $processes = Get-Process -Name "python" -ErrorAction SilentlyContinue | `
        Where-Object {$_.CommandLine -like "*run.py*"}

    if ($processes) {
        $totalMemoryMB = 0
        foreach ($proc in $processes) {
            $memMB = [math]::Round($proc.WorkingSet / 1MB, 2)
            $totalMemoryMB += $memMB
            Write-Host "  Process $($proc.Id): $memMB MB"
        }

        if ($totalMemoryMB -gt 2048) {
            Write-Host "⚠ High memory usage: $totalMemoryMB MB" -ForegroundColor Yellow
            Log-Message "Memory usage HIGH: $totalMemoryMB MB" "WARNING"
            $healthStatus += $false
        } else {
            Write-Host "✓ Memory usage: $totalMemoryMB MB" -ForegroundColor Green
            Log-Message "Memory usage OK: $totalMemoryMB MB" "SUCCESS"
            $healthStatus += $true
        }
    } else {
        Write-Host "✗ Python process not found" -ForegroundColor Red
        Log-Message "Python process not found" "ERROR"
        $healthStatus += $false
    }
} catch {
    Write-Host "⚠ Could not check memory: $_" -ForegroundColor Yellow
    Log-Message "Memory check skipped: $_" "WARNING"
}

# ==================== TEST 5: Disk Space ====================
Write-Host ""
Write-Host "Test 5: Disk Space" -ForegroundColor Yellow
try {
    $drive = Get-Volume -DriveLetter D -ErrorAction SilentlyContinue
    if ($drive) {
        $percentFree = [math]::Round($drive.SizeRemaining / $drive.Size * 100, 2)
        Write-Host "  D: Drive - $percentFree% free"

        if ($percentFree -lt 5) {
            Write-Host "✗ CRITICAL: Disk space critically low!" -ForegroundColor Red
            Log-Message "Disk space CRITICAL: $percentFree% free" "ERROR"
            $healthStatus += $false
        } elseif ($percentFree -lt 10) {
            Write-Host "⚠ Low disk space: $percentFree% free" -ForegroundColor Yellow
            Log-Message "Disk space LOW: $percentFree% free" "WARNING"
            $healthStatus += $false
        } else {
            Write-Host "✓ Disk space OK: $percentFree% free" -ForegroundColor Green
            Log-Message "Disk space OK: $percentFree% free" "SUCCESS"
            $healthStatus += $true
        }
    }
} catch {
    Write-Host "⚠ Could not check disk: $_" -ForegroundColor Yellow
    Log-Message "Disk check skipped: $_" "WARNING"
}

# ==================== SUMMARY ====================
Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
$passCount = ($healthStatus | Where-Object {$_ -eq $true}).Count
$failCount = ($healthStatus | Where-Object {$_ -eq $false}).Count
$skipCount = ($healthStatus | Where-Object {$_ -eq $null}).Count

Write-Host "Passed: $passCount | Failed: $failCount | Skipped: $skipCount"

if ($failCount -eq 0 -and $passCount -gt 0) {
    Write-Host "✓ All checks PASSED" -ForegroundColor Green
    Log-Message "All checks PASSED" "SUCCESS"
    exit 0
} else {
    Write-Host "✗ Some checks FAILED" -ForegroundColor Red
    Log-Message "Some checks FAILED" "ERROR"
    exit 1
}
