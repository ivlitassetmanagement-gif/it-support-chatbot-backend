# IT Support Chatbot - Backup Script
# Backs up ChromaDB, Documents, and PostgreSQL database
# Usage: .\backup_chatbot.ps1
# Schedule: Add to Windows Task Scheduler to run daily

param(
    [string]$BackendPath = "D:\IT_Support_Chatbot\backend",
    [string]$BackupPath = "D:\IT_Support_Chatbot\storage\backups",
    [int]$RetentionDays = 30
)

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "$BackendPath\logs\backup.log"

function Log-Message {
    param([string]$Message, [string]$Level = "INFO")
    $msg = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [$Level] $Message"
    Write-Host $msg
    Add-Content -Path $logFile -Value $msg
}

Write-Host "=== IT Support Chatbot Backup ===" -ForegroundColor Cyan
Write-Host "Backup Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "Backup Path: $BackupPath"
Write-Host ""

# Create backup directory if it doesn't exist
if (-not (Test-Path $BackupPath)) {
    New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
    Write-Host "Created backup directory"
}

# Create logs directory
$logsDir = "$BackendPath\logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

Log-Message "=== Backup Started ===" "INFO"

# ==================== BACKUP 1: ChromaDB ====================
Write-Host "Backing up ChromaDB..." -ForegroundColor Yellow
try {
    $chromaDir = "$BackendPath\storage\chromadb"
    if (Test-Path $chromaDir) {
        $chromaBackup = "$BackupPath\chromadb_$timestamp"
        Copy-Item -Path $chromaDir -Destination $chromaBackup -Recurse -Force
        $size = (Get-ChildItem -Path $chromaBackup -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host "✓ ChromaDB backed up to: $chromaBackup ($([math]::Round($size, 2)) MB)"
        Log-Message "ChromaDB backup successful: $chromaBackup ($([math]::Round($size, 2)) MB)" "SUCCESS"
    } else {
        Write-Host "⚠ ChromaDB directory not found: $chromaDir"
        Log-Message "ChromaDB directory not found" "WARNING"
    }
} catch {
    Write-Host "✗ ChromaDB backup failed: $_" -ForegroundColor Red
    Log-Message "ChromaDB backup FAILED: $_" "ERROR"
}

# ==================== BACKUP 2: Documents ====================
Write-Host ""
Write-Host "Backing up documents..." -ForegroundColor Yellow
try {
    $docsDir = "$BackendPath\storage\docs"
    if (Test-Path $docsDir) {
        $docsBackup = "$BackupPath\docs_$timestamp"
        Copy-Item -Path $docsDir -Destination $docsBackup -Recurse -Force
        $size = (Get-ChildItem -Path $docsBackup -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host "✓ Documents backed up to: $docsBackup ($([math]::Round($size, 2)) MB)"
        Log-Message "Documents backup successful: $docsBackup ($([math]::Round($size, 2)) MB)" "SUCCESS"
    } else {
        Write-Host "⚠ Documents directory not found: $docsDir"
        Log-Message "Documents directory not found" "WARNING"
    }
} catch {
    Write-Host "✗ Documents backup failed: $_" -ForegroundColor Red
    Log-Message "Documents backup FAILED: $_" "ERROR"
}

# ==================== BACKUP 3: Configuration ====================
Write-Host ""
Write-Host "Backing up configuration..." -ForegroundColor Yellow
try {
    $envFile = "$BackendPath\.env"
    if (Test-Path $envFile) {
        $envBackup = "$BackupPath\.env_$timestamp"
        Copy-Item -Path $envFile -Destination $envBackup
        Write-Host "✓ Configuration backed up to: $envBackup"
        Log-Message "Configuration backup successful: $envBackup" "SUCCESS"
    }
} catch {
    Write-Host "✗ Configuration backup failed: $_" -ForegroundColor Red
    Log-Message "Configuration backup FAILED: $_" "ERROR"
}

# ==================== CLEANUP: Remove Old Backups ====================
Write-Host ""
Write-Host "Cleaning up old backups (keeping last $RetentionDays days)..." -ForegroundColor Yellow
try {
    $cutoffDate = (Get-Date).AddDays(-$RetentionDays)
    $oldBackups = Get-ChildItem -Path $BackupPath -Recurse | `
        Where-Object {$_.LastWriteTime -lt $cutoffDate}

    if ($oldBackups) {
        $oldCount = ($oldBackups | Measure-Object).Count
        $oldSize = ($oldBackups | Measure-Object -Property Length -Sum).Sum / 1MB

        foreach ($backup in $oldBackups) {
            Remove-Item -Path $backup.FullName -Force -ErrorAction SilentlyContinue
        }

        Write-Host "✓ Removed $oldCount old backup files ($([math]::Round($oldSize, 2)) MB freed)"
        Log-Message "Cleaned up $oldCount old backups ($([math]::Round($oldSize, 2)) MB freed)" "SUCCESS"
    } else {
        Write-Host "✓ No old backups to remove"
        Log-Message "No old backups to remove" "INFO"
    }
} catch {
    Write-Host "⚠ Cleanup error (non-critical): $_" -ForegroundColor Yellow
    Log-Message "Cleanup warning: $_" "WARNING"
}

# ==================== SUMMARY ====================
Write-Host ""
Write-Host "=== Backup Summary ===" -ForegroundColor Cyan

$totalSize = 0
if (Test-Path $BackupPath) {
    $backupStats = Get-ChildItem -Path $BackupPath -Recurse -ErrorAction SilentlyContinue | `
        Measure-Object -Property Length -Sum
    $totalSize = $backupStats.Sum / 1MB
}

Write-Host "Total backup size: $([math]::Round($totalSize, 2)) MB"
Write-Host "Backup location: $BackupPath"
Write-Host "Retention period: $RetentionDays days"
Write-Host ""
Write-Host "✓ Backup completed successfully!" -ForegroundColor Green
Log-Message "=== Backup Completed Successfully ===" "SUCCESS"
