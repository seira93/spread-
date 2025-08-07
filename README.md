# Google Drive 画像ダウンローダー

このスクリプトは、Google Sheetsに記載されたGoogle Driveフォルダから画像を自動的にダウンロードするツールです。

## 新機能

### 自動URL検索機能
- D列のSKU名からGoogle Drive内のフォルダを自動検索
- 見つかったフォルダのURLをA列に自動記載
- その後、通常通り画像ダウンロードを実行

### コマンドライン版
- 軽量で高速なコマンドラインインターフェース
- スプレッドシートURLとシート名を指定可能
- リアルタイムログ表示
- フォルダ選択ダイアログでダウンロード先を指定

## セットアップ

### 1. 仮想環境の作成とアクティベート
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows
```

### 2. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 3. Google API認証の設定

#### 3.1 Google Cloud Consoleでプロジェクトを作成
1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成
3. Google Sheets APIとGoogle Drive APIを有効化

#### 3.2 OAuth 2.0クライアントIDを作成
1. 「認証情報」→「認証情報を作成」→「OAuth 2.0クライアントID」
2. アプリケーションの種類を「デスクトップアプリケーション」に設定
3. `client_secret.json`ファイルをダウンロード

#### 3.3 クライアントシークレットファイルを配置
ダウンロードした`client_secret.json`をプロジェクトのルートディレクトリに配置してください。

## 配布方法

### 実行可能ファイルの作成
```bash
# 依存関係のインストール
pip install -r requirements.txt

# 実行可能ファイルの作成
python build.py
```

### 配布用パッケージ
`GoogleDriveImageDownloader_Package/` フォルダに以下のファイルが作成されます：

#### macOS版
- `GoogleDriveImageDownloader` (実行可能ファイル)
- `GoogleDriveImageDownloader.app/` (アプリケーションバンドル)
- `README.md` (使用方法)
- `QUICK_START_GUIDE.txt` (クイックスタートガイド)
- `SETUP_GUIDE.txt` (セットアップ手順)

#### Windows版
- `GoogleDriveImageDownloader.exe` (実行可能ファイル)
- `README.md` (使用方法)
- `QUICK_START_GUIDE.txt` (クイックスタートガイド)
- `SETUP_GUIDE.txt` (セットアップ手順)

### 配布時の注意事項
1. **Google API認証**: 各ユーザーが独自の`client_secret.json`ファイルを取得する必要があります
2. **セキュリティ**: `client_secret.json`は機密情報のため適切に管理してください
3. **権限設定**: スプレッドシートの編集権限が必要です

## 使用方法

### 1. Google Sheetsの準備
以下の形式でスプレッドシートを作成してください：

| 列A | 列B | 列C | 列D | 列E |
|-----|-----|-----|-----|-----|
| Google DriveフォルダURL（自動記載） | - | - | SKU名 | 保存するファイル名 |

**注意**: A列は空欄のままでも構いません。スクリプトが自動でURLを記載します。

### 2. スクリプトの実行

#### 基本的な使用方法（デフォルト値）
```bash
python request.py
```

#### カスタム設定での実行
```bash
# スプレッドシートURLとシート名を指定
python request.py --url "https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID" --sheet "シート名"

# 短縮形でも指定可能
python request.py -u "https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID" -s "シート名"

# 開始行も指定
python request.py -u "https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID" -s "シート名" -r 3

# ダウンロード先も指定
python request.py -u "https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID" -s "シート名" -d "/path/to/download"
```

#### コマンドライン引数の説明
- `--url, -u`: Google スプレッドシートのURL
- `--sheet, -s`: シート名（デフォルト: "第3弾"）
- `--start-row, -r`: 開始行番号（デフォルト: 2）
- `--download-dir, -d`: ダウンロード先ディレクトリ

#### 使用例
```bash
# 例1: 別のスプレッドシートを使用
python request.py -u "https://docs.google.com/spreadsheets/d/abc123def456" -s "商品リスト"

# 例2: 3行目から開始
python request.py -u "https://docs.google.com/spreadsheets/d/abc123def456" -s "商品リスト" -r 3

# 例3: ヘルプを表示
python request.py --help
```

### 3. 処理の流れ
1. **ステップ1**: D列のSKU名からGoogle Drive内のフォルダを検索し、A列にURLを記載
2. **ステップ2**: A列のURLから画像をダウンロード

### 4. 認証手順（初回実行時）
1. スクリプトが認証URLを表示します
2. **既に開いているブラウザウィンドウ**でそのURLを開いてください
3. Googleアカウントにログイン済みの場合は、認証画面が表示されます
4. 認証を完了したら、スクリプトのウィンドウに戻ってEnterキーを押してください

**注意**: 新規ウィンドウではなく、既に開いているブラウザウィンドウを使用することで、ログイン済みのセッションを利用できます。

## 機能

- **自動URL検索**: D列のSKU名からGoogle Driveフォルダを自動検索
- **自動URL記載**: 見つかったフォルダのURLをA列に自動記載
- **コマンドライン版**: 軽量で高速なコマンドラインインターフェース
- **コマンドライン引数対応**: スプレッドシートURLとシート名を指定可能
- Google Driveフォルダから最初の画像を自動取得
- レート制限を考慮したAPI呼び出し
- 既存ファイルの重複チェック
- エラーハンドリングとログ出力
- ダウンロードした画像は`downloaded_images`フォルダに保存
- 既存ブラウザセッションを利用した認証

## 注意事項

- Google Sheets APIとGoogle Drive APIの有効化が必要です
- 初回実行時はOAuth認証が必要です
- 大量のフォルダを処理する場合は時間がかかる場合があります
- 認証時は既に開いているブラウザウィンドウを使用することを推奨します 
- D列のSKU名とGoogle Drive内のフォルダ名が完全に一致する必要があります
- スプレッドシートは実行ユーザーが編集権限を持っている必要があります
- 共有されたスプレッドシートを使用する場合は、適切な権限設定が必要です 