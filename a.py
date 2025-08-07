import os
import re
import time
import logging
import threading
import requests

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# 使用スコープ
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
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
    token_path = 'token.json'
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
        flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as f:
            f.write(creds.to_json())

    sheets_service = build('sheets', 'v4', credentials=creds)
    return sheets_service, creds

def extract_folder_id(url: str) -> str | None:
    for pattern in (r'/folders/([a-zA-Z0-9_-]+)', r'\?id=([a-zA-Z0-9_-]+)'):
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None

def fetch_first_image_url(drive_service, folder_id: str) -> str | None:
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
    base_dir = os.path.abspath("downloaded_images")

    for idx, row in enumerate(values, start=start_row):
        folder_url = row[0] if len(row) > 0 else ""
        save_name  = row[4] if len(row) > 4 else ""
        if not folder_url or not save_name:
            logging.warning(f"Row {idx}: A or E is empty. Skipped.")
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
    SPREADSHEET_ID = "1GWc8wGc2ebjxjCXlZdmg97hLvyJUiqYhGMiLqTHMYq0"
    SHEET_NAME    = "第3弾"
    START_ROW     = 2

    sheets_service, creds = authenticate()
    process_all_rows(sheets_service, creds, SPREADSHEET_ID, SHEET_NAME, START_ROW)

if __name__ == "__main__":
    main()