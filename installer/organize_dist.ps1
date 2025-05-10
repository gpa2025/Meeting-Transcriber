# PowerShell script to organize distribution files
# Author: Gianpaolo Albanese
# Date: 05-09-2024

# Set paths
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$distPath = Join-Path $scriptPath "..\dist"
$distPackagePath = Join-Path $distPath "package"

Write-Host "Organizing distribution files..." -ForegroundColor Cyan

# Create distribution package directory
if (-not (Test-Path $distPackagePath)) {
    New-Item -ItemType Directory -Force -Path $distPackagePath | Out-Null
    Write-Host "Created package directory in dist folder" -ForegroundColor Green
}

# Copy necessary files to distribution package
Copy-Item (Join-Path $scriptPath "README.md") -Destination $distPackagePath -Force
Copy-Item (Join-Path $scriptPath "UserGuide.md") -Destination $distPackagePath -Force
Copy-Item (Join-Path $scriptPath ".env.example") -Destination $distPackagePath -Force
Write-Host "Copied documentation files to dist/package folder" -ForegroundColor Green

# Copy icon to distribution package
Copy-Item (Join-Path $scriptPath "icon.ico") -Destination $distPackagePath -Force
Write-Host "Copied icon to dist/package folder" -ForegroundColor Green

# Move MSIX package to dist folder when created
$msixPath = Join-Path $scriptPath "MeetingTranscriber.msix"
if (Test-Path $msixPath) {
    Move-Item $msixPath -Destination $distPath -Force
    Write-Host "Moved MSIX package to dist folder" -ForegroundColor Green
} else {
    Write-Host "Note: MSIX package not found. Run create_msix_package.bat first." -ForegroundColor Yellow
}

# Update create_msix_package.ps1 to output directly to dist folder
$createMsixPath = Join-Path $scriptPath "create_msix_package.ps1"
if (Test-Path $createMsixPath) {
    $content = Get-Content $createMsixPath -Raw
    $newContent = $content -replace '\$outputPath = Join-Path \$scriptPath "MeetingTranscriber.msix"', '$outputPath = Join-Path $scriptPath "..\dist\MeetingTranscriber.msix"'
    Set-Content -Path $createMsixPath -Value $newContent
    Write-Host "Updated create_msix_package.ps1 to output directly to dist folder" -ForegroundColor Green
}

Write-Host ""
Write-Host "Organization complete!" -ForegroundColor Green
Write-Host "Distribution files are now in: $distPackagePath" -ForegroundColor White
Write-Host "MSIX package will be created in: $distPath" -ForegroundColor White
Write-Host ""