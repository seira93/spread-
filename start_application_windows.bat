@echo off
chcp 65001 >nul
echo Google Drive 画像ダウンローダー Web版を起動しています...
echo.
echo 注意: このアプリケーションはmacOSでビルドされています。
echo Windowsで実行するには、Windows環境でビルドする必要があります。
echo.
echo 現在のファイル: GoogleDriveDownloaderWeb (macOS用)
echo 必要なファイル: GoogleDriveDownloaderWeb.exe (Windows用)
echo.
echo ブラウザが自動で開きます。開かない場合は手動で http://localhost:8080 にアクセスしてください。
echo.
echo アプリケーションを停止するには、このウィンドウを閉じてください。
echo.
pause
echo エラー: Windows用の実行ファイルが見つかりません。
echo Windows環境でビルドしてください。
pause 