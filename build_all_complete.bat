@echo off
echo ========================================
echo Building ALL SLAM System Executables
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo ERROR: PyInstaller not found!
    echo Please install: pip install pyinstaller
    pause
    exit /b 1
)

echo [1/8] Building SLAM Complete System...
pyinstaller --clean complete_slam.spec
if %errorlevel% neq 0 (
    echo ERROR building SLAM Complete System!
    pause
    exit /b 1
)

echo.
echo [2/8] Building SLAM Basic...
pyinstaller --clean basic_slam.spec
if %errorlevel% neq 0 (
    echo ERROR building SLAM Basic!
    pause
    exit /b 1
)

echo.
echo [3/8] Building RL Trainer Console...
pyinstaller --clean rl_trainer.spec
if %errorlevel% neq 0 (
    echo ERROR building RL Trainer!
    pause
    exit /b 1
)

echo.
echo [4/8] Building RL Trainer GUI...
pyinstaller --clean rl_gui.spec
if %errorlevel% neq 0 (
    echo ERROR building RL Trainer GUI!
    pause
    exit /b 1
)

echo.
echo [5/8] Building Integrated SLAM...
pyinstaller --clean integrated_slam.spec
if %errorlevel% neq 0 (
    echo ERROR building Integrated SLAM!
    pause
    exit /b 1
)

echo.
echo [6/8] Building Integrated SLAM + RL...
pyinstaller --clean integrated_slam_rl.spec
if %errorlevel% neq 0 (
    echo ERROR building Integrated SLAM + RL!
    pause
    exit /b 1
)

echo.
echo [7/8] Building Camera Stream Handler...
pyinstaller --clean camera_handler.spec
if %errorlevel% neq 0 (
    echo ERROR building Camera Handler!
    pause
    exit /b 1
)

echo.
echo [8/8] Building Stereo SLAM...
pyinstaller --clean stereo_slam.spec
if %errorlevel% neq 0 (
    echo ERROR building Stereo SLAM!
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD COMPLETE!
echo ========================================
echo.
echo All executables are in the 'dist' folder:
echo.
dir /B dist\*.exe
echo.
echo File sizes:
powershell -Command "Get-ChildItem -Path .\dist\*.exe | Select-Object Name, @{Name='Size (MB)';Expression={[math]::Round($_.Length/1MB, 2)}} | Format-Table -AutoSize"
echo.
echo ========================================
pause
