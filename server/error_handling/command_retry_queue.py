import json
import time
import logging
import threading
from typing import Dict, Any, Optional, List
from collections import deque

logger = logging.getLogger(__name__)

class CommandRetryQueue:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.queue = deque()
        self.lock = threading.Lock()
        self.max_size = self.config.get("max_size", 1000)
        self.base_delay = self.config.get("base_delay", 60)
        self.max_delay = self.config.get("max_delay", 3600)
        self.max_attempts = self.config.get("max_attempts", 5)
        self.running = False
        self.worker_thread = None
        self.error_tracker = None
        self.fallback_executor = None

    def set_error_tracker(self, tracker):
        self.error_tracker = tracker

    def set_fallback_executor(self, executor):
        self.fallback_executor = executor

    def start(self):
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.worker_thread.start()
        logger.info("CommandRetryQueue started")

    def stop(self):
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("CommandRetryQueue stopped")

    def push(self, entry: Dict[str, Any]):
        with self.lock:
            if len(self.queue) >= self.max_size:
                self.queue.popleft()
            self.queue.append(entry)
            logger.debug(f"Pushed retry entry for {entry.get('device_id')}")

    def _process_loop(self):
        while self.running:
            try:
                self._process_one()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Process loop error: {e}")
                time.sleep(5)

    def _process_one(self):
        with self.lock:
            if not self.queue:
                return
            now = time.time()
            entry = self.queue[0]
            last_attempt = entry.get("last_attempt", 0)
            attempts = entry.get("attempts", 0)
            delay = min(self.base_delay * (2 ** attempts), self.max_delay)
            if now - last_attempt < delay:
                return
            entry = self.queue.popleft()
        self._retry(entry)

    def _retry(self, entry: Dict[str, Any]):
        device_id = entry.get("device_id")
        command = entry.get("command")
        params = entry.get("params")
        attempts = entry.get("attempts", 0) + 1
        logger.info(f"Retry attempt {attempts} for {device_id}: {command}")

        success = self._execute(device_id, command, params)
        if success:
            logger.info(f"Retry succeeded for {device_id}")
            if self.error_tracker:
                self.error_tracker.mark_resolved(entry.get("error_id"), "retry_success")
            return

        if attempts < self.max_attempts:
            entry["attempts"] = attempts
            entry["last_attempt"] = time.time()
            self.push(entry)
            logger.info(f"Retry failed, requeued for later attempt {attempts+1}")
        else:
            logger.warning(f"Max attempts reached for {device_id}, giving up")
            if self.fallback_executor:
                self.fallback_executor.submit_failed_command(
                    device_id, command, params,
                    entry.get("error_message", "Max retries"),
                    entry.get("error_code", "MAX_RETRY")
                )
            if self.error_tracker:
                self.error_tracker.log_error(
                    device_id, "MAX_RETRY",
                    f"Command {command} failed after {self.max_attempts} attempts",
                    module="retry_queue", command=command
                )

    def _execute(self, device_id: str, command: str, params: Dict) -> bool:
        # Placeholder: actual execution logic to be injected
        logger.debug(f"Executing {command} on {device_id}")
        return False

    def size(self) -> int:
        with self.lock:
            return len(self.queue)

    def clear(self):
        with self.lock:
            self.queue.clear()

    def get_status(self) -> Dict:
        with self.lock:
            return {
                "size": len(self.queue),
                "max_size": self.max_size,
                "max_attempts": self.max_attempts,
                "base_delay": self.base_delay
            }