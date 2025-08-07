# 🪟 Windows用ビルドパッケージ

## 🚀 簡単な使い方

### 1. Pythonをインストール
- [Python公式サイト](https://www.python.org/downloads/)からダウンロード
- インストール時に「Add Python to PATH」にチェック

### 2. ファイルを配置
- このフォルダ内のファイルをWindowsのデスクトップにコピー
- 例: `C:\Users\YourName\Desktop\spread操作\`

### 3. コマンドプロンプトを開く
- Windowsキー + R を押す
- `cmd` と入力してEnter

### 4. プロジェクトフォルダに移動
```cmd
cd C:\Users\YourName\Desktop\spread操作
```

### 5. ビルドスクリプトを実行
```cmd
build_windows.bat
```

### 6. 完了！
- `GoogleDriveDownloaderWeb_Package_Windows` フォルダが作成されます
- `start_application.bat` をダブルクリックしてアプリケーションを起動

## 📋 含まれるファイル

- `simple_gui.py` - メインアプリケーション
- `依頼.py` - 元のスクリプト
- `client_secret.json` - Google API認証ファイル
- `build_windows.bat` - Windows用ビルドスクリプト
- `requirements_windows.txt` - Windows用依存関係
- `README_WINDOWS.md` - Windows専用説明書
- `WINDOWS_SETUP_GUIDE.md` - 詳細セットアップガイド

## 🔧 トラブルシューティング

### Pythonが見つからない場合
```cmd
py --version
```

### 依存関係のインストールエラー
```cmd
pip install --upgrade pip
pip install -r requirements_windows.txt
```

### ビルドエラー
- インターネット接続を確認
- 他のアプリケーションを閉じる
- 仮想メモリを増やす

## 📞 サポート

問題が発生した場合は、エラーメッセージをコピーして保存してください。
