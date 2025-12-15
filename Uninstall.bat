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

REM ===== HANDLE CONFIGURATION FILES =====
echo Checking for configuration files...
if exist "%APPDATA%\MeetingTranscriber\gui_config.json" (
    echo Configuration file found.
    set /p save_config="Do you want to save your settings before uninstalling? (y/n): "
    if /i "!save_config!"=="y" (
        echo Creating settings backup folder on Desktop...
        set "backup_folder=%USERPROFILE%\Desktop\MeetingTranscriber_BACKUP"
        
        REM Create backup folder
        if not exist "!backup_folder!" (
            mkdir "!backup_folder!" 2>nul
            if !errorlevel! equ 0 (
                echo Backup folder created: !backup_folder!
            ) else (
                echo Failed to create backup folder
                goto skip_backup
            )
        )
        
        REM Copy gui_config.json
        copy "%APPDATA%\MeetingTranscriber\gui_config.json" "!backup_folder!\gui_config.json" >nul 2>&1
        if !errorlevel! equ 0 (
            echo GUI settings backed up to: !backup_folder!\gui_config.json
        ) else (
            echo Failed to backup GUI settings
        )
        
        REM Copy .env file if it exists
        if exist ".env" (
            copy ".env" "!backup_folder!\.env" >nul 2>&1
            if !errorlevel! equ 0 (
                echo Environment file backed up to: !backup_folder!\.env
            ) else (
                echo Failed to backup .env file
            )
        ) else (
            echo .env file not found in current directory
        )
        
        echo.
        echo Settings backup folder created at: !backup_folder!
        echo This folder contains your configuration files for future use.
        
        :skip_backup
    )
    
    echo Removing configuration files...
    del "%APPDATA%\MeetingTranscriber\gui_config.json" 2>nul
    if !errorlevel! equ 0 (
        echo Configuration file removed.
    ) else (
        echo Failed to remove configuration file - permission denied.
    )
) else (
    echo No configuration file found.
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

REM Handle .env file (only if not already backed up)
if exist ".env" (
    if not "!save_config!"=="y" (
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
    ) else (
        REM Remove .env file since it was backed up
        del ".env" 2>nul
        if !errorlevel! equ 0 (
            echo .env file removed (backup created).
        ) else (
            echo Failed to remove .env file - permission denied.
        )
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

REM Create temporary file for found shortcuts
echo. > found_shortcuts.txt

REM Use PowerShell to find shortcuts more reliably
powershell -Command "Get-ChildItem -Path '%USERPROFILE%\Desktop' -Filter 'Meeting Transcriber.lnk' -Recurse -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }" >> found_shortcuts.txt 2>nul
powershell -Command "Get-ChildItem -Path '%PUBLIC%\Desktop' -Filter 'Meeting Transcriber.lnk' -Recurse -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }" >> found_shortcuts.txt 2>nul
powershell -Command "Get-ChildItem -Path '%APPDATA%\Microsoft\Windows\Start Menu' -Filter 'Meeting Transcriber.lnk' -Recurse -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }" >> found_shortcuts.txt 2>nul
powershell -Command "Get-ChildItem -Path '%ProgramData%\Microsoft\Windows\Start Menu' -Filter 'Meeting Transcriber.lnk' -Recurse -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }" >> found_shortcuts.txt 2>nul

REM Check if any shortcuts were found and remove them
set "shortcuts_exist=false"
for /f "usebackq tokens=*" %%a in ("found_shortcuts.txt") do (
    if not "%%a"=="" (
        if exist "%%a" (
            echo Found remaining shortcut: %%a
            del "%%a" 2>nul
            if !errorlevel! equ 0 (
                echo Successfully removed: %%a
            ) else (
                echo Failed to remove: %%a
                set "shortcuts_exist=true"
            )
        )
    )
)

REM Delete the temporary file
if exist found_shortcuts.txt del found_shortcuts.txt 2>nul

if "!shortcuts_exist!"=="true" (
    echo WARNING: Some shortcuts could not be removed automatically.
    echo You may need to manually delete them after the uninstall completes.
) else (
    echo All shortcuts search completed.
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
        
        REM Get the current directory path
        set "current_dir=%~dp0"
        
        REM Create a temporary batch file to delete everything including itself
        echo @echo off > "%TEMP%\cleanup_meeting_transcriber.bat"
        echo echo Waiting for uninstaller to close... >> "%TEMP%\cleanup_meeting_transcriber.bat"
        echo timeout /t 3 /nobreak ^> nul >> "%TEMP%\cleanup_meeting_transcriber.bat"
        echo echo Removing Meeting Transcriber directory... >> "%TEMP%\cleanup_meeting_transcriber.bat"
        echo rmdir /s /q "!current_dir!" >> "%TEMP%\cleanup_meeting_transcriber.bat"
        echo if exist "!current_dir!" ^( >> "%TEMP%\cleanup_meeting_transcriber.bat"
        echo     echo Some files could not be deleted. Please delete manually: >> "%TEMP%\cleanup_meeting_transcriber.bat"
        echo     echo !current_dir! >> "%TEMP%\cleanup_meeting_transcriber.bat"
        echo     pause >> "%TEMP%\cleanup_meeting_transcriber.bat"
        echo ^) else ^( >> "%TEMP%\cleanup_meeting_transcriber.bat"
        echo     echo Meeting Transcriber completely removed. >> "%TEMP%\cleanup_meeting_transcriber.bat"
        echo ^) >> "%TEMP%\cleanup_meeting_transcriber.bat"
        echo del "%%~f0" >> "%TEMP%\cleanup_meeting_transcriber.bat"
        
        echo Starting cleanup process in 3 seconds...
        echo You can close this window now.
        start "" "%TEMP%\cleanup_meeting_transcriber.bat"
        timeout /t 2 /nobreak > nul
        exit /b 0
    ) else (
        echo Complete removal canceled.
    )
)

echo.
echo ===================================================
echo Uninstall Process Complete!
echo ===================================================
echo.
echo Summary of actions performed:
echo - Shortcuts removed from Desktop and Start Menu
echo - Configuration files handled
echo - Virtual environment removed
echo - Temporary files cleaned up
echo.
echo If you want to completely remove the application folder,
echo you can delete this folder manually or run the uninstaller again
echo and choose "yes" when asked about complete removal.
echo.
echo The uninstaller will close automatically in 10 seconds...
echo Press any key to close immediately.
echo.
timeout /t 10 /nobreak > nul
echo Uninstaller finished.