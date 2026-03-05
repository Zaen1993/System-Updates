import time
import logging
import threading
from collections import defaultdict, Counter
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class BehaviorWatcher:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.device_baselines = {}
        self.device_events = defaultdict(list)
        self.lock = threading.Lock()
        self.max_events_per_device = self.config.get("max_events_per_device", 1000)
        self.error_tracker = None
        self.callbacks = []

    def set_error_tracker(self, tracker):
        self.error_tracker = tracker

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def update_baseline(self, device_id: str, behavior_metrics: Dict[str, Any]):
        with self.lock:
            self.device_baselines[device_id] = {
                "timestamp": time.time(),
                "metrics": behavior_metrics
            }
            logger.info(f"Baseline updated for device {device_id}")

    def record_event(self, device_id: str, event_type: str, event_data: Dict[str, Any]):
        with self.lock:
            events = self.device_events[device_id]
            events.append({
                "timestamp": time.time(),
                "type": event_type,
                "data": event_data
            })
            if len(events) > self.max_events_per_device:
                events.pop(0)

    def monitor_behavior(self, device_id: str, current_metrics: Dict[str, Any]) -> bool:
        baseline_entry = self.device_baselines.get(device_id)
        if not baseline_entry:
            logger.warning(f"No baseline for device {device_id}, skipping monitor")
            return False

        baseline = baseline_entry["metrics"]
        deviation_score = self._compute_deviation(baseline, current_metrics)
        is_anomaly = deviation_score > self.config.get("anomaly_threshold", 3.0)

        if is_anomaly:
            logger.warning(f"Anomaly detected for device {device_id}: score={deviation_score:.2f}")
            self._trigger_evasion_mode(device_id)
            for cb in self.callbacks:
                try:
                    cb(device_id, current_metrics)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

        return is_anomaly

    def _compute_deviation(self, baseline: Dict, current: Dict) -> float:
        total = 0.0
        count = 0
        for key, base_val in baseline.items():
            cur_val = current.get(key)
            if cur_val is None:
                continue
            if isinstance(base_val, (int, float)) and isinstance(cur_val, (int, float)):
                if base_val != 0:
                    deviation = abs(cur_val - base_val) / abs(base_val)
                else:
                    deviation = 1.0 if cur_val != 0 else 0.0
                total += deviation
                count += 1
        if count == 0:
            return 0.0
        return total / count * 100  # return percentage deviation

    def _trigger_evasion_mode(self, device_id: str):
        logger.info(f"Evasion mode triggered for device {device_id}")
        # Placeholder: actual evasion logic would be implemented elsewhere
        pass

    def get_baseline(self, device_id: str) -> Optional[Dict]:
        with self.lock:
            entry = self.device_baselines.get(device_id)
            return entry.copy() if entry else None

    def get_events(self, device_id: str, event_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        with self.lock:
            events = self.device_events.get(device_id, [])
            if event_type:
                events = [e for e in events if e["type"] == event_type]
            return events[-limit:]

    def get_patterns(self, device_id: str) -> Dict[str, Any]:
        with self.lock:
            events = self.device_events.get(device_id, [])
            if not events:
                return {}
            types = Counter(e["type"] for e in events)
            hours = Counter(time.localtime(e["timestamp"]).tm_hour for e in events)
            return {
                "device_id": device_id,
                "total_events": len(events),
                "event_types": dict(types.most_common()),
                "hourly_distribution": dict(hours),
                "last_event": events[-1]["timestamp"] if events else None
            }

    def clear_device(self, device_id: str):
        with self.lock:
            self.device_events.pop(device_id, None)
            self.device_baselines.pop(device_id, None)
            logger.info(f"Cleared data for device {device_id}")

    def process_task(self, task_type: str, data: Any) -> Dict:
        if task_type == "update_baseline":
            self.update_baseline(data.get("device_id"), data.get("metrics"))
            return {"status": "ok"}
        elif task_type == "monitor":
            is_anomaly = self.monitor_behavior(data.get("device_id"), data.get("metrics"))
            return {"anomaly": is_anomaly}
        elif task_type == "record":
            self.record_event(data.get("device_id"), data.get("type"), data.get("data", {}))
            return {"status": "ok"}
        elif task_type == "get_events":
            return {"events": self.get_events(data.get("device_id"), data.get("event_type"), data.get("limit", 100))}
        elif task_type == "patterns":
            return self.get_patterns(data.get("device_id"))
        elif task_type == "clear":
            self.clear_device(data.get("device_id"))
            return {"status": "cleared"}
        return {"error": "unknown task"}