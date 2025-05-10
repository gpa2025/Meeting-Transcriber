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
$launchScript = Join-Path $installerDir "LaunchApp.bat"
$directInstallScript = Join-Path $installerDir "DirectInstall.ps1"

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

# Create a PowerShell installation script (more reliable)
$directInstallScriptContent = @"
# PowerShell script to install Meeting Transcriber
# This script must be run as administrator

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "This script must be run as Administrator. Please restart with elevated privileges." -ForegroundColor Red
    Write-Host "Right-click on the script and select 'Run as Administrator'." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "Meeting Transcriber Installer" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will:" -ForegroundColor White
Write-Host "1. Install the certificate to your trusted root store" -ForegroundColor White
Write-Host "2. Install the Meeting Transcriber application" -ForegroundColor White
Write-Host "3. Create shortcuts for easy access" -ForegroundColor White
Write-Host ""

# Get the current directory
$currentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$certPath = Join-Path $currentDir "MeetingTranscriberCert.cer"
$msixPath = Join-Path $currentDir "MeetingTranscriber.msix"

# Check if files exist
if (-not (Test-Path $certPath)) {
    Write-Host "Error: Certificate not found at $certPath" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

if (-not (Test-Path $msixPath)) {
    Write-Host "Error: MSIX package not found at $msixPath" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

# Install certificate to trusted root store
Write-Host "Installing certificate..." -ForegroundColor Cyan
try {
    Import-Certificate -FilePath $certPath -CertStoreLocation Cert:\LocalMachine\Root | Out-Null
    Write-Host "Certificate installed successfully." -ForegroundColor Green
} catch {
    Write-Host "Error installing certificate: $_" -ForegroundColor Red
    Write-Host "Trying alternative method..." -ForegroundColor Yellow
    
    try {
        certutil -addstore -f "ROOT" $certPath | Out-Null
        Write-Host "Certificate installed successfully using certutil." -ForegroundColor Green
    } catch {
        Write-Host "Failed to install certificate. Error: $_" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit
    }
}

# Wait a moment for certificate to be fully registered
Write-Host "Waiting for certificate to register..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

# Install MSIX package with multiple fallback methods
Write-Host "Installing Meeting Transcriber..." -ForegroundColor Cyan
try {
    Add-AppxPackage -Path $msixPath
    Write-Host "Standard installation successful." -ForegroundColor Green
} catch {
    Write-Host "Standard installation failed, trying with -AllowUntrusted flag..." -ForegroundColor Yellow
    try {
        Add-AppxPackage -Path $msixPath -AllowUntrusted
        Write-Host "Installation with -AllowUntrusted successful." -ForegroundColor Green
    } catch {
        Write-Host "Installation failed with error:" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        
        Write-Host "Trying to register the package directly..." -ForegroundColor Yellow
        try {
            Add-AppxPackage -Register -Path $msixPath -AllowUntrusted
            Write-Host "Direct registration successful." -ForegroundColor Green
        } catch {
            Write-Host "All installation methods failed. Error: $_" -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit
        }
    }
}

# Create desktop shortcut
Write-Host "Creating desktop shortcut..." -ForegroundColor Cyan
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut([System.Environment]::GetFolderPath('Desktop') + '\Meeting Transcriber.lnk')
    $Shortcut.TargetPath = "$env:SystemRoot\explorer.exe"
    $Shortcut.Arguments = "shell:AppsFolder\GPA.MeetingTranscriber_1.0.0.0_x64__1234567890abc"
    $Shortcut.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,77"
    $Shortcut.Save()
    Write-Host "Desktop shortcut created successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to create desktop shortcut: $_" -ForegroundColor Yellow
    Write-Host "You can still launch the app from the Start menu or using LaunchApp.bat" -ForegroundColor Yellow
}

# Create Start Menu shortcut
Write-Host "Creating Start Menu shortcut..." -ForegroundColor Cyan
try {
    $appData = [Environment]::GetFolderPath('ApplicationData')
    $startMenu = Join-Path $appData 'Microsoft\Windows\Start Menu\Programs'
    $shortcutPath = Join-Path $startMenu 'Meeting Transcriber.lnk'
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($shortcutPath)
    $Shortcut.TargetPath = "$env:SystemRoot\explorer.exe"
    $Shortcut.Arguments = "shell:AppsFolder\GPA.MeetingTranscriber_1.0.0.0_x64__1234567890abc"
    $Shortcut.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,77"
    $Shortcut.Save()
    Write-Host "Start Menu shortcut created successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to create Start Menu shortcut: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "You can now find Meeting Transcriber:" -ForegroundColor White
Write-Host "1. On your desktop (shortcut created)" -ForegroundColor White
Write-Host "2. In the Start menu (shortcut created)" -ForegroundColor White
Write-Host "3. By using the LaunchApp.bat file included in this folder" -ForegroundColor White
Write-Host ""
Write-Host "If you cannot find the application, try restarting your computer." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"
"@

Set-Content -Path $directInstallScript -Value $directInstallScriptContent
Write-Host "Created PowerShell installation script" -ForegroundColor Green

# Create a simple batch file to launch the PowerShell script with admin rights
$installBatchContent = @"
@echo off
echo ===================================================
echo Meeting Transcriber Installer
echo ===================================================
echo.
echo This script will launch the PowerShell installer with administrator privileges.
echo.
echo Please allow administrative access when prompted.
echo.
pause

powershell -ExecutionPolicy Bypass -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File ""DirectInstall.ps1""' -Verb RunAs"

echo.
echo If the installer window doesn't appear, please run DirectInstall.ps1 as administrator manually.
echo.
pause
"@

Set-Content -Path $installerScript -Value $installBatchContent
Write-Host "Created batch launcher for PowerShell installer" -ForegroundColor Green

# Create a direct launch script
$launchBatchContent = @"
@echo off
echo Launching Meeting Transcriber...
explorer.exe shell:AppsFolder\GPA.MeetingTranscriber_1.0.0.0_x64__1234567890abc
"@

Set-Content -Path $launchScript -Value $launchBatchContent
Write-Host "Created direct launch script" -ForegroundColor Green

# Create a README file with detailed instructions
$readmeContent = @"
# Meeting Transcriber Installer

## Installation Instructions

1. Extract all files from this ZIP archive to a folder
2. Right-click on Install.bat and select "Run as administrator"
3. Follow the on-screen instructions
4. The installer will:
   - Install the certificate to your trusted root store
   - Install the Meeting Transcriber application
   - Create shortcuts for easy access

## Alternative Installation Method

If the standard installer doesn't work:
1. Right-click on DirectInstall.ps1
2. Select "Run with PowerShell" or "Run as administrator"
3. Follow the on-screen instructions

## Launching the Application

After installation, you can launch Meeting Transcriber in several ways:

1. From the desktop shortcut
2. From the Start menu (search for "Meeting Transcriber")
3. Using the included LaunchApp.bat file

If you cannot find the application in the Start menu:
- Use the desktop shortcut or LaunchApp.bat file
- Try restarting your computer to refresh the Start menu
- Search specifically for "Meeting" or "Transcriber"

## Troubleshooting

If you encounter installation issues:

1. Make sure you're running the installer as administrator
2. Try enabling Developer Mode:
   - Go to Settings > Update & Security > For developers
   - Turn on "Developer Mode"
3. Try the alternative installation method (DirectInstall.ps1)
4. Check Windows Event Viewer for more detailed error messages
5. Try restarting your computer after installation

## System Requirements

- Windows 10 or Windows 11
- Internet connection for AWS services

## Support

For support, please contact: albaneg@yahoo.com
"@

Set-Content -Path (Join-Path $installerDir "README.txt") -Value $readmeContent
Write-Host "Created README file with detailed instructions" -ForegroundColor Green

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
Write-Host "2. Right-click on Install.bat and select 'Run as administrator'" -ForegroundColor White
Write-Host "3. Follow the on-screen instructions" -ForegroundColor White
Write-Host ""
Write-Host "The installer now includes:" -ForegroundColor Yellow
Write-Host "- A more reliable PowerShell installation script" -ForegroundColor White
Write-Host "- Multiple installation methods" -ForegroundColor White
Write-Host "- Better error handling and feedback" -ForegroundColor White
Write-Host "- Desktop and Start menu shortcuts" -ForegroundColor White