# PowerShell script to clean up the dist folder
# Author: Gianpaolo Albanese
# Date: 05-10-2024

# Set paths
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = Split-Path -Parent $scriptPath
$distPath = Join-Path $rootPath "dist"
$installerZipPath = Join-Path $distPath "MeetingTranscriberInstaller.zip"
$installerDirPath = Join-Path $distPath "MeetingTranscriberInstaller"

# Check if dist folder exists
if (-not (Test-Path $distPath)) {
    Write-Host "Error: dist folder not found at $distPath" -ForegroundColor Red
    exit 1
}

# Check if installer zip exists
if (-not (Test-Path $installerZipPath)) {
    Write-Host "Error: Installer ZIP not found at $installerZipPath" -ForegroundColor Red
    Write-Host "Please run create_installer_bundle.ps1 first" -ForegroundColor Red
    exit 1
}

# List files before cleanup
Write-Host "Files in dist folder before cleanup:" -ForegroundColor Cyan
Get-ChildItem -Path $distPath | Format-Table Name, Length

# Remove unnecessary files
Write-Host "Removing unnecessary files..." -ForegroundColor Yellow

# Remove the MeetingTranscriber.exe (since it's included in the MSIX)
$exePath = Join-Path $distPath "MeetingTranscriber.exe"
if (Test-Path $exePath) {
    Remove-Item -Path $exePath -Force
    Write-Host "Removed $exePath" -ForegroundColor Green
}

# Remove the MeetingTranscriber.msix (since it's included in the installer zip)
$msixPath = Join-Path $distPath "MeetingTranscriber.msix"
if (Test-Path $msixPath) {
    Remove-Item -Path $msixPath -Force
    Write-Host "Removed $msixPath" -ForegroundColor Green
}

# Remove the installer directory (since we have the zip)
if (Test-Path $installerDirPath) {
    Remove-Item -Path $installerDirPath -Recurse -Force
    Write-Host "Removed $installerDirPath" -ForegroundColor Green
}

# List files after cleanup
Write-Host "Files in dist folder after cleanup:" -ForegroundColor Cyan
Get-ChildItem -Path $distPath | Format-Table Name, Length

Write-Host "Cleanup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "The dist folder now contains only the essential installer bundle:" -ForegroundColor Cyan
Write-Host "- MeetingTranscriberInstaller.zip" -ForegroundColor White
Write-Host ""
Write-Host "This file contains everything needed to install the application:" -ForegroundColor Yellow
Write-Host "1. The MSIX package" -ForegroundColor White
Write-Host "2. The certificate" -ForegroundColor White
Write-Host "3. The installation script" -ForegroundColor White
Write-Host "4. The README file" -ForegroundColor White