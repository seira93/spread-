@echo off
chcp 65001 >nul
echo Google Drive 画像ダウンローダー Web版を起動しています...
echo.
echo Pythonスクリプト版を起動します...

REM Pythonの確認
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo エラー: Pythonが見つかりません。
    echo Pythonをインストールしてください: https://www.python.org/
    pause
    exit /b 1
)

REM 必要なファイルの確認
if not exist "simple_gui.py" (
    echo エラー: simple_gui.py が見つかりません。
    echo プロジェクトルートディレクトリで実行してください。
    pause
    exit /b 1
)

if not exist "client_secret.json" (
    echo エラー: client_secret.json が見つかりません。
    echo 認証ファイルが必要です。
    pause
    exit /b 1
)

echo.
echo ブラウザが自動で開きます。開かない場合は手動で http://localhost:8080 にアクセスしてください。
echo.
echo アプリケーションを停止するには、このウィンドウを閉じてください。
echo.
pause

REM Pythonスクリプトを実行
python simple_gui.py

pause 