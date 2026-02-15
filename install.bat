@echo off
:: Self-elevate to admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

setlocal

set PLUGIN_NAME=com.streamdeckscripts.sdPlugin
set SOURCE=%~dp0%PLUGIN_NAME%
set SCRIPTS_SOURCE=%~dp0scripts
set DEST=%APPDATA%\Elgato\StreamDeck\Plugins\%PLUGIN_NAME%
set SCRIPTS_DEST=%APPDATA%\Elgato\StreamDeck\Plugins\scripts

echo === Stream Deck Utils - Install ===
echo.

:: Check source exists
if not exist "%SOURCE%" (
    echo ERROR: Plugin folder not found at %SOURCE%
    pause
    exit /b 1
)

:: Kill Stream Deck
echo Stopping Stream Deck...
taskkill /F /IM StreamDeck.exe >nul 2>&1
timeout /t 2 /noq >nul

:: Remove old install
if exist "%DEST%" (
    echo Removing previous install...
    rmdir /s /q "%DEST%"
)

:: Copy plugin
echo Copying plugin to %DEST%...
xcopy /E /I /Q "%SOURCE%" "%DEST%" >nul

:: Copy scripts folder alongside plugin
echo Copying scripts to %SCRIPTS_DEST%...
if exist "%SCRIPTS_DEST%" rmdir /s /q "%SCRIPTS_DEST%"
xcopy /E /I /Q "%SCRIPTS_SOURCE%" "%SCRIPTS_DEST%" >nul

:: Install Python dependencies
echo Installing Python dependencies...
pip install -q -r "%DEST%\requirements.txt" 2>&1

echo.
echo Done! Restarting Stream Deck...
start "" "%ProgramFiles%\Elgato\StreamDeck\StreamDeck.exe"

echo.
echo Look for "Utilities" in the Stream Deck action list.
echo.
pause
