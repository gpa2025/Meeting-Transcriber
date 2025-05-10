# PowerShell script to sign the MSIX package with a self-signed certificate
# Author: Gianpaolo Albanese
# Date: 05-10-2024

# Set paths
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = Split-Path -Parent $scriptPath
$msixPath = Join-Path $rootPath "dist\MeetingTranscriber.msix"
$certPath = Join-Path $scriptPath "MeetingTranscriberCert.pfx"
$certPublicPath = Join-Path $scriptPath "MeetingTranscriberCert.cer"

# Certificate password
$password = "MeetingTranscriber2024"
$securePassword = ConvertTo-SecureString -String $password -Force -AsPlainText

# Check if the MSIX package exists
if (-not (Test-Path $msixPath)) {
    Write-Host "Error: MSIX package not found at $msixPath" -ForegroundColor Red
    Write-Host "Please build the MSIX package first using create_msix_package.ps1" -ForegroundColor Red
    exit 1
}

# Create a self-signed certificate if it doesn't exist
if (-not (Test-Path $certPath)) {
    Write-Host "Creating self-signed certificate..." -ForegroundColor Cyan
    
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
    Write-Host "Certificate password: $password" -ForegroundColor Yellow
} else {
    Write-Host "Using existing certificate at $certPath" -ForegroundColor Cyan
}

# Alternative approach using Add-AppxPackage
Write-Host "Signing and installing MSIX package using Add-AppxPackage..." -ForegroundColor Cyan

try {
    # Install the certificate to the trusted root store
    Import-PfxCertificate -FilePath $certPath -CertStoreLocation Cert:\LocalMachine\Root -Password $securePassword | Out-Null
    Write-Host "Certificate installed to trusted root store" -ForegroundColor Green
    
    # Install the package
    Add-AppxPackage -Path $msixPath -Register
    
    Write-Host "MSIX package installed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To distribute this package to other users:" -ForegroundColor Cyan
    Write-Host "1. Include the $certPublicPath file with your distribution" -ForegroundColor White
    Write-Host "2. Instruct users to double-click the certificate file and install it to 'Trusted Root Certification Authorities' store" -ForegroundColor White
    Write-Host "3. After installing the certificate, users can install the MSIX package" -ForegroundColor White
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    
    Write-Host ""
    Write-Host "Alternative installation method:" -ForegroundColor Cyan
    Write-Host "Run the following command as administrator:" -ForegroundColor White
    Write-Host "Add-AppxPackage -Path `"$msixPath`" -AllowUntrusted" -ForegroundColor White
}