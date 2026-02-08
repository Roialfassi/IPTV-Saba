@echo off
REM Build script for IPTV-Saba
REM This script builds the application into a standalone EXE

echo ========================================
echo    IPTV-Saba Build Script
echo ========================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found. Using system Python.
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

echo.
echo Building IPTV-Saba...
echo.

REM Clean previous builds
if exist "dist" (
    echo Cleaning previous dist folder...
    rmdir /s /q dist
)
if exist "build" (
    echo Cleaning previous build folder...
    rmdir /s /q build
)

REM Run PyInstaller
pyinstaller iptv_saba.spec --noconfirm

if errorlevel 1 (
    echo.
    echo ========================================
    echo    BUILD FAILED!
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo    BUILD SUCCESSFUL!
echo ========================================
echo.
echo The executable is located at:
echo   dist\IPTV-Saba.exe
echo.
echo IMPORTANT: Users must have VLC Media Player installed!
echo   Download from: https://www.videolan.org/vlc/
echo.
pause
