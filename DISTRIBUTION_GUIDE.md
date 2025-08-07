# 社内配布用ガイド

このプログラムを社内で配布するための方法を説明します。

## 配布方法の選択肢

### 方法1: 実行可能ファイル（推奨）

#### メリット
- PythonがインストールされていないPCでも実行可能
- セットアップが簡単
- 依存関係の管理が不要
- GUIインターフェースで使いやすい

#### 手順
1. PyInstallerをインストール
```bash
pip install pyinstaller pillow
```

2. 実行可能ファイルを作成
```bash
python build.py
```

3. 配布用パッケージが作成されます
   - `GoogleDriveImageDownloader_Package/`フォルダ内に必要なファイルが含まれます

### 方法2: Pythonパッケージ

#### メリット
- ソースコードの確認が可能
- カスタマイズが容易
- 軽量

#### 手順
1. パッケージを作成
```bash
python setup.py sdist bdist_wheel
```

2. 配布用ファイルが作成されます
   - `dist/`フォルダ内に`.tar.gz`と`.whl`ファイルが作成されます

## 配布時の注意事項

### 1. Google API認証の設定
- 各ユーザーが独自の`client_secret.json`ファイルを取得する必要があります
- 社内で共有可能なGoogle Cloudプロジェクトを作成することを推奨します

### 2. セキュリティ
- `client_secret.json`ファイルは機密情報です
- 社内での適切な管理が必要です

### 3. 使用方法の説明
配布時に以下のファイルを含めてください：
- 実行可能ファイル（またはPythonパッケージ）
- `README.md`（使用方法）
- `QUICK_START_GUIDE.txt`（クイックスタートガイド）
- `SETUP_GUIDE.txt`（セットアップ手順）

## 推奨配布構成

```
GoogleDriveImageDownloader_Package/
├── GoogleDriveImageDownloader.exe
├── README.md
├── QUICK_START_GUIDE.txt
├── SETUP_GUIDE.txt
└── sample_client_secret.json (サンプルファイル)
```

## 社内での展開手順

1. **Google Cloudプロジェクトの準備**
   - 社内用のGoogle Cloudプロジェクトを作成
   - Google Sheets APIとGoogle Drive APIを有効化
   - OAuth 2.0クライアントIDを作成

2. **配布パッケージの作成**
   - `python build.py`を実行
   - 作成されたパッケージを社内共有フォルダに配置

3. **ユーザー向け説明**
   - 各ユーザーがGoogle Cloud Consoleでクライアントシークレットを取得
   - `client_secret.json`を実行ファイルと同じフォルダに配置
   - 初回実行時の認証手順を説明

## 新機能（GUI対応）

### GUIインターフェース
- 使いやすいグラフィカルユーザーインターフェース
- スプレッドシートURL、シート名、開始行、ダウンロード先を簡単に指定
- リアルタイムログ表示
- フォルダ選択ダイアログでダウンロード先を指定

### 使用方法
1. `GoogleDriveImageDownloader.exe`をダブルクリック
2. GUIが起動したら、スプレッドシートURLを入力
3. シート名、開始行、ダウンロード先を設定
4. 「ダウンロード開始」ボタンをクリック
5. 初回実行時はブラウザでGoogle認証を実行

## トラブルシューティング

### よくある問題
1. **認証エラー**: `client_secret.json`が正しく配置されているか確認
2. **API制限エラー**: 大量のリクエスト時は時間を空けて再実行
3. **ファイルアクセスエラー**: 実行権限とフォルダ作成権限を確認
4. **GUIが起動しない**: 必要な依存関係がインストールされているか確認

### サポート
- ログファイルを確認してエラーの詳細を把握
- Google Cloud ConsoleでAPI使用量を確認 
- GUIのログ画面でリアルタイムにエラーを確認 