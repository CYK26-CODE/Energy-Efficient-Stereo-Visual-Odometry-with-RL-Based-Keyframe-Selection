@echo off
REM ========================================
REM SLAM System .exe Builder
REM Creates standalone executable
REM ========================================

echo.
echo ========================================
echo    SLAM System EXE Builder
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [1/3] Installing PyInstaller...
    pip install pyinstaller
) else (
    echo [1/3] PyInstaller already installed
)

echo.
echo [2/3] Building executable...
echo This may take 2-5 minutes...
echo.

REM Build using spec file
pyinstaller --clean slam_system.spec

if errorlevel 1 (
    echo.
    echo ❌ Build FAILED!
    echo Check errors above.
    pause
    exit /b 1
)

echo.
echo [3/3] Build successful!
echo.
echo ========================================
echo ✓ Executable created:
echo   dist\SLAM_System.exe
echo.
echo File size: 
for %%A in (dist\SLAM_System.exe) do echo   %%~zA bytes
echo ========================================
echo.
echo You can now run: dist\SLAM_System.exe
echo.
pause
