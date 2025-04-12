# PowerShell script to copy essential files to the package directory

$files = @(
    "price_alerts_refactored.py",
    "ai_analysis.py",
    "telegram_utils.py",
    "test_price_alerts.py",
    "test_alert.py",
    "test_ai_analysis.py",
    "test_openai_direct.py"
)

$targetDir = "price_alerts_package"

# Create target directory if it doesn't exist
if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir | Out-Null
    Write-Host "Created directory: $targetDir"
}

# Copy each file
foreach ($file in $files) {
    if (Test-Path $file) {
        Copy-Item $file -Destination $targetDir
        Write-Host "Copied: $file"
    } else {
        Write-Host "File not found: $file"
    }
}

Write-Host "All files copied to $targetDir"
