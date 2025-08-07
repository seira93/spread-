@echo off
chcp 65001 >nul
echo ============================================================
echo Google Drive Image Downloader Windows Builder
echo ============================================================

echo.
echo Checking required files...

REM Check required files
if not exist "simple_gui.py" (
    echo ERROR: simple_gui.py not found
    pause
    exit /b 1
)

if not exist "client_secret.json" (
    echo ERROR: client_secret.json not found
    pause
    exit /b 1
)

if not exist "requirements_windows.txt" (
    echo ERROR: requirements_windows.txt not found
    pause
    exit /b 1
)

echo OK: Required files confirmed

echo.
echo Checking Python environment...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not installed
    echo Please install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
pip install -r requirements_windows.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Installing PyInstaller...
pip install pyinstaller==6.2.0
if %errorlevel% neq 0 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

echo.
echo Building Windows application...
pyinstaller --onefile --console --name=GoogleDriveDownloaderWeb --add-data=README.md:. --add-data=USAGE_GUIDE.md:. --add-data=request.py:. --exclude-module=backports --exclude-module=jaraco --exclude-module=pkg_resources --exclude-module=tkinter --exclude-module=matplotlib --exclude-module=numpy simple_gui.py

if %errorlevel% neq 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo Creating Windows package...

REM Create package directory
if exist "GoogleDriveDownloaderWeb_Package_Windows" (
    rmdir /s /q "GoogleDriveDownloaderWeb_Package_Windows"
)
mkdir "GoogleDriveDownloaderWeb_Package_Windows"

REM Copy files
copy "dist\GoogleDriveDownloaderWeb.exe" "GoogleDriveDownloaderWeb_Package_Windows\"
copy "client_secret.json" "GoogleDriveDownloaderWeb_Package_Windows\"
copy "依頼.py" "GoogleDriveDownloaderWeb_Package_Windows\"
copy "README.md" "GoogleDriveDownloaderWeb_Package_Windows\"
copy "USAGE_GUIDE.md" "GoogleDriveDownloaderWeb_Package_Windows\"
copy "README_WINDOWS.md" "GoogleDriveDownloaderWeb_Package_Windows\"
copy "request.py" "GoogleDriveDownloaderWeb_Package_Windows\"

REM Create Windows batch file
echo @echo off > "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo chcp 65001 ^>nul >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo echo Google Drive Image Downloader Web Version Starting... >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo echo. >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo echo Browser will open automatically. If not, manually access http://localhost:8080 >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo echo. >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo echo To stop the application, close this window. >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo echo. >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo pause >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo GoogleDriveDownloaderWeb.exe >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo pause >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"

echo.
echo ============================================================
echo SUCCESS: Windows application build completed!
echo ============================================================
echo.
echo Created package: GoogleDriveDownloaderWeb_Package_Windows
echo.
echo Usage:
echo 1. Open GoogleDriveDownloaderWeb_Package_Windows folder
echo 2. Double-click start_application.bat
echo 3. Access http://localhost:8080 in browser
echo 4. Enter settings and execute
echo ============================================================

pause 