import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import requests
import json
import webbrowser
import threading
from datetime import datetime
import os
import re
from pathlib import Path
from urllib.parse import quote_plus

class BlenderStyleSearchTool:
    def __init__(self):
        # Blender風カラーパレット
        self.colors = {
            'bg_dark': '#2d2d2d',
            'bg_medium': '#383838', 
            'bg_light': '#4a4a4a',
            'accent_blue': '#5294cf',
            'text_white': '#ffffff',
            'text_gray': '#b3b3b3',
            'orange': '#ff7700',
            'success': '#5cb85c',
            'panel': '#353535'
        }
        
        # 言語テキストの読み込み
        self.texts = self.load_language_texts()
        self.current_lang = "ja"  # デフォルト言語
        
        # データファイルパス
        self.history_file = "search_history.json"
        self.bookmarks_file = "bookmarks.json"
        
        # データ初期化
        self.search_history = []
        self.bookmarks = []
        
        # ローカルアドオン管理初期化
        self.local_addons = []
        self.addon_folders = self.get_blender_addon_folders()
        
        # GUI初期化
        self.init_gui()
        self.load_data()
        
        # 初期履歴表示（UI作成後）
        self.root.after(100, self.refresh_history)
    
    def get_blender_addon_folders(self):
        """Blenderのアドオンフォルダを取得"""
        folders = []
        
        # Blender標準パス（Windows）
        user_home = Path.home()
        blender_path = user_home / "AppData" / "Roaming" / "Blender Foundation" / "Blender"
        
        # バージョン別フォルダを検索
        if blender_path.exists():
            for version_folder in blender_path.iterdir():
                if version_folder.is_dir() and version_folder.name.replace('.', '').isdigit():
                    addon_folder = version_folder / "scripts" / "addons"
                    if addon_folder.exists():
                        folders.append(str(addon_folder))
        
        # 追加: カスタムフォルダ（後で設定機能追加予定）
        return folders
    
    def extract_addon_info(self, file_path):
        """Pythonファイルからbl_info情報を抽出"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        
            # bl_info辞書を正規表現で抽出
            bl_info_pattern = r'bl_info\s*=\s*{([^}]+)}'
            match = re.search(bl_info_pattern, content, re.DOTALL)
        
            if match:
                bl_info_str = '{' + match.group(1) + '}'
                try:
                    # 安全な評価（基本的な辞書のみ）
                    bl_info = eval(bl_info_str)
                
                    addon_info = {
                        'name': bl_info.get('name', file_path.stem),
                        'version': bl_info.get('version', (0, 0, 0)),
                        'description': bl_info.get('description', '説明なし'),
                        'author': bl_info.get('author', '不明'),
                        'category': bl_info.get('category', 'その他'),
                        'blender_version': bl_info.get('blender', (0, 0, 0)),
                        'file_size': file_path.stat().st_size,
                        'modified_date': file_path.stat().st_mtime
                    }
                    return addon_info
                except:
                    pass
        
            # bl_infoが見つからない場合のフォールバック
            return {
                'name': file_path.stem,
                'version': (0, 0, 0),
                'description': 'bl_info情報が見つかりません',
                'author': '不明',
                'category': 'その他',
                'blender_version': (0, 0, 0),
                'file_size': file_path.stat().st_size,
                'modified_date': file_path.stat().st_mtime
            }
        
        except Exception as e:
            print(f"ファイル読み込みエラー: {file_path} - {e}")
            return None

    def scan_local_addons(self):
        """ローカルアドオンをスキャン"""
        self.local_addons = []
        
        for folder in self.addon_folders:
            try:
                folder_path = Path(folder)
                if not folder_path.exists():
                    continue
                    
                # .pyファイルと__pycache__以外のフォルダをチェック
                for item in folder_path.iterdir():
                    addon_info = None
                    
                    if item.is_file() and item.suffix == '.py':
                        # 単体.pyファイルアドオン
                        addon_info = self.extract_addon_info(item)
                    elif item.is_dir() and item.name != '__pycache__':
                        # フォルダ型アドオン
                        init_file = item / "__init__.py"
                        if init_file.exists():
                            addon_info = self.extract_addon_info(init_file)
                    
                    if addon_info:
                        addon_info['folder_path'] = str(folder)
                        addon_info['file_path'] = str(item)
                        addon_info['type'] = 'file' if item.is_file() else 'folder'
                        self.local_addons.append(addon_info)
                        
            except Exception as e:
                print(f"フォルダスキャンエラー: {folder} - {e}")
        
        return self.local_addons
    
    def load_language_texts(self):
        """言語テキストの定義（ローカルアドオン関連追加）"""
        return {
            "ja": {
                "title": "🔍 Blender アドオン検索ツール",
                "version": "v2.2 Local Library Edition",
                "search_options": " 🔍 検索オプション ",
                "search_query": "検索キーワード:",
                "search_mode": "検索モード:",
                "web_local": "🌐 全検索 (GitHub + Web + ローカル)",
                "web_only": "🌍 Web検索 (GitHub + Google)",
                "local_only": "💾 ローカルのみ",
                "google_search_btn": "🌐 Googleで検索",
                "search_btn": "🚀 検索実行",
                "search_results": " 📋 検索結果 ",
                "local_addons": " 📂 私のアドオン ",
                "language": "🌐 言語:",
                "japanese": "🇯🇵 日本語",
                "english": "🇺🇸 English",
                "help": "？",
                "history": "📚 履歴",
                "clear": "🗑️ クリア",
                "ready": "準備完了",
                "searching": "検索中...",
                "scanning": "スキャン中...",
                "no_results": "結果が見つかりませんでした",
                "warning": "警告",
                "enter_query": "検索キーワードを入力してください",
                "search_for": "検索キーワード: '{}'",
                "found_results": "{}件の結果が見つかりました",
                "found_addons": "{}個のアドオンが見つかりました",
                "error_occurred": "エラーが発生しました",
                "github_stars": "GitHub (⭐{})",
                "web_result": "Web検索結果",
                "local_db": "ローカルデータベース",
                "error_source": "エラー",
                "usage_guide": " 📖 使い方ガイド ",
                "bookmarks": " 📌 ブックマーク ",
                "search_history": " 📚 検索履歴 ",
                "recommendations": " ⭐ おすすめ ",
                "refresh": "🔄 更新",
                "delete": "🗑️ 削除",
                "open": "🌐 開く",
                "scan": "🔄 スキャン",
                "add_folder": "📁 フォルダ追加",
                "open_folder": "📁 フォルダを開く",
                "search_tips": "🔍 検索のコツ",
                "install_guide": "📥 インストール方法",
                "asset_guide": "📦 Asset登録・管理",
                "troubleshooting": "🛠️ トラブルシューティング",
                "faq": "❓ よくある質問",
                "confirm_clear": "検索履歴をすべて削除しますか？",
                "no_history": "まだ検索履歴がありません",
                "no_bookmarks": "まだブックマークがありません",
                "no_addons_found": "アドオンが見つかりませんでした",
                "bookmark_added": "'{}' をブックマークに追加しました",
                "bookmark_exists": "'{}' は既にブックマーク済みです",
                "select_bookmark": "ブックマークを選択してください",
                "folder_added": "フォルダが追加されました",
                "folder_exists": "このフォルダは既に追加されています",
                "add_bookmark_guide": "📖 ブラウザから追加",
                "bookmark_url_label": "URL:",
                "bookmark_name_label": "名前(任意):",
                "bookmark_add_btn": "➕ 追加",
                "url_missing": "URLを入力してください",
                "recommend_text": "初心者におすすめ:\n• Node Wrangler\n• Extra Objects\n• LoopTools\n\n定期的に新しいアドオンをチェックしよう！",
                "help_text": "\n🔍 Blender アドオン検索ツール v2.2\n\n【NEW！】ローカルアドオン管理機能\n• 📂 私のアドオン: PCに保存されたアドオンを一覧表示\n• 🔄 自動スキャン: Blenderアドオンフォルダを自動検出\n• 📁 フォルダ管理: カスタムフォルダの追加・管理（外付けハードディスクのパスも追加可能！）\n\n【検索機能】Google検索対応！\n• GitHub API: 公式アドオン検索\n• Google検索: ブログ・解説記事・チュートリアル\n• ブックマーク: 有用な情報を簡単保存\n\n【使い方】\n1. 検索したいキーワードを入力\n2. 検索モードを選択  \n3. 検索ボタンをクリック\n4. 「📂 私のアドオン」でローカル管理\n\n【検索モード】\n• 全検索: GitHub + Web + ローカル\n• Web検索: GitHub + Google検索\n• ローカルのみ: サンプルデータのみ\n\n作成者: シットさん\nバージョン: 2.2 Local Library Edition\n                ",
                "history_coming": "履歴機能は実装中です"
            },
            "en": {
                "title": "🔍 Blender Addon Search Tool",
                "version": "v2.2 Local Library Edition",
                "search_options": " 🔍 Search Options ",
                "search_query": "Search Query:",
                "search_mode": "Search Mode:",
                "web_local": "🌐 All Search (GitHub + Web + Local)",
                "web_only": "🌍 Web Search (GitHub + Google)",
                "local_only": "💾 Local Only",
                "google_search_btn": "🌐 Search with Google",
                "search_btn": "🚀 SEARCH",
                "search_results": " 📋 Search Results ",
                "local_addons": " 📂 My Addons ",
                "language": "🌐 Language:",
                "japanese": "🇯🇵 日本語",
                "english": "🇺🇸 English",
                "help": "？",
                "history": "📚 History",
                "clear": "🗑️ Clear",
                "ready": "Ready",
                "searching": "Searching...",
                "scanning": "Scanning...",
                "no_results": "No results found",
                "warning": "Warning",
                "enter_query": "Please enter a search query",
                "search_for": "Search Results for: '{}'",
                "found_results": "Found {} results",
                "found_addons": "Found {} addons",
                "error_occurred": "Error occurred",
                "github_stars": "GitHub (⭐{})",
                "web_result": "Web Search Result",
                "local_db": "Local Database",
                "error_source": "Error",
                "usage_guide": " 📖 Usage Guide ",
                "bookmarks": " 📌 Bookmarks ",
                "search_history": " 📚 Search History ",
                "recommendations": " ⭐ Recommendations ",
                "refresh": "🔄 Refresh",
                "delete": "🗑️ Delete",
                "open": "🌐 Open",
                "scan": "🔄 Scan",
                "add_folder": "📁 Add Folder",
                "open_folder": "📁 Open Folder",
                "search_tips": "🔍 Search Tips",
                "install_guide": "📥 Installation Guide",
                "asset_guide": "📦 Asset Registration",
                "troubleshooting": "🛠️ Troubleshooting",
                "faq": "❓ FAQ",
                "confirm_clear": "Clear all search history?",
                "no_history": "No search history yet",
                "no_bookmarks": "No bookmarks yet",
                "no_addons_found": "No addons found",
                "bookmark_added": "'{}' added to bookmarks",
                "bookmark_exists": "'{}' is already bookmarked",
                "select_bookmark": "Please select a bookmark",
                "folder_added": "Folder added successfully",
                "folder_exists": "This folder is already added",
                "add_bookmark_guide": "📖 Add from Browser",
                "bookmark_url_label": "URL:",
                "bookmark_name_label": "Name (Optional):",
                "bookmark_add_btn": "➕ Add",
                "url_missing": "Please enter a URL",
                "recommend_text": "Recommended for beginners:\n• Node Wrangler\n• Extra Objects\n• LoopTools\n\nCheck for new addons regularly!",
                "help_text": "\n🔍 Blender Addon Search Tool v2.2\n\n【NEW!】Local Addon Management\n• 📂 My Addons: View local addons list\n• 🔄 Auto Scan: Auto-detect Blender addon folders\n• 📁 Folder Manager: Add & manage custom folders (External HDD paths can also be added!)\n\n【Search Feature】Google Search Support!\n• GitHub API: Official addon search\n• Google Search: Blogs, tutorials, guides\n• Bookmarks: Easy saving of useful info\n\n【How to Use】\n1. Enter search keywords\n2. Select search mode\n3. Click search button\n4. Use \"📂 My Addons\" for local management\n\n【Search Modes】\n• All Search: GitHub + Web + Local\n• Web Search: GitHub + Google Search\n• Local Only: Sample data only\n\nCreator: sitst\nVersion: 2.2 Local Library Edition\n                ",
                "history_coming": "History feature is under development"
            }
        }
        
    def init_gui(self):
        # メインウィンドウ
        self.root = tk.Tk()
        
        # StringVar変数をroot作成後に初期化
        self.current_language = tk.StringVar(value=self.current_lang)
        
        self.update_window_title()
        self.root.geometry("1100x750")
        self.root.configure(bg=self.colors['bg_dark'])
        
        # アイコン設定（オプション）
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
            
        self.create_header()
        self.create_main_content()
        self.create_footer()
    
    def get_text(self, key):
        """現在の言語のテキストを取得"""
        return self.texts[self.current_language.get()][key]
    
    def update_window_title(self):
        """ウィンドウタイトルを更新"""
        current_lang = getattr(self, 'current_language', None)
        if current_lang:
            self.root.title(f"{self.get_text('title')} - {self.get_text('version')}")
        else:
            # 初期化中の場合
            title = self.texts[self.current_lang]['title']
            version = self.texts[self.current_lang]['version']
            self.root.title(f"{title} - {version}")
    
    def change_language(self):
        """言語変更時の処理"""
        self.current_lang = self.current_language.get()
        self.update_window_title()
        # UI全体を再構築
        for widget in self.root.winfo_children():
            widget.destroy()
        self.create_header()
        self.create_main_content() 
        self.create_footer()
        # データ再読み込み
        self.refresh_history()
        self.refresh_bookmarks()
        
    def create_header(self):
        """ヘッダー部分の作成"""
        header_frame = tk.Frame(self.root, bg=self.colors['bg_light'], height=80)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # タイトル
        title_label = tk.Label(
            header_frame,
            text=self.get_text('title'),
            font=("Segoe UI", 18, "bold"),
            bg=self.colors['bg_light'],
            fg=self.colors['text_white']
        )
        title_label.pack(side='left', padx=20, pady=20)
        
        # バージョン表示
        version_label = tk.Label(
            header_frame,
            text=self.get_text('version'),
            font=("Segoe UI", 10),
            bg=self.colors['bg_light'], 
            fg=self.colors['accent_blue']
        )
        version_label.pack(side='left', padx=10, pady=20)
        
        # 言語選択
        lang_frame = tk.Frame(header_frame, bg=self.colors['bg_light'])
        lang_frame.pack(side='right', padx=10, pady=20)
        
        tk.Label(
            lang_frame,
            text=self.get_text('language'),
            font=("Segoe UI", 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text_white']
        ).pack(side='left')
        
        # 言語ラジオボタン
        jp_radio = tk.Radiobutton(
            lang_frame,
            text=self.get_text('japanese'),
            variable=self.current_language,
            value="ja",
            font=("Segoe UI", 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text_white'],
            selectcolor=self.colors['bg_medium'],
            activebackground=self.colors['bg_light'],
            activeforeground=self.colors['accent_blue'],
            command=self.change_language
        )
        jp_radio.pack(side='left', padx=5)
        
        en_radio = tk.Radiobutton(
            lang_frame,
            text=self.get_text('english'),
            variable=self.current_language,
            value="en",
            font=("Segoe UI", 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text_white'],
            selectcolor=self.colors['bg_medium'],
            activebackground=self.colors['bg_light'],
            activeforeground=self.colors['accent_blue'],
            command=self.change_language
        )
        en_radio.pack(side='left', padx=5)
        
        # ヘルプボタン
        help_btn = tk.Button(
            header_frame,
            text=self.get_text('help'),
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['orange'],
            fg='white',
            relief='flat',
            width=3,
            command=self.show_help
        )
        help_btn.pack(side='right', padx=20, pady=20)
        
    def create_main_content(self):
        """メインコンテンツエリア"""
        main_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 左右分割のPanedWindow
        paned = tk.PanedWindow(main_frame, orient=tk.HORIZONTAL, bg=self.colors['bg_dark'], 
                              sashrelief=tk.FLAT, sashwidth=5)
        paned.pack(fill='both', expand=True)
        
        # 左側：検索エリア
        self.left_frame = tk.Frame(paned, bg=self.colors['bg_dark'])
        paned.add(self.left_frame, minsize=650)
        
        # 検索セクション
        self.create_search_section(self.left_frame)
        
        # タブ切り替えボタン追加
        self.create_tab_buttons(self.left_frame)
        
        # 結果表示セクション 
        self.create_results_section(self.left_frame)
        
        # ローカルアドオン表示セクション（初期は非表示）
        self.create_local_addon_section(self.left_frame)
        
        # 右側：サイドバー
        right_frame = tk.Frame(paned, bg=self.colors['bg_dark'], width=300)
        paned.add(right_frame, minsize=300)
        
        self.create_sidebar(right_frame)
        
        # 初期タブ設定
        self.current_tab = 'search'
        
    def create_tab_buttons(self, parent):
        """タブ切り替えボタンの作成"""
        tab_frame = tk.Frame(parent, bg=self.colors['bg_dark'])
        tab_frame.pack(fill='x', pady=(0, 10))
        
        # 検索結果タブ
        self.search_tab_btn = tk.Button(
            tab_frame, 
            text=self.get_text('search_results').strip(),
            command=lambda: self.switch_tab('search'),
            bg=self.colors['accent_blue'], 
            fg='white', 
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            bd=0,
            padx=15,
            pady=8
        )
        self.search_tab_btn.pack(side='left', padx=(0, 5))
        
        # ローカルアドオンタブ
        self.local_tab_btn = tk.Button(
            tab_frame, 
            text=self.get_text('local_addons').strip(),
            command=lambda: self.switch_tab('local'),
            bg=self.colors['bg_medium'], 
            fg=self.colors['text_white'], 
            font=('Segoe UI', 10),
            relief='flat',
            bd=0,
            padx=15,
            pady=8
        )
        self.local_tab_btn.pack(side='left')
    
    def switch_tab(self, tab_name):
        """タブ切り替え"""
        if tab_name == 'search':
            # 検索結果タブ
            self.local_addon_frame.pack_forget()
            self.results_frame.pack(fill='both', expand=True)
            
            self.search_tab_btn.config(
                bg=self.colors['accent_blue'], 
                font=('Segoe UI', 10, 'bold')
            )
            self.local_tab_btn.config(
                bg=self.colors['bg_medium'], 
                font=('Segoe UI', 10)
            )
            
        elif tab_name == 'local':
            # ローカルアドオンタブ
            self.results_frame.pack_forget()
            self.local_addon_frame.pack(fill='both', expand=True)
            
            self.local_tab_btn.config(
                bg=self.colors['accent_blue'], 
                font=('Segoe UI', 10, 'bold')
            )
            self.search_tab_btn.config(
                bg=self.colors['bg_medium'], 
                font=('Segoe UI', 10)
            )
            
            # 初回表示時にスキャン実行
            if not hasattr(self, '_local_scanned'):
                self.scan_and_display_local_addons()
                self._local_scanned = True
        
        self.current_tab = tab_name
    
    def create_search_section(self, parent):
        """検索セクションの作成"""
        search_frame = tk.LabelFrame(
            parent,
            text=self.get_text('search_options'),
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_white'],
            relief='flat',
            bd=2
        )
        search_frame.pack(fill='x', pady=(0, 15))
        
        # 検索入力
        input_frame = tk.Frame(search_frame, bg=self.colors['bg_medium'])
        input_frame.pack(fill='x', padx=15, pady=15)
        
        tk.Label(
            input_frame,
            text=self.get_text('search_query'),
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_white']
        ).pack(anchor='w')
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            input_frame,
            textvariable=self.search_var,
            font=("Segoe UI", 12),
            bg=self.colors['bg_light'],
            fg=self.colors['text_white'],
            insertbackground=self.colors['text_white'],
            relief='flat',
            bd=5
        )
        self.search_entry.pack(fill='x', pady=(5, 0))
        self.search_entry.bind('<Return>', lambda e: self.search())
        
        # 検索モード選択
        mode_frame = tk.Frame(search_frame, bg=self.colors['bg_medium'])
        mode_frame.pack(fill='x', padx=15, pady=(10, 15))
        
        tk.Label(
            mode_frame,
            text=self.get_text('search_mode'),
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_white']
        ).pack(anchor='w')
        
        self.search_mode = tk.StringVar(value="both")
        
        modes = [
            (self.get_text('web_local'), "both"),
            (self.get_text('web_only'), "web"),
            (self.get_text('local_only'), "local")
        ]
        
        radio_frame = tk.Frame(mode_frame, bg=self.colors['bg_medium'])
        radio_frame.pack(anchor='w', pady=(5, 0))
        
        for text, value in modes:
            rb = tk.Radiobutton(
                radio_frame,
                text=text,
                variable=self.search_mode,
                value=value,
                font=("Segoe UI", 9),
                bg=self.colors['bg_medium'],
                fg=self.colors['text_white'],
                selectcolor=self.colors['bg_light'],
                activebackground=self.colors['bg_medium'],
                activeforeground=self.colors['accent_blue']
            )
            rb.pack(anchor='w', pady=2)
            
        # ボタンフレーム
        btn_frame = tk.Frame(search_frame, bg=self.colors['bg_medium'])
        btn_frame.pack(pady=(0, 15))

        # Google検索ボタン
        google_search_btn = tk.Button(
            btn_frame,
            text=self.get_text('google_search_btn'),
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['success'],
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            command=self.search_on_google
        )
        google_search_btn.pack(side='left', padx=(0, 10))

        # 検索ボタン
        search_btn = tk.Button(
            btn_frame,
            text=self.get_text('search_btn'),
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['accent_blue'],
            fg='white',
            relief='flat',
            padx=30,
            pady=10,
            command=self.search
        )
        search_btn.pack(side='left')

    def search_on_google(self):
        """ブラウザでGoogle検索を実行"""
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning(self.get_text('warning'), self.get_text('enter_query'))
            return
        
        # Blenderに特化した検索キーワードを追加
        search_query = f"{query} blender addon"
        url = f"https://www.google.com/search?q={quote_plus(search_query)}"
        
        try:
            webbrowser.open(url)
            self.status_var.set(f"'{query}' をGoogleで検索しました")
        except Exception as e:
            messagebox.showerror(self.get_text('error_occurred'), str(e))
        
    def create_results_section(self, parent):
        """結果表示セクションの作成"""
        self.results_frame = tk.LabelFrame(
            parent,
            text="",  # タブで表示するので空文字
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_white'],
            relief='flat',
            bd=2
        )
        self.results_frame.pack(fill='both', expand=True)
        
        # 結果表示エリア
        self.results_text = scrolledtext.ScrolledText(
            self.results_frame,
            font=("Consolas", 10),
            bg=self.colors['bg_dark'],
            fg=self.colors['text_white'],
            insertbackground=self.colors['text_white'],
            relief='flat',
            bd=0,
            wrap='none',
            exportselection=True
        )
        self.results_text.pack(fill='both', expand=True, padx=15, pady=15)
        
        # テキストタグ設定（色分け用）
        self.results_text.tag_configure("header", foreground=self.colors['accent_blue'], font=("Segoe UI", 12, "bold"))
        self.results_text.tag_configure("source", foreground=self.colors['orange'], font=("Segoe UI", 9, "bold"))
        self.results_text.tag_configure("url", foreground=self.colors['success'], underline=True)
        self.results_text.tag_configure("description", foreground=self.colors['text_gray'])
        self.results_text.tag_configure("bookmark_btn", foreground=self.colors['accent_blue'], underline=True)
        
        # URLクリック機能
        self.results_text.tag_bind("url", "<Button-1>", self.on_url_click)
        self.results_text.tag_bind("url", "<Enter>", lambda e: self.results_text.config(cursor="hand2"))
        self.results_text.tag_bind("url", "<Leave>", lambda e: self.results_text.config(cursor=""))
    
    def create_local_addon_section(self, parent):
        """ローカルアドオン表示セクションの作成"""
        self.local_addon_frame = tk.LabelFrame(
            parent,
            text="",  # タブで表示するので空文字
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_white'],
            relief='flat',
            bd=2
        )
        # 初期は非表示（pack しない）
        
        # ローカルアドオンツールバー
        local_toolbar = tk.Frame(self.local_addon_frame, bg=self.colors['bg_medium'])
        local_toolbar.pack(fill='x', pady=(10, 0), padx=15)
        
        scan_btn = tk.Button(
            local_toolbar,
            text=self.get_text('scan'),
            command=self.scan_and_display_local_addons,
            bg=self.colors['success'],
            fg='white',
            font=('Segoe UI', 9),
            relief='flat',
            padx=10,
            pady=5
        )
        scan_btn.pack(side='left', padx=(0, 5))
        
        add_folder_btn = tk.Button(
            local_toolbar,
            text=self.get_text('add_folder'),
            command=self.add_custom_folder,
            bg=self.colors['accent_blue'],
            fg='white',
            font=('Segoe UI', 9),
            relief='flat',
            padx=10,
            pady=5
        )
        add_folder_btn.pack(side='left', padx=(0, 5))
        
        # ローカルアドオンリスト表示エリア
        self.local_text = scrolledtext.ScrolledText(
            self.local_addon_frame,
            bg=self.colors['bg_dark'],
            fg=self.colors['text_white'],
            font=('Consolas', 9),
            wrap='word',
            relief='flat',
            bd=0
        )
        self.local_text.pack(fill='both', expand=True, padx=15, pady=15)
        
        # ローカルアドオン用タグ設定
        self.local_text.tag_configure("addon_header", foreground=self.colors['accent_blue'], font=("Segoe UI", 11, "bold"))
        self.local_text.tag_configure("addon_info", foreground=self.colors['text_gray'], font=("Segoe UI", 9))
        self.local_text.tag_configure("addon_path", foreground=self.colors['success'], font=("Consolas", 8))
        self.local_text.tag_configure("addon_action", foreground=self.colors['orange'], underline=True)
    
    def scan_and_display_local_addons(self):
        """ローカルアドオンをスキャンして表示"""
        self.local_text.delete(1.0, tk.END)
        self.local_text.insert(tk.END, f"🔄 {self.get_text('scanning')}\n\n")
        self.local_text.update()
        
        try:
            addons = self.scan_local_addons()
            
            self.local_text.delete(1.0, tk.END)
            
            if not addons:
                self.local_text.insert(tk.END, f"❌ {self.get_text('no_addons_found')}\n\n")
                self.local_text.insert(tk.END, "確認済みフォルダ:\n")
                for folder in self.addon_folders:
                    self.local_text.insert(tk.END, f"📁 {folder}\n")
                return
            
            self.local_text.insert(tk.END, f"✅ {self.get_text('found_addons').format(len(addons))}\n\n")
            self.local_text.insert(tk.END, "=" * 70 + "\n\n")
            
            for i, addon in enumerate(addons, 1):
                # アドオン基本情報
                version_str = ".".join(map(str, addon['version']))
                blender_ver = ".".join(map(str, addon['blender_version']))
                size_mb = addon['file_size'] / (1024 * 1024)
                
                # 更新日時
                try:
                    mod_time = datetime.fromtimestamp(addon['modified_date'])
                    mod_str = mod_time.strftime('%Y-%m-%d %H:%M')
                except:
                    mod_str = "不明"
                
                # アドオン名
                self.local_text.insert(tk.END, f"🔧 {i}. {addon['name']}\n", "addon_header")
                
                # 基本情報
                info_lines = [
                    f"   📊 バージョン: {version_str}",
                    f"   👤 作者: {addon['author']}",
                    f"   📂 カテゴリ: {addon['category']}",
                    f"   🎯 対応Blender: {blender_ver}+",
                    f"   💾 サイズ: {size_mb:.2f} MB",
                    f"   📅 更新: {mod_str}",
                    f"   📄 タイプ: {'ファイル' if addon['type'] == 'file' else 'フォルダ'}"
                ]
                
                for line in info_lines:
                    self.local_text.insert(tk.END, line + "\n", "addon_info")
                
                # パス情報
                self.local_text.insert(tk.END, f"   📍 場所: {addon['file_path']}\n", "addon_path")
                
                # 説明
                desc = addon['description'][:100] + "..." if len(addon['description']) > 100 else addon['description']
                self.local_text.insert(tk.END, f"   📝 {desc}\n", "addon_info")
                
                # アクションボタン（クリッカブルテキスト）
                actions_line = f"   [📁 {self.get_text('open_folder')}] [🗑️ {self.get_text('delete')}] [ℹ️ 詳細]\n"
                start_pos = self.local_text.index("end-1c linestart")
                self.local_text.insert(tk.END, actions_line, "addon_action")
                end_pos = self.local_text.index("end-1c lineend")
                
                # クリックイベント設定
                action_tag = f"action_{i}"
                self.local_text.tag_add(action_tag, start_pos, end_pos)
                self.local_text.tag_bind(action_tag, "<Button-1>", 
                    lambda e, addon_data=addon: self.on_addon_action_click(e, addon_data))
                self.local_text.tag_bind(action_tag, "<Enter>", 
                    lambda e: self.local_text.config(cursor="hand2"))
                self.local_text.tag_bind(action_tag, "<Leave>", 
                    lambda e: self.local_text.config(cursor=""))
                
                self.local_text.insert(tk.END, "\n" + "-" * 70 + "\n\n")
        
        except Exception as e:
            self.local_text.delete(1.0, tk.END)
            self.local_text.insert(tk.END, f"❌ エラーが発生しました: {e}\n")
    
    def on_addon_action_click(self, event, addon_data):
        """アドオンアクションクリック処理"""
        # クリック位置のテキストを取得
        index = self.local_text.index("@%s,%s" % (event.x, event.y))
        line_start = self.local_text.index("%s linestart" % index)
        line_end = self.local_text.index("%s lineend" % index)
        line_text = self.local_text.get(line_start, line_end)
        
        if "📁" in line_text:
            # フォルダを開く
            self.open_addon_folder(addon_data)
        elif "🗑️" in line_text:
            # 削除
            self.delete_addon(addon_data)
        elif "ℹ️" in line_text:
            # 詳細表示
            self.show_addon_details(addon_data)
    
    def open_addon_folder(self, addon_data):
        """アドオンフォルダを開く"""
        try:
            folder_path = Path(addon_data['file_path']).parent
            if folder_path.exists():
                os.startfile(str(folder_path))  # Windows
            else:
                messagebox.showwarning("警告", "フォルダが見つかりません")
        except Exception as e:
            messagebox.showerror("エラー", f"フォルダを開けませんでした: {e}")
    
    def delete_addon(self, addon_data):
        """アドオン削除"""
        addon_name = addon_data['name']
        if messagebox.askyesno("確認", f"'{addon_name}' を削除しますか？\n\n注意: この操作は元に戻せません。"):
            try:
                file_path = Path(addon_data['file_path'])
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    import shutil
                    shutil.rmtree(str(file_path))
                
                messagebox.showinfo("完了", f"'{addon_name}' を削除しました")
                self.scan_and_display_local_addons()  # リストを更新
                
            except Exception as e:
                messagebox.showerror("エラー", f"削除に失敗しました: {e}")
    
    def show_addon_details(self, addon_data):
        """アドオン詳細表示"""
        details = f"""
📦 アドオン詳細情報

🔧 名前: {addon_data['name']}
📊 バージョン: {".".join(map(str, addon_data['version']))}
👤 作者: {addon_data['author']}
📂 カテゴリ: {addon_data['category']}
🎯 対応Blender: {".".join(map(str, addon_data['blender_version']))}+
💾 ファイルサイズ: {addon_data['file_size'] / (1024 * 1024):.2f} MB
📄 タイプ: {'ファイル' if addon_data['type'] == 'file' else 'フォルダ'}
📍 場所: {addon_data['file_path']}
📅 更新日時: {datetime.fromtimestamp(addon_data['modified_date']).strftime('%Y-%m-%d %H:%M:%S')}

📝 説明:
{addon_data['description']}
        """
        messagebox.showinfo(f"'{addon_data['name']}' の詳細", details)
    
    def add_custom_folder(self):
        """カスタムアドオンフォルダを追加"""
        folder = filedialog.askdirectory(title="アドオンフォルダを選択")
        if folder:
            if folder not in self.addon_folders:
                self.addon_folders.append(folder)
                messagebox.showinfo("成功", f"{self.get_text('folder_added')}:\n{folder}")
            else:
                messagebox.showwarning("警告", self.get_text('folder_exists'))
        
    def create_sidebar(self, parent):
        """右側サイドバーの作成"""
        # 使い方ガイドセクション
        usage_frame = tk.LabelFrame(
            parent,
            text=self.get_text('usage_guide'),
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_white'],
            relief='flat',
            bd=2
        )
        usage_frame.pack(fill='x', pady=(0, 15))
        
        # 使い方ボタン群
        usage_buttons = [
            (self.get_text('add_bookmark_guide'), self.show_add_bookmark_guide),
            (self.get_text('search_tips'), self.show_search_tips),
            (self.get_text('install_guide'), self.show_install_guide),
            (self.get_text('asset_guide'), self.show_asset_guide),
            (self.get_text('troubleshooting'), self.show_troubleshooting),
            (self.get_text('faq'), self.show_faq)
        ]
        
        for text, command in usage_buttons:
            btn = tk.Button(
                usage_frame,
                text=text,
                font=("Segoe UI", 9),
                bg=self.colors['bg_light'],
                fg=self.colors['text_white'],
                relief='flat',
                padx=10,
                pady=5,
                command=command,
                anchor='w'
            )
            btn.pack(fill='x', padx=10, pady=2)
        
        # ブックマークセクション
        bookmark_frame = tk.LabelFrame(
            parent,
            text=self.get_text('bookmarks'),
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_white'],
            relief='flat',
            bd=2
        )
        bookmark_frame.pack(fill='x', pady=(0, 15))
        
        # ブックマークリストボックス
        self.bookmark_listbox = tk.Listbox(
            bookmark_frame,
            font=("Segoe UI", 9),
            bg=self.colors['bg_dark'],
            fg=self.colors['text_white'],
            selectbackground=self.colors['accent_blue'],
            relief='flat',
            bd=0,
            height=5
        )
        self.bookmark_listbox.pack(fill='x', padx=10, pady=10)
        self.bookmark_listbox.bind('<Double-Button-1>', self.on_bookmark_double_click)
        
        # ブックマーク操作ボタン
        bookmark_btn_frame = tk.Frame(bookmark_frame, bg=self.colors['bg_medium'])
        bookmark_btn_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        open_bookmark_btn = tk.Button(
            bookmark_btn_frame,
            text=self.get_text('open'),
            font=("Segoe UI", 8),
            bg=self.colors['success'],
            fg='white',
            relief='flat',
            padx=8,
            pady=3,
            command=self.open_bookmark
        )
        open_bookmark_btn.pack(side='left', padx=(0, 5))
        
        delete_bookmark_btn = tk.Button(
            bookmark_btn_frame,
            text=self.get_text('delete'),
            font=("Segoe UI", 8),
            bg=self.colors['orange'],
            fg='white',
            relief='flat',
            padx=8,
            pady=3,
            command=self.delete_bookmark
        )
        delete_bookmark_btn.pack(side='right')

        # 手動追加フレーム
        add_bookmark_frame = tk.Frame(bookmark_frame, bg=self.colors['bg_medium'])
        add_bookmark_frame.pack(fill='x', padx=10, pady=(5, 10))

        tk.Label(add_bookmark_frame, text=self.get_text('bookmark_url_label'), font=("Segoe UI", 8), bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(anchor='w')
        self.bookmark_url_var = tk.StringVar()
        url_entry = tk.Entry(add_bookmark_frame, textvariable=self.bookmark_url_var, font=("Segoe UI", 9), bg=self.colors['bg_dark'], fg=self.colors['text_white'], relief='flat', insertbackground=self.colors['text_white'])
        url_entry.pack(fill='x', pady=(0, 5))

        tk.Label(add_bookmark_frame, text=self.get_text('bookmark_name_label'), font=("Segoe UI", 8), bg=self.colors['bg_medium'], fg=self.colors['text_white']).pack(anchor='w')
        self.bookmark_name_var = tk.StringVar()
        name_entry = tk.Entry(add_bookmark_frame, textvariable=self.bookmark_name_var, font=("Segoe UI", 9), bg=self.colors['bg_dark'], fg=self.colors['text_white'], relief='flat', insertbackground=self.colors['text_white'])
        name_entry.pack(fill='x', pady=(0, 5))

        add_btn = tk.Button(
            add_bookmark_frame,
            text=self.get_text('bookmark_add_btn'),
            font=("Segoe UI", 9, "bold"),
            bg=self.colors['accent_blue'],
            fg='white',
            relief='flat',
            command=self.add_bookmark_manually
        )
        add_btn.pack(fill='x', pady=5)
        
        # 履歴セクション
        history_frame = tk.LabelFrame(
            parent,
            text=self.get_text('search_history'),
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_white'],
            relief='flat',
            bd=2
        )
        history_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # 履歴リストボックス
        self.history_listbox = tk.Listbox(
            history_frame,
            font=("Segoe UI", 9),
            bg=self.colors['bg_dark'],
            fg=self.colors['text_white'],
            selectbackground=self.colors['accent_blue'],
            relief='flat',
            bd=0,
            height=6
        )
        self.history_listbox.pack(fill='both', expand=True, padx=10, pady=10)
        self.history_listbox.bind('<Double-Button-1>', self.on_history_select)
        
        # 履歴操作ボタン
        history_btn_frame = tk.Frame(history_frame, bg=self.colors['bg_medium'])
        history_btn_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        refresh_btn = tk.Button(
            history_btn_frame,
            text=self.get_text('refresh'),
            font=("Segoe UI", 8),
            bg=self.colors['bg_light'],
            fg=self.colors['text_white'],
            relief='flat',
            padx=8,
            pady=3,
            command=self.refresh_history
        )
        refresh_btn.pack(side='left', padx=(0, 5))
        
        clear_history_btn = tk.Button(
            history_btn_frame,
            text=self.get_text('delete'),
            font=("Segoe UI", 8),
            bg=self.colors['orange'],
            fg='white',
            relief='flat',
            padx=8,
            pady=3,
            command=self.clear_history
        )
        clear_history_btn.pack(side='right')
        
        # おすすめセクション
        recommend_frame = tk.LabelFrame(
            parent,
            text=self.get_text('recommendations'),
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_white'],
            relief='flat',
            bd=2
        )
        recommend_frame.pack(fill='x')
        
        recommend_text = tk.Text(
            recommend_frame,
            font=("Segoe UI", 8),
            bg=self.colors['bg_dark'],
            fg=self.colors['text_gray'],
            relief='flat',
            bd=0,
            height=4,
            wrap='word'
        )
        recommend_text.pack(fill='x', padx=10, pady=10)
        
        recommend_content = self.get_text('recommend_text')
        recommend_text.insert('1.0', recommend_content)
        recommend_text.config(state='disabled')
        
    def create_footer(self):
        """フッター部分の作成"""
        footer_frame = tk.Frame(self.root, bg=self.colors['bg_light'], height=50)
        footer_frame.pack(fill='x', side='bottom')
        footer_frame.pack_propagate(False)
        
        # ステータス表示
        self.status_var = tk.StringVar(value=self.get_text('ready'))
        status_label = tk.Label(
            footer_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text_gray']
        )
        status_label.pack(side='left', padx=20, pady=15)
        
        # 履歴ボタン
        history_btn = tk.Button(
            footer_frame,
            text=self.get_text('history'),
            font=("Segoe UI", 9),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_white'],
            relief='flat',
            padx=15,
            command=self.show_history
        )
        history_btn.pack(side='right', padx=10, pady=15)
        
        # クリアボタン
        clear_btn = tk.Button(
            footer_frame,
            text=self.get_text('clear'),
            font=("Segoe UI", 9),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_white'],
            relief='flat',
            padx=15,
            command=self.clear_results
        )
        clear_btn.pack(side='right', padx=5, pady=15)
        
    def search(self):
        """検索実行"""
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning(self.get_text('warning'), self.get_text('enter_query'))
            return
            
        # 検索結果タブに切り替え
        self.switch_tab('search')
            
        self.status_var.set(self.get_text('searching'))
        self.clear_results()
        
        # 非同期検索実行
        threading.Thread(target=self._perform_search, args=(query,), daemon=True).start()
        
    def _perform_search(self, query):
        """実際の検索処理（バックグラウンド）"""
        try:
            mode = self.search_mode.get()
            results = []

            # ローカル検索の前に、必要であればアドオンをスキャンする
            if mode in ["local", "both"] and not hasattr(self, '_local_scanned'):
                self.scan_local_addons()
                self._local_scanned = True # スキャン済みフラグを立てる
            
            if mode in ["local", "both"]:
                local_results = self.search_local(query)
                results.extend(local_results)
                
            if mode in ["web", "both"]:
                # GitHub検索
                github_results = self.search_github(query)
                results.extend(github_results)
                
                # Google検索（Web検索）
                google_results = self.search_google(query)
                results.extend(google_results)
                
            # UI更新
            self.root.after(0, lambda: self._display_results(results, query))
            
        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))
            
    def search_local(self, query):
        """ローカルアドオンリストから検索"""
        if not self.local_addons:
            self.scan_local_addons() #念のためスキャン

        results = []
        for addon in self.local_addons:
            #名前にクエリが含まれているか、説明にクエリが含まれているか
            if query.lower() in addon.get('name', '').lower() or \
               query.lower() in addon.get('description', '').lower():
                # _display_results が期待する形式に変換
                results.append({
                    'name': addon.get('name', '名前なし'),
                    'description': addon.get('description', '説明なし'),
                    'url': f"file:///{addon.get('file_path', '')}", #クリック可能なようにfile URIスキームを使用
                    'type': 'local'
                })
        return results
        
    def search_github(self, query):
        """GitHub API検索"""
        try:
            url = "https://api.github.com/search/repositories"
            params = {
                "q": f"{query} blender addon",
                "sort": "stars",
                "order": "desc",
                "per_page": 3  # Google検索も含むので減らす
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            results = []
            for item in data.get("items", []):
                results.append({
                    "name": item["name"],
                    "description": item.get("description", "No description"),
                    "url": item["html_url"],
                    "stars": item["stargazers_count"],
                    "type": "github"
                })
                
            return results
            
        except Exception as e:
            return [{"name": "GitHub Search Error", "description": str(e), "type": "error"}]
    
    def search_google(self, query):
        """Google検索（カスタムサイト検索）"""
        try:
            results = []
            
            # よく使われるBlender情報サイト
            search_sites = [
                {
                    "name": f"Qiita - {query}",
                    "url": f"https://qiita.com/search?q={quote_plus(query + ' blender')}",
                    "description": f"Qiitaで'{query} blender'の記事を検索します"
                },
                {
                    "name": f"Zenn - {query}",
                    "url": f"https://zenn.dev/search?q={quote_plus(query + ' blender')}",
                    "description": f"Zennで'{query} blender'の記事を検索します"
                },
                {
                    "name": f"YouTube - {query} Tutorial",
                    "url": f"https://www.youtube.com/results?search_query={quote_plus(query + ' blender tutorial')}",
                    "description": f"YouTubeで'{query} blender tutorial'の動画を検索します"
                },
                {
                    "name": f"Google - {query} 使い方",
                    "url": f"https://www.google.com/search?q={quote_plus(query + ' blender 使い方 解説')}",
                    "description": f"Googleで'{query} blender 使い方'を検索します"
                }
            ]
            
            # 検索対象を3個に絞って追加
            for site in search_sites[:3]:
                results.append({
                    "name": site['name'],
                    "description": site["description"],
                    "url": site["url"],
                    "type": "web"
                })
            
            return results
            
        except Exception as e:
            return [{"name": "Web Search Error", "description": str(e), "type": "error"}]
            
    def _display_results(self, results, query):
        """検索結果の表示（ブックマーク機能付き）"""
        self.results_text.delete(1.0, tk.END)
        
        if not results:
            self.results_text.insert(tk.END, self.get_text('no_results') + "\n")
            self.status_var.set(self.get_text('no_results'))
            return
            
        self.results_text.insert(tk.END, f"{self.get_text('search_for').format(query)}\n", "header")
        self.results_text.insert(tk.END, "=" * 60 + "\n\n")
        
        for i, result in enumerate(results, 1):
            # 結果番号とタイトル
            self.results_text.insert(tk.END, f"{i}. {result['name']}\n", "header")
            
            # ソース表示
            if result["type"] == "github":
                source_text = self.get_text('github_stars').format(result.get('stars', 0))
                self.results_text.insert(tk.END, f"   📁 {source_text}\n", "source")
            elif result["type"] == "web":
                self.results_text.insert(tk.END, f"   🌐 {self.get_text('web_result')}\n", "source")
            elif result["type"] == "local":
                self.results_text.insert(tk.END, f"   💾 {self.get_text('local_db')}\n", "source")
            else:
                self.results_text.insert(tk.END, f"   ❌ {self.get_text('error_source')}\n", "source")
            
            # URL表示（全タイプ共通）
            if result.get("url"):
                self.results_text.insert(tk.END, f"   🔗 {result['url']}\n", "url")
                
            # 説明
            self.results_text.insert(tk.END, f"   📝 {result['description']}\n", "description")
            
            # ブックマークボタン（URLがある場合のみ）
            if result.get("url"):
                bookmark_text = "   📌 ブックマークに追加\n"
                start_pos = self.results_text.index("end-1c linestart")
                self.results_text.insert(tk.END, bookmark_text, "bookmark_btn")
                end_pos = self.results_text.index("end-1c lineend")
                
                # クリックイベント設定
                tag_name = f"bookmark_{i}"
                self.results_text.tag_add(tag_name, start_pos, end_pos)
                self.results_text.tag_bind(tag_name, "<Button-1>", 
                    lambda e, r=result: self.add_bookmark_from_result(r))
                self.results_text.tag_bind(tag_name, "<Enter>", 
                    lambda e: self.results_text.config(cursor="hand2"))
                self.results_text.tag_bind(tag_name, "<Leave>", 
                    lambda e: self.results_text.config(cursor=""))
            
            self.results_text.insert(tk.END, "\n")
            
        self.save_search_history(query, len(results))
        self.status_var.set(self.get_text('found_results').format(len(results)))
        self.refresh_history()
        
    def _show_error(self, error_msg):
        """エラー表示"""
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"Error: {error_msg}\n")
        self.status_var.set(self.get_text('error_occurred'))
        
    def clear_results(self):
        """結果クリア"""
        self.results_text.delete(1.0, tk.END)
        self.status_var.set(self.get_text('ready'))
        
    # ブックマーク機能
    def add_bookmark_from_result(self, result):
        """検索結果からブックマーク追加"""
        success = self.add_bookmark(
            result["name"],
            result["url"],
            result["description"]
        )
        
        if success:
            messagebox.showinfo("ブックマーク", self.get_text('bookmark_added').format(result["name"]))
        else:
            messagebox.showwarning("ブックマーク", self.get_text('bookmark_exists').format(result["name"]))
    
    def add_bookmark_manually(self):
        """UIから手動でブックマークを追加"""
        url = self.bookmark_url_var.get().strip()
        if not url:
            messagebox.showwarning(self.get_text('warning'), self.get_text('url_missing'))
            return

        name = self.bookmark_name_var.get().strip()
        if not name:
            # 名前が空の場合はURLからドメイン名を抽出して仮の名前とする
            try:
                domain = url.split('//')[1].split('/')[0]
                name = domain
            except:
                name = url # パース失敗時はURLそのもの

        success = self.add_bookmark(name, url, "手動で追加されたブックマーク")

        if success:
            messagebox.showinfo("ブックマーク", self.get_text('bookmark_added').format(name))
            # 入力欄をクリア
            self.bookmark_url_var.set("")
            self.bookmark_name_var.set("")
        else:
            messagebox.showwarning("ブックマーク", self.get_text('bookmark_exists').format(name))

    def add_bookmark(self, name, url, description):
        """ブックマーク追加"""
        # 重複チェック
        if any(bookmark['url'] == url for bookmark in self.bookmarks):
            return False
        
        bookmark = {
            "name": name,
            "url": url,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        self.bookmarks.append(bookmark)
        self.save_bookmarks()
        self.refresh_bookmarks()
        return True
    
    def refresh_bookmarks(self):
        """ブックマーク表示を更新"""
        self.bookmark_listbox.delete(0, tk.END)
        
        if not self.bookmarks:
            self.bookmark_listbox.insert(0, self.get_text('no_bookmarks'))
            return
            
        for bookmark in self.bookmarks[-10:]:  # 最新10件表示
            display_text = bookmark['name'][:30] + "..." if len(bookmark['name']) > 30 else bookmark['name']
            self.bookmark_listbox.insert(tk.END, display_text)
    
    def on_bookmark_double_click(self, event):
        """ブックマークダブルクリックで開く"""
        self.open_bookmark()
    
    def open_bookmark(self):
        """選択されたブックマークを開く"""
        selection = self.bookmark_listbox.curselection()
        if selection and self.bookmarks:
            index = selection[0]
            if index < len(self.bookmarks):
                bookmark = self.bookmarks[index]
                webbrowser.open(bookmark['url'])
        else:
            messagebox.showwarning("ブックマーク", self.get_text('select_bookmark'))
    
    def delete_bookmark(self):
        """選択されたブックマークを削除"""
        selection = self.bookmark_listbox.curselection()
        if selection and self.bookmarks:
            index = selection[0]
            if index < len(self.bookmarks):
                bookmark = self.bookmarks[index]
                if messagebox.askyesno("確認", f"'{bookmark['name']}' を削除しますか？"):
                    self.bookmarks.pop(index)
                    self.save_bookmarks()
                    self.refresh_bookmarks()
        else:
            messagebox.showwarning("ブックマーク", self.get_text('select_bookmark'))
    
    def on_url_click(self, event):
        """URL クリック処理"""
        # クリック位置のテキストを取得してURLを開く
        index = self.results_text.index("@%s,%s" % (event.x, event.y))
        line_start = self.results_text.index("%s linestart" % index)
        line_end = self.results_text.index("%s lineend" % index)
        line_text = self.results_text.get(line_start, line_end)
        
        # URLを抽出
        if "http" in line_text:
            url = line_text.strip().replace("🔗 ", "").replace("   ", "")
            webbrowser.open(url)
        
    def _show_scrollable_info(self, title, content):
        """スクロール可能な情報表示ウィンドウ"""
        info_window = tk.Toplevel(self.root)
        info_window.title(title)
        info_window.geometry("800x600") # より大きな初期サイズを設定
        
        info_window.transient(self.root) # 親ウィンドウの上に表示
        info_window.grab_set() # 親ウィンドウの操作をロック

        # ウィンドウの背景色を設定
        info_window.configure(bg=self.colors['bg_dark'])

        text_area = scrolledtext.ScrolledText(
            info_window,
            font=("Segoe UI", 8), # フォントサイズを8に変更
            bg=self.colors['bg_dark'],
            fg=self.colors['text_white'],
            insertbackground=self.colors['text_white'],
            relief='flat',
            bd=0,
            wrap='word',
            height=15 # 明示的に高さを設定
        )
        text_area.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        text_area.insert(tk.END, content)
        text_area.update_idletasks() # UIの更新を強制
        text_area.config(state='disabled') # 編集不可にする

        print(f"[DEBUG] Info Window Content Length: {len(content)}")
        print(f"[DEBUG] Info Window Content Lines: {content.count('\n') + 1}")

        # 閉じるボタン
        close_button = tk.Button(
            info_window,
            text=self.get_text('clear'), # 「クリア」ボタンのテキストを流用
            command=info_window.destroy,
            bg=self.colors['accent_blue'],
            fg='white',
            font=("Segoe UI", 10, "bold"),
            relief='flat',
            padx=15,
            pady=5
        )
        close_button.grid(row=1, column=0, pady=5)

        # gridの行と列の拡張を設定
        info_window.grid_rowconfigure(0, weight=1)
        info_window.grid_columnconfigure(0, weight=1)

        self.root.wait_window(info_window) # ウィンドウが閉じるまで待機

    def show_help(self):
        """ヘルプ表示"""
        self._show_scrollable_info("Help", self.get_text('help_text'))
        
    def show_history(self):
        """履歴表示"""
        history_content = ""
        if not self.search_history:
            history_content = self.get_text('no_history')
        else:
            # 最新の履歴から表示
            for entry in reversed(self.search_history):
                query = entry.get('query', '')
                count = entry.get('result_count', 0)
                timestamp = entry.get('timestamp', '')

                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    time_str = timestamp[:10] if timestamp else ''

                if self.current_language.get() == "ja":
                    history_content += f"検索: {query} ({count}件) - {time_str}\n"
                else:
                    history_content += f"Search: {query} ({count} results) - {time_str}\n"
            
        self._show_scrollable_info(self.get_text('search_history'), history_content)
        
    # ガイド機能
    def show_search_tips(self):
        """検索のコツを表示"""
        if self.current_language.get() == "ja":
            tips = """🔍 検索のコツ\n\n効果的な検索方法:\n• 英語キーワードを使用\n• 具体的な機能名で検索\n• 複数のキーワードを組み合わせ\n\nおすすめ検索例:\n- "mesh tools" → メッシュ編集系\n- "animation rigging" → アニメーション系\n- "import export" → インポート/エクスポート系\n- "node editor" → ノード編集系\n- "modeling" → モデリング支援系\n\n🌐 新機能：Google検索\n• 個人ブログの使い方解説\n• Qiita・Zennの技術記事\n• YouTubeのチュートリアル動画\n• 実際のユーザー体験談\n\n📂 NEW！ローカルアドオン管理\n• 「私のアドオン」タブで既存アドオンを管理\n• フォルダ追加でカスタムパス設定（外付けハードディスクのパスも追加可能！）\n• アドオン詳細情報の確認・削除機能\n\n検索のコツ:\n- 短めのキーワードから始める\n- 結果が多すぎる場合は単語を追加\n- GitHubの⭐数が多いものほど人気・安定性が高い\n- Web検索結果をブックマークして後で確認\n            """
        else:
            tips = """🔍 Search Tips\n\nEffective Search Methods:\n• Use English keywords\n• Search by specific function names\n• Combine multiple keywords\n\nRecommended Examples:\n- "mesh tools" → Mesh editing addons\n- "animation rigging" → Animation addons  \n- "import export" → Import/Export tools\n- "node editor" → Node editing tools\n- "modeling" → Modeling assistance\n\n🌐 New Feature: Google Search\n• Personal blog tutorials\n• Qiita & Zenn technical articles\n• YouTube tutorial videos\n• Real user experiences\n\n📂 NEW! Local Addon Management\n• Use "My Addons" tab to manage existing addons\n• Add custom folders for additional paths (External HDD paths can also be added!)\n• View detailed info and delete addons\n\nSearch Tips:\n- Start with shorter keywords\n- Add words if too many results\n- Higher ⭐ count indicates popularity & stability\n- Bookmark web results for later reference\n            """
        self._show_scrollable_info(self.get_text('search_tips'), tips)

    def show_add_bookmark_guide(self):
        """ブラウザからのブックマーク追加方法を表示"""
        if self.current_language.get() == "ja":
            guide = """📖 ブラウザで見つけたページをブックマークする方法\n\nWebブラウザで見つけた便利なアドオン配布ページや解説記事を、このツールに直接ブックマークとして登録できます。\n\n【登録手順】\n\n1. **URLをコピー**\n   Webブラウザのアドレスバーに表示されているページのURL全体を選択し、コピーします。(ショートカットキー: Ctrl + C)\n\n2. **URLを貼り付け**\n   本ツールの右側にあるブックマーク欄の「URL:」入力エリアに、コピーしたURLを貼り付けます。(ショートカットキー: Ctrl + V)\n\n3. **名前を入力（任意）**\n   「名前(任意):」の欄に、ブックマークの分かりやすい名前を入力します。もし空欄のままにした場合は、URLから自動的に名前が設定されます。\n\n4. **「➕ 追加」ボタンをクリック**\n   入力欄の下にある「➕ 追加」ボタンを押すと、ブックマークがリストの一番上に追加されます。\n\nこれで、気になったページをいつでもこのツールから直接開くことができます。\n            """
        else:
            guide = """📖 How to Add Bookmarks from Your Browser\n\nYou can directly save useful addon distribution pages or tutorial articles you find in your web browser to this tool's bookmarks.\n\n【Steps】\n\n1. **Copy the URL**\n   Select the entire URL from your web browser's address bar and copy it. (Shortcut: Ctrl + C)\n\n2. **Paste the URL**\n   Paste the copied URL into the "URL:" input field in the bookmark section on the right side of this tool. (Shortcut: Ctrl + V)\n\n3. **Enter a Name (Optional)**\n   In the "Name (Optional):" field, enter a descriptive name for the bookmark. If you leave it blank, a name will be automatically generated from the URL.\n\n4. **Click the "➕ Add" Button**\n   Press the "➕ Add" button below the input fields. The bookmark will be added to the top of your list.\n\nNow you can easily access your favorite pages directly from this tool.\n            """
        self._show_scrollable_info(self.get_text('add_bookmark_guide'), guide)
        
    def show_install_guide(self):
        """インストール方法を表示"""
        if self.current_language.get() == "ja":
            guide = """📥 アドオンインストール方法\n\n【基本的なインストール手順】\n\n1. Blenderを起動\n2. 上部メニュー「Edit」→「Preferences」\n3. 左側メニューから「Add-ons」を選択\n4. 右上の「Install...」ボタンをクリック\n5. ダウンロードした.pyまたは.zipファイルを選択\n6. 「Install Add-on」をクリック\n7. アドオン一覧から該当アドオンを見つける\n8. チェックボックス☑️をクリックして有効化\n\n【重要なポイント】\n• .zipファイルは展開せずそのまま選択\n• インストール後は必ずチェックボックスで有効化\n• User Preferencesを保存推奨\n\n【GitHubからのダウンロード】\n1. GitHubページの「Code」ボタンをクリック\n2. 「Download ZIP」を選択\n3. ダウンロードしたzipファイルをそのまま使用\n\n【🌐 Web検索結果の活用】\n• ブックマークした解説記事を参考に\n• YouTubeチュートリアルで視覚的に学習\n• 個人ブログの体験談で注意点を確認\n\n【📂 ローカルアドオン管理機能】\n• インストール後は「私のアドオン」タブで確認\n• アドオンフォルダを直接開いて管理\n• 不要なアドオンの削除も可能\n\n【トラブル時】\n• Blenderのバージョン互換性を確認\n• アドオンが表示されない場合は再起動\n• エラーが出る場合はBlenderのコンソールを確認\n            """
        else:
            guide = """📥 Addon Installation Guide\n\n【Basic Installation Steps】\n\n1. Start Blender\n2. Go to Edit → Preferences\n3. Select "Add-ons" from left menu\n4. Click "Install..." button on top right\n5. Select downloaded .py or .zip file\n6. Click "Install Add-on"\n7. Find the addon in the list\n8. Check the checkbox ☑️ to enable\n\n【Important Points】\n• Don't extract .zip files, select them directly\n• Always enable with checkbox after installation\n• Save User Preferences recommended\n\n【Downloading from GitHub】\n1. Click "Code" button on GitHub page\n2. Select "Download ZIP"\n3. Use the downloaded zip file directly\n\n【🌐 Using Web Search Results】\n• Reference bookmarked tutorial articles\n• Learn visually with YouTube tutorials\n• Check personal blog experiences for tips\n\n【📂 Local Addon Management】\n• Check installed addons in "My Addons" tab\n• Open addon folders directly for management\n• Delete unnecessary addons when needed\n\n【Troubleshooting】\n• Check Blender version compatibility\n• Restart Blender if addon doesn't appear\n• Check Blender console for errors\n            """
        self._show_scrollable_info(self.get_text('install_guide'), guide)

    def show_asset_guide(self):
        """Asset管理ガイドを表示"""
        if self.current_language.get() == "ja":
            guide = """📦 Asset登録・管理ガイド\n\n【Asset Browserとは？】\nBlender 3.0以降の素材管理システム。テクスチャ、マテリアル、オブジェクト、ノードグループなどを効率的に保存・再利用できます。\n\n【ダウンロードしたAssetの登録方法】\n\n1️⃣ Asset Libraryフォルダの準備\n• Windows: C:\\Users\\\\[ユーザー名]\\\\Documents\\\\Blender\\\\Assets\\\
• Mac: ~/Documents/Blender/Assets/\n• または任意のフォルダを指定\n\n2️⃣ Asset Libraryの設定\n• Edit → Preferences → File Paths\n• 「Asset Libraries」セクション\n• 「+」ボタンでライブラリ追加\n• フォルダパスを指定\n\n3️⃣ ファイルの配置\n• ダウンロードした.blendファイルをライブラリフォルダに配置\n• サブフォルダで分類（例：Materials/, Objects/, Textures/）\n\n【オブジェクトをAssetとして登録】\n\n1️⃣ オブジェクトの準備\n• 登録したいオブジェクトを選択\n• 適切な名前に変更\n• マテリアル・テクスチャを適用\n\n2️⃣ Asset登録\n• Outlinerで対象オブジェクトを右クリック\n• 「Mark as Asset」を選択\n• または Asset Browser でドラッグ&ドロップ\n\n3️⃣ Asset情報の設定\n• Asset Browser でアセット選択\n• 右パネルでプレビュー、説明、タグを設定\n• カタログで分類（推奨）\n\n【Asset Browserからの利用】\n\n1️⃣ Asset Browserを開く\n• ファイルエリアのエディタタイプを「Asset Browser」に変更\n• またはShift+F1で切り替え\n\n2️⃣ Assetの配置\n• 使いたいAssetを選択\n• 3Dビューポートにドラッグ&ドロップ\n• またはダブルクリックで追加\n\n【🌐 Web検索との連携】\n• ブックマークしたAsset配布サイトを定期チェック\n• YouTubeのAsset管理チュートリアルを参考\n• Qiita・Zennの技術記事で効率的な管理法を学習\n\n【📂 ローカルアドオン管理との連携】\n• 「私のアドオン」でアドオンフォルダを管理\n• Asset関連アドオンの動作確認\n• アドオンによるAsset自動生成機能の活用\n\n【便利なTips】\n• カタログ機能で分類整理\n• プレビュー画像の自動生成\n• 検索・フィルター機能活用\n• .blend1バックアップファイルの定期削除\n• チームでの共有にはクラウドストレージ活用\n            """
        else:
            guide = """📦 Asset Registration & Management Guide\n\n【What is Asset Browser?】\nMaterial management system in Blender 3.0+. Efficiently save and reuse textures, materials, objects, node groups, etc.\n\n【Registering Downloaded Assets】\n\n1️⃣ Prepare Asset Library Folder\n• Windows: C:\\Users\\\\[username]\\\\Documents\\\\Blender\\\\Assets\\\
• Mac: ~/Documents/Blender/Assets/\n• Or specify custom folder\n\n2️⃣ Asset Library Setup\n• Edit → Preferences → File Paths\n• "Asset Libraries" section\n• Click "+" to add library\n• Specify folder path\n\n3️⃣ File Placement\n• Place downloaded .blend files in library folder\n• Organize with subfolders (e.g., Materials/, Objects/, Textures/)\n\n【Register Objects as Assets】\n\n1️⃣ Prepare Object\n• Select object to register\n• Rename appropriately\n• Apply materials/textures\n\n2️⃣ Asset Registration\n• Right-click object in Outliner\n• Select "Mark as Asset"\n• Or drag & drop in Asset Browser\n\n3️⃣ Asset Information Setup\n• Select asset in Asset Browser\n• Set preview, description, tags in right panel\n• Use catalogs for organization (recommended)\n\n【Using Assets from Asset Browser】\n\n1️⃣ Open Asset Browser\n• Change file area editor type to "Asset Browser"\n• Or use Shift+F1 to switch\n\n2️⃣ Asset Placement\n• Select desired asset\n• Drag & drop to 3D viewport\n• Or double-click to add\n\n【🌐 Web Search Integration】\n• Regularly check bookmarked asset distribution sites\n• Reference YouTube asset management tutorials\n• Learn efficient management from Qiita & Zenn articles\n\n【📂 Local Addon Management Integration】\n• Manage addon folders with "My Addons"\n• Check asset-related addon functionality\n• Utilize automatic asset generation features\n\n【Useful Tips】\n• Use catalog feature for organization\n• Automatic preview generation\n• Utilize search & filter functions\n• Regularly delete .blend1 backup files\n• Use cloud storage for team sharing\n            """
        self._show_scrollable_info(self.get_text('asset_guide'), guide)
        
    def show_troubleshooting(self):
        """トラブルシューティングを表示"""
        if self.current_language.get() == "ja":
            trouble = """🛠️ トラブルシューティング\n\n【よくある問題と解決法】\n\n❌ アドオンが表示されない\n✅ 解決法:\n  • Blenderバージョンの互換性確認\n  • Blenderを再起動\n  • Add-ons画面で「Refresh」ボタン\n  • ファイルパスに日本語が含まれていないか確認\n  • 「私のアドオン」タブでローカル確認\n\n❌ アドオン機能が動作しない  \n✅ 解決法:\n  • アドオンが有効化(☑️)されているか確認\n  • 他のアドオンとの競合チェック\n  • Blenderコンソールでエラー確認\n  • ブックマークした解説記事を参考\n  • 「私のアドオン」で詳細情報確認\n\n❌ インストール時にエラー\n✅ 解決法:\n  • ファイルが破損していないか確認\n  • 管理者権限でBlenderを起動\n  • ウイルスソフトが干渉していないか確認\n  • 古いバージョンのアドオンを削除\n  • 「私のアドオン」で重複チェック\n\n❌ Web検索結果が見つからない\n✅ 解決法:\n  • より一般的なキーワードを使用\n  • 英語での検索を試す\n  • 検索モードを「全検索」に変更\n  • ブックマークした情報サイトを直接確認\n\n❌ 検索結果が少ない\n✅ 解決法:\n  • キーワードを短く、シンプルに\n  • 「mesh」「animation」など基本用語で検索\n  • YouTube検索で動画チュートリアルを探す\n\n❌ ローカルアドオンが見つからない\n✅ 解決法:\n  • 「フォルダ追加」で追加パス設定（外付けハードディスクのパスも追加可能！）\n  • Blenderのアドオンフォルダを確認\n  • 手動でフォルダパスを追加\n  • スキャンボタンで再検索実行\n            """
        else:
            trouble = """🛠️ Troubleshooting\n\n【Common Issues & Solutions】\n\n❌ Addon not showing\n✅ Solutions:\n  • Check Blender version compatibility\n  • Restart Blender\n  • Click "Refresh" in Add-ons panel\n  • Check if file path contains special characters\n  • Verify in "My Addons" tab\n\n❌ Addon features not working\n✅ Solutions:\n  • Verify addon is enabled (☑️)\n  • Check for conflicts with other addons\n  • Check Blender console for errors\n  • Reference bookmarked tutorial articles\n  • Check details in "My Addons"\n\n❌ Installation errors\n✅ Solutions:\n  • Check if file is corrupted\n  • Run Blender as administrator\n  • Check antivirus interference\n  • Remove old addon versions\n  • Check for duplicates in "My Addons"\n\n❌ Web search results not found\n✅ Solutions:\n  • Use more general keywords\n  • Try searching in English\n  • Change search mode to "All Search"\n  • Check bookmarked information sites directly\n\n❌ Few search results\n✅ Solutions:\n  • Use shorter, simpler keywords\n  • Search with basic terms like "mesh", "animation"\n  • Look for video tutorials on YouTube\n\n❌ Local addons not found\n✅ Solutions:\n  • Use "Add Folder" to set additional paths (External HDD paths can also be added!)\n  • Check Blender addon folder locations\n  • Manually add folder paths\n  • Use "Scan" button to re-search\n            """
        self._show_scrollable_info(self.get_text('troubleshooting'), trouble)
        
    def show_faq(self):
        """よくある質問を表示"""
        if self.current_language.get() == "ja":
            faq = """❓ よくある質問\n\nQ: 無料のアドオンはありますか？\nA: はい！多くのアドオンがオープンソースで無料提供されています。特にGitHubには優秀な無料アドオンが豊富にあります。\n\nQ: Web検索結果の信頼性は？\nA: ⭐数の多いGitHubリポジトリは比較的安全です。個人ブログやQiita記事は参考程度に、公式ドキュメントと合わせて確認してください。\n\nQ: ブックマーク機能の使い方は？\nA: 検索結果の「📌 ブックマークに追加」をクリックするだけです。後でサイドバーから簡単にアクセスできます。\n\nQ: Google検索結果が期待通りでない\nA: 検索キーワードを変更してみてください。「mesh tools 使い方」「animation rigging tutorial」など具体的に。\n\nQ: Asset管理機能はありますか？\nA: 「📦 Asset登録・管理」ガイドで詳しく解説しています。Blender 3.0以降のAsset Browser活用法を学べます。\n\nQ: 古いBlenderでも使えますか？  \nA: アドオンによって対応バージョンが異なります。GitHubページやアドオンの説明文で確認してください。\n\nQ: 商用利用は可能ですか？\nA: ライセンスによって異なります。GPL、MIT、Apache等のオープンソースライセンスなら商用利用可能な場合が多いです。\n\nQ: 「私のアドオン」機能とは？\nA: PCにインストール済みのアドオンを一覧表示・管理する機能です。詳細確認、フォルダ表示、削除が可能です。\n\nQ: このツール自体の使い方がわかりません\nA: 1)検索キーワードを入力、2)検索モード選択、3)検索ボタンクリック、4)「私のアドオン」でローカル管理 の手順です。\n            """
        else:
            faq = """❓ Frequently Asked Questions\n\nQ: Are there free addons available?\nA: Yes! Many addons are open source and free. GitHub has a wealth of excellent free addons.\n\nQ. How reliable are web search results?\nA: GitHub repositories with many ⭐ are relatively safe. Personal blogs and Qiita articles should be used as reference, verified with official documentation.\n\nQ: How to use bookmark feature?\nA: Simply click "📌 Add to bookmarks" in search results. Access them easily from sidebar later.\n\nQ: Web search results not as expected?\nA: Try changing search keywords. Be specific like "mesh tools tutorial", "animation rigging guide".\n\nQ: Is there asset management feature?\nA: Check "📦 Asset Registration" guide for detailed Asset Browser usage in Blender 3.0+.\n\nQ: Can I use them with older Blender?\nA: Compatibility varies by addon. Check descriptions for version info.\n\nQ: Can I use addons commercially?\nA: Depends on the license. GPL, MIT, Apache open source licenses usually allow commercial use.\n\nQ: What is "My Addons" feature?\nA: A feature to list and manage addons installed on your PC. You can view details, open folders, and delete addons.\n\nQ: How to use this tool itself?\nA: 1) Enter search keywords, 2) Select search mode, 3) Click search button, 4) Use "My Addons" for local management.\n            """
        self._show_scrollable_info(self.get_text('faq'), faq)
        
    def refresh_history(self):
        """履歴表示を更新"""
        self.history_listbox.delete(0, tk.END)
        
        if not self.search_history:
            self.history_listbox.insert(0, self.get_text('no_history'))
            return
        
        # 最新10件の履歴を表示
        recent_history = self.search_history[-10:] if len(self.search_history) > 10 else self.search_history
        
        for entry in reversed(recent_history):
            query = entry.get('query', '')
            count = entry.get('result_count', 0)
            timestamp = entry.get('timestamp', '')
            
            # 日時をフォーマット
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%m/%d %H:%M')
            except:
                time_str = timestamp[:10] if timestamp else ''
            
            if self.current_language.get() == "ja":
                display_text = f"{query} ({count}件) - {time_str}"
            else:
                display_text = f"{query} ({count} results) - {time_str}"
            self.history_listbox.insert(0, display_text)
            
    def on_history_select(self, event):
        """履歴項目選択時の処理"""
        selection = self.history_listbox.curselection()
        if selection:
            selected_text = self.history_listbox.get(selection[0])
            # クエリ部分を抽出
            if " (" in selected_text:
                query = selected_text.split(' (')[0]
                self.search_var.set(query)
                self.search()  # 自動的に検索実行
            
    def clear_history(self):
        """履歴をクリア"""
        if messagebox.askyesno(self.get_text('warning'), self.get_text('confirm_clear')):
            self.search_history = []
            self.refresh_history()
            try:
                if os.path.exists(self.history_file):
                    os.remove(self.history_file)
            except:
                pass
        
    def load_data(self):
        """データファイル読み込み"""
        # 検索履歴読み込み
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.search_history = json.load(f)
            else:
                self.search_history = []
        except:
            self.search_history = []
            
        # ブックマーク読み込み
        try:
            if os.path.exists(self.bookmarks_file):
                with open(self.bookmarks_file, 'r', encoding='utf-8') as f:
                    self.bookmarks = json.load(f)
            else:
                self.bookmarks = []
        except:
            self.bookmarks = []
            
    def save_search_history(self, query, result_count):
        """検索履歴保存"""
        try:
            entry = {
                "query": query,
                "result_count": result_count,
                "timestamp": datetime.now().isoformat()
            }
            self.search_history.append(entry)
            
            # 履歴を最新50件に制限
            if len(self.search_history) > 50:
                self.search_history = self.search_history[-50:]
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.search_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"履歴保存エラー: {e}")
            
    def save_bookmarks(self):
        """ブックマーク保存"""
        try:
            with open(self.bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"ブックマーク保存エラー: {e}")
            
    def run(self):
        """アプリケーション実行"""
        self.root.mainloop()

if __name__ == "__main__":
    app = BlenderStyleSearchTool()
    app.run()