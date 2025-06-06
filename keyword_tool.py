# Internet Keyword Research Tool
# Made by Abd El Mouhaimen (@stiwy_xd)

import requests
import json
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
import threading
import os
from requests.sessions import Session

class NetworkTrackingSession(Session):
    def __init__(self):
        super().__init__()
        self.bytes_sent = 0
        self.bytes_received = 0
        self.start_time = time.time()

    def request(self, *args, **kwargs):
        start = time.time()
        response = super().request(*args, **kwargs)
        end = time.time()
        if 'data' in kwargs:
            self.bytes_sent += len(kwargs.get('data', b''))
        elif 'json' in kwargs:
            self.bytes_sent += len(json.dumps(kwargs.get('json', {})))
        self.bytes_sent += len(str(kwargs.get('headers', {})))
        self.bytes_received += len(response.content)
        return response

    def get_network_stats(self):
        elapsed = max(time.time() - self.start_time, 1)
        upload_speed = self.bytes_sent / elapsed / 1024
        download_speed = self.bytes_received / elapsed / 1024
        total_data = (self.bytes_sent + self.bytes_received) / 1024
        return upload_speed, download_speed, total_data

class InternetKeywordTool:
    def __init__(self):
        self.session = NetworkTrackingSession()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.keywords = set()
        self.proxy_config = None
        
    def set_proxy(self, proxy_type, proxy_url):
        if proxy_type == "proxyless":
            self.proxy_config = None
            self.session.proxies.clear()
        else:
            if proxy_type == "http":
                self.proxy_config = {
                    'http': f'http://{proxy_url}',
                    'https': f'http://{proxy_url}'
                }
            elif proxy_type == "socks4":
                self.proxy_config = {
                    'http': f'socks4://{proxy_url}',
                    'https': f'socks4://{proxy_url}'
                }
            elif proxy_type == "socks5":
                self.proxy_config = {
                    'http': f'socks5://{proxy_url}',
                    'https': f'socks5://{proxy_url}'
                }
            if self.proxy_config:
                self.session.proxies.update(self.proxy_config)
    
    def test_proxy(self, proxy_type, proxy_url, timeout=10):
        test_session = NetworkTrackingSession()
        if proxy_type == "http":
            proxy_config = {
                'http': f'http://{proxy_url}',
                'https': f'http://{proxy_url}'
            }
        elif proxy_type == "socks4":
            proxy_config = {
                'http': f'socks4://{proxy_url}',
                'https': f'socks4://{proxy_url}'
            }
        elif proxy_type == "socks5":
            proxy_config = {
                'http': f'socks5://{proxy_url}',
                'https': f'socks5://{proxy_url}'
            }
        try:
            test_session.proxies.update(proxy_config)
            response = test_session.get('http://httpbin.org/ip', timeout=timeout)
            if response.status_code == 200:
                return True, response.json().get('origin', 'Unknown')
        except Exception as e:
            return False, str(e)
        return False, "Connection failed"
        
    def get_network_stats(self):
        return self.session.get_network_stats()
        
    def get_google_suggestions(self, keyword):
        suggestions = []
        try:
            url = f"http://suggestqueries.google.com/complete/search?client=chrome&q={quote_plus(keyword)}"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = json.loads(response.text)
                if len(data) > 1:
                    suggestions.extend(data[1][:15])
        except Exception:
            pass
        return suggestions
    
    def get_bing_suggestions(self, keyword):
        suggestions = []
        try:
            url = f"https://www.bing.com/AS/Suggestions?pt=page.serp&mkt=en-us&qry={quote_plus(keyword)}&cp=7&cvid=123"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                suggestion_items = soup.find_all('li', class_='sa_sg')
                for item in suggestion_items:
                    query = item.get('query', '')
                    if query and query != keyword:
                        suggestions.append(query)
        except Exception:
            pass
        return suggestions[:10]
    
    def get_duckduckgo_suggestions(self, keyword):
        suggestions = []
        try:
            url = f"https://duckduckgo.com/ac/?q={quote_plus(keyword)}&type=list"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = json.loads(response.text)
                if isinstance(data, list) and len(data) > 1:
                    suggestions.extend([item['phrase'] for item in data[1] if 'phrase' in item])
        except Exception:
            pass
        return suggestions[:10]
    
    def get_youtube_suggestions(self, keyword):
        suggestions = []
        try:
            url = f"https://suggestqueries.google.com/complete/search?client=youtube&ds=yt&q={quote_plus(keyword)}"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                text = response.text
                if text.startswith('window.google.ac.h('):
                    json_text = text[19:-1]
                    data = json.loads(json_text)
                    if len(data) > 1:
                        suggestions.extend([item[0] for item in data[1]])
        except Exception:
            pass
        return suggestions[:10]
    
    def get_amazon_suggestions(self, keyword):
        suggestions = []
        try:
            url = f"https://completion.amazon.com/search/complete?search-alias=aps&client=amazon-search-ui&mkt=1&q={quote_plus(keyword)}"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = json.loads(response.text)
                if len(data) > 1:
                    suggestions.extend(data[1])
        except Exception:
            pass
        return suggestions[:10]
    
    def get_related_searches_from_serp(self, keyword, page=1):
        related_searches = []
        try:
            url = f"https://www.google.com/search?q={quote_plus(keyword)}&start={(page-1)*10}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            response = self.session.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                related_elements = soup.find_all(['div', 'span'], string=re.compile(r'related|people also|searches for', re.I))
                for element in soup.find_all('div'):
                    text = element.get_text().lower()
                    if 'related searches' in text or 'people also search' in text:
                        for link in element.find_all('a'):
                            link_text = link.get_text().strip()
                            if link_text and len(link_text) > 3 and link_text != keyword:
                                related_searches.append(link_text)
                suggestion_divs = soup.find_all('div', {'data-ved': True})
                for div in suggestion_divs:
                    text = div.get_text().strip()
                    if text and len(text.split()) <= 8 and keyword.lower() in text.lower():
                        related_searches.append(text)
        except Exception:
            pass
        return list(set(related_searches))[:15]
    
    def get_alphabet_suggestions(self, keyword):
        alphabet_suggestions = []
        letters = 'abcdefghijklmnopqrstuvwxyz'
        def fetch_letter_suggestions(letter):
            try:
                query = f"{keyword} {letter}"
                url = f"http://suggestqueries.google.com/complete/search?client=chrome&q={quote_plus(query)}"
                response = self.session.get(url, timeout=5)
                if response.status_code == 200:
                    data = json.loads(response.text)
                    if len(data) > 1:
                        return data[1][:3]
            except Exception:
                pass
            return []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_letter = {executor.submit(fetch_letter_suggestions, letter): letter for letter in letters[:10]}
            for future in as_completed(future_to_letter):
                suggestions = future.result()
                alphabet_suggestions.extend(suggestions)
        return alphabet_suggestions
    
    def search_keywords(self, seed_keyword, max_results=200, max_pages=1, progress_callback=None):
        all_keywords = set()
        all_keywords.add(seed_keyword)
        search_functions = [
            ("Google Autocomplete", self.get_google_suggestions, False),
            ("Bing Suggestions", self.get_bing_suggestions, False),
            ("DuckDuckGo Suggestions", self.get_duckduckgo_suggestions, False),
            ("YouTube Suggestions", self.get_youtube_suggestions, False),
            ("Amazon Suggestions", self.get_amazon_suggestions, False),
            ("Google Related Searches", self.get_related_searches_from_serp, True),
            ("Alphabet Suggestions", self.get_alphabet_suggestions, False)
        ]
        total_steps = sum(1 + (max_pages - 1) if supports_pagination else 1 for _, _, supports_pagination in search_functions)
        current_step = 0
        for source_name, search_func, supports_pagination in search_functions:
            try:
                if supports_pagination:
                    for page in range(1, max_pages + 1):
                        if progress_callback:
                            progress_callback(f"🔍 {source_name} (Page {page}/{max_pages})...")
                        keywords = search_func(seed_keyword, page=page) if source_name == "Google Related Searches" else search_func(seed_keyword)
                        if keywords:
                            valid_keywords = [kw for kw in keywords if kw and len(kw.strip()) > 2]
                            all_keywords.update(valid_keywords)
                        current_step += 1
                        if progress_callback:
                            progress = (current_step / total_steps) * 100
                            progress_callback(f"📊 Progress: {progress:.0f}%")
                        time.sleep(random.uniform(1, 2))
                else:
                    if progress_callback:
                        progress_callback(f"🔍 {source_name}...")
                    keywords = search_func(seed_keyword)
                    if keywords:
                        valid_keywords = [kw for kw in keywords if kw and len(kw.strip()) > 2]
                        all_keywords.update(valid_keywords)
                    current_step += 1
                    if progress_callback:
                        progress = (current_step / total_steps) * 100
                        progress_callback(f"📊 Progress: {progress:.0f}%")
                    time.sleep(0.5)
            except Exception:
                pass
        cleaned_keywords = []
        for keyword in all_keywords:
            if keyword and isinstance(keyword, str):
                keyword = keyword.strip()
                if (len(keyword) > 2 and 
                    len(keyword) < 100 and 
                    not keyword.startswith('http') and
                    not re.search(r'[^\w\s\-\']', keyword)):
                    cleaned_keywords.append(keyword)
        unique_keywords = list(set(cleaned_keywords))
        unique_keywords.sort(key=len)
        if len(unique_keywords) > max_results:
            unique_keywords = unique_keywords[:max_results]
        return unique_keywords

class ModernKeywordToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 Internet Keyword Research Tool")
        self.root.geometry("1200x800")
        self.tool = InternetKeywordTool()
        self.all_keywords = set()
        self.proxy_list = []
        self.valid_proxies = []
        self.current_proxy = None
        self.setup_ui()
        self.update_network_stats()
        
    def setup_ui(self):
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=BOTH, expand=True, padx=25, pady=25)
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=X, pady=(0, 25))
        credits_label = ttk.Label(header_frame, text="MADE BY: ABD EL MOUHAIMEN", 
                                 font=('Segoe UI', 14, 'bold'), foreground='#FF6B6B')
        credits_label.pack(side=LEFT, padx=(10, 0))
        title_label = ttk.Label(header_frame, text="🔍 Internet Keyword Research Tool", 
                               font=('Segoe UI', 28, 'bold'), foreground='#00D4FF')
        title_label.pack(pady=(5, 0))
        self.notebook = ttk.Notebook(main_container, bootstyle="info")
        self.notebook.pack(fill=BOTH, expand=True, pady=(0, 15))
        self.keyword_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.keyword_tab, text="🎯 Keyword Research")
        self.proxy_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.proxy_tab, text="🌐 Proxy Manager")
        self.setup_keyword_tab()
        self.setup_proxy_tab()
        
        footer_frame = ttk.Frame(main_container)
        footer_frame.pack(side=BOTTOM, fill=X, pady=(15, 0))
        
        social_frame = ttk.Frame(footer_frame)
        social_frame.pack(side=LEFT, padx=10)
        
        github_icon = ttk.Label(social_frame, text="🐙", font=('Segoe UI', 12))
        github_icon.pack(side=LEFT, padx=(0, 5))
        github_label = ttk.Label(
            social_frame, 
            text="GitHub", 
            font=('Segoe UI', 12, 'underline'), 
            foreground='#FFFFFF', 
            cursor="hand2"
        )
        github_label.pack(side=LEFT)
        github_label.bind("<Button-1>", lambda e: self.open_link("https://github.com/Stiwyxd/"))
        
        ttk.Label(social_frame, text="•", foreground='#555555').pack(side=LEFT, padx=10)
        
        telegram_icon = ttk.Label(social_frame, text="📱", font=('Segoe UI', 12))
        telegram_icon.pack(side=LEFT, padx=(0, 5))
        telegram_label = ttk.Label(
            social_frame, 
            text="Telegram", 
            font=('Segoe UI', 12, 'underline'), 
            foreground='#1DA1F2', 
            cursor="hand2"
        )
        telegram_label.pack(side=LEFT)
        telegram_label.bind("<Button-1>", lambda e: self.open_link("https://t.me/stiwy_xd"))
        
        credits_frame = ttk.Frame(footer_frame)
        credits_frame.pack(side=RIGHT, padx=10)
        
        made_by_label = ttk.Label(
            credits_frame,
            text="MADE BY: ABD EL MOUHAIMEN",
            font=('Segoe UI', 14, 'bold'),
            foreground='#FF00FF'
        )
        made_by_label.pack(side=RIGHT)
        
        self.animate_glow(made_by_label)
        
    def animate_glow(self, label):
        colors = ['#FF00FF', '#FF33FF', '#FF66FF', '#FF99FF', '#FFCCFF', '#FFFFFF', '#FFCCFF', '#FF99FF', '#FF66FF', '#FF33FF']
        def cycle_colors(index=0):
            color = colors[index]
            label.config(foreground=color)
            next_index = (index + 1) % len(colors)
            label.after(200, lambda: cycle_colors(next_index))
        cycle_colors()
    
    def open_link(self, url):
        import webbrowser
        webbrowser.open(url)
        
    def setup_keyword_tab(self):
        keyword_container = ttk.Frame(self.keyword_tab)
        keyword_container.pack(fill=BOTH, expand=True, padx=20, pady=20)
        search_frame = ttk.Labelframe(keyword_container, text="🎯 Search Parameters", 
                                     bootstyle="info", padding=20)
        search_frame.pack(fill=X, pady=(0, 20))
        input_frame = ttk.Frame(search_frame)
        input_frame.pack(fill=X, pady=(0, 15))
        ttk.Label(input_frame, text="Enter Keyword:", font=('Segoe UI', 12, 'bold'), 
                 foreground='#87CEEB').pack(anchor=W)
        keyword_frame = ttk.Frame(input_frame)
        keyword_frame.pack(fill=X, pady=(8, 0))
        self.keyword_entry = ttk.Entry(keyword_frame, font=('Segoe UI', 13), 
                                      bootstyle="info", width=40)
        self.keyword_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 15))
        self.keyword_entry.bind('<Return>', self.search_keywords_wrapper)
        self.search_button = ttk.Button(keyword_frame, text="🚀 Search Keywords", 
                                       bootstyle="success", command=self.search_keywords_wrapper)
        self.search_button.pack(side=RIGHT)
        settings_row1 = ttk.Frame(search_frame)
        settings_row1.pack(fill=X, pady=(0, 10))
        ttk.Label(settings_row1, text="Max Results:", font=('Segoe UI', 11), 
                 foreground='#87CEEB').pack(side=LEFT)
        self.max_results_var = tk.StringVar(value="200")
        max_results_entry = ttk.Entry(settings_row1, textvariable=self.max_results_var, 
                                     width=12, bootstyle="info")
        max_results_entry.pack(side=LEFT, padx=(15, 0))
        ttk.Label(settings_row1, text="Max Pages:", font=('Segoe UI', 11), 
                 foreground='#87CEEB').pack(side=LEFT, padx=(20, 0))
        self.max_pages_var = tk.StringVar(value="1")
        max_pages_entry = ttk.Entry(settings_row1, textvariable=self.max_pages_var, 
                                   width=12, bootstyle="info")
        max_pages_entry.pack(side=LEFT, padx=(15, 0))
        button_frame = ttk.Frame(settings_row1)
        button_frame.pack(side=RIGHT)
        self.export_button = ttk.Button(button_frame, text="💾 Export", 
                                       bootstyle="warning", command=self.export_keywords)
        self.export_button.pack(side=RIGHT, padx=(15, 0))
        self.clear_button = ttk.Button(button_frame, text="🗑️ Clear All", 
                                      bootstyle="danger", command=self.clear_results)
        self.clear_button.pack(side=RIGHT, padx=(15, 0))
        status_frame = ttk.Labelframe(keyword_container, text="📊 Status", 
                                     bootstyle="success", padding=12)
        status_frame.pack(fill=X, pady=(0, 20))
        self.status_label = ttk.Label(status_frame, text="✨ Ready to discover keywords...", 
                                     font=('Segoe UI', 11), foreground='#98FB98')
        self.status_label.pack(side=LEFT)
        self.keyword_count_label = ttk.Label(status_frame, text="Total Keywords: 0", 
                                           font=('Segoe UI', 11, 'bold'), foreground='#00FF7F')
        self.keyword_count_label.pack(side=RIGHT)
        network_frame = ttk.Labelframe(keyword_container, text="🌐 Network Stats", 
                                      bootstyle="warning", padding=12)
        network_frame.pack(fill=X, pady=(0, 20))
        self.upload_label = ttk.Label(network_frame, text="Upload: 0.0 KB/s", 
                                    font=('Segoe UI', 11), foreground='#FFD700')
        self.upload_label.pack(side=LEFT, padx=(0, 20))
        self.download_label = ttk.Label(network_frame, text="Download: 0.0 KB/s", 
                                       font=('Segoe UI', 11), foreground='#FFD700')
        self.download_label.pack(side=LEFT, padx=(0, 20))
        self.data_label = ttk.Label(network_frame, text="Data Used: 0.0 KB", 
                                   font=('Segoe UI', 11), foreground='#FFD700')
        self.data_label.pack(side=LEFT)
        self.progress = ttk.Progressbar(keyword_container, bootstyle="info", mode='determinate', maximum=100)
        self.progress.pack(fill=X, pady=(0, 20))
        results_frame = ttk.Labelframe(keyword_container, text="🎯 Discovered Keywords", 
                                      bootstyle="primary", padding=20)
        results_frame.pack(fill=BOTH, expand=True)
        self.results_text = ScrolledText(results_frame, wrap=tk.WORD, height=20,
                                        font=('Consolas', 12), 
                                        background='#1a1a2e', foreground='#00D4FF',
                                        insertbackground='#00D4FF', selectbackground='#16213e')
        self.results_text.pack(fill=BOTH, expand=True)
        
    def setup_proxy_tab(self):
        proxy_container = ttk.Frame(self.proxy_tab)
        proxy_container.pack(fill=BOTH, expand=True, padx=20, pady=20)
        config_frame = ttk.Labelframe(proxy_container, text="🌐 Proxy Configuration", 
                                     bootstyle="secondary", padding=20)
        config_frame.pack(fill=X, pady=(0, 20))
        file_frame = ttk.Frame(config_frame)
        file_frame.pack(fill=X, pady=(0, 15))
        ttk.Label(file_frame, text="Proxy File:", font=('Segoe UI', 12, 'bold'), 
                 foreground='#DDA0DD').pack(anchor=W)
        file_select_frame = ttk.Frame(file_frame)
        file_select_frame.pack(fill=X, pady=(8, 0))
        self.proxy_file_var = tk.StringVar(value="No file selected")
        self.proxy_file_entry = ttk.Entry(file_select_frame, textvariable=self.proxy_file_var, 
                                         font=('Segoe UI', 11), state="readonly", bootstyle="secondary")
        self.proxy_file_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 15))
        self.browse_button = ttk.Button(file_select_frame, text="📁 Browse", 
                                       bootstyle="secondary", command=self.browse_proxy_file)
        self.browse_button.pack(side=RIGHT)
        proxy_config_frame = ttk.Frame(config_frame)
        proxy_config_frame.pack(fill=X, pady=(0, 15))
        ttk.Label(proxy_config_frame, text="Proxy Type:", font=('Segoe UI', 11), 
                 foreground='#DDA0DD').pack(side=LEFT)
        self.proxy_type_var = tk.StringVar(value="http")
        proxy_types = ["http", "socks4", "socks5"]
        proxy_type_combo = ttk.Combobox(proxy_config_frame, textvariable=self.proxy_type_var, 
                                       values=proxy_types, state="readonly", width=12,
                                       bootstyle="secondary")
        proxy_type_combo.pack(side=LEFT, padx=(15, 0))
        validation_frame = ttk.Frame(proxy_config_frame)
        validation_frame.pack(side=RIGHT)
        self.show_valid_var = tk.BooleanVar(value=True)
        self.show_valid_check = ttk.Checkbutton(validation_frame, text="Show Valid Proxies", 
                                               variable=self.show_valid_var, bootstyle="success")
        self.show_valid_check.pack(side=LEFT, padx=(0, 15))
        self.validate_button = ttk.Button(validation_frame, text="🔍 Validate Proxies", 
                                         bootstyle="info", command=self.validate_proxies)
        self.validate_button.pack(side=RIGHT, padx=(15, 0))
        self.load_button = ttk.Button(validation_frame, text="📥 Load Proxies", 
                                     bootstyle="primary", command=self.load_proxies)
        self.load_button.pack(side=RIGHT, padx=(15, 0))
        proxy_status_frame = ttk.Labelframe(proxy_container, text="📊 Proxy Status", 
                                           bootstyle="info", padding=12)
        proxy_status_frame.pack(fill=X, pady=(0, 20))
        self.proxy_status_label = ttk.Label(proxy_status_frame, text="🔄 No proxies loaded", 
                                           font=('Segoe UI', 11), foreground='#87CEEB')
        self.proxy_status_label.pack(side=LEFT)
        self.proxy_count_label = ttk.Label(proxy_status_frame, text="Total: 0 | Valid: 0", 
                                          font=('Segoe UI', 11, 'bold'), foreground='#00D4FF')
        self.proxy_count_label.pack(side=RIGHT)
        controls_frame = ttk.Frame(proxy_container)
        controls_frame.pack(fill=X, pady=(0, 20))
        self.use_proxy_button = ttk.Button(controls_frame, text="🔗 Use Selected Proxy", 
                                          bootstyle="success", command=self.use_selected_proxy)
        self.use_proxy_button.pack(side=LEFT)
        self.proxyless_button = ttk.Button(controls_frame, text="🌐 Go Proxyless", 
                                          bootstyle="warning", command=self.go_proxyless)
        self.proxyless_button.pack(side=LEFT, padx=(15, 0))
        self.export_valid_button = ttk.Button(controls_frame, text="💾 Export Valid", 
                                             bootstyle="secondary", command=self.export_valid_proxies)
        self.export_valid_button.pack(side=RIGHT)
        proxy_list_frame = ttk.Labelframe(proxy_container, text="📋 Proxy List", 
                                         bootstyle="primary", padding=20)
        proxy_list_frame.pack(fill=BOTH, expand=True)
        list_container = ttk.Frame(proxy_list_frame)
        list_container.pack(fill=BOTH, expand=True)
        self.proxy_listbox = tk.Listbox(list_container, font=('Consolas', 11),
                                       background='#1a1a2e', foreground='#00D4FF',
                                       selectbackground='#16213e', selectforeground='#FFFFFF')
        proxy_scrollbar = ttk.Scrollbar(list_container, orient=VERTICAL, command=self.proxy_listbox.yview)
        self.proxy_listbox.configure(yscrollcommand=proxy_scrollbar.set)
        self.proxy_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        proxy_scrollbar.pack(side=RIGHT, fill=Y)
        
    def update_network_stats(self):
        upload_speed, download_speed, total_data = self.tool.get_network_stats()
        self.upload_label.config(text=f"Upload: {upload_speed:.2f} KB/s")
        self.download_label.config(text=f"Download: {download_speed:.2f} KB/s")
        self.data_label.config(text=f"Data Used: {total_data:.2f} KB")
        self.root.after(1000, self.update_network_stats)
        
    def browse_proxy_file(self):
        filename = filedialog.askopenfilename(
            title="Select Proxy File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.proxy_file_var.set(filename)
            
    def load_proxies(self):
        filename = self.proxy_file_var.get()
        if filename == "No file selected" or not os.path.exists(filename):
            messagebox.showwarning("⚠️ Warning", "Please select a valid proxy file first")
            return
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            self.proxy_list = []
            for line in lines:
                line = line.strip()
                if line and ':' in line:
                    self.proxy_list.append(line)
            self.proxy_listbox.delete(0, tk.END)
            if self.proxy_list:
                for proxy in self.proxy_list:
                    self.proxy_listbox.insert(tk.END, f"⚪ {proxy}")
                self.proxy_status_label.config(text=f"📥 Loaded {len(self.proxy_list)} proxies")
                self.update_proxy_count()
                messagebox.showinfo("✅ Success", f"Loaded {len(self.proxy_list)} proxies from file")
            else:
                messagebox.showwarning("⚠️ Warning", "No valid proxies found in file")
        except Exception as e:
            messagebox.showerror("❌ Error", f"Failed to load proxy file:\n{str(e)}")
            
    def validate_proxies(self):
        if not self.proxy_list:
            messagebox.showwarning("⚠️ Warning", "Please load proxies first")
            return
        self.validate_button.config(state='disabled', text="🔍 Validating...")
        self.proxy_status_label.config(text="🔍 Validating proxies...")
        self.progress['value'] = 0
        self.progress['maximum'] = len(self.proxy_list)
        thread = threading.Thread(target=self.validate_proxies_thread)
        thread.daemon = True
        thread.start()
        
    def validate_proxies_thread(self):
        self.valid_proxies = []
        proxy_type = self.proxy_type_var.get()
        for i, proxy in enumerate(self.proxy_list):
            try:
                self.root.after(0, self.update_validation_status, f"🔍 Testing {i+1}/{len(self.proxy_list)}: {proxy}")
                is_valid, result = self.tool.test_proxy(proxy_type, proxy, timeout=5)
                if is_valid:
                    self.valid_proxies.append(proxy)
                    self.root.after(0, self.update_proxy_in_list, i, proxy, "✅", "valid")
                else:
                    self.root.after(0, self.update_proxy_in_list, i, proxy, "❌", "invalid")
                self.root.after(0, self.progress.step, 100/len(self.proxy_list))
                self.root.after(0, self.update_network_stats)
            except Exception as e:
                self.root.after(0, self.update_proxy_in_list, i, proxy, "❌", "error")
        self.root.after(0, self.validation_complete)
        
    def update_validation_status(self, message):
        self.proxy_status_label.config(text=message)
        
    def update_proxy_in_list(self, index, proxy, status, result_type):
        if self.show_valid_var.get():
            if result_type == "valid":
                self.proxy_listbox.delete(index)
                self.proxy_listbox.insert(index, f"{status} {proxy}")
        else:
            self.proxy_listbox.delete(index)
            self.proxy_listbox.insert(index, f"{status} {proxy}")
            
    def validation_complete(self):
        self.validate_button.config(state='normal', text="🔍 Validate Proxies")
        self.proxy_status_label.config(text=f"✅ Validation complete! Found {len(self.valid_proxies)} valid proxies")
        self.progress['value'] = 0
        self.update_proxy_count()
        self.update_network_stats()
        if self.show_valid_var.get():
            self.filter_proxy()
            
    def filter_proxy(self):
        self.proxy_listbox.delete(0, tk.END)
        if self.show_valid_var.get():
            for proxy in self.valid_proxies:
                self.proxy_listbox.insert(tk.END, f"✅ {proxy}")
        else:
            for proxy in self.proxy_list:
                status = "✅" if proxy in self.valid_proxies else "❌"
                self.proxy_listbox.insert(tk.END, f"{status} {proxy}")
        self.update_proxy_count()
        
    def update_proxy_count(self):
        total = len(self.proxy_list)
        valid = len(self.valid_proxies)
        self.proxy_count_label.config(text=f"Total: {total} | Valid: {valid}")
        
    def use_selected_proxy(self):
        try:
            selected = self.proxy_listbox.curselection()
            if not selected:
                messagebox.showwarning("⚠️ Warning", "Please select a proxy from the list")
                return
            proxy = self.proxy_listbox.get(selected[0]).split(" ", 1)[1]
            proxy_type = self.proxy_type_var.get()
            self.tool.set_proxy(proxy_type, proxy)
            self.current_proxy = proxy
            self.proxy_status_label.config(text=f"🔗 Using proxy: {proxy}")
            messagebox.showinfo("✅ Success", f"Now using {proxy_type} proxy: {proxy}")
        except Exception as e:
            messagebox.showerror("❌ Error", f"Failed to use proxy:\n{str(e)}")
            
    def go_proxyless(self):
        try:
            self.tool.set_proxy("proxyless", "")
            self.current_proxy = None
            self.proxy_status_label.config(text="🌐 Running proxyless")
            messagebox.showinfo("✅ Success", "Switched to proxyless mode")
        except Exception as e:
            messagebox.showerror("❌ Error", f"Failed to switch to proxyless mode:\n{str(e)}")
            
    def export_valid_proxies(self):
        if not self.valid_proxies:
            messagebox.showwarning("⚠️ Warning", "No valid proxies to export")
            return
        filename = filedialog.asksaveasfilename(
            title="Save Valid Proxies",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for proxy in self.valid_proxies:
                        f.write(f"{proxy}\n")
                messagebox.showinfo("✅ Success", f"Exported {len(self.valid_proxies)} valid proxies to {filename}")
            except Exception as e:
                messagebox.showerror("❌ Error", f"Failed to export proxies:\n{str(e)}")
                
    def search_keywords_wrapper(self, event=None):
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showwarning("⚠️ Warning", "Please enter a keyword")
            return
        try:
            max_results = int(self.max_results_var.get())
            if max_results <= 0:
                raise ValueError("Max results must be positive")
        except ValueError:
            messagebox.showwarning("⚠️ Warning", "Please enter a valid number for max results")
            return
        try:
            max_pages = int(self.max_pages_var.get())
            if max_pages <= 0 or max_pages > 10:
                raise ValueError("Max pages must be between 1 and 10")
        except ValueError:
            messagebox.showwarning("⚠️ Warning", "Please enter a valid number for max pages (1-10)")
            return
        self.search_button.config(state='disabled')
        self.progress['value'] = 0
        self.progress['maximum'] = 100
        self.status_label.config(text="🔍 Starting keyword research...")
        thread = threading.Thread(target=self.search_keywords_thread, args=(keyword, max_results, max_pages))
        thread.daemon = True
        thread.start()
        
    def search_keywords_thread(self, keyword, max_results, max_pages):
        def update_progress(message):
            self.status_label.config(text=message)
            if "Progress:" in message:
                try:
                    percentage = float(message.split("Progress: ")[1].split("%")[0])
                    self.progress['value'] = percentage
                except:
                    pass
            self.update_network_stats()
        try:
            self.tool.session.bytes_sent = 0
            self.tool.session.bytes_received = 0
            self.tool.session.start_time = time.time()
            keywords = self.tool.search_keywords(keyword, max_results, max_pages, progress_callback=update_progress)
            self.all_keywords.update(keywords)
            self.root.after(0, self.update_results, keywords)
        except Exception as e:
            self.root.after(0, self.search_error, str(e))
            
    def update_results(self, keywords):
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "\n".join(keywords))
        self.keyword_count_label.config(text=f"Total Keywords: {len(self.all_keywords)}")
        self.status_label.config(text="✅ Keyword research complete!")
        self.progress['value'] = 0
        self.search_button.config(state='normal')
        self.update_network_stats()
        messagebox.showinfo("✅ Success", f"Found {len(keywords)} new keywords!\nTotal accumulated: {len(self.all_keywords)}")
        
    def search_error(self, error_message):
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"❌ Error during search:\n{error_message}")
        self.status_label.config(text="❌ Search failed!")
        self.progress['value'] = 0
        self.search_button.config(state='normal')
        self.update_network_stats()
        messagebox.showerror("❌ Error", f"Search failed:\n{error_message}")
        
    def export_keywords(self):
        if not self.all_keywords:
            messagebox.showwarning("⚠️ Warning", "No keywords to export")
            return
        filename = filedialog.asksaveasfilename(
            title="Save Keywords",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for keyword in self.all_keywords:
                        f.write(f"{keyword}\n")
                messagebox.showinfo("✅ Success", f"Exported {len(self.all_keywords)} keywords to {filename}")
            except Exception as e:
                messagebox.showerror("❌ Error", f"Failed to export keywords:\n{str(e)}")
                
    def clear_results(self):
        if messagebox.askyesno("🗑️ Confirm", "Are you sure you want to clear all keywords?"):
            self.all_keywords.clear()
            self.results_text.delete(1.0, tk.END)
            self.keyword_count_label.config(text="Total Keywords: 0")
            self.status_label.config(text="✨ Ready to discover keywords...")
            self.progress['value'] = 0
            self.update_network_stats()

def main():
    root = ttk.Window(themename="darkly")
    app = ModernKeywordToolGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
