# 🪟 Windows環境でのビルド手順

## 📋 前提条件

### 必要なソフトウェア
1. **Python 3.8以上**
   - [Python公式サイト](https://www.python.org/downloads/)からダウンロード
   - インストール時に「Add Python to PATH」にチェック

2. **インターネット接続**
   - 依存関係のダウンロードに必要

## 🚀 セットアップ手順

### ステップ1: プロジェクトファイルの準備

#### 方法A: USBメモリを使用
1. USBメモリに以下のファイルをコピー：
   ```
   spread操作/
   ├── simple_gui.py
   ├── request.py
   ├── client_secret.json
   ├── build_windows.bat
   ├── requirements_windows.txt
   ├── README.md
   └── README_WINDOWS.md
   ```

2. Windowsのデスクトップにフォルダを作成：
   ```cmd
   mkdir C:\Users\%USERNAME%\Desktop\spread操作
   ```

3. USBメモリからファイルをコピー

#### 方法B: クラウドストレージを使用
1. ファイルをGoogle Drive、OneDrive、Dropboxなどにアップロード
2. Windowsでダウンロードしてデスクトップに配置

### ステップ2: コマンドプロンプトを開く
1. Windowsキー + R を押す
2. `cmd` と入力してEnter
3. プロジェクトフォルダに移動：
   ```cmd
   cd C:\Users\%USERNAME%\Desktop\spread操作
   ```

### ステップ3: Python環境の確認
```cmd
python --version
```
バージョンが表示されればOK

### ステップ4: ビルドスクリプトを実行
```cmd
build_windows.bat
```

## 🔧 トラブルシューティング

### よくある問題

#### 1. "python"コマンドが見つからない
**解決方法**:
- Pythonを再インストール
- インストール時に「Add Python to PATH」にチェック
- または、`py`コマンドを使用：
  ```cmd
  py --version
  ```

#### 2. 依存関係のインストールエラー
**解決方法**:
```cmd
pip install --upgrade pip
pip install -r requirements_windows.txt
```

#### 3. PyInstallerのエラー
**解決方法**:
```cmd
pip uninstall pyinstaller
pip install pyinstaller==6.2.0
```

#### 4. ビルド時のメモリエラー
**解決方法**:
- 他のアプリケーションを閉じる
- 仮想メモリを増やす
- または、Pythonスクリプト版を使用

## 📁 生成されるファイル

ビルド成功後、以下のファイルが生成されます：

```
GoogleDriveDownloaderWeb_Package_Windows/
├── GoogleDriveDownloaderWeb.exe    # Windows用実行ファイル
├── start_application.bat           # 起動スクリプト
├── client_secret.json              # 認証ファイル
├── README.md                       # 基本説明書
├── README_WINDOWS.md              # Windows専用説明書
├── USAGE_GUIDE.md                 # 使用方法ガイド
└── request.py                      # 元のスクリプト
```

## 🎯 使用方法

### 1. アプリケーションの起動
```cmd
cd GoogleDriveDownloaderWeb_Package_Windows
start_application.bat
```

### 2. ブラウザでアクセス
- 自動でブラウザが開きます
- 手動で開く場合: http://localhost:8080

### 3. 設定と実行
- スプレッドシートURLを入力
- シート名を入力
- ダウンロード先を指定
- 「🚀 実行開始」をクリック

## 🔒 セキュリティ

### Windows Defenderの警告
初回実行時に警告が表示される場合：
1. 「詳細情報」をクリック
2. 「実行」をクリック
3. 「許可」を選択

### ファイアウォール
- ローカルホスト（localhost）のみアクセス
- 外部通信はGoogle API認証時のみ

## 📞 サポート

### ログの確認
- Web画面の「ログ表示」エリアを確認
- エラーメッセージをコピーして保存

### よくある質問

**Q: ビルドに時間がかかります**
A: 初回ビルドは依存関係のダウンロードのため時間がかかります（5-10分程度）

**Q: アプリケーションが起動しません**
A: ファイアウォールの設定を確認してください

**Q: ブラウザが開きません**
A: 手動で http://localhost:8080 にアクセスしてください

## 🆕 更新履歴

### v1.0.0
- 初回リリース
- Windows対応ビルドスクリプト
- 自動パッケージ作成
- エラーハンドリング機能 