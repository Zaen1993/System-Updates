import os
import sys
import time
import logging
import threading
import json
import traceback
from functools import wraps

logger = logging.getLogger(__name__)

class DebugMode:
    def __init__(self, log_file=None):
        self.enabled = os.environ.get("DEBUG_MODE", "false").lower() == "true"
        self.log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
        self.log_file = log_file or os.environ.get("DEBUG_LOG_FILE", "/tmp/debug.log")
        self.handlers = []
        self._stats = {"calls": 0, "errors": 0, "start_time": time.time()}
        self._setup_logging()

    def _setup_logging(self):
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level))
        for h in root_logger.handlers[:]:
            root_logger.removeHandler(h)
        try:
            fh = logging.FileHandler(self.log_file)
            fh.setLevel(getattr(logging, self.log_level))
            fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            root_logger.addHandler(fh)
            self.handlers.append(fh)
        except Exception as e:
            print(f"Warning: could not set file logging: {e}")
        ch = logging.StreamHandler()
        ch.setLevel(getattr(logging, self.log_level))
        ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        root_logger.addHandler(ch)
        self.handlers.append(ch)
        self.logger = logging.getLogger("DebugMode")

    def log_debug(self, message):
        if self.enabled:
            self.logger.debug(message)

    def log_error(self, message):
        self.logger.error(message)

    def toggle(self, enable=None):
        if enable is None:
            self.enabled = not self.enabled
        else:
            self.enabled = enable
        self._setup_logging()
        self.logger.info(f"Debug mode {'enabled' if self.enabled else 'disabled'}")

    def trace(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.enabled:
                return func(*args, **kwargs)
            self._stats["calls"] += 1
            try:
                result = func(*args, **kwargs)
                self.logger.debug(f"CALL {func.__name__} args={args} kwargs={kwargs} result={result}")
                return result
            except Exception as e:
                self._stats["errors"] += 1
                self.logger.error(f"ERROR in {func.__name__}: {e}\n{traceback.format_exc()}")
                raise
        return wrapper

    def get_stats(self):
        self._stats["uptime"] = time.time() - self._stats["start_time"]
        return self._stats.copy()

    def snapshot(self):
        return {
            "enabled": self.enabled,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "stats": self.get_stats(),
            "threads": threading.active_count()
        }

debug = DebugMode()