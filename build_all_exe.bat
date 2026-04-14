@echo off
REM ========================================
REM Build All SLAM Executables
REM Creates 3 separate .exe files
REM ========================================

echo.
echo ========================================
echo    SLAM PROJECT - BUILD ALL EXE FILES
echo ========================================
echo.
echo This will create 3 executable files:
echo   1. SLAM_Complete_System.exe  - Full SLAM + RL + GUI
echo   2. SLAM_Basic.exe             - Basic SLAM with 2D overlay
echo   3. SLAM_RL_Trainer.exe        - RL Agent training tool
echo.
echo ========================================
echo.

REM Check PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [SETUP] Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo ❌ Failed to install PyInstaller
        pause
        exit /b 1
    )
) else (
    echo [SETUP] PyInstaller already installed
)

echo.
echo ========================================
echo Building Executables...
echo This will take 5-10 minutes
echo ========================================
echo.

REM Build 1: Complete SLAM System
echo.
echo [1/3] Building Complete SLAM System...
echo ----------------------------------------
pyinstaller --clean complete_slam.spec
if errorlevel 1 (
    echo ❌ Failed to build Complete SLAM System
    pause
    exit /b 1
)
echo ✓ SLAM_Complete_System.exe created

REM Build 2: Basic SLAM
echo.
echo [2/3] Building Basic SLAM...
echo ----------------------------------------
pyinstaller --clean basic_slam.spec
if errorlevel 1 (
    echo ❌ Failed to build Basic SLAM
    pause
    exit /b 1
)
echo ✓ SLAM_Basic.exe created

REM Build 3: RL Trainer
echo.
echo [3/3] Building RL Trainer...
echo ----------------------------------------
pyinstaller --clean rl_trainer.spec
if errorlevel 1 (
    echo ❌ Failed to build RL Trainer
    pause
    exit /b 1
)
echo ✓ SLAM_RL_Trainer.exe created

echo.
echo ========================================
echo ✓ BUILD COMPLETE!
echo ========================================
echo.
echo Created executables in dist\ folder:
echo.

if exist "dist\SLAM_Complete_System.exe" (
    for %%A in (dist\SLAM_Complete_System.exe) do echo   [1] SLAM_Complete_System.exe  (%%~zA bytes^)
)
if exist "dist\SLAM_Basic.exe" (
    for %%A in (dist\SLAM_Basic.exe) do echo   [2] SLAM_Basic.exe              (%%~zA bytes^)
)
if exist "dist\SLAM_RL_Trainer.exe" (
    for %%A in (dist\SLAM_RL_Trainer.exe) do echo   [3] SLAM_RL_Trainer.exe         (%%~zA bytes^)
)

echo.
echo ========================================
echo 📦 Ready to Use!
echo ========================================
echo.
echo Double-click any .exe file to run
echo All executables have dynamic IP configuration
echo.
pause
