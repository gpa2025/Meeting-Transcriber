# PowerShell script to create an optimized Python-based launcher
# Author: Gianpaolo Albanese
# Date: 05-10-2024

# Set paths
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = Split-Path -Parent $scriptPath
$outputDir = Join-Path $rootPath "dist"
$installerDir = Join-Path $outputDir "MeetingTranscriberPython"
$installerZip = Join-Path $outputDir "MeetingTranscriberPython.zip"
$launchScript = Join-Path $installerDir "LaunchApp.bat"

# Create installer directory
if (Test-Path $installerDir) {
    Remove-Item -Recurse -Force $installerDir
}
New-Item -ItemType Directory -Force -Path $installerDir | Out-Null
Write-Host "Created installer directory at $installerDir" -ForegroundColor Green

# Essential Python files - only include what's needed
$pythonFiles = @(
    "meeting_transcriber_gui.py",
    "aws_transcribe.py",
    "format_meeting_notes.py",
    "summarizer_bedrock.py",
    "utils.py",
    "requirements.txt",
    ".env.example",
    "icon.ico"
)

foreach ($file in $pythonFiles) {
    $filePath = Join-Path $rootPath $file
    if (Test-Path $filePath) {
        Copy-Item $filePath -Destination $installerDir
        Write-Host "Copied $file to installer directory" -ForegroundColor Green
    } else {
        Write-Host "Warning: $file not found, skipping" -ForegroundColor Yellow
    }
}

# Create splash_screen.py file
$splashScreenContent = @"
"""
Splash Screen for Meeting Transcriber

This module provides a splash screen for the Meeting Transcriber application.

Author: Gianpaolo Albanese
Date: 05-10-2024
"""

from PyQt5.QtWidgets import QSplashScreen
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
import os

class SplashScreen(QSplashScreen):
    def __init__(self):
        # Try to load splash screen image from assets directory
        splash_image_path = os.path.join('assets', 'SplashScreen.png')
        
        if os.path.exists(splash_image_path):
            # Use the provided splash screen image
            pixmap = QPixmap(splash_image_path)
        else:
            # Create a basic splash screen with text
            pixmap = QPixmap(400, 200)
            pixmap.fill(Qt.white)
            
        super(SplashScreen, self).__init__(pixmap)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setEnabled(False)
        
        # Add text to the splash screen if we're using the default
        if not os.path.exists(splash_image_path):
            self.showMessage("Loading Meeting Transcriber...", 
                            Qt.AlignCenter | Qt.AlignBottom, 
                            Qt.black)
        
    def show_and_finish(self, main_window, duration=2000):
        """Show the splash screen and close it after duration milliseconds"""
        self.show()
        QTimer.singleShot(duration, lambda: self.finish(main_window))
"@

$splashScreenPath = Join-Path $installerDir "splash_screen.py"
Set-Content -Path $splashScreenPath -Value $splashScreenContent
Write-Host "Created splash_screen.py file" -ForegroundColor Green

# Create main.py file that shows splash screen before launching the GUI
$mainPyContent = @"
"""
Main entry point for Meeting Transcriber

This script shows a splash screen and then launches the Meeting Transcriber GUI.

Author: Gianpaolo Albanese
Date: 05-10-2024
"""

import sys
import time
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from splash_screen import SplashScreen
from meeting_transcriber_gui import MeetingTranscriberGUI

def main():
    # Create application
    app = QApplication(sys.argv)
    
    # Show splash screen
    splash = SplashScreen()
    splash.show()
    
    # Process events to make sure splash screen is displayed
    app.processEvents()
    
    try:
        print("Creating main window...")
        main_window = MeetingTranscriberGUI()
        print("Main window created successfully")
        
        # Show splash screen for 2 seconds, then show main window
        print("Configuring splash screen to finish...")
        splash.show_and_finish(main_window, 2000)
        print("Splash configured to finish")
        
        # Explicitly show and raise the main window
        print("Explicitly showing main window...")
        main_window.show()
        main_window.raise_()
        main_window.activateWindow()
        print("Main window should now be visible")
        
    except Exception as e:
        print(f"ERROR: Failed to create or show main window: {e}")
        traceback.print_exc()
        QMessageBox.critical(None, "Error", f"Application failed to start: {str(e)}\n\nSee console for details.")
        return 1
    
    # Start the application
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
"@

$mainPyPath = Join-Path $installerDir "main.py"
Set-Content -Path $mainPyPath -Value $mainPyContent
Write-Host "Created main.py file with splash screen integration" -ForegroundColor Green

# Copy SplashScreen.png from installer\Assets folder
$installerAssetsPath = Join-Path $scriptPath "Assets"
$splashImagePath = Join-Path $installerAssetsPath "SplashScreen.png"

if (Test-Path $splashImagePath) {
    # Create assets directory in the installer directory
    $installerAssetsDir = Join-Path $installerDir "assets"
    if (-not (Test-Path $installerAssetsDir)) {
        New-Item -ItemType Directory -Force -Path $installerAssetsDir | Out-Null
        Write-Host "Created assets directory in installer" -ForegroundColor Green
    }
    
    # Copy the splash screen image
    Copy-Item $splashImagePath -Destination $installerAssetsDir
    Write-Host "Copied SplashScreen.png from installer\Assets to installer\assets directory" -ForegroundColor Green
} else {
    Write-Host "Warning: SplashScreen.png not found in installer\Assets folder, skipping" -ForegroundColor Yellow
}

# Update requirements.txt to include nltk and remove pyinstaller
$requirementsPath = Join-Path $installerDir "requirements.txt"
if (Test-Path $requirementsPath) {
    $requirements = Get-Content $requirementsPath
    $updatedRequirements = $requirements | Where-Object { $_ -notmatch "pyinstaller" }
    if ($updatedRequirements -notmatch "nltk") {
        $updatedRequirements += "nltk>=3.8.1"
    }
    Set-Content -Path $requirementsPath -Value $updatedRequirements
    Write-Host "Updated requirements.txt to include nltk and remove pyinstaller" -ForegroundColor Green
}

# Create a setup script with VBScript for creating shortcuts
$setupScript = Join-Path $installerDir "Setup.bat"
$setupBatchContent = @"
@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo Meeting Transcriber Setup
echo ===================================================
echo.
echo This script will:
echo 1. Check if Python is installed
echo 2. Create a virtual environment and install required packages
echo 3. Download NLTK data
echo 4. Create desktop and Start menu shortcuts
echo.
echo Please wait while the setup completes...
echo.

REM Set the current directory to the script's directory
cd /d "%~dp0"

REM Check if Python is installed
echo Checking Python installation...
python --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.7 or higher from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Check if requirements.txt exists
if not exist requirements.txt (
    echo Error: requirements.txt not found in the current directory.
    echo Current directory: %CD%
    echo Files in current directory:
    dir
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating Python virtual environment...
if exist venv (
    echo Virtual environment already exists. Removing old one...
    rmdir /s /q venv
)

echo Creating new virtual environment...
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo Failed to create virtual environment.
    echo Trying alternative method...
    python -m pip install --user virtualenv
    python -m virtualenv venv
    
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment.
        echo Please make sure you have the venv module installed.
        pause
        exit /b 1
    )
)

REM Activate virtual environment and install packages
echo Activating virtual environment and installing packages...
call venv\Scripts\activate.bat

echo Installing required packages...
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Some packages may not have installed correctly.
    echo The application might not work properly.
    pause
)

REM Download NLTK data
echo Downloading NLTK data...
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

REM Create .env file from example if it doesn't exist
if not exist .env (
    if exist .env.example (
        echo Creating .env file from .env.example...
        copy .env.example .env
    )
)

REM Update LaunchApp.bat to use virtual environment
echo Creating LaunchApp.bat...
echo @echo off > LaunchApp.bat
echo echo Launching Meeting Transcriber... >> LaunchApp.bat
echo cd /d "%%~dp0" >> LaunchApp.bat
echo call venv\Scripts\activate.bat >> LaunchApp.bat
echo python main.py >> LaunchApp.bat
echo call venv\Scripts\deactivate.bat >> LaunchApp.bat

REM Create desktop shortcut using a direct method
echo Creating desktop shortcut...
echo Set oWS = CreateObject("WScript.Shell") > CreateShortcut.vbs
echo Set oFSO = CreateObject("Scripting.FileSystemObject") >> CreateShortcut.vbs
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\Meeting Transcriber.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%~dp0LaunchApp.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%~dp0" >> CreateShortcut.vbs
echo If oFSO.FileExists("%~dp0icon.ico") Then oLink.IconLocation = "%~dp0icon.ico" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript //nologo CreateShortcut.vbs
del CreateShortcut.vbs

REM Create Start Menu shortcut using a direct method
echo Creating Start Menu shortcut...
echo Set oWS = CreateObject("WScript.Shell") > CreateShortcut.vbs
echo Set oFSO = CreateObject("Scripting.FileSystemObject") >> CreateShortcut.vbs
echo sLinkFile = oWS.SpecialFolders("Programs") ^& "\Meeting Transcriber.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%~dp0LaunchApp.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%~dp0" >> CreateShortcut.vbs
echo If oFSO.FileExists("%~dp0icon.ico") Then oLink.IconLocation = "%~dp0icon.ico" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript //nologo CreateShortcut.vbs
del CreateShortcut.vbs

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

echo.
echo Setup complete!
echo You can now run the application using LaunchApp.bat
echo or by using the desktop/Start menu shortcuts.
echo.
pause
"@

Set-Content -Path $setupScript -Value $setupBatchContent
Write-Host "Created setup script with VBScript for creating shortcuts" -ForegroundColor Green

# Create a launch script that runs main.py (which shows splash screen)
$launchBatchContent = @"
@echo off
echo Launching Meeting Transcriber...
cd /d "%~dp0"
python main.py
"@

Set-Content -Path $launchScript -Value $launchBatchContent
Write-Host "Created launch script to run main.py with splash screen" -ForegroundColor Green

# Copy the Uninstall.bat file
$uninstallSourcePath = Join-Path $rootPath "Uninstall.bat"
$uninstallDestPath = Join-Path $installerDir "Uninstall.bat"
if (Test-Path $uninstallSourcePath) {
    Copy-Item $uninstallSourcePath -Destination $uninstallDestPath
    Write-Host "Copied Uninstall.bat to installer directory" -ForegroundColor Green
} else {
    Write-Host "Warning: Uninstall.bat not found at $uninstallSourcePath, skipping" -ForegroundColor Yellow
}

# Create a README file - simplified and focused
$readmeContent = @"
# Meeting Transcriber

A tool for transcribing meeting audio and generating detailed meeting notes using AWS services.

## Installation Instructions

1. Extract all files from this ZIP archive to a folder
2. Run Setup.bat to install required Python packages and create shortcuts

## Requirements

- Python 3.7 or higher
- Internet connection for AWS services
- AWS credentials with appropriate permissions

## First-time Setup

1. Run Setup.bat to:
   - Install required Python packages
   - Download NLTK data
   - Create desktop and Start menu shortcuts
   - Create a .env file from .env.example
2. Edit the .env file to add your AWS credentials:
   - AWS_ACCESS_KEY_ID=your_access_key
   - AWS_SECRET_ACCESS_KEY=your_secret_key
   - AWS_REGION=your_region (e.g., us-east-1)
   - S3_BUCKET=your_bucket_name
3. Run LaunchApp.bat to start the application

## Launching the Application

You can launch Meeting Transcriber in several ways:
- Run LaunchApp.bat directly
- Use the desktop shortcut (created by Setup.bat)
- Use the Start menu shortcut (created by Setup.bat)

## Troubleshooting

If you encounter issues with the Setup.bat script:
- Make sure Python is installed and added to your PATH
- Try running the commands manually:
  ```
  cd /path/to/extracted/folder
  python -m pip install -r requirements.txt
  python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
  ```
- If you see errors related to NLTK, try running:
  ```
  python -m nltk.downloader punkt stopwords
  ```

## Support

For support, please contact: albaneg@yahoo.com
"@

Set-Content -Path (Join-Path $installerDir "README.txt") -Value $readmeContent
Write-Host "Created README file with updated instructions" -ForegroundColor Green

# Create ZIP archive
if (Test-Path $installerZip) {
    Remove-Item -Force $installerZip
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($installerDir, $installerZip)

Write-Host "Created optimized Python launcher bundle at $installerZip" -ForegroundColor Green
Write-Host ""
Write-Host "Installation Instructions:" -ForegroundColor Cyan
Write-Host "1. Extract all files from $installerZip to a folder" -ForegroundColor White
Write-Host "2. Run Setup.bat to install required Python packages and create shortcuts" -ForegroundColor White
Write-Host ""
Write-Host "This optimized launcher contains only essential files and includes splash screen integration." -ForegroundColor Yellow