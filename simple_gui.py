#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import threading
import webbrowser
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import time
import re
import logging
import requests
import gc
from typing import Union

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError

class SimpleGUIHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, app_instance=None, **kwargs):
        self.app_instance = app_instance
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """GETリクエストを処理"""
        try:
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                html = self.app_instance.get_html()
                self.wfile.write(html.encode('utf-8'))
            
            elif self.path == '/api/config':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                config = self.app_instance.get_config()
                self.wfile.write(json.dumps(config, ensure_ascii=False).encode('utf-8'))
            
            elif self.path.startswith('/api/run'):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                # クエリパラメータを取得
                parsed_url = urllib.parse.urlparse(self.path)
                query = urllib.parse.parse_qs(parsed_url.query)
                
                # 設定を更新
                config = {
                    'spreadsheet_url': query.get('url', [''])[0],
                    'sheet_name': query.get('sheet', [''])[0],
                    'start_row': int(query.get('start_row', ['2'])[0]),
                    'download_dir': query.get('download_dir', [''])[0],
                    'mode': query.get('mode', ['download'])[0]
                }
                
                # 設定を保存
                self.app_instance.save_config(config)
                
                # 実行を開始
                self.app_instance.start_execution(config)
                
                response = {'status': 'started'}
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
            elif self.path == '/api/logs':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                logs = self.app_instance.get_logs()
                self.wfile.write(json.dumps(logs, ensure_ascii=False).encode('utf-8'))
            
            elif self.path == '/api/stop':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                self.app_instance.stop_execution()
                response = {'status': 'stopped'}
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'404 Not Found')
        
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
    
    def do_POST(self):
        """POSTリクエストを処理"""
        try:
            if self.path == '/api/config':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                # POSTデータを読み取り
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                config = json.loads(post_data.decode('utf-8'))
                
                # 設定を保存
                self.app_instance.save_config(config)
                
                response = {'status': 'saved'}
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'404 Not Found')
        
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
    
    def do_OPTIONS(self):
        """OPTIONSリクエストを処理（CORS対応）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """ログメッセージを無効化"""
        pass

class SimpleGUI:
    def __init__(self):
        self.config_file = 'config.json'
        self.config = self.load_config()
        self.logs = []
        self.is_running = False
        self.server = None
        self.server_thread = None
        self.current_process = None  # 現在実行中のプロセス
        self.stop_requested = False  # 停止要求フラグ
        
        # Google API設定（image.pyと同じスコープ）
        self.SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # レート制御用
        self.RATE_LIMIT_MAX_DRIVE = 2000
        self.token_bucket = self.RATE_LIMIT_MAX_DRIVE
        self.last_refill = time.time()
        self.rate_limit_lock = threading.Lock()
        
        # 進捗管理用
        self.progress = 0
        self.total_rows = 1
        self.progress_lock = threading.Lock()
        self.processing_done = False
    
    def check_drive_api_rate_limit(self):
        """Drive APIのレート制御（image.pyと同じ方式）"""
        with self.rate_limit_lock:
            now = time.time()
            if now - self.last_refill >= 60:
                self.add_log("1分経過のため、10秒待機してレート使用率をリセットします。")
                time.sleep(10)
                self.token_bucket = self.RATE_LIMIT_MAX_DRIVE
                self.last_refill = time.time()
                now = self.last_refill

            # 補充：1分間にRATE_LIMIT_MAX_DRIVE個補充される（1秒あたり RATE_LIMIT_MAX_DRIVE/60 個）
            elapsed = now - self.last_refill
            refill = elapsed * (self.RATE_LIMIT_MAX_DRIVE / 60)
            self.token_bucket = min(self.RATE_LIMIT_MAX_DRIVE, self.token_bucket + refill)
            self.last_refill = now

            while self.token_bucket < 1:
                wait_time = (1 - self.token_bucket) * (60 / self.RATE_LIMIT_MAX_DRIVE)
                self.add_log(f"トークン不足のため、{wait_time:.2f}秒待機します。")
                time.sleep(wait_time)
                now = time.time()
                elapsed = now - self.last_refill
                self.token_bucket = min(self.RATE_LIMIT_MAX_DRIVE, self.token_bucket + elapsed * (self.RATE_LIMIT_MAX_DRIVE / 60))
                self.last_refill = now

            self.token_bucket -= 1
            usage_percentage = (1 - self.token_bucket / self.RATE_LIMIT_MAX_DRIVE) * 100
            self.add_log(f"ドライブAPI使用率: {usage_percentage:.2f}% (残トークン: {self.token_bucket:.2f})")
    
    def authenticate(self):
        """Google API認証（image.pyと同じ方式）"""
        self.add_log("Google APIs の認証を開始します。")
        creds = None
        
        # 実行ファイルのディレクトリを取得
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # image.pyと同じファイル名を使用
        client_secret_path = os.path.join(base_path, 'client_secret_595218989803-l6aqsgjkiu5b0smq0lsd1t02ulpt73uo.apps.googleusercontent.com.json')
        token_path = os.path.join(base_path, 'token.json')
        
        if not os.path.exists(client_secret_path):
            # 通常のclient_secret.jsonも試す
            client_secret_path = os.path.join(base_path, 'client_secret.json')
            if not os.path.exists(client_secret_path):
                self.add_log("=" * 60)
                self.add_log("❌ エラー: client_secret.jsonファイルが見つかりません")
                self.add_log("=" * 60)
                self.add_log("以下の手順でGoogle API認証ファイルを取得してください：")
                self.add_log("1. Google Cloud Consoleにアクセス: https://console.cloud.com/")
                self.add_log("2. プロジェクトを作成または選択")
                self.add_log("3. 以下のAPIを有効化:")
                self.add_log("   - Google Sheets API")
                self.add_log("   - Google Drive API")
                self.add_log("4. 認証情報を作成:")
                self.add_log("   - 「APIとサービス」→「認証情報」")
                self.add_log("   - 「認証情報を作成」→「OAuth 2.0クライアントID」")
                self.add_log("   - アプリケーションの種類: 「デスクトップアプリケーション」")
                self.add_log("5. JSONファイルをダウンロード")
                self.add_log("6. ダウンロードしたファイルを「client_secret.json」にリネーム")
                self.add_log("7. この実行ファイルと同じフォルダに配置")
                self.add_log("=" * 60)
                return None, None
        
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
                self.add_log("token.json から認証情報を読み込みました。")
            except Exception as e:
                self.add_log(f"古いトークンのスコープ不整合検出。token.json を削除して再認証します。")
                os.remove(token_path)
                creds = None
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self.add_log("認証情報をリフレッシュしました。")
                except Exception as e:
                    self.add_log(f"認証情報のリフレッシュに失敗しました: {e}")
                    creds = None
            
            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                    self.add_log("ブラウザ認証が完了しました。")
                    with open(token_path, 'w') as f:
                        f.write(creds.to_json())
                    self.add_log("新しい token.json を保存しました。")
                except Exception as e:
                    self.add_log(f"認証エラー: {e}")
                    return None, None
        
        sheets_service = build('sheets', 'v4', credentials=creds)
        self.add_log("Google Sheets および Drive API の認証が完了しました。")
        return sheets_service, creds
    
    def extract_spreadsheet_id(self, url: str) -> Union[str, None]:
        """スプレッドシートURLからIDを抽出"""
        pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    def search_folder_by_sku(self, drive_service, sku: str) -> Union[str, None]:
        """SKU名でフォルダを検索"""
        self.check_drive_api_rate_limit()
        query = f"name='{sku}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        try:
            resp = drive_service.files().list(
                q=query,
                fields="files(id,name)",
                pageSize=1
            ).execute()
            files = resp.get('files', [])
            if not files:
                return None
            folder_id = files[0]['id']
            folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
            return folder_url
        except Exception as e:
            self.add_log(f"SKU '{sku}' の検索でエラー: {e}")
            return None
    
    def update_sheet_with_urls(self, sheets_service, drive_service, spreadsheet_id: str, sheet_name: str, start_row: int = 2):
        """A列にURLを記載"""
        self.add_log("=" * 60)
        self.add_log("🚀 A列URL記載を高速化モードで開始します...")
        self.add_log("=" * 60)
        
        RANGE = f"{sheet_name}!A{start_row}:E"
        resp = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=RANGE).execute()
        values = resp.get('values', [])
        
        target_rows = []
        for idx, row in enumerate(values, start=start_row):
            if len(row) > 0 and row[0].strip():
                continue
            sku = row[3] if len(row) > 3 else ""
            if not sku:
                continue
            target_rows.append((idx, sku))
        
        if not target_rows:
            self.add_log("✅ 更新対象の行がありませんでした")
            return
        
        self.add_log(f"📊 処理対象: {len(target_rows)}行")
        
        # キャッシュを使用した高速処理
        sku_cache = {}
        updates = []
        processed_count = 0
        BATCH_SIZE = 50
        
        for i in range(0, len(target_rows), BATCH_SIZE):
            # 停止要求チェック
            if self.stop_requested:
                self.add_log("🛑 A列URL記載が停止されました")
                return
            
            batch = target_rows[i:i + BATCH_SIZE]
            
            for idx, sku in batch:
                if sku in sku_cache:
                    folder_url = sku_cache[sku]
                else:
                    folder_url = self.search_folder_by_sku(drive_service, sku)
                    sku_cache[sku] = folder_url
                
                if folder_url:
                    updates.append({'range': f"{sheet_name}!A{idx}", 'values': [[folder_url]]})
                    processed_count += 1
                    if processed_count % 10 == 0:
                        self.add_log(f"⏳ 処理中... {processed_count}/{len(target_rows)}行完了")
            
            if updates:
                try:
                    body = {'valueInputOption': 'RAW', 'data': updates}
                    sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
                    self.add_log(f"✅ バッチ更新完了: {len(updates)}行")
                    updates = []
                except Exception as e:
                    self.add_log(f"バッチ更新でエラー: {e}")
        
        self.add_log("=" * 60)
        self.add_log(f"🎉 A列URL記載が完了しました！")
        self.add_log(f"📈 処理結果: {processed_count}行のURLを記載")
        self.add_log("=" * 60)
    
    def extract_folder_id(self, url: str) -> Union[str, None]:
        """フォルダURLからIDを抽出"""
        for pattern in (r'/folders/([a-zA-Z0-9_-]+)', r'\?id=([a-zA-Z0-9_-]+)'):
            m = re.search(pattern, url)
            if m:
                return m.group(1)
        return None
    
    def fetch_first_image_url(self, drive_service, folder_id: str) -> Union[str, None]:
        """フォルダ内の最初の画像URLを取得"""
        self.check_drive_api_rate_limit()
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
    
    def download_image(self, url: str, save_path: str):
        """画像をダウンロード"""
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        self.add_log(f"✅ ダウンロード完了: {save_path}")
    
    def process_all_rows(self, sheets_service, drive_service, spreadsheet_id: str, sheet_name: str, start_row: int = 2, download_dir: str = None):
        """全行を処理して画像をダウンロード"""
        self.add_log("=" * 60)
        self.add_log("🖼️ 画像ダウンロードを開始します...")
        self.add_log("=" * 60)
        
        RANGE = f"{sheet_name}!A{start_row}:E"
        resp = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=RANGE
        ).execute()
        values = resp.get('values', [])
        
        if not download_dir:
            download_dir = os.path.abspath("downloaded_images")
        
        self.add_log(f"📁 ダウンロード先: {download_dir}")
        
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        for idx, row in enumerate(values, start=start_row):
            # 停止要求チェック
            if self.stop_requested:
                self.add_log("🛑 画像ダウンロードが停止されました")
                return
            
            folder_url = row[0] if len(row) > 0 else ""
            save_name = row[4] if len(row) > 4 else ""
            
            # A列にURLが記載されていない場合はスキップ
            if not folder_url:
                self.add_log(f"⚠️ Row {idx}: A列にURLが記載されていません。スキップします。")
                skipped_count += 1
                continue
                
            if not save_name:
                self.add_log(f"⚠️ Row {idx}: E列（保存名）が空です。スキップします。")
                skipped_count += 1
                continue

            save_path = os.path.join(download_dir, f"{save_name}.jpg")
            if os.path.exists(save_path):
                self.add_log(f"⏭️ Row {idx}: {save_name}.jpg は既に存在します。スキップします。")
                skipped_count += 1
                continue

            folder_id = self.extract_folder_id(folder_url)
            if not folder_id:
                self.add_log(f"❌ Row {idx}: フォルダIDの抽出に失敗: {folder_url}")
                error_count += 1
                continue

            image_url = self.fetch_first_image_url(drive_service, folder_id)
            if not image_url:
                self.add_log(f"❌ Row {idx}: フォルダ {folder_id} に画像が見つかりません")
                error_count += 1
                continue

            try:
                self.download_image(image_url, save_path)
                processed_count += 1
                self.add_log(f"✅ Row {idx}: {save_name}.jpg をダウンロードしました")
            except Exception as e:
                self.add_log(f"❌ Row {idx}: ダウンロード失敗: {e}")
                error_count += 1
        
        self.add_log("=" * 60)
        self.add_log(f"🎉 画像ダウンロードが完了しました！")
        self.add_log(f"📈 処理結果: {processed_count}個ダウンロード, {skipped_count}個スキップ, {error_count}個エラー")
        self.add_log("=" * 60)
    
    def get_folder_link_by_sku(self, drive_service, sku):
        """SKUに対応するGoogle Driveフォルダを検索し、フォルダリンクを返す"""
        self.check_drive_api_rate_limit()
        query = f"name = '{sku}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        self.add_log(f"🔍 SKU '{sku}' の検索を開始...")
        try:
            response = drive_service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()
        except Exception as e:
            self.add_log(f"❌ SKU '{sku}' の検索でエラー: {e}")
            return None
        
        files = response.get('files', [])
        if not files:
            self.add_log(f"⚠️ SKU '{sku}' に対応するフォルダが見つかりませんでした")
            return None
        
        folder_id = files[0].get('id')
        folder_link = f"https://drive.google.com/drive/folders/{folder_id}"
        self.add_log(f"✅ SKU '{sku}' のフォルダリンクを取得: {folder_link}")
        return folder_link
    
    def get_first_image_url_from_folder(self, drive_service, folder_id):
        """フォルダ内の最初の画像URLを取得"""
        self.check_drive_api_rate_limit()
        query = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed = false"
        try:
            response = drive_service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()
        except Exception as e:
            self.add_log(f"❌ フォルダ {folder_id} の画像検索でエラー: {e}")
            return None
        
        files = response.get('files', [])
        if not files:
            self.add_log(f"⚠️ フォルダ {folder_id} 内に画像が見つかりませんでした")
            return None
        
        files.sort(key=lambda f: f.get('name', ''))
        first_file = files[0]
        file_id = first_file.get('id')
        image_url = f"https://drive.google.com/uc?export=view&id={file_id}"
        self.add_log(f"✅ フォルダ {folder_id} の最初の画像URLを取得: {image_url}")
        return image_url
    
    def process_single_row_image_formula(self, row_index, sku, drive_service):
        """1行分のIMAGE関数処理（image.pyと同じ方式）"""
        try:
            # レート制御
            self.check_drive_api_rate_limit()
            
            # SKUに対応するフォルダを検索
            folder_link = self.get_folder_link_by_sku(drive_service, sku)
            
            if folder_link:
                # フォルダから最初の画像URLを取得
                folder_id = self.extract_folder_id(folder_link)
                if folder_id:
                    image_url = self.get_first_image_url_from_folder(drive_service, folder_id)
                    
                    if image_url:
                        # IMAGE関数を生成
                        image_formula = f'=IMAGE("{image_url}")'
                        self.add_log(f"✅ 行{row_index}: IMAGE関数とフォルダリンクを生成完了")
                        return image_formula, folder_link, sku
                    else:
                        self.add_log(f"⚠️ 行{row_index}: 画像が見つかりません")
                else:
                    self.add_log(f"⚠️ 行{row_index}: フォルダIDの抽出に失敗")
            else:
                self.add_log(f"⚠️ 行{row_index}: SKU '{sku}' に対応するフォルダが見つかりません")
            
            return "", "", sku
            
        except Exception as e:
            self.add_log(f"❌ 行{row_index}の処理でエラー: {e}")
            return "", "", sku
    
    def process_sheet_image_formula(self, sheets_service, drive_service, spreadsheet_id, sheet_name, start_row=2):
        """IMAGE関数生成モードのメイン処理（image.pyと同じ方式）"""
        try:
            self.add_log("🖼️ IMAGE関数生成モードで実行します")
            
            # シートのデータを取得
            range_name = f"{sheet_name}!A:Z"
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                self.add_log("❌ シートにデータが見つかりません")
                return
            
            # 処理対象の行を特定（C列のSKUを確認）
            target_rows = []
            for i, row in enumerate(values, 1):
                if i < start_row:
                    continue
                if len(row) >= 3 and row[2]:  # C列（インデックス2）にSKUがある
                    target_rows.append((i, row[2]))
            
            if not target_rows:
                self.add_log("❌ 処理対象のSKUが見つかりません")
                return
            
            self.add_log(f"📊 処理対象: {len(target_rows)}行")
            
            # 処理カウンター
            processed_count = 0
            
            # 順次処理でIMAGE関数とフォルダリンクを生成（image.pyと同じ方式）
            batch_size = 10  # メモリ使用量を削減するため小さなバッチサイズ
            current_batch = []
            
            for row_index, sku in target_rows:
                if self.stop_requested:
                    self.add_log("🛑 IMAGE関数生成が停止されました")
                    return
                
                try:
                    self.add_log(f"📝 行{row_index} (SKU: {sku}) を処理中...")
                    
                    # レート制御
                    self.check_drive_api_rate_limit()
                    
                    # SKUに対応するフォルダを検索
                    folder_link = self.get_folder_link_by_sku(drive_service, sku)
                    
                    if folder_link:
                        # フォルダから最初の画像URLを取得
                        folder_id = self.extract_folder_id(folder_link)
                        if folder_id:
                            image_url = self.get_first_image_url_from_folder(drive_service, folder_id)
                            
                            if image_url:
                                # IMAGE関数を生成
                                image_formula = f'=IMAGE("{image_url}")'
                                
                                # バッチに追加
                                current_batch.append({
                                    'range': f'{sheet_name}!A{row_index}',
                                    'values': [[image_formula]]
                                })
                                current_batch.append({
                                    'range': f'{sheet_name}!B{row_index}',
                                    'values': [[folder_link]]
                                })
                                
                                processed_count += 1
                                self.add_log(f"✅ 行{row_index}: IMAGE関数とフォルダリンクを生成完了")
                            else:
                                self.add_log(f"⚠️ 行{row_index}: 画像が見つかりません")
                        else:
                            self.add_log(f"⚠️ 行{row_index}: フォルダIDの抽出に失敗")
                    else:
                        self.add_log(f"⚠️ 行{row_index}: SKU '{sku}' に対応するフォルダが見つかりません")
                    
                    # バッチサイズに達したら更新を実行
                    if len(current_batch) >= batch_size * 2:  # A列とB列の2つずつ
                        self.add_log(f"📝 バッチ更新を実行中... ({len(current_batch)}個のセル)")
                        batch_update_body = {
                            'valueInputOption': 'USER_ENTERED',
                            'data': current_batch
                        }
                        
                        try:
                            sheets_service.spreadsheets().values().batchUpdate(
                                spreadsheetId=spreadsheet_id,
                                body=batch_update_body
                            ).execute()
                            self.add_log(f"✅ バッチ更新完了: {len(current_batch)}個のセル")
                        except Exception as e:
                            self.add_log(f"❌ バッチ更新でエラー: {e}")
                        
                        current_batch = []  # バッチをリセット
                        gc.collect()  # メモリをクリア
                    
                    # 進捗表示
                    progress = (processed_count / len(target_rows)) * 100
                    self.add_log(f"📈 進捗: {processed_count}/{len(target_rows)} ({progress:.1f}%)")
                    
                except Exception as e:
                    self.add_log(f"❌ 行{row_index}の処理でエラー: {e}")
            
            # 残りのバッチを更新
            if current_batch:
                self.add_log(f"📝 最終バッチ更新を実行中... ({len(current_batch)}個のセル)")
                batch_update_body = {
                    'valueInputOption': 'USER_ENTERED',
                    'data': current_batch
                }
                
                try:
                    sheets_service.spreadsheets().values().batchUpdate(
                        spreadsheetId=spreadsheet_id,
                        body=batch_update_body
                    ).execute()
                    self.add_log(f"✅ 最終バッチ更新完了: {len(current_batch)}個のセル")
                except Exception as e:
                    self.add_log(f"❌ 最終バッチ更新でエラー: {e}")
            
            gc.collect()  # 最終的なメモリクリア
            self.add_log(f"✅ IMAGE関数生成が完了しました！処理された行数: {processed_count}")
            
        except Exception as e:
            self.add_log(f"❌ IMAGE関数生成エラー: {e}")
            import traceback
            self.add_log(f"📋 エラー詳細: {traceback.format_exc()}")
    
    def load_config(self):
        """設定ファイルを読み込む"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 既存の設定でダウンロード先が固定パスやdownloaded_imagesの場合は更新
                    if 'download_dir' in config:
                        old_path = config['download_dir']
                        if '/Users/yamadaseira/' in old_path or 'downloaded_images' in old_path:
                            home_dir = os.path.expanduser("~")
                            config['download_dir'] = os.path.join(home_dir, "Downloads")
                    return config
            except Exception as e:
                print(f"設定ファイルの読み込みに失敗: {e}")
        return {}
    
    def save_config(self, config):
        """設定を保存する"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.add_log("✅ 設定を保存しました")
        except Exception as e:
            self.add_log(f"❌ 設定の保存に失敗しました: {e}")
    
    def get_config(self):
        """現在の設定を取得"""
        # 現在のPCのユーザーホームディレクトリを動的に取得
        home_dir = os.path.expanduser("~")
        
        # プラットフォーム別のデフォルトダウンロードディレクトリ
        if os.name == 'nt':  # Windows
            default_download_dir = os.path.join(home_dir, "Downloads")
        else:  # macOS/Linux
            default_download_dir = os.path.join(home_dir, "Downloads")
        
        # ダウンロードフォルダが存在しない場合は作成
        if not os.path.exists(default_download_dir):
            try:
                os.makedirs(default_download_dir, exist_ok=True)
            except:
                # 作成できない場合は現在のディレクトリ
                default_download_dir = os.path.abspath("Downloads")
        
        return {
            'spreadsheet_url': self.config.get('spreadsheet_url', 
                                              "https://docs.google.com/spreadsheets/d/1GWc8wGc2ebjxjCXlZdmg97hLvyJUiqYhGMiLqTHMYq0"),
            'sheet_name': self.config.get('sheet_name', "第3弾"),
            'start_row': self.config.get('start_row', 2),
            'download_dir': self.config.get('download_dir', default_download_dir),
            'mode': self.config.get('mode', 'download')  # 'download' または 'image_formula'
        }
    
    def add_log(self, message):
        """ログを追加"""
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        # ログが多すぎる場合は古いものを削除
        if len(self.logs) > 100:
            self.logs = self.logs[-50:]
    
    def get_logs(self):
        """ログを取得"""
        return self.logs
    
    def start_execution(self, config):
        """実行を開始"""
        if self.is_running:
            self.add_log("⚠️ 既に実行中です")
            return
        
        self.is_running = True
        self.stop_requested = False
        self.add_log("🚀 Google Drive 画像ダウンローダーを開始します...")
        
        # 別スレッドで実行
        thread = threading.Thread(target=self.run_downloader_thread, args=(config,))
        thread.daemon = True
        thread.start()
    
    def stop_execution(self):
        """実行を停止"""
        if not self.is_running:
            self.add_log("⚠️ 実行中ではありません")
            return
        
        self.stop_requested = True
        self.add_log("🛑 停止要求を受け付けました。処理を安全に終了します...")
        
        # 現在のプロセスを停止
        if self.current_process:
            try:
                self.current_process.terminate()
                self.add_log("📋 プロセスを停止しました")
            except Exception as e:
                self.add_log(f"❌ プロセス停止エラー: {e}")
        
        self.is_running = False
        self.current_process = None
    
    def run_downloader_thread(self, config):
        """ダウンローダーを別スレッドで実行"""
        try:
            # 停止要求チェック
            if self.stop_requested:
                self.add_log("🛑 処理が停止されました")
                return
            
            # 実行ファイルのディレクトリを取得
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            self.add_log(f"📁 作業ディレクトリ: {base_path}")
            self.add_log(f"📁 現在のディレクトリ: {os.getcwd()}")
            
            # 必要なファイルの存在確認
            required_files = ['request.py', 'client_secret.json']
            for file in required_files:
                file_path = os.path.join(base_path, file)
                if os.path.exists(file_path):
                    self.add_log(f"✅ {file} が見つかりました")
                else:
                    self.add_log(f"❌ {file} が見つかりません: {file_path}")
                    return
            
            # 停止要求チェック
            if self.stop_requested:
                self.add_log("🛑 処理が停止されました")
                return
            
            # Google API認証
            self.add_log("🔐 Google API認証を開始します...")
            sheets_service, creds = self.authenticate()
            
            if not sheets_service or not creds:
                self.add_log("❌ 認証に失敗しました")
                return
            
            self.add_log("✅ Google API認証が完了しました")
            
            # 停止要求チェック
            if self.stop_requested:
                self.add_log("🛑 処理が停止されました")
                return
            
            # スプレッドシートIDを抽出
            spreadsheet_id = self.extract_spreadsheet_id(config['spreadsheet_url'])
            if not spreadsheet_id:
                self.add_log("❌ スプレッドシートIDの抽出に失敗しました")
                return
            
            self.add_log(f"📊 スプレッドシートID: {spreadsheet_id}")
            self.add_log(f"📋 シート名: {config['sheet_name']}")
            self.add_log(f"📈 開始行: {config['start_row']}")
            self.add_log(f"📁 ダウンロード先: {config['download_dir']}")
            
            # Driveサービスを構築
            drive_service = build('drive', 'v3', credentials=creds)
            
            # 停止要求チェック
            if self.stop_requested:
                self.add_log("🛑 処理が停止されました")
                return
            
            # モードに応じて処理を実行
            mode = config.get('mode', 'download')
            self.add_log(f"🎯 実行モード: {mode}")
            
            if mode == 'image_formula':
                # IMAGE関数生成モード
                self.add_log("🖼️ IMAGE関数生成モードで実行します")
                self.process_sheet_image_formula(sheets_service, drive_service, spreadsheet_id, config['sheet_name'], config['start_row'])
            else:
                # 画像ダウンロードモード（デフォルト）
                self.add_log("📥 画像ダウンロードモードで実行します")
                # A列にURLを記載
                self.update_sheet_with_urls(sheets_service, drive_service, spreadsheet_id, config['sheet_name'], config['start_row'])
                
                # 停止要求チェック
                if self.stop_requested:
                    self.add_log("🛑 処理が停止されました")
                    return
                
                # 画像ダウンロードを実行
                self.process_all_rows(sheets_service, drive_service, spreadsheet_id, config['sheet_name'], config['start_row'], config['download_dir'])
            
            if not self.stop_requested:
                self.add_log("🎉 処理が正常に完了しました！")
                
        except Exception as e:
            self.add_log(f"❌ 実行エラー: {e}")
            import traceback
            self.add_log(f"📋 エラー詳細: {traceback.format_exc()}")
        finally:
            self.is_running = False
    
    def get_html(self):
        """HTMLページを生成"""
        config = self.get_config()
        
        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Drive 画像ダウンローダー</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .content {{
            padding: 30px;
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        label {{
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #333;
        }}
        input[type="text"], input[type="number"] {{
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            box-sizing: border-box;
        }}
        input[type="text"]:focus, input[type="number"]:focus {{
            border-color: #667eea;
            outline: none;
        }}
        .button {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 5px;
            transition: transform 0.2s;
        }}
        .button:hover {{
            transform: translateY(-2px);
        }}
        .button:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
        }}
        .logs {{
            background: #f5f5f5;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            height: 300px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            margin-top: 20px;
        }}
        .status {{
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-weight: bold;
        }}
        .status.running {{
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        .status.stopped {{
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Google Drive 画像ダウンローダー</h1>
            <p>簡単なGUIで画像ダウンロードを実行</p>
        </div>
        
        <div class="content">
            <form id="configForm">
                <div class="form-group">
                    <label for="url">スプレッドシートURL:</label>
                    <input type="text" id="url" name="url" value="{config['spreadsheet_url']}" required>
                </div>
                
                <div class="form-group">
                    <label for="sheet">シート名:</label>
                    <input type="text" id="sheet" name="sheet" value="{config['sheet_name']}" required>
                </div>
                
                <div class="form-group">
                    <label for="start_row">開始行:</label>
                    <input type="number" id="start_row" name="start_row" value="{config['start_row']}" min="1" required>
                </div>
                
                <div class="form-group">
                    <label for="download_dir">ダウンロード先:</label>
                    <input type="text" id="download_dir" name="download_dir" value="{config['download_dir']}" required>
                </div>
                
                <div class="form-group">
                    <label for="mode">実行モード:</label>
                    <select id="mode" name="mode" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 5px; font-size: 14px;">
                        <option value="download" {'selected' if config.get('mode', 'download') == 'download' else ''}>📥 画像ダウンロードモード</option>
                        <option value="image_formula" {'selected' if config.get('mode', 'download') == 'image_formula' else ''}>🖼️ IMAGE関数生成モード</option>
                    </select>
                    <small style="color: #666; font-size: 12px;">
                        📥 画像ダウンロード: A列にURL記載 → 画像をダウンロード<br>
                        🖼️ IMAGE関数生成: C列のSKUからA列にIMAGE関数、B列にフォルダリンクを生成
                    </small>
                </div>
                
                <div style="text-align: center; margin: 20px 0;">
                    <button type="button" class="button" onclick="saveConfig()">💾 設定保存</button>
                    <button type="button" class="button" onclick="runDownloader()" id="runBtn">🚀 実行開始</button>
                    <button type="button" class="button" onclick="stopDownloader()" id="stopBtn" style="display: none; background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);">🛑 実行停止</button>
                    <button type="button" class="button" onclick="resetConfig()">🔄 リセット</button>
                </div>
            </form>
            
            <div id="status" class="status stopped">
                ⏹️ 停止中
            </div>
            
            <div class="logs" id="logs">
                <div>ログがここに表示されます...</div>
            </div>
        </div>
    </div>
    
    <script>
        let isRunning = false;
        
        function saveConfig() {{
            const config = {{
                spreadsheet_url: document.getElementById('url').value,
                sheet_name: document.getElementById('sheet').value,
                start_row: parseInt(document.getElementById('start_row').value),
                download_dir: document.getElementById('download_dir').value,
                mode: document.getElementById('mode').value
            }};
            
            fetch('/api/config', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify(config)
            }}).then(response => response.json())
            .then(data => {{
                if (data.status === 'saved') {{
                    alert('設定を保存しました');
                }}
            }});
        }}
        
        function runDownloader() {{
            if (isRunning) {{
                alert('既に実行中です');
                return;
            }}
            
            const url = document.getElementById('url').value;
            const sheet = document.getElementById('sheet').value;
            const start_row = document.getElementById('start_row').value;
            const download_dir = document.getElementById('download_dir').value;
            const mode = document.getElementById('mode').value;
            
            if (!url || !sheet || !start_row || !download_dir) {{
                alert('すべての項目を入力してください');
                return;
            }}
            
            const modeText = mode === 'image_formula' ? '🖼️ IMAGE関数生成モード' : '📥 画像ダウンロードモード';
            // 実行前の確認
            const confirmMessage = `以下の設定で実行しますか？\\n\\nスプレッドシートURL: ${{url}}\\nシート名: ${{sheet}}\\n開始行: ${{start_row}}\\nダウンロード先: ${{download_dir}}\\n実行モード: ${{modeText}}\\n\\n※ 実行中は停止ボタンで安全に停止できます`;
            
            if (!confirm(confirmMessage)) {{
                return;
            }}
            
            isRunning = true;
            document.getElementById('runBtn').disabled = true;
            document.getElementById('runBtn').style.display = 'none';
            document.getElementById('stopBtn').style.display = 'inline-block';
            document.getElementById('status').className = 'status running';
            document.getElementById('status').innerHTML = '🔄 実行中...';
            
            fetch(`/api/run?url=${{encodeURIComponent(url)}}&sheet=${{encodeURIComponent(sheet)}}&start_row=${{start_row}}&download_dir=${{encodeURIComponent(download_dir)}}&mode=${{encodeURIComponent(mode)}}`)
            .then(response => {{
                if (!response.ok) {{
                    throw new Error(`HTTP error! status: ${{response.status}}`);
                }}
                return response.json();
            }})
            .then(data => {{
                if (data.status === 'started') {{
                    startLogPolling();
                }}
            }})
            .catch(error => {{
                console.error('実行エラー:', error);
                alert('実行に失敗しました: ' + error.message);
                isRunning = false;
                document.getElementById('runBtn').disabled = false;
                document.getElementById('runBtn').style.display = 'inline-block';
                document.getElementById('stopBtn').style.display = 'none';
                document.getElementById('status').className = 'status stopped';
                document.getElementById('status').innerHTML = '⏹️ 停止中';
            }});
        }}
        
        function stopDownloader() {{
            if (!isRunning) {{
                alert('実行中ではありません');
                return;
            }}
            
            if (!confirm('実行を停止しますか？\\n\\n※ 現在の処理は安全に終了されます')) {{
                return;
            }}
            
            fetch('/api/stop')
            .then(response => {{
                if (!response.ok) {{
                    throw new Error(`HTTP error! status: ${{response.status}}`);
                }}
                return response.json();
            }})
            .then(data => {{
                if (data.status === 'stopped') {{
                    isRunning = false;
                    document.getElementById('runBtn').disabled = false;
                    document.getElementById('runBtn').style.display = 'inline-block';
                    document.getElementById('stopBtn').style.display = 'none';
                    document.getElementById('status').className = 'status stopped';
                    document.getElementById('status').innerHTML = '⏹️ 停止中';
                }}
            }})
            .catch(error => {{
                console.error('停止エラー:', error);
                alert('停止に失敗しました: ' + error.message);
            }});
        }}
        
        function resetConfig() {{
            if (confirm('設定をリセットしますか？')) {{
                document.getElementById('url').value = 'https://docs.google.com/spreadsheets/d/1GWc8wGc2ebjxjCXlZdmg97hLvyJUiqYhGMiLqTHMYq0';
                document.getElementById('sheet').value = '第3弾';
                document.getElementById('start_row').value = '2';
                // 現在のPCのダウンロードフォルダを動的に設定
                const homeDir = '{os.path.expanduser("~")}';
                document.getElementById('download_dir').value = homeDir + '/Downloads';
            }}
        }}
        
        function startLogPolling() {{
            setInterval(() => {{
                fetch('/api/logs')
                .then(response => {{
                    if (!response.ok) {{
                        throw new Error(`HTTP error! status: ${{response.status}}`);
                    }}
                    return response.json();
                }})
                .then(logs => {{
                    const logsDiv = document.getElementById('logs');
                    logsDiv.innerHTML = logs.map(log => `<div>${{log}}</div>`).join('');
                    logsDiv.scrollTop = logsDiv.scrollHeight;
                    
                    // 実行が完了したかチェック
                    if (logs.length > 0) {{
                        const lastLog = logs[logs.length - 1];
                        if (lastLog.includes('🎉 処理が正常に完了しました！') || 
                            lastLog.includes('🎉 IMAGE関数生成が完了しました！') ||
                            lastLog.includes('🛑 処理が停止されました') ||
                            lastLog.includes('🛑 A列URL記載が停止されました') ||
                            lastLog.includes('🛑 画像ダウンロードが停止されました') ||
                            lastLog.includes('🛑 IMAGE関数生成が停止されました') ||
                            lastLog.includes('❌ 実行エラー')) {{
                            isRunning = false;
                            document.getElementById('runBtn').disabled = false;
                            document.getElementById('runBtn').style.display = 'inline-block';
                            document.getElementById('stopBtn').style.display = 'none';
                            document.getElementById('status').className = 'status stopped';
                            document.getElementById('status').innerHTML = '⏹️ 停止中';
                        }}
                    }}
                }})
                .catch(error => {{
                    console.error('ログ取得エラー:', error);
                }});
            }}, 1000);
        }}
        
        // 初期ログ取得
        startLogPolling();
    </script>
</body>
</html>
        """
        return html
    
    def start_server(self, port=8080):
        """Webサーバーを開始"""
        # ポートが使用中の場合は別のポートを試す
        for test_port in range(port, port + 10):
            try:
                self.server = HTTPServer(('localhost', test_port), 
                                       lambda *args, **kwargs: SimpleGUIHandler(*args, app_instance=self, **kwargs))
                self.server_thread = threading.Thread(target=self.server.serve_forever)
                self.server_thread.daemon = True
                self.server_thread.start()
                
                print(f"🌐 Webサーバーを開始しました: http://localhost:{test_port}")
                print("📱 ブラウザで上記URLを開いてください")
                
                # ブラウザを自動で開く（新規タブを避ける）
                try:
                    # 既存のブラウザウィンドウで開く
                    webbrowser.open(f'http://localhost:{test_port}', new=0)
                except:
                    pass
                
                return self.server
                
            except OSError as e:
                if e.errno == 48:  # Address already in use
                    print(f"⚠️ ポート {test_port} は使用中です。次のポートを試します...")
                    continue
                else:
                    raise e
        
        # すべてのポートが使用中の場合
        print(f"❌ ポート {port} から {port + 9} まで使用中です。")
        print("既存のアプリケーションを終了してから再実行してください。")
        return None
    
    def stop_server(self):
        """Webサーバーを停止"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()

def main():
    """メイン関数"""
    print("=" * 60)
    print("🌐 Google Drive 画像ダウンローダー Web版")
    print("=" * 60)
    
    # 実行ファイルのディレクトリを取得
    if getattr(sys, 'frozen', False):
        # PyInstallerで作成された実行ファイルの場合
        base_path = os.path.dirname(sys.executable)
    else:
        # 通常のPythonスクリプトの場合
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # 作業ディレクトリを実行ファイルのディレクトリに変更
    os.chdir(base_path)
    print(f"📁 作業ディレクトリ: {base_path}")
    
    # 必要なファイルの存在確認
    required_files = ['request.py', 'client_secret.json']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ 必要なファイルが見つかりません: {missing_files}")
        print(f"📁 現在のディレクトリ: {os.getcwd()}")
        print(f"📁 実行ファイルのディレクトリ: {base_path}")
        return False
    
    # GUIアプリケーションを作成
    gui = SimpleGUI()
    
    try:
        # サーバーを開始
        server = gui.start_server()
        
        if server is None:
            print("❌ サーバーの開始に失敗しました")
            return False
        
        print("=" * 60)
        print("🎉 Web版GUIアプリケーションが起動しました！")
        print("=" * 60)
        print("使用方法:")
        print("1. ブラウザで表示されたURLを開く")
        print("2. 設定を入力")
        print("3. 「🚀 実行開始」ボタンをクリック")
        print("4. ログで進捗を確認")
        print("=" * 60)
        print("終了するには Ctrl+C を押してください")
        print("=" * 60)
        
        # サーバーを継続実行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 アプリケーションを終了します...")
    
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False
    finally:
        gui.stop_server()
    
    return True

if __name__ == "__main__":
    main() 