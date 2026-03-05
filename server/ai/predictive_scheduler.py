import json
import time
import logging
import hashlib
import threading
from collections import defaultdict
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

class PredictiveScheduler:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.device_patterns = {}
        self.scheduled_tasks = defaultdict(list)
        self.lock = threading.Lock()
        self.learning_rate = self.config.get("learning_rate", 0.1)
        self.min_confidence = self.config.get("min_confidence", 0.7)
        self.error_tracker = None
        self.data_store = {}

    def set_error_tracker(self, tracker):
        self.error_tracker = tracker

    def analyze_target_behavior(self, target_id: str, historical_data: List[Dict]) -> Dict:
        """
        Analyze historical data to determine activity patterns for a target.
        historical_data: list of dicts with keys 'timestamp' and 'active' (bool)
        Returns a pattern dict with safe_hours and other metrics.
        """
        logger.info(f"Analyzing behavior patterns for {target_id}")
        if not historical_data:
            return {"safe_hours": (0, 23), "confidence": 0.0}

        active_hours = []
        inactive_hours = []
        for entry in historical_data:
            ts = entry.get("timestamp")
            if isinstance(ts, (int, float)):
                dt = datetime.fromtimestamp(ts)
                hour = dt.hour
                if entry.get("active", False):
                    active_hours.append(hour)
                else:
                    inactive_hours.append(hour)

        if not inactive_hours:
            # No inactivity recorded, assume safe hours are least active
            if active_hours:
                # Find hour with minimal activity
                hour_counts = {h: active_hours.count(h) for h in set(active_hours)}
                safest = min(hour_counts, key=hour_counts.get)
                safe_start = max(0, safest - 1)
                safe_end = min(23, safest + 1)
                safe_hours = (safe_start, safe_end)
            else:
                safe_hours = (0, 23)
            confidence = 0.5
        else:
            # Use inactive hours as base
            from collections import Counter
            inactive_counter = Counter(inactive_hours)
            # Find contiguous most inactive periods (simplified)
            sorted_inactive = sorted(inactive_counter.items(), key=lambda x: x[1], reverse=True)
            best_hour = sorted_inactive[0][0] if sorted_inactive else 0
            safe_start = max(0, best_hour - 2)
            safe_end = min(23, best_hour + 2)
            safe_hours = (safe_start, safe_end)
            confidence = min(1.0, len(inactive_hours) / (len(active_hours) + len(inactive_hours) + 1))

        pattern = {
            "safe_hours": safe_hours,
            "confidence": confidence,
            "last_updated": time.time()
        }
        with self.lock:
            self.device_patterns[target_id] = pattern
        logger.info(f"Pattern for {target_id}: safe hours {safe_hours}, confidence {confidence:.2f}")
        return pattern

    def schedule_task(self, target_id: str, task: Dict, schedule_time: Optional[datetime] = None) -> Optional[datetime]:
        """
        Schedule a task for a target. If schedule_time is None, predict optimal time.
        Returns the scheduled datetime.
        """
        if schedule_time is None:
            schedule_time = self._predict_optimal_time(target_id)
        if schedule_time is None:
            logger.warning(f"Could not predict time for {target_id}, scheduling now + 30min")
            schedule_time = datetime.now() + timedelta(minutes=30)

        task_id = hashlib.md5(f"{target_id}_{task}_{time.time()}".encode()).hexdigest()[:16]
        scheduled_entry = {
            "id": task_id,
            "target": target_id,
            "task": task,
            "scheduled_time": schedule_time.timestamp(),
            "inserted": time.time(),
            "executed": False
        }
        with self.lock:
            self.scheduled_tasks[target_id].append(scheduled_entry)
            self.scheduled_tasks[target_id].sort(key=lambda x: x["scheduled_time"])
        logger.info(f"Scheduled task {task_id} for {target_id} at {schedule_time.isoformat()}")
        return schedule_time

    def _predict_optimal_time(self, target_id: str) -> Optional[datetime]:
        """Internal prediction: returns next safe datetime or None."""
        with self.lock:
            pattern = self.device_patterns.get(target_id)
        if not pattern:
            return None
        safe_hours = pattern["safe_hours"]
        now = datetime.now()
        current_hour = now.hour
        if current_hour < safe_hours[0]:
            # schedule today at safe_hours[0]
            scheduled = now.replace(hour=safe_hours[0], minute=0, second=0, microsecond=0)
        elif current_hour > safe_hours[1]:
            # schedule tomorrow at safe_hours[0]
            tomorrow = now + timedelta(days=1)
            scheduled = tomorrow.replace(hour=safe_hours[0], minute=0, second=0, microsecond=0)
        else:
            # within safe window, schedule next safe hour (could be random later)
            # choose a random minute in current safe block
            safe_end = safe_hours[1]
            if safe_end > current_hour:
                scheduled = now.replace(hour=random.randint(current_hour, safe_end), minute=random.randint(0,59))
            else:
                scheduled = now + timedelta(hours=1)  # fallback
        return scheduled

    def get_due_tasks(self, target_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        Return tasks that are due (scheduled time <= now), optionally filtered by target.
        """
        now = time.time()
        due = []
        with self.lock:
            if target_id:
                targets = [target_id]
            else:
                targets = list(self.scheduled_tasks.keys())
            for tid in targets:
                remaining = []
                for task in self.scheduled_tasks.get(tid, []):
                    if task["scheduled_time"] <= now and not task["executed"]:
                        task["executed"] = True  # mark as executed (will be removed later)
                        due.append(task)
                    else:
                        remaining.append(task)
                if target_id:
                    self.scheduled_tasks[tid] = remaining
                else:
                    self.scheduled_tasks[tid] = remaining
                if len(due) >= limit:
                    break
        return due

    def mark_executed(self, task_id: str):
        """Mark a task as executed (optional, but used by get_due_tasks)."""
        with self.lock:
            for tid, tasks in self.scheduled_tasks.items():
                for t in tasks:
                    if t["id"] == task_id:
                        t["executed"] = True
                        return True
        return False

    def get_statistics(self) -> Dict:
        with self.lock:
            return {
                "devices_tracked": len(self.device_patterns),
                "pending_tasks": sum(len(t) for t in self.scheduled_tasks.values()),
                "patterns": {k: v["safe_hours"] for k, v in self.device_patterns.items()}
            }

    def process_task(self, task_type: str, data: Any) -> Dict:
        if task_type == "analyze":
            target = data.get("target_id")
            hist = data.get("historical_data", [])
            if not target:
                return {"error": "missing target_id"}
            pattern = self.analyze_target_behavior(target, hist)
            return pattern
        elif task_type == "schedule":
            target = data.get("target_id")
            task = data.get("task")
            if not target or not task:
                return {"error": "missing target_id or task"}
            sched = self.schedule_task(target, task)
            return {"scheduled": sched.isoformat() if sched else None}
        elif task_type == "due":
            target = data.get("target_id")
            limit = data.get("limit", 10)
            due = self.get_due_tasks(target, limit)
            return {"tasks": due}
        elif task_type == "stats":
            return self.get_statistics()
        return {"error": "unknown task type"}