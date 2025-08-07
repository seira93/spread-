# 🚀 Google Drive 画像ダウンローダー 使用方法

## 📋 簡単な設定方法

### 方法1: 設定ファイル作成（推奨）
```bash
# 初回設定
./GoogleDriveImageDownloader --setup
```

設定ファイル（config.json）が作成され、次回から自動で読み込まれます。

### 方法2: 対話式設定
```bash
# 実行時に設定を変更
./GoogleDriveImageDownloader --interactive
```

### 方法3: コマンドライン引数
```bash
# 直接指定
./GoogleDriveImageDownloader --url "スプレッドシートURL" --sheet "シート名" --download-dir "/ダウンロード先"
```

## 🔧 設定項目

| 項目 | 説明 | デフォルト値 |
|------|------|-------------|
| `spreadsheet_url` | Google スプレッドシートのURL | 現在のURL |
| `sheet_name` | シート名 | "第3弾" |
| `start_row` | 開始行番号 | 2 |
| `download_dir` | ダウンロード先ディレクトリ | "downloaded_images" |

## 📝 使用例

### 基本的な使用方法
```bash
# 設定ファイルを使用（推奨）
./GoogleDriveImageDownloader

# 対話式で設定
./GoogleDriveImageDownloader --interactive

# 設定ファイルを作成
./GoogleDriveImageDownloader --setup
```

### コマンドライン引数の例
```bash
# URLとシート名を指定
./GoogleDriveImageDownloader --url "https://docs.google.com/spreadsheets/d/..." --sheet "商品リスト"

# ダウンロード先を指定
./GoogleDriveImageDownloader --download-dir "/Users/username/Pictures"

# 開始行を指定
./GoogleDriveImageDownloader --start-row 5
```

## 📁 ファイル構成

```
GoogleDriveImageDownloader_Package/
├── GoogleDriveImageDownloader (実行ファイル)
├── client_secret.json (認証ファイル)
├── config.json (設定ファイル - 作成後)
├── README.md
└── USAGE_GUIDE.md (このファイル)
```

## ⚡ 高速化機能

- **並列処理**: 複数のSKUを同時に検索
- **キャッシュ機能**: 同じSKUの重複検索を回避
- **バッチ更新**: スプレッドシートへの一括更新
- **進捗表示**: リアルタイムで処理状況を表示

## 🔍 トラブルシューティング

### よくある問題

1. **認証エラー**
   - `client_secret.json`が正しく配置されているか確認
   - Google Cloud ConsoleでAPIが有効化されているか確認

2. **設定ファイルが見つからない**
   - `--setup`オプションで設定ファイルを作成

3. **ダウンロード先が存在しない**
   - 指定したディレクトリが存在するか確認
   - 書き込み権限があるか確認

## 📞 サポート

問題が発生した場合は、以下の情報を確認してください：
- エラーメッセージ
- 使用したコマンド
- 設定ファイルの内容（config.json） 