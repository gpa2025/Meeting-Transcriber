# PowerShell script to create MSIX package for Meeting Transcriber
# Author: Gianpaolo Albanese
# Date: 05-09-2024

# Set paths
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$exePath = Join-Path $scriptPath "..\dist\MeetingTranscriber.exe"
$outputPath = Join-Path $scriptPath "..\dist\MeetingTranscriber.msix"
$assetsPath = Join-Path $scriptPath "Assets"
$iconPath = Join-Path $scriptPath "..\icon.ico"

# Check if executable exists
if (-not (Test-Path $exePath)) {
    Write-Host "Error: Executable not found at $exePath" -ForegroundColor Red
    Write-Host "Please build the executable first using build_exe.py" -ForegroundColor Red
    exit 1
}

# Create Assets directory if it doesn't exist
if (-not (Test-Path $assetsPath)) {
    New-Item -ItemType Directory -Force -Path $assetsPath | Out-Null
    Write-Host "Created Assets directory" -ForegroundColor Green
}

# Function to convert icon to PNG with specified size
function Convert-IconToPng {
    param (
        [string]$iconPath,
        [string]$outputPath,
        [int]$width,
        [int]$height
    )
    
    try {
        Add-Type -AssemblyName System.Drawing
        
        # Load the icon
        $icon = [System.Drawing.Icon]::ExtractAssociatedIcon($iconPath)
        if (-not $icon) {
            $icon = [System.Drawing.Icon]::ExtractAssociatedIcon($exePath)
        }
        
        # Convert to bitmap and resize
        $bitmap = New-Object System.Drawing.Bitmap($width, $height)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.DrawImage($icon.ToBitmap(), 0, 0, $width, $height)
        
        # Save as PNG
        $bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
        $graphics.Dispose()
        $bitmap.Dispose()
        
        Write-Host "Created $outputPath" -ForegroundColor Green
    }
    catch {
        Write-Host "Error creating $outputPath`: $_" -ForegroundColor Red
    }
}

# Create PNG assets from icon
Write-Host "Creating PNG assets from icon..." -ForegroundColor Cyan
Convert-IconToPng -iconPath $iconPath -outputPath "$assetsPath\Square44x44Logo.png" -width 44 -height 44
Convert-IconToPng -iconPath $iconPath -outputPath "$assetsPath\Square150x150Logo.png" -width 150 -height 150
Convert-IconToPng -iconPath $iconPath -outputPath "$assetsPath\Wide310x150Logo.png" -width 310 -height 150
Convert-IconToPng -iconPath $iconPath -outputPath "$assetsPath\StoreLogo.png" -width 50 -height 50
Convert-IconToPng -iconPath $iconPath -outputPath "$assetsPath\SplashScreen.png" -width 620 -height 300

# Create a temporary directory for the package contents
$tempDir = Join-Path $scriptPath "msix_temp"
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
Write-Host "Created temporary directory for package contents" -ForegroundColor Green

# Copy files to the temporary directory
Copy-Item $exePath -Destination $tempDir
Copy-Item $iconPath -Destination $tempDir
Copy-Item (Join-Path $scriptPath "README.md") -Destination $tempDir
Copy-Item (Join-Path $scriptPath "UserGuide.md") -Destination $tempDir
Copy-Item (Join-Path $scriptPath ".env.example") -Destination $tempDir
Copy-Item (Join-Path $scriptPath "AppxManifest.xml") -Destination $tempDir
Copy-Item -Recurse $assetsPath -Destination $tempDir
Write-Host "Copied all required files to temporary directory" -ForegroundColor Green

# Check if MakeAppx.exe exists in Windows SDK
$sdkVersions = @("10.0.22621.0", "10.0.20348.0", "10.0.19041.0", "10.0.18362.0", "10.0.17763.0")
$makeAppxPath = $null

foreach ($version in $sdkVersions) {
    $path = "C:\Program Files (x86)\Windows Kits\10\bin\$version\x64\makeappx.exe"
    if (Test-Path $path) {
        $makeAppxPath = $path
        break
    }
}

if (-not $makeAppxPath) {
    # Try to find makeappx.exe in any location
    $makeAppxPath = Get-ChildItem -Path "C:\Program Files (x86)\Windows Kits" -Recurse -Filter "makeappx.exe" | Select-Object -First 1 -ExpandProperty FullName
}

if ($makeAppxPath) {
    # Create MSIX package using MakeAppx.exe
    Write-Host "Creating MSIX package using $makeAppxPath..." -ForegroundColor Cyan
    $currentLocation = Get-Location
    Set-Location $tempDir
    
    & $makeAppxPath pack /d . /p $outputPath
    
    Set-Location $currentLocation
    
    if (Test-Path $outputPath) {
        Write-Host "MSIX package created successfully at: $outputPath" -ForegroundColor Green
    } else {
        Write-Host "Failed to create MSIX package" -ForegroundColor Red
    }
} else {
    Write-Host "MakeAppx.exe not found. Please install Windows SDK or Windows App Certification Kit." -ForegroundColor Red
    Write-Host "You can download it from: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/" -ForegroundColor Yellow
}

# Clean up the temporary directory
Remove-Item -Recurse -Force $tempDir
Write-Host "Cleaned up temporary directory" -ForegroundColor Green

# Final instructions
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Install the MSIX package by double-clicking $outputPath" -ForegroundColor White
Write-Host "2. If you see a security warning, click 'Install anyway'" -ForegroundColor White
Write-Host "3. The application will be installed and available in the Start menu" -ForegroundColor White
Write-Host ""
Write-Host "Note: To distribute this package to other users, they may need to install the" -ForegroundColor Yellow
Write-Host "certificate used to sign the package. For proper distribution, consider" -ForegroundColor Yellow
Write-Host "signing the package with a trusted certificate." -ForegroundColor Yellow

