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
