import os
import json
import time
import logging
import threading
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class FallbackExecutor:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.retry_queue = []
        self.lock = threading.Lock()
        self.max_attempts = self.config.get("max_attempts", 3)
        self.retry_delay_base = self.config.get("retry_delay_base", 60)
        self.ai_advisor = None
        self.command_generator = None
        self.error_tracker = None

    def set_ai_advisor(self, advisor):
        self.ai_advisor = advisor

    def set_command_generator(self, generator):
        self.command_generator = generator

    def set_error_tracker(self, tracker):
        self.error_tracker = tracker

    def submit_failed_command(self, device_id: str, command_name: str, command_params: Dict,
                               error_message: str, error_code: str) -> str:
        task_id = f"{device_id}_{command_name}_{int(time.time())}"
        with self.lock:
            self.retry_queue.append({
                "id": task_id,
                "device_id": device_id,
                "command_name": command_name,
                "command_params": command_params,
                "error_message": error_message,
                "error_code": error_code,
                "attempts": 0,
                "last_attempt": 0,
                "status": "pending"
            })
        logger.info(f"Failed command submitted: {task_id}")
        return task_id

    def process_retry_queue(self):
        with self.lock:
            now = time.time()
            for task in self.retry_queue:
                if task["status"] != "pending":
                    continue
                if now - task["last_attempt"] < self.retry_delay_base * (2 ** task["attempts"]):
                    continue
                task["attempts"] += 1
                task["last_attempt"] = now
                threading.Thread(target=self._attempt_retry, args=(task,)).start()

    def _attempt_retry(self, task: Dict):
        device_id = task["device_id"]
        command_name = task["command_name"]
        params = task["command_params"]
        error_code = task["error_code"]
        error_msg = task["error_message"]

        if task["attempts"] <= self.max_attempts:
            logger.info(f"Retry attempt {task['attempts']} for {task['id']}")
            success = self._execute_original(device_id, command_name, params)
            if success:
                self._mark_resolved(task, "retry_success")
                return

        if self.ai_advisor:
            advice = self.ai_advisor.suggest_alternative(device_id, command_name, params, error_code, error_msg)
            if advice and advice.get("alternative"):
                alt_cmd = advice["alternative"]
                logger.info(f"Executing alternative command: {alt_cmd} for {task['id']}")
                success = self._execute_command(device_id, alt_cmd, advice.get("params", {}))
                if success:
                    self._mark_resolved(task, "ai_alternative")
                    return

        if self.command_generator:
            new_cmd = self.command_generator.generate_fallback(device_id, command_name, params, error_code)
            if new_cmd:
                logger.info(f"Generated fallback command for {task['id']}")
                success = self._execute_command(device_id, new_cmd, {})
                if success:
                    self._mark_resolved(task, "generated_fallback")
                    return

        self._mark_failed(task)

    def _execute_original(self, device_id: str, command_name: str, params: Dict) -> bool:
        return self._execute_command(device_id, command_name, params)

    def _execute_command(self, device_id: str, command_name: str, params: Dict) -> bool:
        logger.info(f"Executing {command_name} on {device_id} with params {params}")
        return False

    def _mark_resolved(self, task: Dict, method: str):
        with self.lock:
            task["status"] = "resolved"
            task["resolution"] = method
        if self.error_tracker:
            self.error_tracker.mark_resolved(task["id"], method)

    def _mark_failed(self, task: Dict):
        with self.lock:
            task["status"] = "failed"
        if self.error_tracker:
            self.error_tracker.log_error(task["device_id"], "FALLBACK_FAILED",
                                         f"All fallbacks failed for {task['command_name']}",
                                         module="fallback_executor", command=task["command_name"])

    def get_status(self) -> Dict:
        with self.lock:
            return {
                "queue_size": len(self.retry_queue),
                "pending": sum(1 for t in self.retry_queue if t["status"] == "pending"),
                "resolved": sum(1 for t in self.retry_queue if t["status"] == "resolved"),
                "failed": sum(1 for t in self.retry_queue if t["status"] == "failed")
            }

    def process_task(self, task_type: str, data: Any) -> Dict:
        if task_type == "submit":
            task_id = self.submit_failed_command(
                data.get("device_id"),
                data.get("command_name"),
                data.get("command_params", {}),
                data.get("error_message"),
                data.get("error_code")
            )
            return {"task_id": task_id}
        elif task_type == "process":
            self.process_retry_queue()
            return {"status": "processing"}
        elif task_type == "status":
            return self.get_status()
        return {"error": "unknown task"}