import os
import json
import time
import logging
import threading
from typing import Dict, Any, Optional, List
from flask import Flask, request, jsonify

logger = logging.getLogger(__name__)

app = Flask(__name__)

class ErrorTracker:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.errors = []
        self.lock = threading.Lock()
        self.max_errors = self.config.get("max_errors", 1000)
        self.stats = {"total": 0, "resolved": 0, "by_type": {}}
        self.fallback_executor = None

    def set_fallback_executor(self, executor):
        self.fallback_executor = executor

    def log_error(self, device_id: str, error_code: str, error_message: str,
                  module: str = None, command: str = None, stack_trace: str = None,
                  context: Dict = None) -> str:
        error_id = f"{int(time.time())}_{hash(error_code)}_{len(self.errors)}"
        with self.lock:
            error_entry = {
                "id": error_id,
                "device_id": device_id,
                "error_code": error_code,
                "error_message": error_message,
                "module": module,
                "command": command,
                "stack_trace": stack_trace,
                "context": context or {},
                "timestamp": time.time(),
                "resolved": False,
                "resolution_method": None
            }
            self.errors.append(error_entry)
            if len(self.errors) > self.max_errors:
                self.errors.pop(0)
            self.stats["total"] += 1
            self.stats["by_type"][error_code] = self.stats["by_type"].get(error_code, 0) + 1
            logger.info(f"Error logged: {error_id} - {error_code}")
        if self.fallback_executor and command:
            self.fallback_executor.submit_failed_command(
                device_id=device_id,
                command_name=command,
                command_params=context.get("params", {}) if context else {},
                error_message=error_message,
                error_code=error_code
            )
        return error_id

    def mark_resolved(self, error_id: str, resolution_method: str = None) -> bool:
        with self.lock:
            for e in self.errors:
                if e["id"] == error_id:
                    e["resolved"] = True
                    e["resolution_method"] = resolution_method
                    self.stats["resolved"] += 1
                    return True
        return False

    def get_errors(self, device_id: str = None, error_code: str = None,
                   resolved: bool = None, limit: int = 100) -> List[Dict]:
        results = []
        with self.lock:
            for e in self.errors:
                if device_id and e["device_id"] != device_id:
                    continue
                if error_code and e["error_code"] != error_code:
                    continue
                if resolved is not None and e["resolved"] != resolved:
                    continue
                results.append(e)
                if len(results) >= limit:
                    break
        return results

    def get_error(self, error_id: str) -> Optional[Dict]:
        with self.lock:
            for e in self.errors:
                if e["id"] == error_id:
                    return e
        return None

    def get_statistics(self) -> Dict:
        with self.lock:
            return self.stats.copy()

    def clear_old_errors(self, seconds: int = 86400):
        cutoff = time.time() - seconds
        with self.lock:
            self.errors = [e for e in self.errors if e["timestamp"] > cutoff]

    def save_to_file(self, filepath: str):
        try:
            with open(filepath, "w") as f:
                json.dump({"errors": self.errors, "stats": self.stats}, f)
        except Exception as e:
            logger.error(f"Failed to save errors: {e}")

    def load_from_file(self, filepath: str):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                with self.lock:
                    self.errors = data.get("errors", [])
                    self.stats = data.get("stats", {"total": 0, "resolved": 0, "by_type": {}})
        except Exception as e:
            logger.error(f"Failed to load errors: {e}")

    def process_task(self, task_type: str, data: Any) -> Dict:
        if task_type == "log":
            eid = self.log_error(
                data.get("device_id"),
                data.get("error_code"),
                data.get("error_message"),
                data.get("module"),
                data.get("command"),
                data.get("stack_trace"),
                data.get("context")
            )
            return {"error_id": eid}
        elif task_type == "resolve":
            ok = self.mark_resolved(data.get("error_id"), data.get("method"))
            return {"resolved": ok}
        elif task_type == "get":
            eid = data.get("error_id")
            if eid:
                return {"error": self.get_error(eid)}
            return {"errors": self.get_errors(
                data.get("device_id"),
                data.get("error_code"),
                data.get("resolved"),
                data.get("limit", 100)
            )}
        elif task_type == "stats":
            return self.get_statistics()
        return {"error": "unknown task"}

tracker = ErrorTracker()

@app.route('/api/v1/report-error', methods=['POST'])
def report_error():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400
        device_id = data.get("device_id")
        error_code = data.get("error_code")
        error_message = data.get("error_message")
        module = data.get("module")
        command = data.get("command")
        stack_trace = data.get("stack_trace")
        context = data.get("context")
        if not device_id or not error_code:
            return jsonify({"error": "Missing device_id or error_code"}), 400
        eid = tracker.log_error(device_id, error_code, error_message, module, command, stack_trace, context)
        if error_code == "CriticalError" or "CRITICAL" in error_code.upper():
            logger.warning(f"ALERT: Critical error from {device_id}: {error_message}")
        return jsonify({"status": "received", "error_id": eid}), 200
    except Exception as e:
        logger.exception("Error in report_error endpoint")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/get-errors', methods=['GET'])
def get_errors():
    try:
        device_id = request.args.get("device_id")
        error_code = request.args.get("error_code")
        resolved = request.args.get("resolved")
        if resolved is not None:
            resolved = resolved.lower() == "true"
        limit = int(request.args.get("limit", 100))
        errors = tracker.get_errors(device_id, error_code, resolved, limit)
        return jsonify(errors), 200
    except Exception as e:
        logger.exception("Error in get_errors endpoint")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("ERROR_TRACKER_PORT", 8081))
    app.run(host='0.0.0.0', port=port, debug=False)