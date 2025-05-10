@echo off
echo Creating Meeting Transcriber Installer...

:: Check if Inno Setup is installed
set "INNO_COMPILER=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%INNO_COMPILER%" (
    echo Inno Setup not found at %INNO_COMPILER%
    echo Please download and install Inno Setup from https://jrsoftware.org/isdl.php
    echo After installation, run this script again.
    pause
    exit /b 1
)

:: Copy the executable if it doesn't exist in the dist folder
if not exist "..\dist\MeetingTranscriber.exe" (
    echo Executable not found. Please build the executable first using build_exe.py
    pause
    exit /b 1
)

:: Run Inno Setup compiler
echo Running Inno Setup compiler...
"%INNO_COMPILER%" MeetingTranscriberSetup.iss

:: Check if compilation was successful
if %ERRORLEVEL% neq 0 (
    echo Error: Inno Setup compilation failed.
    pause
    exit /b 1
)

echo.
echo Installer created successfully!
echo The installer is located at: %CD%\MeetingTranscriberSetup.exe
echo.

pause