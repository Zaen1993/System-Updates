import os
import json
import time
import logging
import threading
import numpy as np
from typing import Dict, Any, Optional, List
from collections import defaultdict

logger = logging.getLogger(__name__)

class AnomalyDetector:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.sensitivity = self.config.get("sensitivity", 3.0)
        self.window_size = self.config.get("window_size", 100)
        self.history = defaultdict(list)
        self.stats = {}
        self.lock = threading.Lock()
        self.error_tracker = None
        self.callbacks = []

    def set_error_tracker(self, tracker):
        self.error_tracker = tracker

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def process_task(self, task_type: str, data: Any) -> Dict:
        if task_type == "record":
            device_id = data.get("device_id")
            value = data.get("value")
            metadata = data.get("metadata", {})
            if device_id is None or value is None:
                return {"error": "Missing device_id or value"}
            anomaly = self.record_value(device_id, value, metadata)
            return {"anomaly": anomaly}
        elif task_type == "detect":
            device_id = data.get("device_id")
            value = data.get("value")
            if device_id is None or value is None:
                return {"error": "Missing device_id or value"}
            result = self.detect(device_id, value)
            return result
        elif task_type == "stats":
            device_id = data.get("device_id")
            return self.get_statistics(device_id)
        return {"error": f"Unknown task type: {task_type}"}

    def record_value(self, device_id: str, value: float, metadata: Dict = None) -> bool:
        with self.lock:
            self.history[device_id].append({
                "timestamp": time.time(),
                "value": value,
                "metadata": metadata or {}
            })
            if len(self.history[device_id]) > self.window_size:
                self.history[device_id].pop(0)
            # Recompute stats
            values = [entry["value"] for entry in self.history[device_id]]
            if len(values) >= 10:
                mean = np.mean(values)
                std = np.std(values)
                self.stats[device_id] = {"mean": mean, "std": std}
            else:
                self.stats[device_id] = None

            # Check anomaly on the latest value
            is_anomaly = self._is_anomaly(device_id, value)
            if is_anomaly:
                self._trigger_anomaly(device_id, value, metadata)
            return is_anomaly

    def detect(self, device_id: str, value: float) -> Dict:
        is_anomaly = self._is_anomaly(device_id, value)
        return {
            "device_id": device_id,
            "value": value,
            "anomaly": is_anomaly,
            "stats": self.stats.get(device_id)
        }

    def _is_anomaly(self, device_id: str, value: float) -> bool:
        stats = self.stats.get(device_id)
        if stats is None or stats["std"] == 0:
            return False
        mean = stats["mean"]
        std = stats["std"]
        lower = mean - self.sensitivity * std
        upper = mean + self.sensitivity * std
        return value < lower or value > upper

    def _trigger_anomaly(self, device_id: str, value: float, metadata: Dict = None):
        logger.warning(f"Anomaly detected for {device_id}: value={value}")
        event = {
            "device_id": device_id,
            "value": value,
            "timestamp": time.time(),
            "metadata": metadata
        }
        for cb in self.callbacks:
            try:
                cb(event)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        if self.error_tracker:
            self.error_tracker.log_error(
                device_id, "ANOMALY_DETECTED",
                f"Anomaly value {value} exceeds threshold",
                module="anomaly_detector"
            )

    def get_statistics(self, device_id: str = None) -> Dict:
        with self.lock:
            if device_id:
                return {
                    "device_id": device_id,
                    "stats": self.stats.get(device_id),
                    "history_length": len(self.history.get(device_id, []))
                }
            else:
                return {
                    device: {
                        "stats": self.stats.get(device),
                        "history_length": len(self.history.get(device, []))
                    } for device in self.history
                }

    def clear_device(self, device_id: str):
        with self.lock:
            if device_id in self.history:
                del self.history[device_id]
            if device_id in self.stats:
                del self.stats[device_id]