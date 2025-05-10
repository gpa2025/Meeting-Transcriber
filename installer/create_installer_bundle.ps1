# PowerShell script to create a self-contained installer bundle with MSIX and certificate
# Author: Gianpaolo Albanese
# Date: 05-10-2024

# Set paths
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = Split-Path -Parent $scriptPath
$msixPath = Join-Path $rootPath "dist\MeetingTranscriber.msix"
$certPath = Join-Path $scriptPath "MeetingTranscriberCert.pfx"
$certPublicPath = Join-Path $scriptPath "MeetingTranscriberCert.cer"
$outputDir = Join-Path $rootPath "dist"
$installerDir = Join-Path $outputDir "MeetingTranscriberInstaller"
$installerZip = Join-Path $outputDir "MeetingTranscriberInstaller.zip"
$installerScript = Join-Path $installerDir "Install.bat"

# Check if the MSIX package exists
if (-not (Test-Path $msixPath)) {
    Write-Host "Error: MSIX package not found at $msixPath" -ForegroundColor Red
    Write-Host "Please build the MSIX package first using create_msix_package.ps1" -ForegroundColor Red
    exit 1
}

# Create certificate if it doesn't exist
if (-not (Test-Path $certPublicPath)) {
    Write-Host "Certificate not found. Creating self-signed certificate..." -ForegroundColor Cyan
    
    # Certificate password
    $password = "MeetingTranscriber2024"
    $securePassword = ConvertTo-SecureString -String $password -Force -AsPlainText
    
    # Create the certificate
    $cert = New-SelfSignedCertificate -Type Custom -Subject "CN=GPA Meeting Transcriber" `
        -KeyUsage DigitalSignature -FriendlyName "Meeting Transcriber Certificate" `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
    
    # Export the certificate as PFX (with private key)
    Export-PfxCertificate -cert "Cert:\CurrentUser\My\$($cert.Thumbprint)" `
        -FilePath $certPath -Password $securePassword | Out-Null
    
    # Export the public certificate for installation
    Export-Certificate -Cert "Cert:\CurrentUser\My\$($cert.Thumbprint)" `
        -FilePath $certPublicPath -Type CERT | Out-Null
    
    Write-Host "Certificate created and exported to:" -ForegroundColor Green
    Write-Host "  - Private key (PFX): $certPath" -ForegroundColor Green
    Write-Host "  - Public key (CER): $certPublicPath" -ForegroundColor Green
}

# Create installer directory
if (Test-Path $installerDir) {
    Remove-Item -Recurse -Force $installerDir
}
New-Item -ItemType Directory -Force -Path $installerDir | Out-Null
Write-Host "Created installer directory at $installerDir" -ForegroundColor Green

# Copy MSIX package and certificate to installer directory
Copy-Item $msixPath -Destination $installerDir
Copy-Item $certPublicPath -Destination $installerDir
Write-Host "Copied MSIX package and certificate to installer directory" -ForegroundColor Green

# Create installation script
$installBatchContent = @"
@echo off
echo ===================================================
echo Meeting Transcriber Installer
echo ===================================================
echo.
echo This script will:
echo 1. Install the certificate to your trusted root store
echo 2. Install the Meeting Transcriber application
echo.
echo Please allow administrative access when prompted.
echo.
pause

REM Install certificate to trusted root store (requires admin)
echo Installing certificate...
powershell -Command "Start-Process certutil -ArgumentList '-addstore', 'ROOT', 'MeetingTranscriberCert.cer' -Verb RunAs -Wait"
echo Certificate installed.
echo.

REM Install MSIX package
echo Installing Meeting Transcriber...
powershell -Command "Add-AppxPackage -Path 'MeetingTranscriber.msix'"
echo.

echo Installation complete!
echo You can now find Meeting Transcriber in your Start menu.
echo.
pause
"@

Set-Content -Path $installerScript -Value $installBatchContent
Write-Host "Created installation script" -ForegroundColor Green

# Create a README file
$readmeContent = @"
# Meeting Transcriber Installer

## Installation Instructions

1. Extract all files from this ZIP archive to a folder
2. Run the Install.bat file
3. Allow administrative access when prompted
4. The installer will:
   - Install the certificate to your trusted root store
   - Install the Meeting Transcriber application
5. After installation, you can find Meeting Transcriber in your Start menu

## System Requirements

- Windows 10 or Windows 11
- Internet connection for AWS services

## Support

For support, please contact: albaneg@yahoo.com
"@

Set-Content -Path (Join-Path $installerDir "README.txt") -Value $readmeContent
Write-Host "Created README file" -ForegroundColor Green

# Create ZIP archive
if (Test-Path $installerZip) {
    Remove-Item -Force $installerZip
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($installerDir, $installerZip)

Write-Host "Created installer bundle at $installerZip" -ForegroundColor Green
Write-Host ""
Write-Host "Installation Instructions:" -ForegroundColor Cyan
Write-Host "1. Extract all files from $installerZip to a folder" -ForegroundColor White
Write-Host "2. Run the Install.bat file" -ForegroundColor White
Write-Host "3. Allow administrative access when prompted" -ForegroundColor White
Write-Host "4. The installer will install the certificate and the application" -ForegroundColor White
Write-Host ""
Write-Host "This installer bundle can be distributed to other users." -ForegroundColor Yellow