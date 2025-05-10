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
