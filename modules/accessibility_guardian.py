import os
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AccessibilityGuardian:
    def __init__(self, android_version: int, service_name: str):
        self.android_version = android_version
        self.service_name = service_name
        self.is_restricted = self.android_version >= 13

    def check_service_status(self) -> bool:
        try:
            cmd = "settings get secure enabled_accessibility_services"
            output = os.popen(cmd).read().strip()
            return self.service_name in output
        except Exception as e:
            logger.error(f"check_service_status failed: {e}")
            return False

    def _open_app_info(self):
        try:
            pkg = self.service_name.split('/')[0]
            os.system(f"am start -a android.settings.APPLICATION_DETAILS_SETTINGS --ei uid {os.getuid()}")
        except Exception as e:
            logger.error(f"_open_app_info failed: {e}")

    def _open_accessibility_settings(self):
        try:
            os.system("am start -a android.settings.ACCESSIBILITY_SETTINGS")
        except Exception as e:
            logger.error(f"_open_accessibility_settings failed: {e}")

    def trigger_request(self):
        if not self.check_service_status():
            if self.is_restricted:
                logger.warning("Restricted mode detected, opening app info")
                self._open_app_info()
            else:
                logger.info("Opening accessibility settings")
                self._open_accessibility_settings()

    def smart_monitor(self, interval: int = 3600):
        while True:
            if not self.check_service_status():
                self.trigger_request()
            time.sleep(interval)

    def get_report(self) -> Dict[str, Any]:
        return {
            "status": "enabled" if self.check_service_status() else "disabled",
            "android_version": self.android_version,
            "restricted_mode": self.is_restricted,
            "service": self.service_name
        }
