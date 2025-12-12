@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo Meeting Transcriber Uninstaller
echo ===================================================
echo.
echo This script will:
echo 1. Remove desktop and Start Menu shortcuts
echo 2. Remove configuration files
echo 3. Remove the virtual environment
echo 4. Optionally remove all application files
echo 5. A REBOOT IS RECOMMENDED TO DELETE ANY LINGERING FILES!
echo.
echo Please wait while the uninstall completes...
echo.

REM Set the current directory to the script's directory
cd /d "%~dp0"

REM ===== REMOVE SHORTCUTS (DIRECT METHOD) =====
echo Removing shortcuts (direct method)...

REM Try to remove desktop shortcut from all possible locations
echo Removing desktop shortcuts...

REM Standard user desktop
if exist "%USERPROFILE%\Desktop\Meeting Transcriber.lnk" (
    del "%USERPROFILE%\Desktop\Meeting Transcriber.lnk"
    echo Removed: %USERPROFILE%\Desktop\Meeting Transcriber.lnk
)

REM OneDrive desktop
if exist "%USERPROFILE%\OneDrive\Desktop\Meeting Transcriber.lnk" (
    del "%USERPROFILE%\OneDrive\Desktop\Meeting Transcriber.lnk"
    echo Removed: %USERPROFILE%\OneDrive\Desktop\Meeting Transcriber.lnk
)

REM Public desktop
if exist "%PUBLIC%\Desktop\Meeting Transcriber.lnk" (
    del "%PUBLIC%\Desktop\Meeting Transcriber.lnk"
    echo Removed: %PUBLIC%\Desktop\Meeting Transcriber.lnk
)

REM Try to remove Start Menu shortcuts from all possible locations
echo Removing Start Menu shortcuts...

REM User's Start Menu
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Meeting Transcriber.lnk" (
    del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Meeting Transcriber.lnk"
    echo Removed: %APPDATA%\Microsoft\Windows\Start Menu\Programs\Meeting Transcriber.lnk
)

REM All Users Start Menu
if exist "%ProgramData%\Microsoft\Windows\Start Menu\Programs\Meeting Transcriber.lnk" (
    del "%ProgramData%\Microsoft\Windows\Start Menu\Programs\Meeting Transcriber.lnk"
    echo Removed: %ProgramData%\Microsoft\Windows\Start Menu\Programs\Meeting Transcriber.lnk
)

REM ===== REMOVE SHORTCUTS USING POWERSHELL (BACKUP METHOD) =====
echo Using PowerShell as backup method...

REM Remove desktop shortcut using PowerShell
powershell -Command "Get-ChildItem -Path ([Environment]::GetFolderPath('Desktop')) -Filter 'Meeting Transcriber.lnk' -ErrorAction SilentlyContinue | Remove-Item -Force"
powershell -Command "Get-ChildItem -Path ([Environment]::GetFolderPath('CommonDesktopDirectory')) -Filter 'Meeting Transcriber.lnk' -ErrorAction SilentlyContinue | Remove-Item -Force"

REM Remove Start Menu shortcut using PowerShell
powershell -Command "Get-ChildItem -Path (Join-Path ([Environment]::GetFolderPath('ApplicationData')) 'Microsoft\Windows\Start Menu\Programs') -Filter 'Meeting Transcriber.lnk' -ErrorAction SilentlyContinue | Remove-Item -Force"
powershell -Command "Get-ChildItem -Path (Join-Path ([Environment]::GetFolderPath('CommonPrograms')) '') -Filter 'Meeting Transcriber.lnk' -ErrorAction SilentlyContinue | Remove-Item -Force"

REM ===== REMOVE CONFIGURATION FILES =====
echo Removing configuration files...
if exist "%APPDATA%\MeetingTranscriber\gui_config.json" (
    del "%APPDATA%\MeetingTranscriber\gui_config.json" 2>nul
    if !errorlevel! equ 0 (
        echo Configuration file removed.
    ) else (
        echo Failed to remove configuration file - permission denied.
    )
) else (
    echo Configuration file not found.
)

REM Try to remove the config directory
if exist "%APPDATA%\MeetingTranscriber" (
    rmdir "%APPDATA%\MeetingTranscriber" 2>nul
    if !errorlevel! equ 0 (
        echo Configuration directory removed.
    ) else (
        echo Failed to remove configuration directory - it may not be empty or you don't have permission.
    )
)

REM ===== REMOVE VIRTUAL ENVIRONMENT =====
if exist "venv" (
    echo Removing Python virtual environment...
    rmdir /s /q venv
    echo Virtual environment removed.
) else (
    echo Virtual environment not found.
)

REM ===== CLEAN UP TEMPORARY FILES =====
echo Cleaning up temporary files...
if exist "*.pyc" del *.pyc
if exist "__pycache__" rmdir /s /q __pycache__

REM Handle .env file
if exist ".env" (
    set /p remove_env="Do you want to remove the .env file with your AWS credentials? (y/n): "
    if /i "!remove_env!"=="y" (
        del ".env" 2>nul
        if !errorlevel! equ 0 (
            echo .env file removed.
        ) else (
            echo Failed to remove .env file - permission denied.
        )
    ) else (
        echo .env file kept.
    )
)

REM ===== REMOVE LAUNCHER =====
if exist "LaunchApp.bat" (
    echo Removing launcher script...
    del "LaunchApp.bat" 2>nul
    if !errorlevel! equ 0 (
        echo Launcher script removed.
    ) else (
        echo Failed to remove launcher script - permission denied.
    )
) else (
    echo Launcher script not found.
)

REM ===== DEEP SEARCH FOR SHORTCUTS =====
echo.
echo Performing deep search for any remaining shortcuts...

REM Use where command to find any remaining shortcuts in Desktop folders
where /r "%USERPROFILE%\Desktop" "Meeting Transcriber.lnk" 2>nul > found_shortcuts.txt
where /r "%PUBLIC%\Desktop" "Meeting Transcriber.lnk" 2>nul >> found_shortcuts.txt

REM Use where command to find any remaining shortcuts in Start Menu folders
where /r "%APPDATA%\Microsoft\Windows\Start Menu" "Meeting Transcriber.lnk" 2>nul >> found_shortcuts.txt
where /r "%ProgramData%\Microsoft\Windows\Start Menu" "Meeting Transcriber.lnk" 2>nul >> found_shortcuts.txt

REM Check if any shortcuts were found
set "shortcuts_exist=false"
for /f "tokens=*" %%a in (found_shortcuts.txt) do (
    echo Found remaining shortcut: %%a
    del "%%a" 2>nul
    if !errorlevel! equ 0 (
        echo Successfully removed: %%a
    ) else (
        echo Failed to remove: %%a
        set "shortcuts_exist=true"
    )
)

REM Delete the temporary file
del found_shortcuts.txt 2>nul

if "%shortcuts_exist%"=="true" (
    echo WARNING: Some shortcuts could not be removed automatically.
    echo You may need to manually delete them after the uninstall completes.
) else (
    echo All shortcuts were successfully removed.
)

REM ===== ASK ABOUT COMPLETE REMOVAL =====
echo.
set /p complete_removal="Do you want to completely remove all application files? (y/n): "
if /i "!complete_removal!"=="y" (
    echo.
    echo This will delete ALL files in the current directory.
    echo The uninstaller itself will be deleted.
    echo.
    set /p confirm_removal="Are you sure? This cannot be undone. (y/n): "
    if /i "!confirm_removal!"=="y" (
        echo Creating cleanup script...
        
        REM Create a temporary batch file to delete everything including itself
        echo @echo off > cleanup_temp.bat
        echo timeout /t 1 /nobreak > nul >> cleanup_temp.bat
        echo rmdir /s /q "%~dp0" >> cleanup_temp.bat
        
        echo Starting cleanup process...
        start "" "cleanup_temp.bat"
        exit
    ) else (
        echo Complete removal canceled.
    )
)

echo.
echo Uninstall complete!
echo If you want to completely remove the application, you can delete this folder manually.
echo.
pause