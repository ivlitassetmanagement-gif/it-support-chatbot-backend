# IT Support Chatbot - Document Upload Script
# Upload IT documents to the knowledge base
# Usage: .\upload_document.ps1 -FilePath "C:\path\to\document.pdf"

param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath,
    [string]$ApiUrl = "http://localhost:8001",
    [string]$ApiKey = "sk_live_test"
)

Write-Host "=== IT Support Chatbot - Document Upload ===" -ForegroundColor Cyan
Write-Host ""

# Validate file exists
if (-not (Test-Path $FilePath)) {
    Write-Host "ERROR: File not found: $FilePath" -ForegroundColor Red
    exit 1
}

$file = Get-Item -Path $FilePath
Write-Host "File: $($file.Name)"
Write-Host "Size: $([math]::Round($file.Length / 1MB, 2)) MB"
Write-Host "Type: $($file.Extension)"
Write-Host ""

# Validate file type
$allowedTypes = @('.pdf', '.txt', '.docx', '.doc', '.md')
if ($file.Extension -notin $allowedTypes) {
    Write-Host "WARNING: File type $($file.Extension) may not be supported" -ForegroundColor Yellow
    Write-Host "Supported types: $($allowedTypes -join ', ')"
    Write-Host ""
}

# Check file size (warn if over 100MB)
if ($file.Length -gt 100MB) {
    Write-Host "WARNING: Large file (>100MB). Upload may take a while." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Uploading..." -ForegroundColor Yellow

try {
    $uri = "$ApiUrl/upload-kb"
    $headers = @{"X-API-Key" = $ApiKey}

    $response = Invoke-WebRequest -Uri $uri `
        -Method Post `
        -Headers $headers `
        -Form @{file = $file} `
        -UseBasicParsing `
        -TimeoutSec 300

    $result = $response.Content | ConvertFrom-Json

    Write-Host ""
    Write-Host "✓ Upload successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Result:" -ForegroundColor Cyan
    Write-Host "  Document: $($result.file)"
    Write-Host "  Status: $($result.status)"
    Write-Host "  Chunks indexed: $($result.chunks)"
    Write-Host "  Message: $($result.message)"
    Write-Host ""
    Write-Host "The document is now searchable in the chatbot!" -ForegroundColor Green

} catch {
    Write-Host ""
    Write-Host "✗ Upload failed!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Is the backend running? (http://localhost:8001/health)"
    Write-Host "  2. Is the file readable?"
    Write-Host "  3. Check backend logs for details"
    exit 1
}
