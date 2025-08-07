#!/bin/bash

echo "============================================================"
echo "🌐 Windows用ビルドパッケージ作成スクリプト"
echo "============================================================"

# Windows用パッケージディレクトリを作成
PACKAGE_DIR="Windows_Build_Package"
if [ -d "$PACKAGE_DIR" ]; then
    rm -rf "$PACKAGE_DIR"
fi
mkdir -p "$PACKAGE_DIR"

echo "📁 Windows用ビルドパッケージを作成中..."

# 必要なファイルをコピー
files_to_copy=(
    "simple_gui.py"
    "request.py"
    "client_secret.json"
    "build_windows.bat"
    "requirements_windows.txt"
    "README.md"
    "README_WINDOWS.md"
    "USAGE_GUIDE.md"
    "WINDOWS_SETUP_GUIDE.md"
)

for file in "${files_to_copy[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$PACKAGE_DIR/"
        echo "✅ $file をコピーしました"
    else
        echo "⚠️ $file が見つかりません"
    fi
done

# Windows用のクイックスタートガイドを作成
cat > "$PACKAGE_DIR/QUICK_START_WINDOWS.md" << 'EOF'
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
- `request.py` - 元のスクリプト
- `