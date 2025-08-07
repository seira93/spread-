#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
from PIL import Image, ImageDraw, ImageFont

def create_icon():
    """アイコンを作成"""
    # 64x64のアイコンを作成
    size = (64, 64)
    icon = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(icon)
    
    # 背景円
    draw.ellipse([4, 4, 60, 60], fill=(66, 133, 244, 255))
    
    # クラウドアイコン
    draw.ellipse([12, 20, 28, 36], fill=(255, 255, 255, 255))
    draw.ellipse([20, 16, 36, 32], fill=(255, 255, 255, 255))
    draw.ellipse([28, 12, 44, 28], fill=(255, 255, 255, 255))
    
    # ダウンロード矢印
    draw.polygon([(32, 40), (28, 44), (36, 44)], fill=(255, 255, 255, 255))
    draw.line([(32, 44), (32, 52)], fill=(255, 255, 255, 255), width=2)
    
    # 保存
    icon.save('icon.ico', format='ICO', sizes=[(64, 64), (32, 32), (16, 16)])
    icon.save('icon.png', format='PNG')
    
    print("✅ アイコンを作成しました")

def build_gui_app():
    """GUIアプリケーションをビルド"""
    print("🚀 GUIアプリケーションのビルドを開始します...")
    
    # アイコンを作成
    create_icon()
    
    # PyInstallerコマンドを構築
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',  # GUIアプリケーション
        '--name=GoogleDriveDownloaderGUI',
        '--icon=icon.ico',
        '--add-data=README.md:.',
        '--add-data=USAGE_GUIDE.md:.',
        '--exclude-module=backports',
        '--exclude-module=jaraco',
        '--exclude-module=pkg_resources',
        'gui_app.py'
    ]
    
    print(f"実行コマンド: {' '.join(cmd)}")
    
    # ビルド実行
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ GUIアプリケーションのビルドが完了しました！")
        
        # 配布用パッケージを作成
        create_gui_package()
        
    except subprocess.CalledProcessError as e:
        print(f"❌ ビルドエラー: {e}")
        print(f"エラー出力: {e.stderr}")
        return False
    
    return True

def create_gui_package():
    """GUIアプリケーション用の配布パッケージを作成"""
    package_dir = "GoogleDriveDownloaderGUI_Package"
    
    # 既存のパッケージディレクトリを削除
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    
    # パッケージディレクトリを作成
    os.makedirs(package_dir, exist_ok=True)
    
    # ファイルをコピー
    files_to_copy = [
        ('dist/GoogleDriveDownloaderGUI', 'GoogleDriveDownloaderGUI'),
        ('client_secret.json', 'client_secret.json'),
        ('README.md', 'README.md'),
        ('USAGE_GUIDE.md', 'USAGE_GUIDE.md'),
        ('config.json', 'config.json'),
        ('icon.png', 'icon.png')
    ]
    
    for src, dst in files_to_copy:
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(package_dir, dst))
            print(f"✅ {dst} をコピーしました")
        else:
            print(f"⚠️ {src} が見つかりません")
    
    # クイックスタートガイドを作成
    create_gui_quick_start_guide(package_dir)
    
    print(f"🎉 GUIアプリケーションパッケージが作成されました: {package_dir}")

def create_gui_quick_start_guide(package_dir):
    """GUIアプリケーション用のクイックスタートガイドを作成"""
    guide_content = """# 🖥️ Google Drive 画像ダウンローダー GUI版

## 🚀 簡単な使い方

### 1. アプリケーションを起動
```bash
./GoogleDriveDownloaderGUI
```

### 2. 設定を入力
- **スプレッドシートURL**: Google スプレッドシートのURLを入力
- **シート名**: 使用するシート名を入力（例: "第3弾"）
- **開始行**: 処理を開始する行番号（通常は2）
- **ダウンロード先**: 画像を保存するフォルダを選択

### 3. 設定を保存（オプション）
「💾 設定保存」ボタンをクリックすると、次回から自動で読み込まれます。

### 4. 実行開始
「🚀 実行開始」ボタンをクリックして処理を開始します。

## 📋 機能

- ✅ **GUI操作**: マウスクリックで簡単操作
- ✅ **設定保存**: 一度設定すれば次回から自動読み込み
- ✅ **リアルタイムログ**: 処理状況をリアルタイムで表示
- ✅ **プログレス表示**: 処理中の進捗を表示
- ✅ **エラーハンドリング**: 分かりやすいエラーメッセージ

## 🔧 トラブルシューティング

### よくある問題

1. **アプリケーションが起動しない**
   - macOSの場合: セキュリティ設定で「このまま開く」を選択
   - Windowsの場合: ウイルス対策ソフトの除外設定を確認

2. **認証エラー**
   - `client_secret.json`が正しく配置されているか確認
   - 初回実行時はGoogle認証が必要です

3. **設定が保存されない**
   - アプリケーションに書き込み権限があるか確認
   - ディスク容量を確認

## 📞 サポート

問題が発生した場合は、ログ表示エリアの内容を確認してください。
"""
    
    with open(os.path.join(package_dir, 'GUI_QUICK_START.md'), 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print("✅ GUIクイックスタートガイドを作成しました")

def main():
    """メイン関数"""
    print("=" * 60)
    print("🖥️ Google Drive 画像ダウンローダー GUI版ビルダー")
    print("=" * 60)
    
    # 必要なファイルの存在確認
    required_files = ['gui_app.py', '依頼.py', 'client_secret.json']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ 必要なファイルが見つかりません: {missing_files}")
        return False
    
    # ビルド実行
    success = build_gui_app()
    
    if success:
        print("=" * 60)
        print("🎉 GUIアプリケーションのビルドが完了しました！")
        print("=" * 60)
        print("使用方法:")
        print("1. GoogleDriveDownloaderGUI_Package フォルダを開く")
        print("2. GoogleDriveDownloaderGUI をダブルクリック")
        print("3. GUIで設定を入力して実行")
        print("=" * 60)
    else:
        print("❌ ビルドに失敗しました")
    
    return success

if __name__ == "__main__":
    main() 