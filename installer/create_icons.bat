@echo off
echo Creating icons for MSIX package...
echo.

:: Check if PowerShell is available
where powershell >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: PowerShell is required but not found.
    echo Please install PowerShell and try again.
    exit /b 1
)

:: Run the PowerShell script with execution policy bypass
powershell -ExecutionPolicy Bypass -File "%~dp0create_icons.ps1"

echo.
echo Done!