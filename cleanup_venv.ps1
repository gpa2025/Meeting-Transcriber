# PowerShell script to clean up .venv directory
# Author: Gianpaolo Albanese

Write-Host "Cleaning up .venv directory..." -ForegroundColor Cyan

$venvPath = Join-Path $PSScriptRoot ".venv"

# Remove __pycache__ directories
Get-ChildItem -Path $venvPath -Filter "__pycache__" -Directory -Recurse | ForEach-Object {
    Write-Host "Removing $($_.FullName)" -ForegroundColor Yellow
    Remove-Item -Path $_.FullName -Recurse -Force
}

# Remove .dist-info directories
Get-ChildItem -Path "$venvPath\Lib\site-packages" -Filter "*.dist-info" -Directory | ForEach-Object {
    Write-Host "Removing $($_.FullName)" -ForegroundColor Yellow
    Remove-Item -Path $_.FullName -Recurse -Force
}

# Remove .egg-info directories
Get-ChildItem -Path "$venvPath\Lib\site-packages" -Filter "*.egg-info" -Directory | ForEach-Object {
    Write-Host "Removing $($_.FullName)" -ForegroundColor Yellow
    Remove-Item -Path $_.FullName -Recurse -Force
}

# Remove test directories
Get-ChildItem -Path "$venvPath\Lib\site-packages" -Filter "tests" -Directory -Recurse | ForEach-Object {
    Write-Host "Removing $($_.FullName)" -ForegroundColor Yellow
    Remove-Item -Path $_.FullName -Recurse -Force
}

# Remove documentation files
Get-ChildItem -Path "$venvPath\Lib\site-packages" -Include "*.md", "*.rst", "*.txt" -File -Recurse | ForEach-Object {
    # Skip important files like LICENSE.txt
    if ($_.Name -notmatch "^(LICENSE|NOTICE|README)") {
        Write-Host "Removing $($_.FullName)" -ForegroundColor Yellow
        Remove-Item -Path $_.FullName -Force
    }
}

# Remove certifi cacert.pem (large file)
$certPath = "$venvPath\Lib\site-packages\pip\_vendor\certifi\cacert.pem"
if (Test-Path $certPath) {
    Write-Host "Removing $certPath" -ForegroundColor Yellow
    Remove-Item -Path $certPath -Force
}

# Remove distlib binaries (large files)
$distlibPaths = @(
    "$venvPath\Lib\site-packages\pip\_vendor\distlib\t32",
    "$venvPath\Lib\site-packages\pip\_vendor\distlib\t64",
    "$venvPath\Lib\site-packages\pip\_vendor\distlib\w32",
    "$venvPath\Lib\site-packages\pip\_vendor\distlib\w64"
)

foreach ($path in $distlibPaths) {
    if (Test-Path $path) {
        Write-Host "Removing $path" -ForegroundColor Yellow
        Remove-Item -Path $path -Recurse -Force
    }
}

# Remove setuptools script templates
Get-ChildItem -Path "$venvPath\Lib\site-packages\setuptools" -Filter "script*.tmpl" -File | ForEach-Object {
    Write-Host "Removing $($_.FullName)" -ForegroundColor Yellow
    Remove-Item -Path $_.FullName -Force
}

# Remove unnecessary executables from Scripts directory
Get-ChildItem -Path "$venvPath\Scripts" -Include "*.exe", "*.bat", "*.ps1" -File | ForEach-Object {
    # Keep activate scripts and python.exe
    if ($_.Name -notmatch "^(activate|python)") {
        Write-Host "Removing $($_.FullName)" -ForegroundColor Yellow
        Remove-Item -Path $_.FullName -Force
    }
}

Write-Host "Cleanup complete!" -ForegroundColor Green