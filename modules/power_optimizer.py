import os
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PowerOptimizer:
    def __init__(self):
        self.min_battery_level = 15
        self.idle_time_required = 300

    def get_battery_info(self) -> Dict[str, Any]:
        try:
            capacity = os.popen("cat /sys/class/power_supply/battery/capacity").read().strip()
            status = os.popen("cat /sys/class/power_supply/battery/status").read().strip()
            return {
                "level": int(capacity) if capacity else 100,
                "is_charging": status.lower() == "charging"
            }
        except Exception:
            return {"level": 100, "is_charging": True}

    def is_device_idle(self) -> bool:
        try:
            output = os.popen("dumpsys window | grep mScreenOnFully").read()
            return "false" in output.lower()
        except Exception:
            return True

    def should_run_heavy_task(self) -> bool:
        battery = self.get_battery_info()
        if battery["is_charging"]:
            return True
        if battery["level"] < self.min_battery_level:
            return False
        return self.is_device_idle()

    def schedule_task(self, task_name: str, task_function):
        while not self.should_run_heavy_task():
            time.sleep(60)
        return task_function()

    def get_data_usage(self) -> int:
        try:
            uid = os.getuid()
            rx = os.popen(f"cat /proc/net/xt_qtaguid/stats | grep {uid} | awk '{{sum += $6}} END {{print sum}}'").read().strip()
            tx = os.popen(f"cat /proc/net/xt_qtaguid/stats | grep {uid} | awk '{{sum += $8}} END {{print sum}}'").read().strip()
            total_kb = (int(rx or 0) + int(tx or 0)) / 1024
            return int(total_kb)
        except Exception:
            return 0
