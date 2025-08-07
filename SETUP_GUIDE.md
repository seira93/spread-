# 🚀 セットアップガイド

## 📋 前提条件

### 必要なソフトウェア
- **Python 3.8以上**
- **Git**
- **GitHub CLI** (オプション)

### Google API設定
1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクトを作成
2. Google Drive APIとGoogle Sheets APIを有効化
3. OAuth 2.0クライアントIDを作成
4. `client_secret.json`ファイルをダウンロード

## 🔧 セットアップ手順

### 1. リポジトリのクローン
```bash
git clone https://github.com/seira93/spread-.git
cd spread-
```

### 2. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 3. 設定ファイルの準備

#### A. Google API認証ファイル
```bash
# client_secret_sample.jsonをコピー
cp client_secret_sample.json client_secret.json

# 実際の認証情報に置き換え
# client_secret.jsonを編集して実際の認証情報を入力
```

#### B. 設定ファイル
```bash
# config_sample.jsonをコピー
cp config_sample.json config.json

# 設定を編集
# config.jsonを編集して実際の設定を入力
```

### 4. 初回実行
```bash
python simple_gui.py
```

## 🪟 Windows用ビルド

### 自動ビルド (推奨)
1. GitHubのActionsタブでビルドを確認
2. ビルド完了後、成果物をダウンロード

### 手動ビルド
1. GitHubのActionsタブで「Manual Windows Build」を選択
2. 「Run workflow」をクリック
3. ビルド完了後、成果物をダウンロード

## 📁 ファイル構成

```
spread操作/
├── simple_gui.py              # メインアプリケーション
├── request.py                     # 元のスクリプト
├── client_secret_sample.json  # 認証ファイルのサンプル
├── config_sample.json         # 設定ファイルのサンプル
├── requirements.txt           # Python依存関係
├── requirements_windows.txt   # Windows用依存関係
├── .github/workflows/        # CI/CD設定
├── README.md                 # 基本説明書
├── README_WINDOWS.md        # Windows専用説明書
├── README_CI_CD.md          # CI/CD説明書
└── SETUP_GUIDE.md           # このファイル
```

## 🔒 セキュリティ

### 機密情報の管理
- `client_secret.json`はGitにコミットしない
- 実際の認証情報はローカルでのみ使用
- サンプルファイルを使用して設定を確認

### 環境変数 (推奨)
```bash
# 環境変数で認証情報を管理
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"
```

## 🚨 トラブルシューティング

### よくある問題

#### 1. 認証エラー
```bash
# client_secret.jsonが正しく配置されているか確認
ls -la client_secret.json
```

#### 2. 依存関係エラー
```bash
# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate     # Windows
```

#### 3. ビルドエラー
- GitHub Actionsのログを確認
- ローカルでビルドを試行
- 依存関係のバージョンを確認

## 📞 サポート

### 問題の報告
1. GitHubのIssuesタブで新しいIssueを作成
2. エラーメッセージとログを添付
3. 環境情報を記載

### ドキュメント
- [README.md](README.md) - 基本使用方法
- [README_WINDOWS.md](README_WINDOWS.md) - Windows専用ガイド
- [README_CI_CD.md](README_CI_CD.md) - CI/CD使用方法

## 🆕 更新履歴

### v1.0.0
- 初回リリース
- Web GUI実装
- CI/CD自動化
- Windows対応 