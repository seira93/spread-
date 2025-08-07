#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
import platform

def build_web_gui():
    """Web版GUIアプリケーションをビルド（クロスプラットフォーム対応）"""
    print("🌐 Web版GUIアプリケーションのビルドを開始します...")
    
    # プラットフォームを検出
    current_platform = platform.system()
    print(f"🖥️ プラットフォーム: {current_platform}")
    
    # PyInstallerコマンドを構築
    cmd = [
        'pyinstaller',
        '--onefile',
        '--console',  # Webサーバーなのでコンソール表示
        '--name=GoogleDriveDownloaderWeb',
        '--add-data=README.md:.',
        '--add-data=USAGE_GUIDE.md:.',
        '--add-data=依頼.py:.',
        '--exclude-module=backports',
        '--exclude-module=jaraco',
        '--exclude-module=pkg_resources',
        'simple_gui.py'
    ]
    
    # Windows用の追加設定
    if current_platform == "Windows":
        cmd.extend([
            '--exclude-module=tkinter',  # Windowsではtkinterが問題を起こすことがある
            '--exclude-module=matplotlib',
            '--exclude-module=numpy',
        ])
    
    print(f"実行コマンド: {' '.join(cmd)}")
    
    # ビルド実行
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Web版GUIアプリケーションのビルドが完了しました！")
        
        # 配布用パッケージを作成
        create_web_gui_package(current_platform)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ ビルドエラー: {e}")
        print(f"エラー出力: {e.stderr}")
        return False
    
    return True

def create_web_gui_package(platform_name):
    """Web版GUIアプリケーション用の配布パッケージを作成（クロスプラットフォーム対応）"""
    package_dir = f"GoogleDriveDownloaderWeb_Package_{platform_name}"
    
    # 既存のパッケージディレクトリを削除
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    
    # パッケージディレクトリを作成
    os.makedirs(package_dir, exist_ok=True)
    
    # 実行ファイル名をプラットフォーム別に設定
    if platform_name == "Windows":
        executable_name = "GoogleDriveDownloaderWeb.exe"
        dist_path = "dist/GoogleDriveDownloaderWeb.exe"
    else:
        executable_name = "GoogleDriveDownloaderWeb"
        dist_path = "dist/GoogleDriveDownloaderWeb"
    
    # ファイルをコピー
    files_to_copy = [
        (dist_path, executable_name),
        ('client_secret.json', 'client_secret.json'),
        ('依頼.py', '依頼.py'),
        ('README.md', 'README.md'),
        ('USAGE_GUIDE.md', 'USAGE_GUIDE.md'),
        ('config.json', 'config.json')
    ]
    
    # Windows用の追加ファイル
    if platform_name == "Windows":
        files_to_copy.append(('README_WINDOWS.md', 'README_WINDOWS.md'))
    
    for src, dst in files_to_copy:
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(package_dir, dst))
            print(f"✅ {dst} をコピーしました")
        else:
            print(f"⚠️ {src} が見つかりません")
    
    # クイックスタートガイドを作成
    create_web_gui_quick_start_guide(package_dir, platform_name, executable_name)
    
    # Windows用のバッチファイルを作成
    if platform_name == "Windows":
        create_windows_batch_file(package_dir, executable_name)
    
    print(f"🎉 Web版GUIアプリケーションパッケージが作成されました: {package_dir}")

def create_web_gui_quick_start_guide(package_dir, platform_name, executable_name):
    """Web版GUIアプリケーション用のクイックスタートガイドを作成（プラットフォーム別）"""
    
    if platform_name == "Windows":
        guide_content = f"""# 🌐 Google Drive 画像ダウンローダー Web版 (Windows)

## 🚀 簡単な使い方

### 1. アプリケーションを起動
```cmd
{executable_name}
```
または、エクスプローラーで `{executable_name}` をダブルクリック

### 2. ブラウザでアクセス
アプリケーション起動後、自動でブラウザが開きます。
手動で開く場合は: http://localhost:8080

### 3. 設定を入力
- **スプレッドシートURL**: Google スプレッドシートのURLを入力
- **シート名**: 使用するシート名を入力（例: "第3弾"）
- **開始行**: 処理を開始する行番号（通常は2）
- **ダウンロード先**: 画像を保存するフォルダのパス（例: C:\\Users\\YourName\\Downloads）

### 4. 設定を保存（オプション）
「💾 設定保存」ボタンをクリックすると、次回から自動で読み込まれます。

## 🔧 トラブルシューティング

### ファイアウォールの警告が出る場合
Windows Defender やファイアウォールで警告が出た場合は「許可」を選択してください。

### ポート8080が使用中の場合
アプリケーションが自動的に別のポート（8081-8089）を試行します。

### ブラウザが開かない場合
手動でブラウザを開いて http://localhost:8080 にアクセスしてください。
"""
    else:
        guide_content = f"""# 🌐 Google Drive 画像ダウンローダー Web版

## 🚀 簡単な使い方

### 1. アプリケーションを起動
```bash
./{executable_name}
```

### 2. ブラウザでアクセス
アプリケーション起動後、自動でブラウザが開きます。
手動で開く場合は: http://localhost:8080

### 3. 設定を入力
- **スプレッドシートURL**: Google スプレッドシートのURLを入力
- **シート名**: 使用するシート名を入力（例: "第3弾"）
- **開始行**: 処理を開始する行番号（通常は2）
- **ダウンロード先**: 画像を保存するフォルダのパス

### 4. 設定を保存（オプション）
「💾 設定保存」ボタンをクリックすると、次回から自動で読み込まれます。
"""
    
    guide_path = os.path.join(package_dir, "QUICK_START_GUIDE.md")
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print(f"✅ クイックスタートガイドを作成しました: {guide_path}")

def create_windows_batch_file(package_dir, executable_name):
    """Windows用のバッチファイルを作成"""
    batch_content = f"""@echo off
echo 🌐 Google Drive 画像ダウンローダー Web版を起動しています...
echo.
echo ブラウザが自動で開きます。開かない場合は手動で http://localhost:8080 にアクセスしてください。
echo.
echo アプリケーションを停止するには、このウィンドウを閉じてください。
echo.
pause
{executable_name}
pause
"""
    
    batch_path = os.path.join(package_dir, "start_application.bat")
    with open(batch_path, 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    print(f"✅ Windows用バッチファイルを作成しました: {batch_path}")

def main():
    """メイン関数"""
    print("=" * 60)
    print("🌐 Google Drive 画像ダウンローダー Web版ビルダー")
    print("=" * 60)
    
    # 必要なファイルの存在確認
    required_files = ['simple_gui.py', '依頼.py', 'client_secret.json']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ 必要なファイルが見つかりません: {missing_files}")
        return False
    
    # ビルド実行
    if build_web_gui():
        print("=" * 60)
        print("🎉 Web版GUIアプリケーションのビルドが完了しました！")
        print("=" * 60)
        
        # 使用方法を表示
        current_platform = platform.system()
        if current_platform == "Windows":
            print("使用方法:")
            print("1. GoogleDriveDownloaderWeb_Package_Windows フォルダを開く")
            print("2. GoogleDriveDownloaderWeb.exe を実行")
            print("3. ブラウザで http://localhost:8080 にアクセス")
            print("4. Web画面で設定を入力して実行")
        else:
            print("使用方法:")
            print("1. GoogleDriveDownloaderWeb_Package フォルダを開く")
            print("2. ./GoogleDriveDownloaderWeb を実行")
            print("3. ブラウザで http://localhost:8080 にアクセス")
            print("4. Web画面で設定を入力して実行")
        print("=" * 60)
    else:
        print("❌ ビルドに失敗しました")

if __name__ == "__main__":
    main() 