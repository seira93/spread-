#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess

class GoogleDriveDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Drive 画像ダウンローダー")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 設定ファイルの読み込み
        self.config_file = 'config.json'
        self.config = self.load_config()
        
        self.setup_ui()
        self.load_current_settings()
    
    def load_config(self):
        """設定ファイルを読み込む"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"設定ファイルの読み込みに失敗: {e}")
        return {}
    
    def save_config(self):
        """設定を保存する"""
        try:
            config = {
                'spreadsheet_url': self.url_var.get(),
                'sheet_name': self.sheet_var.get(),
                'start_row': int(self.start_row_var.get()),
                'download_dir': self.download_dir_var.get()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("成功", "設定を保存しました")
        except Exception as e:
            messagebox.showerror("エラー", f"設定の保存に失敗しました: {e}")
    
    def setup_ui(self):
        """UIを構築する"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # タイトル
        title_label = ttk.Label(main_frame, text="Google Drive 画像ダウンローダー", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # スプレッドシートURL
        ttk.Label(main_frame, text="スプレッドシートURL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=50)
        url_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # シート名
        ttk.Label(main_frame, text="シート名:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.sheet_var = tk.StringVar()
        sheet_entry = ttk.Entry(main_frame, textvariable=self.sheet_var, width=30)
        sheet_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 開始行
        ttk.Label(main_frame, text="開始行:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.start_row_var = tk.StringVar()
        start_row_entry = ttk.Entry(main_frame, textvariable=self.start_row_var, width=10)
        start_row_entry.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # ダウンロード先
        ttk.Label(main_frame, text="ダウンロード先:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.download_dir_var = tk.StringVar()
        download_dir_entry = ttk.Entry(main_frame, textvariable=self.download_dir_var, width=40)
        download_dir_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # フォルダ選択ボタン
        browse_button = ttk.Button(main_frame, text="参照", command=self.browse_directory)
        browse_button.grid(row=4, column=2, padx=(5, 0), pady=5)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        # 実行ボタン
        self.run_button = ttk.Button(button_frame, text="🚀 実行開始", 
                                    command=self.run_downloader, style="Accent.TButton")
        self.run_button.grid(row=0, column=0, padx=5)
        
        # 設定保存ボタン
        save_button = ttk.Button(button_frame, text="💾 設定保存", command=self.save_config)
        save_button.grid(row=0, column=1, padx=5)
        
        # 設定リセットボタン
        reset_button = ttk.Button(button_frame, text="🔄 リセット", command=self.reset_settings)
        reset_button.grid(row=0, column=2, padx=5)
        
        # ログ表示エリア
        ttk.Label(main_frame, text="実行ログ:").grid(row=6, column=0, sticky=tk.W, pady=(20, 5))
        
        # ログテキストエリア
        self.log_text = tk.Text(main_frame, height=10, width=70, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_scrollbar.grid(row=7, column=2, sticky=(tk.N, tk.S), pady=5)
        
        # プログレスバー
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           maximum=100, mode='indeterminate')
        self.progress_bar.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # グリッドの重み設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)
    
    def load_current_settings(self):
        """現在の設定を読み込む"""
        self.url_var.set(self.config.get('spreadsheet_url', 
                                        "https://docs.google.com/spreadsheets/d/1GWc8wGc2ebjxjCXlZdmg97hLvyJUiqYhGMiLqTHMYq0"))
        self.sheet_var.set(self.config.get('sheet_name', "第3弾"))
        self.start_row_var.set(str(self.config.get('start_row', 2)))
        self.download_dir_var.set(self.config.get('download_dir', 
                                                 os.path.abspath("downloaded_images")))
    
    def browse_directory(self):
        """フォルダ選択ダイアログを表示"""
        directory = filedialog.askdirectory(initialdir=self.download_dir_var.get())
        if directory:
            self.download_dir_var.set(directory)
    
    def reset_settings(self):
        """設定をリセット"""
        if messagebox.askyesno("確認", "設定をデフォルトにリセットしますか？"):
            self.config = {}
            self.load_current_settings()
            self.log_message("設定をリセットしました")
    
    def log_message(self, message):
        """ログメッセージを表示"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def run_downloader(self):
        """ダウンローダーを実行"""
        # 入力値の検証
        if not self.url_var.get().strip():
            messagebox.showerror("エラー", "スプレッドシートURLを入力してください")
            return
        
        if not self.sheet_var.get().strip():
            messagebox.showerror("エラー", "シート名を入力してください")
            return
        
        try:
            start_row = int(self.start_row_var.get())
            if start_row < 1:
                raise ValueError()
        except ValueError:
            messagebox.showerror("エラー", "開始行は1以上の数値を入力してください")
            return
        
        if not self.download_dir_var.get().strip():
            messagebox.showerror("エラー", "ダウンロード先を指定してください")
            return
        
        # 実行ボタンを無効化
        self.run_button.config(state='disabled')
        self.progress_bar.start()
        
        # 別スレッドで実行
        thread = threading.Thread(target=self.run_downloader_thread)
        thread.daemon = True
        thread.start()
    
    def run_downloader_thread(self):
        """ダウンローダーを別スレッドで実行"""
        try:
            self.log_message("=" * 50)
            self.log_message("🚀 Google Drive 画像ダウンローダーを開始します...")
            self.log_message("=" * 50)
            
            # コマンドライン引数を構築
            cmd = [
                sys.executable, "request.py",
                "--url", self.url_var.get().strip(),
                "--sheet", self.sheet_var.get().strip(),
                "--start-row", str(int(self.start_row_var.get())),
                "--download-dir", self.download_dir_var.get().strip()
            ]
            
            self.log_message(f"実行コマンド: {' '.join(cmd)}")
            self.log_message("")
            
            # プロセスを実行
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # 出力をリアルタイムで表示
            for line in iter(process.stdout.readline, ''):
                if line:
                    self.log_message(line.rstrip())
            
            process.wait()
            
            if process.returncode == 0:
                self.log_message("")
                self.log_message("✅ 処理が正常に完了しました！")
                messagebox.showinfo("完了", "画像ダウンロードが完了しました")
            else:
                self.log_message("")
                self.log_message("❌ 処理中にエラーが発生しました")
                messagebox.showerror("エラー", "処理中にエラーが発生しました")
                
        except Exception as e:
            self.log_message(f"❌ 実行エラー: {e}")
            messagebox.showerror("エラー", f"実行エラー: {e}")
        finally:
            # UIを元に戻す
            self.root.after(0, self.finish_execution)
    
    def finish_execution(self):
        """実行完了時の処理"""
        self.run_button.config(state='normal')
        self.progress_bar.stop()

def main():
    """メイン関数"""
    root = tk.Tk()
    
    # スタイル設定
    style = ttk.Style()
    style.theme_use('clam')
    
    # アプリケーションを作成
    app = GoogleDriveDownloaderGUI(root)
    
    # ウィンドウを中央に配置
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    # アプリケーションを開始
    root.mainloop()

if __name__ == "__main__":
    main() 