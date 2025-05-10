# PowerShell script to clean up build and dist directories
# Author: Gianpaolo Albanese

Write-Host "Cleaning up build and dist directories..." -ForegroundColor Cyan

$buildPath = Join-Path $PSScriptRoot "build"
$distPath = Join-Path $PSScriptRoot "dist"

# Remove build directory
if (Test-Path $buildPath) {
    Write-Host "Removing build directory..." -ForegroundColor Yellow
    Remove-Item -Path $buildPath -Recurse -Force
    Write-Host "Build directory removed." -ForegroundColor Green
}

# Remove dist directory
if (Test-Path $distPath) {
    Write-Host "Removing dist directory..." -ForegroundColor Yellow
    Remove-Item -Path $distPath -Recurse -Force
    Write-Host "Dist directory removed." -ForegroundColor Green
}

# Remove .spec files
Get-ChildItem -Path $PSScriptRoot -Filter "*.spec" -File | ForEach-Object {
    Write-Host "Removing $($_.Name)..." -ForegroundColor Yellow
    Remove-Item -Path $_.FullName -Force
}

# Remove __pycache__ directories in the main project
Get-ChildItem -Path $PSScriptRoot -Filter "__pycache__" -Directory -Recurse | ForEach-Object {
    Write-Host "Removing $($_.FullName)" -ForegroundColor Yellow
    Remove-Item -Path $_.FullName -Recurse -Force
}

Write-Host "Cleanup complete!" -ForegroundColor Green