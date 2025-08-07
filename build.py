#!/usr/bin/env python3
"""
Google Drive 画像ダウンローダーのビルドスクリプト
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def build_executable():
    """PyInstallerを使用して実行可能ファイルを作成"""
    
    # プラットフォームに応じてアイコンファイルを設定
    icon_file = get_icon_file()
    
    # PyInstallerのコマンド
    cmd = [
        'pyinstaller',
        '--onefile',  # 単一の実行可能ファイルにまとめる
        '--console',  # コンソールウィンドウを表示
        '--name=GoogleDriveImageDownloader',  # 実行可能ファイルの名前
        '--add-data=README.md:.',  # READMEファイルを含める
        '--exclude-module=backports',  # 問題のあるbackportsモジュールを除外
        '--exclude-module=jaraco',  # jaracoモジュールを除外
        '--exclude-module=pkg_resources',  # pkg_resourcesを除外
        '依頼.py'
    ]
    
    # アイコンファイルが存在する場合のみ追加
    if icon_file and os.path.exists(icon_file):
        cmd.append(f'--icon={icon_file}')
    
    print("ビルドを開始します...")
    print(f"実行コマンド: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("ビルドが完了しました！")
        
        # 配布用フォルダを作成
        create_distribution_package()
        
    except subprocess.CalledProcessError as e:
        print(f"ビルドエラー: {e}")
        sys.exit(1)

def get_icon_file():
    """プラットフォームに応じてアイコンファイルを取得"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        icon_file = "icon.icns"
        if not os.path.exists(icon_file):
            create_macos_icon()
    elif system == "Windows":
        icon_file = "icon.ico"
        if not os.path.exists(icon_file):
            create_windows_icon()
    else:  # Linux
        icon_file = None
    
    return icon_file if os.path.exists(icon_file) else None

def create_macos_icon():
    """macOS用のアイコンファイルを作成"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # 128x128のアイコンを作成（macOSでは大きなサイズが必要）
        img = Image.new('RGBA', (128, 128), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # 背景の円を描画
        draw.ellipse([8, 8, 120, 120], fill=(66, 133, 244, 255), outline=(52, 168, 83, 255), width=4)
        
        # 中央に「G」を描画
        try:
            font = ImageFont.truetype("arial.ttf", 64)
        except:
            font = ImageFont.load_default()
        
        draw.text((48, 32), "G", fill=(255, 255, 255, 255), font=font)
        
        # icnsファイルとして保存
        img.save('icon.icns', format='ICNS')
        print("macOS用アイコンファイルを作成しました: icon.icns")
        
    except ImportError:
        print("PILがインストールされていないため、アイコンファイルの作成をスキップします。")
    except Exception as e:
        print(f"アイコンファイルの作成に失敗しました: {e}")

def create_windows_icon():
    """Windows用のアイコンファイルを作成"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # 32x32のアイコンを作成
        img = Image.new('RGBA', (32, 32), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # 背景の円を描画
        draw.ellipse([2, 2, 30, 30], fill=(66, 133, 244, 255), outline=(52, 168, 83, 255), width=2)
        
        # 中央に「G」を描画
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        draw.text((12, 8), "G", fill=(255, 255, 255, 255), font=font)
        
        # icoファイルとして保存
        img.save('icon.ico', format='ICO')
        print("Windows用アイコンファイルを作成しました: icon.ico")
        
    except ImportError:
        print("PILがインストールされていないため、アイコンファイルの作成をスキップします。")
    except Exception as e:
        print(f"アイコンファイルの作成に失敗しました: {e}")

def create_distribution_package():
    """配布用パッケージを作成"""
    
    dist_dir = Path("dist")
    package_dir = Path("GoogleDriveImageDownloader_Package")
    
    # 既存のパッケージディレクトリを削除
    if package_dir.exists():
        shutil.rmtree(package_dir)
    
    # パッケージディレクトリを作成
    package_dir.mkdir()
    
    # 実行可能ファイルをコピー
    system = platform.system()
    if system == "Darwin":  # macOS
        # macOS用の実行可能ファイル
        exe_file = dist_dir / "GoogleDriveImageDownloader"
        app_file = dist_dir / "GoogleDriveImageDownloader.app"
        
        if exe_file.exists():
            shutil.copy2(exe_file, package_dir)
            print(f"macOS実行可能ファイルをコピーしました: {exe_file}")
        
        if app_file.exists():
            shutil.copytree(app_file, package_dir / "GoogleDriveImageDownloader.app")
            print(f"macOSアプリケーションバンドルをコピーしました: {app_file}")
            
    elif system == "Windows":
        # Windows用の実行可能ファイル
    exe_file = dist_dir / "GoogleDriveImageDownloader.exe"
    if exe_file.exists():
        shutil.copy2(exe_file, package_dir)
            print(f"Windows実行可能ファイルをコピーしました: {exe_file}")
    
    # READMEファイルをコピー
    if Path("README.md").exists():
        shutil.copy2("README.md", package_dir)
        print("READMEファイルをコピーしました")
    
    # 設定サンプルファイルを作成
    create_sample_config(package_dir)
    
    # サンプルのclient_secret.jsonファイルを作成
    create_sample_client_secret(package_dir)
    
    # クイックスタートガイドを作成
    create_quick_start_guide(package_dir)
    
    print(f"配布用パッケージが作成されました: {package_dir}")

def create_sample_config(package_dir):
    """設定サンプルファイルを作成"""
    
    config_content = """# Google Drive 画像ダウンローダー 設定サンプル

## 使用方法

1. Google Cloud Consoleでプロジェクトを作成
2. Google Sheets APIとGoogle Drive APIを有効化
3. OAuth 2.0クライアントIDを作成
4. client_secret.jsonファイルをダウンロード
5. client_secret.jsonをこのフォルダに配置
6. GoogleDriveImageDownloaderを実行

## 必要なファイル

- GoogleDriveImageDownloader (実行ファイル)
- client_secret.json (Google API認証ファイル) ← 各自で取得
- README.md (使用方法)

## 注意事項

- 初回実行時はブラウザでGoogleアカウントの認証が必要です
- 認証後はtoken.jsonファイルが自動生成されます
- ダウンロードした画像はdownloaded_imagesフォルダに保存されます
- client_secret.jsonは機密情報のため、各自で取得してください
"""
    
    with open(package_dir / "SETUP_GUIDE.txt", "w", encoding="utf-8") as f:
        f.write(config_content)

def create_sample_client_secret(package_dir):
    """サンプルのclient_secret.jsonファイルを作成"""
    
    sample_content = """{
  "installed": {
    "client_id": "YOUR_CLIENT_ID_HERE.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET_HERE",
    "redirect_uris": ["http://localhost"]
  }
}"""
    
    with open(package_dir / "client_secret_sample.json", "w", encoding="utf-8") as f:
        f.write(sample_content)
    
    # サンプルファイルの説明も作成
    sample_readme = """# client_secret.json サンプルファイル

このファイルは参考用のサンプルです。

## 使用方法

1. Google Cloud Consoleで独自の認証情報を作成
2. ダウンロードしたJSONファイルを「client_secret.json」にリネーム
3. このサンプルファイルを置き換えてください

## 注意事項

- このサンプルファイルは実際には使用できません
- 各自でGoogle Cloud Consoleから取得したファイルを使用してください
- client_secret.jsonは機密情報のため、他人と共有しないでください

詳細な手順は QUICK_START_GUIDE.txt を参照してください。
"""
    
    with open(package_dir / "client_secret_sample_README.txt", "w", encoding="utf-8") as f:
        f.write(sample_readme)

def create_quick_start_guide(package_dir):
    """クイックスタートガイドを作成"""
    
    quick_start_content = """# クイックスタートガイド

## 1. Google Cloud Consoleの設定

### 1.1 プロジェクトの作成
1. https://console.cloud.google.com/ にアクセス
2. 新しいプロジェクトを作成
3. プロジェクト名を入力（例: "画像ダウンローダー"）

### 1.2 APIの有効化
1. 「APIとサービス」→「ライブラリ」を選択
2. 以下のAPIを検索して有効化:
   - Google Sheets API
   - Google Drive API

### 1.3 認証情報の作成
1. 「APIとサービス」→「認証情報」を選択
2. 「認証情報を作成」→「OAuth 2.0クライアントID」
3. アプリケーションの種類: 「デスクトップアプリケーション」
4. 名前を入力（例: "画像ダウンローダー"）
5. 「作成」をクリック

### 1.4 クライアントシークレットのダウンロード
1. 作成されたOAuth 2.0クライアントIDをクリック
2. 「JSONをダウンロード」をクリック
3. ダウンロードしたファイルを「client_secret.json」にリネーム
4. このフォルダに配置

## 2. スプレッドシートの準備

### 2.1 スプレッドシートの作成
1. Google スプレッドシートを新規作成
2. 以下の形式でデータを入力:

| A列 | B列 | C列 | D列 | E列 |
|-----|-----|-----|-----|-----|
| (自動記載) | - | - | SKU名 | 保存ファイル名 |

### 2.2 共有設定
1. スプレッドシートの「共有」ボタンをクリック
2. 実行するユーザーのメールアドレスを追加
3. 権限を「編集者」に設定

## 3. アプリケーションの実行

### 3.1 初回実行
1. GoogleDriveImageDownloader.exeをダブルクリック
2. GUIが起動したら、スプレッドシートURLを入力
3. シート名、開始行、ダウンロード先を設定
4. 「ダウンロード開始」ボタンをクリック
5. ブラウザでGoogle認証を実行
6. 認証完了後、処理が開始されます

### 3.2 2回目以降
1. GoogleDriveImageDownloader.exeをダブルクリック
2. 設定を入力して「ダウンロード開始」をクリック
3. 処理が開始されます

## トラブルシューティング

### よくある問題
1. **認証エラー**: client_secret.jsonが正しく配置されているか確認
2. **権限エラー**: スプレッドシートの共有設定を確認
3. **フォルダが見つからない**: D列のSKU名とGoogle Drive内のフォルダ名が一致しているか確認

### サポート
- ログ画面でエラーの詳細を確認
- README.mdで詳細な使用方法を確認
"""
    
    with open(package_dir / "QUICK_START_GUIDE.txt", "w", encoding="utf-8") as f:
        f.write(quick_start_content)

if __name__ == "__main__":
    build_executable() 