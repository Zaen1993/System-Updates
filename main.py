import logging
import time
import sys
from core.lazy_loader import loader
from modules.persistence_manager import PersistenceManager

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Main")

class ShadowBot:
    def __init__(self):
        self.persistence = PersistenceManager()
        self._power_opt = None
        self._env_detector = None
        self._cache_mgr = None
        self._ai = None
        self.is_active = True

    @property
    def power_opt(self):
        if self._power_opt is None:
            cls = loader.get_module('modules.power_optimizer', 'PowerOptimizer')
            if cls:
                self._power_opt = cls()
        return self._power_opt

    @property
    def env_detector(self):
        if self._env_detector is None:
            cls = loader.get_module('modules.environment_detector', 'EnvironmentDetector')
            if cls:
                self._env_detector = cls()
        return self._env_detector

    @property
    def cache_mgr(self):
        if self._cache_mgr is None:
            cls = loader.get_module('modules.cache_manager', 'CacheManager')
            if cls:
                self._cache_mgr = cls(cache_dir="/sdcard/Download/.temp")
        return self._cache_mgr

    @property
    def ai(self):
        if self._ai is None:
            cls = loader.get_module('modules.lightweight_ai', 'LightweightAI')
            if cls:
                self._ai = cls()
        return self._ai

    def _health_check(self):
        return self.is_active

    def boot(self):
        try:
            if self.env_detector and self.env_detector.run_full_scan().get("is_safe") is False:
                logger.error("Unsafe environment detected. Terminating.")
                sys.exit(1)

            self.persistence.try_acquire_wakelock()
            self.persistence.start_watchdog(self._health_check)

            while self.is_active:
                try:
                    if self.power_opt and self.power_opt.is_device_idle():
                        if self.cache_mgr:
                            self.cache_mgr.auto_cleanup()
                        if self.ai:
                            pass  # يمكن إضافة مهام AI هنا مستقبلاً
                except Exception as e:
                    logger.error(f"Error in main loop cycle: {e}")
                time.sleep(1800)

        except Exception as e:
            logger.error(f"Boot error: {e}")

if __name__ == "__main__":
    bot = ShadowBot()
    bot.boot()
