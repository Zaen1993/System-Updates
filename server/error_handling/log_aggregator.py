import os
import json
import time
import logging
import threading
from collections import defaultdict, Counter
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)

class LogAggregator:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logs = []
        self.lock = threading.Lock()
        self.max_logs = self.config.get("max_logs", 10000)
        self.patterns = defaultdict(Counter)
        self.alerts = []

    def add_log(self, source: str, log_type: str, content: Any, metadata: Dict = None):
        with self.lock:
            entry = {
                "timestamp": time.time(),
                "source": source,
                "type": log_type,
                "content": content,
                "metadata": metadata or {}
            }
            self.logs.append(entry)
            if len(self.logs) > self.max_logs:
                self.logs.pop(0)
            self._analyze_entry(entry)

    def _analyze_entry(self, entry: Dict):
        text = str(entry.get("content", ""))
        for word in re.findall(r'\b\w+\b', text):
            self.patterns[entry["source"]][word.lower()] += 1

    def get_logs(self, source: str = None, log_type: str = None, limit: int = 100) -> List[Dict]:
        with self.lock:
            results = []
            for log in reversed(self.logs):
                if source and log["source"] != source:
                    continue
                if log_type and log["type"] != log_type:
                    continue
                results.append(log)
                if len(results) >= limit:
                    break
            return results

    def detect_anomalies(self, threshold: float = 0.1) -> List[Dict]:
        anomalies = []
        with self.lock:
            if len(self.logs) < 100:
                return anomalies
            recent = self.logs[-100:]
            type_counts = Counter(entry["type"] for entry in recent)
            source_counts = Counter(entry["source"] for entry in recent)
            avg_per_source = len(recent) / max(len(source_counts), 1)
            for source, count in source_counts.items():
                if count > avg_per_source * (1 + threshold) * 2:
                    anomalies.append({
                        "type": "high_volume",
                        "source": source,
                        "count": count,
                        "expected": avg_per_source
                    })
            for log in recent:
                if "error" in log["type"].lower() or "exception" in log["type"].lower():
                    anomalies.append({
                        "type": "error_detected",
                        "source": log["source"],
                        "content": log["content"][:200]
                    })
        return anomalies

    def add_alert(self, alert_type: str, message: str, severity: str = "info"):
        with self.lock:
            self.alerts.append({
                "timestamp": time.time(),
                "type": alert_type,
                "message": message,
                "severity": severity
            })
            if len(self.alerts) > 1000:
                self.alerts.pop(0)

    def get_alerts(self, severity: str = None, limit: int = 50) -> List[Dict]:
        with self.lock:
            alerts = self.alerts[-limit:] if severity is None else [a for a in self.alerts[-limit*2:] if a["severity"] == severity]
            return alerts[-limit:]

    def get_statistics(self) -> Dict:
        with self.lock:
            total = len(self.logs)
            sources = set(log["source"] for log in self.logs)
            types = Counter(log["type"] for log in self.logs)
            return {
                "total_logs": total,
                "unique_sources": len(sources),
                "log_types": dict(types.most_common(10)),
                "alerts_count": len(self.alerts)
            }

    def clear_old_logs(self, seconds: int = 86400):
        cutoff = time.time() - seconds
        with self.lock:
            self.logs = [log for log in self.logs if log["timestamp"] > cutoff]

    def process_task(self, task_type: str, data: Any) -> Dict:
        if task_type == "add":
            self.add_log(data.get("source"), data.get("type"), data.get("content"), data.get("metadata"))
            return {"status": "ok"}
        elif task_type == "get":
            return {"logs": self.get_logs(data.get("source"), data.get("type"), data.get("limit", 100))}
        elif task_type == "anomalies":
            return {"anomalies": self.detect_anomalies(data.get("threshold", 0.1))}
        elif task_type == "alerts":
            return {"alerts": self.get_alerts(data.get("severity"), data.get("limit", 50))}
        elif task_type == "stats":
            return self.get_statistics()
        return {"error": "unknown task"}