@echo off
chcp 65001 >nul
echo ============================================================
echo 🌐 Google Drive 画像ダウンローダー Windows版ビルダー
echo ============================================================

echo.
echo 必要なファイルを確認中...

REM 必要なファイルの存在確認
if not exist "simple_gui.py" (
    echo ❌ エラー: simple_gui.py が見つかりません
    pause
    exit /b 1
)

if not exist "client_secret.json" (
    echo ❌ エラー: client_secret.json が見つかりません
    pause
    exit /b 1
)

if not exist "requirements_windows.txt" (
    echo ❌ エラー: requirements_windows.txt が見つかりません
    pause
    exit /b 1
)

echo ✅ 必要なファイルが確認されました

echo.
echo Python環境を確認中...
python --version
if %errorlevel% neq 0 (
    echo ❌ エラー: Pythonがインストールされていません
    echo Pythonをインストールしてください: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo 依存関係をインストール中...
pip install -r requirements_windows.txt
if %errorlevel% neq 0 (
    echo ❌ エラー: 依存関係のインストールに失敗しました
    pause
    exit /b 1
)

echo.
echo PyInstallerをインストール中...
pip install pyinstaller==6.2.0
if %errorlevel% neq 0 (
    echo ❌ エラー: PyInstallerのインストールに失敗しました
    pause
    exit /b 1
)

echo.
echo Windows版アプリケーションをビルド中...
pyinstaller --onefile --console --name=GoogleDriveDownloaderWeb --add-data=README.md:. --add-data=USAGE_GUIDE.md:. --add-data=request.py:. --exclude-module=backports --exclude-module=jaraco --exclude-module=pkg_resources --exclude-module=tkinter --exclude-module=matplotlib --exclude-module=numpy simple_gui.py

if %errorlevel% neq 0 (
    echo ❌ エラー: ビルドに失敗しました
    pause
    exit /b 1
)

echo.
echo Windows版パッケージを作成中...

REM パッケージディレクトリを作成
if exist "GoogleDriveDownloaderWeb_Package_Windows" (
    rmdir /s /q "GoogleDriveDownloaderWeb_Package_Windows"
)
mkdir "GoogleDriveDownloaderWeb_Package_Windows"

REM ファイルをコピー
copy "dist\GoogleDriveDownloaderWeb.exe" "GoogleDriveDownloaderWeb_Package_Windows\"
copy "client_secret.json" "GoogleDriveDownloaderWeb_Package_Windows\"
copy "request.py" "GoogleDriveDownloaderWeb_Package_Windows\"
copy "README.md" "GoogleDriveDownloaderWeb_Package_Windows\"
copy "USAGE_GUIDE.md" "GoogleDriveDownloaderWeb_Package_Windows\"
copy "README_WINDOWS.md" "GoogleDriveDownloaderWeb_Package_Windows\"

REM Windows用バッチファイルを作成
echo @echo off > "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo chcp 65001 ^>nul >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo echo Google Drive 画像ダウンローダー Web版を起動しています... >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo echo. >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo echo ブラウザが自動で開きます。開かない場合は手動で http://localhost:8080 にアクセスしてください。 >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo echo. >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo echo アプリケーションを停止するには、このウィンドウを閉じてください。 >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo echo. >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo pause >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo GoogleDriveDownloaderWeb.exe >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"
echo pause >> "GoogleDriveDownloaderWeb_Package_Windows\start_application.bat"

echo.
echo ============================================================
echo 🎉 Windows版アプリケーションのビルドが完了しました！
echo ============================================================
echo.
echo 作成されたパッケージ: GoogleDriveDownloaderWeb_Package_Windows
echo.
echo 使用方法:
echo 1. GoogleDriveDownloaderWeb_Package_Windows フォルダを開く
echo 2. start_application.bat をダブルクリック
echo 3. ブラウザで http://localhost:8080 にアクセス
echo 4. Web画面で設定を入力して実行
echo ============================================================

pause 