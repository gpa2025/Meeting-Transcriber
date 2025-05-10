# PowerShell script to create proper icons for MSIX package
# Author: Gianpaolo Albanese
# Date: 05-09-2024

# Set paths
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$assetsPath = Join-Path $scriptPath "Assets"

# Create Assets directory if it doesn't exist
if (-not (Test-Path $assetsPath)) {
    New-Item -ItemType Directory -Force -Path $assetsPath | Out-Null
    Write-Host "Created Assets directory" -ForegroundColor Green
}

# Load System.Drawing assembly
Add-Type -AssemblyName System.Drawing

# Function to create an icon with GPA as main text and Meeting Transcriber as subtext
function Create-Icon {
    param (
        [string]$outputPath,
        [int]$width,
        [int]$height,
        [string]$mainText = "GPA",
        [string]$subText = "Meeting Transcriber V1",
        [int]$mainFontSize = 0,
        [int]$subFontSize = 0
    )
    
    # Calculate font sizes if not specified
    if ($mainFontSize -eq 0) {
        $mainFontSize = [Math]::Max(10, [Math]::Floor($width / 5))
    }
    
    if ($subFontSize -eq 0) {
        $subFontSize = [Math]::Max(8, [Math]::Floor($mainFontSize / 3))
    }
    
    try {
        # Create a bitmap with the specified dimensions
        $bitmap = New-Object System.Drawing.Bitmap($width, $height)
        
        # Create a graphics object from the bitmap with high quality settings
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
        $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias
        
        # Fill the background with blue
        $graphics.Clear([System.Drawing.Color]::FromArgb(0, 120, 212))
        
        # Create a brush for the text
        $brush = [System.Drawing.Brushes]::White
        
        # For very small icons, just show GPA
        if ($width -le 50) {
            $font = New-Object System.Drawing.Font("Arial", $mainFontSize, [System.Drawing.FontStyle]::Bold)
            $textSize = $graphics.MeasureString($mainText, $font)
            $textX = ($width - $textSize.Width) / 2
            $textY = ($height - $textSize.Height) / 2
            $graphics.DrawString($mainText, $font, $brush, $textX, $textY)
        }
        else {
            # Draw GPA as the main text
            $mainFont = New-Object System.Drawing.Font("Arial", $mainFontSize, [System.Drawing.FontStyle]::Bold)
            $mainSize = $graphics.MeasureString($mainText, $mainFont)
            $mainX = ($width - $mainSize.Width) / 2
            
            # Position text at the top for Square150x150Logo.png
            if ($width -eq 150 -and $height -eq 150) {
                $mainY = $height * 0.15  # Position higher up in the box
            } else {
                $mainY = $height * 0.25  # Default position for other icons
            }
            
            $graphics.DrawString($mainText, $mainFont, $brush, $mainX, $mainY)
            
            # Draw Meeting Transcriber as subtext
            $subFont = New-Object System.Drawing.Font("Arial", $subFontSize, [System.Drawing.FontStyle]::Regular)
            
            # For wide icons, show the full text
            if ($width -ge 300) {
                $subSize = $graphics.MeasureString($subText, $subFont)
                $subX = ($width - $subSize.Width) / 2
                $subY = $height * 0.6
                $graphics.DrawString($subText, $subFont, $brush, $subX, $subY)
            }
            # For medium icons, show abbreviated text
            else {
                # Special case for Square150x150Logo.png
                if ($width -eq 150 -and $height -eq 150) {
                    # Draw "Meeting Transcriber" in the middle
                    $mtText = "Meeting Transcriber"
                    $mtFont = New-Object System.Drawing.Font("Arial", [Math]::Max(8, $subFontSize - 2), [System.Drawing.FontStyle]::Regular)
                    $mtSize = $graphics.MeasureString($mtText, $mtFont)
                    $mtX = ($width - $mtSize.Width) / 2
                    $mtY = $height * 0.55
                    $graphics.DrawString($mtText, $mtFont, $brush, $mtX, $mtY)
                    
                    # Draw "V1" at the bottom
                    $v1Text = "V1"
                    $v1Font = New-Object System.Drawing.Font("Arial", $subFontSize, [System.Drawing.FontStyle]::Bold)
                    $v1Size = $graphics.MeasureString($v1Text, $v1Font)
                    $v1X = ($width - $v1Size.Width) / 2
                    $v1Y = $height * 0.8
                    $graphics.DrawString($v1Text, $v1Font, $brush, $v1X, $v1Y)
                } else {
                    # Default behavior for other medium icons
                    $shorterSubText = "Meeting Transcriber"
                    $subSize = $graphics.MeasureString($shorterSubText, $subFont)
                    $subX = ($width - $subSize.Width) / 2
                    $subY = $height * 0.6
                    $graphics.DrawString($shorterSubText, $subFont, $brush, $subX, $subY)
                }
            }
        }
        
        # Save the bitmap as a PNG file
        $bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
        
        # Clean up
        $graphics.Dispose()
        $bitmap.Dispose()
        
        Write-Host "Created $outputPath" -ForegroundColor Green
    }
    catch {
        Write-Host "Error creating $outputPath`: $_" -ForegroundColor Red
    }
}

# Function to create a splash screen
function Create-SplashScreen {
    param (
        [string]$outputPath,
        [int]$width = 620,
        [int]$height = 300
    )
    
    try {
        # Create a bitmap with the specified dimensions
        $bitmap = New-Object System.Drawing.Bitmap($width, $height)
        
        # Create a graphics object from the bitmap
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
        $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias
        
        # Fill the background with blue
        $graphics.Clear([System.Drawing.Color]::FromArgb(0, 120, 212))
        
        # Create a brush for the text
        $brush = [System.Drawing.Brushes]::White
        
        # Draw "GPA" as the main text (larger)
        $mainFont = New-Object System.Drawing.Font("Arial", 80, [System.Drawing.FontStyle]::Bold)
        $mainText = "GPA"
        $mainSize = $graphics.MeasureString($mainText, $mainFont)
        $mainX = ($width - $mainSize.Width) / 2
        $mainY = $height * 0.2
        $graphics.DrawString($mainText, $mainFont, $brush, $mainX, $mainY)
        
        # Draw "Meeting Transcriber" as smaller text
        $subFont = New-Object System.Drawing.Font("Arial", 40, [System.Drawing.FontStyle]::Bold)
        $subText = "Meeting Transcriber"
        $subSize = $graphics.MeasureString($subText, $subFont)
        $subX = ($width - $subSize.Width) / 2
        $subY = $height * 0.55
        $graphics.DrawString($subText, $subFont, $brush, $subX, $subY)
        
        # Draw version at the bottom
        $versionFont = New-Object System.Drawing.Font("Arial", 24, [System.Drawing.FontStyle]::Regular)
        $versionText = "V1.0"
        $versionSize = $graphics.MeasureString($versionText, $versionFont)
        $versionX = ($width - $versionSize.Width) / 2
        $versionY = $height * 0.8
        $graphics.DrawString($versionText, $versionFont, $brush, $versionX, $versionY)
        
        # Save the bitmap as a PNG file
        $bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
        
        # Clean up
        $graphics.Dispose()
        $bitmap.Dispose()
        
        Write-Host "Created $outputPath" -ForegroundColor Green
    }
    catch {
        Write-Host "Error creating $outputPath`: $_" -ForegroundColor Red
    }
}

# Create all the required icons
Write-Host "Creating icons for MSIX package..." -ForegroundColor Cyan

# Small icon (44x44) - Just "GPA"
Create-Icon -outputPath "$assetsPath\Square44x44Logo.png" -width 44 -height 44 -mainText "GPA" -mainFontSize 14

# Medium icon (150x150)
Create-Icon -outputPath "$assetsPath\Square150x150Logo.png" -width 150 -height 150 -mainText "GPA" -mainFontSize 38 -subText "Meeting Transcriber V1" -subFontSize 10

# Wide icon (310x150)
Create-Icon -outputPath "$assetsPath\Wide310x150Logo.png" -width 310 -height 150 -mainText "GPA" -mainFontSize 40 -subText "Meeting Transcriber V1" -subFontSize 20

# Store logo (50x50)
Create-Icon -outputPath "$assetsPath\StoreLogo.png" -width 50 -height 50 -mainText "GPA" -mainFontSize 16

# Splash screen (620x300)
Create-SplashScreen -outputPath "$assetsPath\SplashScreen.png" -width 620 -height 300

Write-Host "All icons created successfully!" -ForegroundColor Green