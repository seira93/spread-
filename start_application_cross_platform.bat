@echo off
chcp 65001 >nul
echo Google Drive 画像ダウンローダー Web版を起動しています...
echo.
echo プラットフォームを確認中...

REM Windows用の実行ファイルを確認
if exist "GoogleDriveDownloaderWeb.exe" (
    echo Windows用の実行ファイルを発見しました。
    set EXECUTABLE=GoogleDriveDownloaderWeb.exe
    goto :run
)

REM macOS/Linux用の実行ファイルを確認
if exist "GoogleDriveDownloaderWeb" (
    echo macOS/Linux用の実行ファイルを発見しました。
    echo 注意: このファイルはWindowsでは動作しません。
    echo Windows環境でビルドしてください。
    set EXECUTABLE=GoogleDriveDownloaderWeb
    goto :error
)

echo 実行ファイルが見つかりません。
goto :error

:run
echo.
echo ブラウザが自動で開きます。開かない場合は手動で http://localhost:8080 にアクセスしてください。
echo.
echo アプリケーションを停止するには、このウィンドウを閉じてください。
echo.
pause
%EXECUTABLE%
pause
goto :end

:error
echo.
echo エラー: 適切な実行ファイルが見つかりません。
echo.
echo 解決方法:
echo 1. Windows環境でビルドする
echo 2. または、Pythonがインストールされている場合は以下を実行:
echo    python simple_gui.py
echo.
pause

:end 