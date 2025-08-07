import os
import re
import sys
import time
import logging
import threading
import requests
import argparse
from typing import Union

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# 使用スコープ
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly'
]

# スレッドローカルに Drive サービス保持
_thread_local = threading.local()

# トークンバケット方式で Drive API レート制御
RATE_LIMIT_MAX_DRIVE = 2000
token_bucket = RATE_LIMIT_MAX_DRIVE
last_refill = time.time()
rate_limit_lock = threading.Lock()

def check_drive_api_rate_limit():
    global token_bucket, last_refill
    with rate_limit_lock:
        now = time.time()
        if now - last_refill >= 60:
            logging.info("1分経過のため、10秒待機してトークンをリセットします。")
            time.sleep(10)
            token_bucket = RATE_LIMIT_MAX_DRIVE
            last_refill = time.time()
            now = last_refill

        elapsed = now - last_refill
        token_bucket = min(RATE_LIMIT_MAX_DRIVE, token_bucket + elapsed * (RATE_LIMIT_MAX_DRIVE/60))
        last_refill = now

        while token_bucket < 1:
            wait_time = (1 - token_bucket) * (60 / RATE_LIMIT_MAX_DRIVE)
            logging.info(f"トークン不足のため {wait_time:.2f}秒待機します。")
            time.sleep(wait_time)
            now = time.time()
            elapsed = now - last_refill
            token_bucket = min(RATE_LIMIT_MAX_DRIVE, token_bucket + elapsed * (RATE_LIMIT_MAX_DRIVE/60))
            last_refill = now

        token_bucket -= 1

def get_drive_service(creds):
    if not hasattr(_thread_local, 'drive'):
        _thread_local.drive = build('drive', 'v3', credentials=creds)
    return _thread_local.drive

def authenticate():
    """
    token.json のスコープ不整合で RefreshError が出たら自動的に削除して再認証します。
    """
    creds = None
    
    # 実行ファイルのディレクトリを取得
    if getattr(sys, 'frozen', False):
        # PyInstallerで作成された実行ファイルの場合
        base_path = os.path.dirname(sys.executable)
    else:
        # 通常のPythonスクリプトの場合
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    client_secret_path = os.path.join(base_path, 'client_secret.json')
    token_path = os.path.join(base_path, 'token.json')
    
    # client_secret.jsonファイルの存在確認
    # 実行ファイルのディレクトリを取得
    if getattr(sys, 'frozen', False):
        # PyInstallerで作成された実行ファイルの場合
        base_path = os.path.dirname(sys.executable)
    else:
        # 通常のPythonスクリプトの場合
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    client_secret_path = os.path.join(base_path, 'client_secret.json')
    token_path = os.path.join(base_path, 'token.json')
    
    if not os.path.exists(client_secret_path):
        print("=" * 60)
        print("❌ エラー: client_secret.jsonファイルが見つかりません")
        print("=" * 60)
        print("以下の手順でGoogle API認証ファイルを取得してください：")
        print()
        print("1. Google Cloud Consoleにアクセス:")
        print("   https://console.cloud.google.com/")
        print()
        print("2. プロジェクトを作成または選択")
        print()
        print("3. 以下のAPIを有効化:")
        print("   - Google Sheets API")
        print("   - Google Drive API")
        print()
        print("4. 認証情報を作成:")
        print("   - 「APIとサービス」→「認証情報」")
        print("   - 「認証情報を作成」→「OAuth 2.0クライアントID」")
        print("   - アプリケーションの種類: 「デスクトップアプリケーション」")
        print()
        print("5. JSONファイルをダウンロード")
        print("6. ダウンロードしたファイルを「client_secret.json」にリネーム")
        print("7. この実行ファイルと同じフォルダに配置")
        print()
        print("詳細な手順は README.md または QUICK_START_GUIDE.txt を参照してください。")
        print("=" * 60)
        return None, None
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    try:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
    except RefreshError:
        logging.warning("古いトークンのスコープ不整合検出。token.json を削除して再認証します。")
        os.remove(token_path)
        return authenticate()

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as f:
            f.write(creds.to_json())

    sheets_service = build('sheets', 'v4', credentials=creds)
    return sheets_service, creds

def extract_folder_id(url: str) -> Union[str, None]:
    for pattern in (r'/folders/([a-zA-Z0-9_-]+)', r'\?id=([a-zA-Z0-9_-]+)'):
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None

def extract_spreadsheet_id(url: str) -> Union[str, None]:
    """
    スプレッドシートURLからスプレッドシートIDを抽出する
    """
    # 様々なURL形式に対応
    patterns = [
        r'/spreadsheets/d/([a-zA-Z0-9_-]+)',  # 標準的なURL形式
        r'/d/([a-zA-Z0-9_-]+)',              # 短縮URL形式
        r'id=([a-zA-Z0-9_-]+)',              # クエリパラメータ形式
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def fetch_first_image_url(drive_service, folder_id: str) -> Union[str, None]:
    check_drive_api_rate_limit()
    resp = drive_service.files().list(
        q=f"'{folder_id}' in parents and mimeType contains 'image/' and trashed=false",
        fields="files(id,name)"
    ).execute()
    files = resp.get('files', [])
    if not files:
        return None
    files.sort(key=lambda f: f['name'])
    file_id = files[0]['id']
    return f"https://drive.google.com/uc?export=view&id={file_id}"

def search_folder_by_sku(drive_service, sku: str) -> Union[str, None]:
    """
    SKU名でGoogle Drive内のフォルダを検索し、フォルダURLを返す（高速化版）
    """
    check_drive_api_rate_limit()
    
    # SKU名でフォルダを検索（より効率的なクエリ）
    query = f"name='{sku}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    try:
        resp = drive_service.files().list(
            q=query,
            fields="files(id,name)",
            pageSize=1  # 最初の1件のみ取得
        ).execute()
        files = resp.get('files', [])
        
        if not files:
            return None
        
        folder_id = files[0]['id']
        folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
        return folder_url
    except Exception as e:
        logging.error(f"SKU '{sku}' の検索でエラー: {e}")
        return None

def update_sheet_with_urls(sheets_service, drive_service, spreadsheet_id: str, sheet_name: str, start_row: int = 2):
    """
    D列のSKUからフォルダURLを検索してA列に記載する（高速化版）
    """
    print("=" * 60)
    print("🚀 A列URL記載を高速化モードで開始します...")
    print("=" * 60)
    
    RANGE = f"{sheet_name}!A{start_row}:E"
    resp = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=RANGE
    ).execute()
    values = resp.get('values', [])
    
    # 処理対象の行を特定
    target_rows = []
    for idx, row in enumerate(values, start=start_row):
        # A列にURLが既に記載されている場合はスキップ
        if len(row) > 0 and row[0].strip():
            continue
        
        # D列のSKUを取得
        sku = row[3] if len(row) > 3 else ""
        if not sku:
            continue
        
        target_rows.append((idx, sku))
    
    if not target_rows:
        print("✅ 更新対象の行がありませんでした")
        return
    
    print(f"📊 処理対象: {len(target_rows)}行")
    
    # 並列処理でURL検索を高速化
    import concurrent.futures
    from functools import partial
    
    def search_sku_with_cache(sku, cache):
        if sku in cache:
            return cache[sku]
        result = search_folder_by_sku(drive_service, sku)
        cache[sku] = result
        return result
    
    # キャッシュを初期化
    sku_cache = {}
    updates = []
    processed_count = 0
    
    # バッチサイズを設定（API制限を考慮）
    BATCH_SIZE = 50
    
    for i in range(0, len(target_rows), BATCH_SIZE):
        batch = target_rows[i:i + BATCH_SIZE]
        
        # 並列処理でURL検索
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # 部分関数を作成
            search_func = partial(search_sku_with_cache, cache=sku_cache)
            # 並列実行
            future_to_sku = {executor.submit(search_func, sku): (idx, sku) for idx, sku in batch}
            
            for future in concurrent.futures.as_completed(future_to_sku):
                idx, sku = future_to_sku[future]
                try:
                    folder_url = future.result()
                    if folder_url:
                        updates.append({
                            'range': f"{sheet_name}!A{idx}",
                            'values': [[folder_url]]
                        })
                        processed_count += 1
                        if processed_count % 10 == 0:
                            print(f"⏳ 処理中... {processed_count}/{len(target_rows)}行完了")
                except Exception as e:
                    logging.error(f"Row {idx}: SKU '{sku}' の処理でエラー: {e}")
        
        # バッチごとに更新を実行
        if updates:
            try:
                body = {
                    'valueInputOption': 'RAW',
                    'data': updates
                }
                sheets_service.spreadsheets().values().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body=body
                ).execute()
                print(f"✅ バッチ更新完了: {len(updates)}行")
                updates = []  # 更新リストをリセット
            except Exception as e:
                logging.error(f"バッチ更新でエラー: {e}")
    
    print("=" * 60)
    print(f"🎉 A列URL記載が完了しました！")
    print(f"📈 処理結果: {processed_count}行のURLを記載")
    print("=" * 60)

def download_image(url: str, save_path: str):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    with open(save_path, 'wb') as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)
    logging.info(f"Downloaded: {save_path}")

def process_all_rows(sheets_service, creds, spreadsheet_id: str, sheet_name: str, start_row: int = 2):
    RANGE = f"{sheet_name}!A{start_row}:E"
    resp = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=RANGE
    ).execute()
    values = resp.get('values', [])

    drive_service = get_drive_service(creds)
    
    # ダウンロード先ディレクトリを取得（GUIで指定された場合）
    if 'DOWNLOAD_BASE_DIR' in globals():
        base_dir = DOWNLOAD_BASE_DIR
    else:
        base_dir = os.path.abspath("downloaded_images")

    for idx, row in enumerate(values, start=start_row):
        folder_url = row[0] if len(row) > 0 else ""
        save_name  = row[4] if len(row) > 4 else ""
        
        # A列にURLが記載されていない場合はスキップ
        if not folder_url:
            logging.warning(f"Row {idx}: A列にURLが記載されていません。スキップします。")
            continue
            
        if not save_name:
            logging.warning(f"Row {idx}: E列（保存名）が空です。スキップします。")
            continue

        save_path = os.path.join(base_dir, f"{save_name}.jpg")
        if os.path.exists(save_path):
            logging.info(f"Row {idx}: {save_name}.jpg already exists. Skipped.")
            continue

        folder_id = extract_folder_id(folder_url)
        if not folder_id:
            logging.warning(f"Row {idx}: Failed to extract folder ID from {folder_url}")
            continue

        image_url = fetch_first_image_url(drive_service, folder_id)
        if not image_url:
            logging.warning(f"Row {idx}: No images found in folder {folder_id}")
            continue

        try:
            download_image(image_url, save_path)
        except Exception as e:
            logging.error(f"Row {idx}: Download failed: {e}")

def main():
    # 設定ファイルの読み込み
    config_file = 'config.json'
    config = {}
    
    if os.path.exists(config_file):
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("✅ 設定ファイルを読み込みました")
        except Exception as e:
            print(f"⚠️ 設定ファイルの読み込みに失敗しました: {e}")
    
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description='Google Drive 画像ダウンローダー')
    parser.add_argument('--url', '-u', 
                       default=config.get('spreadsheet_url', "https://docs.google.com/spreadsheets/d/1GWc8wGc2ebjxjCXlZdmg97hLvyJUiqYhGMiLqTHMYq0"),
                       help='Google スプレッドシートのURL')
    parser.add_argument('--sheet', '-s', 
                       default=config.get('sheet_name', "第3弾"),
                       help='シート名')
    parser.add_argument('--start-row', '-r', 
                       type=int, default=config.get('start_row', 2),
                       help='開始行番号（デフォルト: 2）')
    parser.add_argument('--download-dir', '-d',
                       default=config.get('download_dir', os.path.abspath("downloaded_images")),
                       help='ダウンロード先ディレクトリ')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='対話式で設定を入力')
    parser.add_argument('--setup', action='store_true',
                       help='設定ファイルを作成')
    
    args = parser.parse_args()
    
    # 設定ファイル作成モード
    if args.setup:
        print("=" * 60)
        print("🔧 設定ファイル作成モード")
        print("=" * 60)
        
        config = {}
        
        # スプレッドシートURL
        url = input("Google スプレッドシートのURLを入力: ").strip()
        if url:
            config['spreadsheet_url'] = url
        
        # シート名
        sheet = input("シート名を入力（デフォルト: 第3弾）: ").strip()
        config['sheet_name'] = sheet if sheet else "第3弾"
        
        # 開始行
        start_row = input("開始行番号を入力（デフォルト: 2）: ").strip()
        config['start_row'] = int(start_row) if start_row.isdigit() else 2
        
        # ダウンロード先
        download_dir = input("ダウンロード先ディレクトリを入力（デフォルト: downloaded_images）: ").strip()
        config['download_dir'] = download_dir if download_dir else os.path.abspath("downloaded_images")
        
        # 設定を保存
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print("✅ 設定ファイルを作成しました: config.json")
            print("次回からは設定ファイルが自動で読み込まれます")
        except Exception as e:
            print(f"❌ 設定ファイルの作成に失敗しました: {e}")
        
        print("=" * 60)
        return
    
    # 対話式設定モード
    if args.interactive:
        print("=" * 60)
        print("🔧 対話式設定モード")
        print("=" * 60)
        
        # スプレッドシートURL
        current_url = args.url
        print(f"現在のスプレッドシートURL: {current_url}")
        new_url = input("新しいURLを入力（Enterで現在のまま）: ").strip()
        if new_url:
            args.url = new_url
        
        # シート名
        current_sheet = args.sheet
        print(f"現在のシート名: {current_sheet}")
        new_sheet = input("新しいシート名を入力（Enterで現在のまま）: ").strip()
        if new_sheet:
            args.sheet = new_sheet
        
        # 開始行
        current_row = args.start_row
        print(f"現在の開始行: {current_row}")
        new_row = input("新しい開始行を入力（Enterで現在のまま）: ").strip()
        if new_row.isdigit():
            args.start_row = int(new_row)
        
        # ダウンロード先
        current_dir = args.download_dir
        print(f"現在のダウンロード先: {current_dir}")
        new_dir = input("新しいダウンロード先を入力（Enterで現在のまま）: ").strip()
        if new_dir:
            args.download_dir = new_dir
        
        # 設定を保存するか確認
        save_config = input("設定をconfig.jsonに保存しますか？ (y/N): ").strip().lower()
        if save_config == 'y':
            try:
                config = {
                    'spreadsheet_url': args.url,
                    'sheet_name': args.sheet,
                    'start_row': args.start_row,
                    'download_dir': args.download_dir
                }
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                print("✅ 設定を保存しました")
            except Exception as e:
                print(f"❌ 設定の保存に失敗しました: {e}")
        
        print("=" * 60)
    
    # URLからスプレッドシートIDを抽出
    spreadsheet_id = extract_spreadsheet_id(args.url)
    if not spreadsheet_id:
        logging.error(f"スプレッドシートIDを抽出できませんでした: {args.url}")
        logging.error("正しいGoogle スプレッドシートのURLを指定してください。")
        return
    
    print("=" * 60)
    print("🚀 Google Drive 画像ダウンローダーを開始します")
    print("=" * 60)
    print(f"📊 スプレッドシートID: {spreadsheet_id}")
    print(f"📋 シート名: {args.sheet}")
    print(f"📈 開始行: {args.start_row}")
    print(f"📁 ダウンロード先: {args.download_dir}")
    print("=" * 60)
    
    logging.info(f"スプレッドシートID: {spreadsheet_id}")
    logging.info(f"シート名: {args.sheet}")
    logging.info(f"開始行: {args.start_row}")
    logging.info(f"ダウンロード先: {args.download_dir}")

    # 認証
    print("🔐 Google認証を開始します...")
    sheets_service, creds = authenticate()
    if sheets_service is None or creds is None:
        print("❌ 認証に失敗しました。")
        print("client_secret.jsonファイルが正しく配置されているか確認してください。")
        print("初回実行時はGoogle Cloud Consoleで認証情報を取得する必要があります。")
        return
    
    print("✅ Google認証が完了しました！")
    
    drive_service = get_drive_service(creds)
    
    # ダウンロード先ディレクトリを設定
    global DOWNLOAD_BASE_DIR
    DOWNLOAD_BASE_DIR = args.download_dir
    
    # ステップ1: D列のSKUからフォルダURLを検索してA列に記載
    logging.info("=== ステップ1: SKUからフォルダURLを検索してA列に記載 ===")
    update_sheet_with_urls(sheets_service, drive_service, spreadsheet_id, args.sheet, args.start_row)
    
    # ステップ2: 通常通りダウンロードを実行
    logging.info("=== ステップ2: 画像ダウンロードを開始 ===")
    process_all_rows(sheets_service, creds, spreadsheet_id, args.sheet, args.start_row)

if __name__ == "__main__":
    main()