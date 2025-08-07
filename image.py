




import os
import re
import time
import logging
import threading
import concurrent.futures
import tkinter as tk

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ============================================================
# ログ設定（DEBUGレベルで詳細ログ出力）
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

# ============================================================
# 使用するAPIのスコープ（Sheets と Drive）
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# ------------------------------------------------------------
# 各スレッドごとのDriveサービス保持用のスレッドローカル変数
_thread_local = threading.local()

# ------------------------------------------------------------
# レートリミット管理用（トークンバケット方式）
# ここでは1分間あたりの最大リクエスト数（トークン数）を1500と仮定
RATE_LIMIT_MAX_DRIVE = 2000
token_bucket = RATE_LIMIT_MAX_DRIVE  # 初期状態は満タン
last_refill = time.time()
rate_limit_lock = threading.Lock()
# ------------------------------------------------------------

def check_drive_api_rate_limit():
    """
    トークンバケット方式でドライブAPIのレート使用状況を管理する。
    
    ・1分間にRATE_LIMIT_MAX_DRIVE個のトークン（＝リクエスト）が補充されると仮定。
    ・もし前回のリセットから1分以上経過している場合、10秒間待機してからトークンバケットをリセット（＝満タンに戻す）します。
    ・その後、トークンが不足している場合は、十分なトークンが貯まるまで待機し、各API呼び出し時に1トークンを消費します。
    ・使用率はログに出力されます。（使用率＝(1 - (残トークン/最大トークン))×100）
    """
    global token_bucket, last_refill
    with rate_limit_lock:
        now = time.time()
        if now - last_refill >= 60:
            logging.info("1分経過のため、10秒待機してレート使用率をリセットします。")
            time.sleep(10)
            token_bucket = RATE_LIMIT_MAX_DRIVE  # リセット
            last_refill = time.time()
            now = last_refill  # リセット後の時刻

        # 補充：1分間にRATE_LIMIT_MAX_DRIVE個補充される（1秒あたり RATE_LIMIT_MAX_DRIVE/60 個）
        elapsed = now - last_refill
        refill = elapsed * (RATE_LIMIT_MAX_DRIVE / 60)
        token_bucket = min(RATE_LIMIT_MAX_DRIVE, token_bucket + refill)
        last_refill = now

        while token_bucket < 1:
            wait_time = (1 - token_bucket) * (60 / RATE_LIMIT_MAX_DRIVE)
            logging.info("トークン不足のため、{:.2f}秒待機します。".format(wait_time))
            time.sleep(wait_time)
            now = time.time()
            elapsed = now - last_refill
            token_bucket = min(RATE_LIMIT_MAX_DRIVE, token_bucket + elapsed * (RATE_LIMIT_MAX_DRIVE / 60))
            last_refill = now

        token_bucket -= 1  # API呼び出しとして1トークン消費
        usage_percentage = (1 - token_bucket / RATE_LIMIT_MAX_DRIVE) * 100
        logging.info("ドライブAPI使用率: {:.2f}% (残トークン: {:.2f})".format(usage_percentage, token_bucket))

def get_thread_local_drive_service(creds):
    """
    各スレッドで独自の Drive サービスオブジェクトを取得します。
    """
    if not hasattr(_thread_local, 'drive_service'):
        _thread_local.drive_service = build('drive', 'v3', credentials=creds)
        logging.debug("新しいDriveサービスオブジェクトを生成しました。")
    return _thread_local.drive_service

def authenticate_google_apis():
    """
    Google Sheets API および Drive API の認証処理を実施します。
    token.json が存在すればそれを利用し、なければブラウザ認証を行います。
    """
    logging.info("Google APIs の認証を開始します。")
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        logging.debug("token.json から認証情報を読み込みました。")
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logging.info("認証情報をリフレッシュしました。")
            except Exception as e:
                logging.error("認証情報のリフレッシュに失敗しました: %s", e)
                creds = None
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret_595218989803-l6aqsgjkiu5b0smq0lsd1t02ulpt73uo.apps.googleusercontent.com.json',
                SCOPES
            )
            creds = flow.run_local_server(port=0)
            logging.info("ブラウザ認証が完了しました。")
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            logging.debug("新しい token.json を保存しました。")
    sheets_service = build('sheets', 'v4', credentials=creds)
    logging.info("Google Sheets および Drive API の認証が完了しました。")
    return sheets_service, creds

def extract_folder_id(url):
    """
    フォルダリンクからGoogle DriveのフォルダIDを抽出します。
    対応例：
      - https://drive.google.com/drive/folders/フォルダID
      - https://drive.google.com/open?id=フォルダID
    単純なID文字列の場合はそのまま返します。
    """
    patterns = [
        r'/folders/([a-zA-Z0-9_-]+)',
        r'\?id=([a-zA-Z0-9_-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            folder_id = match.group(1)
            logging.debug("抽出したフォルダID: %s (URL: %s)", folder_id, url)
            return folder_id
    if url and url.strip().isdigit():
        folder_id = url.strip()
        logging.debug("単純なID文字列としてフォルダIDを返します: %s", folder_id)
        return folder_id
    logging.warning("フォルダIDの抽出に失敗しました。URL: %s", url)
    return None

def get_folder_link_by_sku(creds, sku):
    """
    SKU（フォルダ名と仮定）に対応するGoogle Drive上のフォルダを検索し、
    該当する場合はフォルダリンク（https://drive.google.com/drive/folders/{folder_id}）を返します。
    """
    drive_service = get_thread_local_drive_service(creds)
    query = f"name = '{sku}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    logging.debug("SKU '%s' の検索クエリ: %s", sku, query)
    try:
        check_drive_api_rate_limit()
        response = drive_service.files().list(
            q=query,
            fields="files(id, name)"
        ).execute()
    except Exception as e:
        logging.error("SKU '%s' のフォルダ検索中にエラー発生: %s", sku, e)
        return None
    files = response.get('files', [])
    if not files:
        logging.warning("SKU '%s' に対応するフォルダが見つかりませんでした。", sku)
        return None
    folder_id = files[0].get('id')
    folder_link = f"https://drive.google.com/drive/folders/{folder_id}"
    logging.info("SKU '%s' に対するフォルダリンクを取得: %s", sku, folder_link)
    return folder_link

def get_first_image_url_from_folder(creds, folder_id):
    """
    指定されたフォルダ内の画像ファイル（mimeTypeが'image/'で始まる）を
    名前順にソートし、先頭の画像の表示用URLを返します。画像が見つからなければNoneを返します。
    """
    drive_service = get_thread_local_drive_service(creds)
    query = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed = false"
    logging.debug("フォルダID '%s' の画像検索クエリ: %s", folder_id, query)
    try:
        check_drive_api_rate_limit()
        response = drive_service.files().list(
            q=query,
            fields="files(id, name)"
        ).execute()
    except Exception as e:
        logging.error("フォルダ %s 内の画像一覧取得に失敗しました: %s", folder_id, e)
        return None
    files = response.get('files', [])
    if not files:
        logging.warning("フォルダ %s 内に画像が見つかりませんでした。", folder_id)
        return None
    files.sort(key=lambda f: f.get('name', ''))
    first_file = files[0]
    file_id = first_file.get('id')
    image_url = f"https://drive.google.com/uc?export=view&id={file_id}"
    logging.info("フォルダ %s 内の最初の画像URLを取得: %s", folder_id, image_url)
    return image_url

# ----- グローバル進捗変数（処理進捗用）
global_progress = 0      # 0～100(%)
global_total_rows = 1    
progress_lock = threading.Lock()
processing_done = False
# -------------------------------------------------------

def process_single_row(row_index, sku, creds):
    """
    1行分の処理:
      - SKUからフォルダリンク（B列用）取得
      - フォルダ内の1枚目の画像URL取得しIMAGE関数（A列用）生成
    戻り値は (IMAGE関数, フォルダリンク, SKU) のタプル
    """
    logging.info("行 %d: SKU = '%s' の処理を開始します。", row_index, sku)
    folder_link = ""
    image_formula = ""
    if sku:
        folder_link = get_folder_link_by_sku(creds, sku)
        if folder_link:
            folder_id = extract_folder_id(folder_link)
            if folder_id:
                image_url = get_first_image_url_from_folder(creds, folder_id)
                if image_url:
                    image_formula = f'=IMAGE("{image_url}")'
                    logging.info("行 %d: IMAGE関数数式を生成しました: %s", row_index, image_formula)
                else:
                    logging.warning("行 %d: フォルダ %s から画像URLの取得に失敗しました。", row_index, folder_id)
            else:
                logging.warning("行 %d: フォルダリンクからフォルダIDの抽出に失敗しました。", row_index)
        else:
            logging.warning("行 %d: SKU '%s' に対応するフォルダリンクが見つかりませんでした。", row_index, sku)
    else:
        logging.warning("行 %d: SKU の値が空です。", row_index)
    return (image_formula, folder_link, sku)

def update_sheet_values(sheets_service, spreadsheet_id, update_data, max_retries=3):
    """
    sheets_service の batchUpdate を再試行処理付きで実施します。
    失敗した場合は指数的バックオフで再試行し、最大 max_retries 回試行します。
    """
    for attempt in range(max_retries):
        try:
            result = sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=update_data
            ).execute()
            logging.info("バッチ更新成功")
            return result
        except Exception as e:
            logging.error("バッチ更新エラー（試行 %d/%d）: %s", attempt + 1, max_retries, e)
            sleep_time = 2 ** attempt
            time.sleep(sleep_time)
    raise Exception("バッチ更新に失敗しました")

def process_sheet(sheets_service, creds, spreadsheet_id, sheet_name, start_row=2, max_workers=20):
    """
    シートのC列（SKU）を読み込み、各行を処理後、
    A列（IMAGE関数）、B列（フォルダリンク）、C列（SKU）をバッチ更新します。
    また、処理進捗はglobal_progressにより更新します。
    
    ※ここでは並列処理部分を全体の90%として進捗を更新し、バッチ更新部分で残り10%を更新します。
    """
    global global_progress, global_total_rows, processing_done
    logging.info("シート '%s' の処理を開始します。開始行: %d", sheet_name, start_row)
    range_c = f"{sheet_name}!C{start_row}:C"
    logging.debug("セル範囲 %s を取得します。", range_c)
    response = sheets_service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        ranges=[range_c],
        includeGridData=True
    ).execute()

    sheet_data = response['sheets'][0]['data'][0]
    row_data = sheet_data.get('rowData', [])
    sku_list = []
    for row in row_data:
        cell_value = ""
        if 'values' in row and row['values']:
            cell = row['values'][0]
            cell_value = cell.get('formattedValue', '').strip()
        sku_list.append(cell_value)
    num_rows = len(sku_list)
    global_total_rows = num_rows
    logging.info("処理対象の行数（SKUの数）: %d", num_rows)

    image_formulas = ["" for _ in range(num_rows)]
    folder_links   = ["" for _ in range(num_rows)]
    sku_values     = sku_list[:]

    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(process_single_row, start_row + idx, sku_list[idx], creds): idx
            for idx in range(num_rows)
        }
        processed = 0
        for future in concurrent.futures.as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                image_formula, folder_link, sku = future.result()
                image_formulas[idx] = image_formula
                folder_links[idx] = folder_link
                sku_values[idx] = sku
            except Exception as e:
                logging.error("行 %d の処理中にエラー: %s", start_row + idx, e)
                image_formulas[idx] = ""
                folder_links[idx] = ""
                sku_values[idx] = ""
            processed += 1
            # 進捗更新（全体の90%が並列処理側とする）
            with progress_lock:
                global_progress = (processed / num_rows) * 90
            if processed % 10 == 0 or processed == num_rows:
                logging.info("進捗: %d/%d 行（並列処理）を処理しました。", processed, num_rows)
    elapsed = time.time() - start_time
    logging.info("全行の並列処理が完了しました。処理時間: %.2f秒", elapsed)

    # バッチ更新フェーズ：全体の進捗90%から100%にする
    CHUNK_SIZE = 500
    total_chunks = -(-num_rows // CHUNK_SIZE)  # 天井除算
    chunk_index = 0
    for i in range(0, num_rows, CHUNK_SIZE):
        start_idx = i
        end_idx = min(num_rows, i + CHUNK_SIZE)
        chunk_image_formulas = image_formulas[start_idx:end_idx]
        chunk_folder_links   = folder_links[start_idx:end_idx]
        chunk_sku_values     = sku_values[start_idx:end_idx]
        update_data = {
            "data": [
                {
                    "range": f"{sheet_name}!A{start_row + start_idx}:A{start_row + end_idx - 1}",
                    "majorDimension": "COLUMNS",
                    "values": [chunk_image_formulas]
                },
                {
                    "range": f"{sheet_name}!B{start_row + start_idx}:B{start_row + end_idx - 1}",
                    "majorDimension": "COLUMNS",
                    "values": [chunk_folder_links]
                },
                {
                    "range": f"{sheet_name}!C{start_row + start_idx}:C{start_row + end_idx - 1}",
                    "majorDimension": "COLUMNS",
                    "values": [chunk_sku_values]
                }
            ],
            "valueInputOption": "USER_ENTERED"
        }
        logging.info("シートのバッチ更新を開始します。（行 %d～%d）", start_idx + start_row, end_idx + start_row - 1)
        update_sheet_values(sheets_service, spreadsheet_id, update_data)
        chunk_index += 1
        # バッチ更新進捗の更新（全体で残り10%）
        with progress_lock:
            global_progress = 90 + (chunk_index / total_chunks) * 10
    logging.info("シートのバッチ更新が全て完了しました。")
    processing_done = True

# ============================================================
# GUIパート：Tkinter で 円形プログレスバーを表示するウィンドウ
# ============================================================
class CircularProgressbar(tk.Canvas):
    def __init__(self, parent, width=200, height=200, bg="#ffffff", fg="#3498db", thickness=15, label_text="", *args, **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, *args, **kwargs)
        self.width = width
        self.height = height
        self.default_fg = fg
        self.fg = fg
        self.thickness = thickness
        self.angle = 0  
        self.create_oval(thickness, thickness, width - thickness, height - thickness, outline="#cccccc", width=thickness)
        self.arc = self.create_arc(thickness, thickness, width - thickness, height - thickness, start=-90, extent=0, style="arc", outline=fg, width=thickness)
        self.progress_text = self.create_text(width/2, height/2, text="0%", fill="black", font=("Helvetica", 16, "bold"))
        # キャンバス内にラベルを配置
        self.label = tk.Label(self, text=label_text, font=("Helvetica", 12))
        self.create_window(width/2, height - thickness/2, window=self.label)
        
    def update_progress(self, percentage, arc_color=None):
        self.angle = (percentage / 100) * 360
        self.itemconfig(self.arc, extent=self.angle)
        self.itemconfig(self.progress_text, text=f"{int(percentage)}%")
        if arc_color:
            self.itemconfig(self.arc, outline=arc_color)
            self.itemconfig(self.progress_text, fill=arc_color)
        else:
            self.itemconfig(self.arc, outline=self.fg)
            self.itemconfig(self.progress_text, fill=self.fg)
        self.update_idletasks()

# ------------------------------------------------------------
def gui_update_processing(progressbar, root):
    with progress_lock:
        prog = global_progress
    progressbar.update_progress(prog)
    if processing_done:
        progressbar.update_progress(100)
    else:
        root.after(100, gui_update_processing, progressbar, root)

def gui_update_api_usage(api_usage_bar, root):
    with rate_limit_lock:
        # 使用率 = (1 - (残トークン / 最大トークン)) * 100
        usage_percentage = (1 - token_bucket / RATE_LIMIT_MAX_DRIVE) * 100
    # 色：80%以上なら赤、それ以外は緑
    arc_color = "red" if usage_percentage >= 80 else "green"
    api_usage_bar.update_progress(usage_percentage, arc_color=arc_color)
    root.after(100, gui_update_api_usage, api_usage_bar, root)

def start_processing(sheets_service, creds, spreadsheet_id, sheet_name, start_row, max_workers):
    process_sheet(sheets_service, creds, spreadsheet_id, sheet_name, start_row=start_row, max_workers=max_workers)

# ============================================================
# メイン
def main():
    SPREADSHEET_ID = "1ib53Y_cLkn-Mk1IWst_BF3rbU9syUZDtcHYbIOx2znU"  
    SHEET_NAME = "原本 のコピー"  
    START_ROW = 2
    MAX_WORKERS = 20

    logging.info("プログラムを開始します。")
    sheets_service, creds = authenticate_google_apis()

    root = tk.Tk()
    root.title("進捗状況")
    
    frame = tk.Frame(root)
    frame.pack(padx=20, pady=20)
    
    processing_label = tk.Label(frame, text="処理進捗", font=("Helvetica", 12, "bold"))
    processing_label.grid(row=0, column=0, pady=(0,10))
    processing_bar = CircularProgressbar(frame, width=200, height=200, fg="#3498db", thickness=15)
    processing_bar.grid(row=1, column=0, padx=20)
    
    api_usage_label = tk.Label(frame, text="API 使用率", font=("Helvetica", 12, "bold"))
    api_usage_label.grid(row=0, column=1, pady=(0,10))
    api_usage_bar = CircularProgressbar(frame, width=200, height=200, fg="green", thickness=15)
    api_usage_bar.grid(row=1, column=1, padx=20)

    processing_thread = threading.Thread(
        target=start_processing, 
        args=(sheets_service, creds, SPREADSHEET_ID, SHEET_NAME, START_ROW, MAX_WORKERS),
        daemon=True
    )
    processing_thread.start()
    
    root.after(100, gui_update_processing, processing_bar, root)
    root.after(100, gui_update_api_usage, api_usage_bar, root)
    
    root.mainloop()
    logging.info("プログラムを終了します。")

if __name__ == '__main__':
    main()