@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo Meeting Transcriber Uninstaller
echo ===================================================
echo.
echo This will remove Meeting Transcriber components.
echo.

cd /d "%~dp0"

echo Removing shortcuts...
del "%USERPROFILE%\Desktop\Meeting Transcriber.lnk" 2>nul
del "%USERPROFILE%\Desktop\Meeting Transcriber Async.lnk" 2>nul
del "%USERPROFILE%\OneDrive\Desktop\Meeting Transcriber.lnk" 2>nul
del "%USERPROFILE%\OneDrive\Desktop\Meeting Transcriber Async.lnk" 2>nul
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Meeting Transcriber.lnk" 2>nul
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Meeting Transcriber Async.lnk" 2>nul
del "%PUBLIC%\Desktop\Meeting Transcriber.lnk" 2>nul
del "%ProgramData%\Microsoft\Windows\Start Menu\Programs\Meeting Transcriber.lnk" 2>nul
echo - Shortcuts removed

echo Handling configuration files...
if exist "%APPDATA%\MeetingTranscriber\gui_config.json" (
    set /p save_config="Save settings before removing? (y/n): "
    if /i "!save_config!"=="y" (
        set "backup_dir=%USERPROFILE%\Desktop\MeetingTranscriber_BACKUP"
        mkdir "!backup_dir!" 2>nul
        copy "%APPDATA%\MeetingTranscriber\gui_config.json" "!backup_dir!\gui_config.json" >nul 2>&1
        if exist ".env" copy ".env" "!backup_dir!\.env" >nul 2>&1
        echo - Settings backed up to: !backup_dir!
    )
    del "%APPDATA%\MeetingTranscriber\gui_config.json" 2>nul
    rmdir "%APPDATA%\MeetingTranscriber" 2>nul
    echo - Configuration files removed
)

echo Removing virtual environment...
if exist "venv" (
    rmdir /s /q venv 2>nul
    echo - Virtual environment removed
)

echo Cleaning temporary files...
del *.pyc 2>nul
rmdir /s /q __pycache__ 2>nul
del LaunchApp.bat 2>nul
echo - Temporary files cleaned

echo Handling environment file...
if exist ".env" (
    if not "!save_config!"=="y" (
        set /p remove_env="Remove .env file? (y/n): "
        if /i "!remove_env!"=="y" (
            del ".env" 2>nul
            echo - Environment file removed
        )
    ) else (
        del ".env" 2>nul
        echo - Environment file removed (backup created)
    )
)

echo.
set /p complete_removal="Remove ALL application files? (y/n): "
if /i "!complete_removal!"=="y" (
    echo.
    echo WARNING: This will delete ALL files in this directory!
    set /p confirm="Type YES to confirm complete removal: "
    if /i "!confirm!"=="YES" (
        echo Creating cleanup script...
        set "cleanup=%TEMP%\cleanup_mt_%RANDOM%.bat"
        echo @echo off > "!cleanup!"
        echo ping 127.0.0.1 -n 3 ^> nul >> "!cleanup!"
        echo rmdir /s /q "%~dp0" >> "!cleanup!"
        echo if exist "%~dp0" echo Failed to remove some files. >> "!cleanup!"
        echo ping 127.0.0.1 -n 2 ^> nul >> "!cleanup!"
        echo del "%%~f0" 2^>nul >> "!cleanup!"
        
        start /min "" "!cleanup!"
        echo Cleanup started. Exiting...
        ping 127.0.0.1 -n 2 > nul
        exit /b 0
    )
)

echo.
echo ===================================================
echo Uninstall Complete!
echo ===================================================
echo.
echo Actions performed:
echo - Shortcuts removed
echo - Configuration handled
echo - Virtual environment removed
echo - Temporary files cleaned
echo.
echo Press any key to exit...
pause >nul
exit /b 0