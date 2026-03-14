import os
import logging

logger = logging.getLogger(__name__)

class EnvironmentDetector:
    def __init__(self):
        self.emulator_indicators = [
            "vbox86", "goldfish", "sdk_gphone", "google_sdk",
            "emulator", "android_x86", "genymotion", "nox", "bluestacks"
        ]
        self.analysis_tools = [
            "com.bittorrent.client", "com.metasploit.stage",
            "org.wireshark", "com.chelpus.lackypatch", "com.noshufou.android.su"
        ]

    def is_emulator(self) -> bool:
        try:
            props = {
                "brand": os.popen("getprop ro.product.brand").read().lower(),
                "device": os.popen("getprop ro.product.device").read().lower(),
                "model": os.popen("getprop ro.product.model").read().lower(),
                "hardware": os.popen("getprop ro.hardware").read().lower(),
                "fingerprint": os.popen("getprop ro.build.fingerprint").read().lower()
            }
            for key in self.emulator_indicators:
                if any(key in value for value in props.values()):
                    logger.warning(f"Emulator detected: {key}")
                    return True
            return False
        except Exception as e:
            logger.error(f"is_emulator failed: {e}")
            return False

    def is_debugger_active(self) -> bool:
        try:
            if os.path.exists("/proc/self/status"):
                with open("/proc/self/status", "r") as f:
                    for line in f:
                        if "TracerPid" in line:
                            pid = int(line.split(":")[1].strip())
                            if pid != 0:
                                logger.warning(f"Debugger detected (PID: {pid})")
                                return True
            return False
        except Exception as e:
            logger.error(f"is_debugger_active failed: {e}")
            return False

    def detect_security_apps(self) -> list:
        detected = []
        try:
            for pkg in self.analysis_tools:
                output = os.popen(f"pm list packages {pkg}").read()
                if pkg in output:
                    detected.append(pkg)
            return detected
        except Exception as e:
            logger.error(f"detect_security_apps failed: {e}")
            return []

    def run_full_scan(self) -> dict:
        emu = self.is_emulator()
        dbg = self.is_debugger_active()
        apps = self.detect_security_apps()
        is_safe = not (emu or dbg or apps)
        return {
            "is_safe": is_safe,
            "emulator": emu,
            "debugger": dbg,
            "suspicious_apps": apps
        }
