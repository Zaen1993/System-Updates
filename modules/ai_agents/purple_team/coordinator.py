import json
import time
import hashlib
import base64
import threading
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CoordinatorAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.red_team = None
        self.blue_team = None
        self.session_id = hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
        self.lock = threading.Lock()
        self.results = []

    def set_teams(self, red_team, blue_team):
        self.red_team = red_team
        self.blue_team = blue_team
        logger.info(f"Teams set for session {self.session_id}")

    def run_coordinated_exercise(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Starting coordinated exercise: {scenario.get('name', 'unknown')}")
        self.results = []
        threads = []

        if self.red_team and hasattr(self.red_team, 'execute'):
            t1 = threading.Thread(target=self._run_red, args=(scenario,))
            threads.append(t1)
            t1.start()

        if self.blue_team and hasattr(self.blue_team, 'monitor'):
            t2 = threading.Thread(target=self._run_blue, args=(scenario,))
            threads.append(t2)
            t2.start()

        for t in threads:
            t.join(timeout=300)

        report = self._generate_report()
        logger.info("Coordinated exercise completed")
        return report

    def _run_red(self, scenario: Dict[str, Any]):
        try:
            result = self.red_team.execute(scenario)
            with self.lock:
                self.results.append({"team": "red", "result": result})
        except Exception as e:
            logger.error(f"Red team error: {e}")

    def _run_blue(self, scenario: Dict[str, Any]):
        try:
            result = self.blue_team.monitor(scenario)
            with self.lock:
                self.results.append({"team": "blue", "result": result})
        except Exception as e:
            logger.error(f"Blue team error: {e}")

    def _generate_report(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "timestamp": time.time(),
            "results": self.results
        }

    def encrypt_report(self, key: bytes) -> str:
        data = json.dumps(self._generate_report()).encode()
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.backends import default_backend
        import os

        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(128).padder()
        padded = padder.update(data) + padder.finalize()
        ct = encryptor.update(padded) + encryptor.finalize()
        combined = iv + ct
        return base64.b64encode(combined).decode()

    def process_task(self, task_type: str, data: Any) -> Dict[str, Any]:
        if task_type == "run":
            scenario = data.get("scenario", {})
            return self.run_coordinated_exercise(scenario)
        elif task_type == "set_teams":
            # expects red and blue agent objects
            return {"status": "ok"}
        return {"error": "unknown task"}