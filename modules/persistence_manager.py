import time
import logging
from threading import Thread

logger = logging.getLogger(__name__)

try:
    from jnius import autoclass
except ImportError:
    autoclass = None

class PersistenceManager:
    def __init__(self, check_interval: int = 600):
        self.is_running = True
        self.check_interval = check_interval
        self._monitor_thread = None

    def try_acquire_wakelock(self):
        if autoclass is None:
            logger.warning("jnius not available, cannot acquire WakeLock")
            return
        try:
            Context = autoclass('android.content.Context')
            PowerManager = autoclass('android.os.PowerManager')
            PythonService = autoclass('org.kivy.android.PythonService')
            service = PythonService.mService
            pm = service.getSystemService(Context.POWER_SERVICE)
            lock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "MyApp:StayAlive")
            lock.acquire()
            logger.info("WakeLock acquired")
        except Exception as e:
            logger.error(f"WakeLock acquisition failed: {e}")

    def start_watchdog(self, health_check_func):
        def monitor():
            while self.is_running:
                try:
                    if not health_check_func():
                        logger.warning("Health check failed, attempting recovery...")
                        self._recover()
                except Exception as e:
                    logger.error(f"Watchdog error: {e}")
                time.sleep(self.check_interval)

        self._monitor_thread = Thread(target=monitor, daemon=True)
        self._monitor_thread.start()
        logger.info("Watchdog started")

    def _recover(self):
        logger.info("Recovery mechanism triggered")
        # هنا يمكن للمطور إضافة منطق إعادة تشغيل الخدمات أو إعادة الاتصال

    def stop(self):
        self.is_running = False
        logger.info("PersistenceManager stopped")
