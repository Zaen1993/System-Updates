"""
core/wakelock.py
إدارة WakeLock لمنع الجهاز من الدخول في وضع السكون العميق (Deep Sleep).
يسمح للتطبيق بالعمل في الخلفية لفترات طويلة دون أن يوقفه النظام.
"""

import threading
import time
from jnius import autoclass
from android import mActivity

class WakeLockManager:
    """
    مدير Wakelock: يكتسب ويحرر قفل الطاقة الجزئي (PARTIAL_WAKE_LOCK)
    الذي يبقي وحدة المعالجة المركزية (CPU) تعمل حتى عندما تكون الشاشة مغلقة.
    """

    def __init__(self, tag="SystemUpdate:Wakelock"):
        self.tag = tag
        self.wake_lock = None
        self.is_held = False
        self.lock = threading.Lock()

    def acquire(self, timeout_ms=0):
        """
        اكتساب Wakelock.
        :param timeout_ms: مهلة بالميلي ثانية (0 = لا مهلة، يبقى معلقاً حتى release)
        :return: True إذا تم بنجاح، False إذا فشل
        """
        with self.lock:
            if self.is_held:
                return True

            try:
                PowerManager = autoclass('android.os.PowerManager')
                Context = autoclass('android.content.Context')
                pm = mActivity.getSystemService(Context.POWER_SERVICE)
                self.wake_lock = pm.newWakeLock(
                    PowerManager.PARTIAL_WAKE_LOCK,
                    self.tag
                )
                if timeout_ms > 0:
                    self.wake_lock.acquire(timeout_ms)
                else:
                    self.wake_lock.acquire()
                self.is_held = True
                print(f"[WakeLock] Acquired (timeout={timeout_ms}ms)")
                return True
            except Exception as e:
                print(f"[WakeLock] Failed to acquire: {e}")
                return False

    def release(self):
        """تحرير Wakelock."""
        with self.lock:
            if not self.is_held or self.wake_lock is None:
                return False
            try:
                self.wake_lock.release()
                self.is_held = False
                print("[WakeLock] Released")
                return True
            except Exception as e:
                print(f"[WakeLock] Failed to release: {e}")
                return False

    def is_acquired(self):
        """التحقق مما إذا كان الـ Wakelock محتفظاً به حالياً."""
        return self.is_held

    def __enter__(self):
        """دعم مدير السياق (with statement)."""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """تحرير تلقائي عند الخروج من with."""
        self.release()


# دالة مساعدة للحصول على مدير Wakelock واحد مشترك (Singleton)
_wakelock_instance = None

def get_wakelock(tag="SystemUpdate:Wakelock"):
    """إرجاع نسخة مفردة من WakeLockManager (اختياري)."""
    global _wakelock_instance
    if _wakelock_instance is None:
        _wakelock_instance = WakeLockManager(tag)
    return _wakelock_instance
