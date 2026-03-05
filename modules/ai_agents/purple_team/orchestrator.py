import json
import logging
import os
import base64
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography not installed, using base64 encoding (insecure)")

class TaskOrchestrator:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self._init_components()

    def _load_config(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"config load failed: {e}")
            return {}

    def _init_components(self):
        from modules.ai_agents.purple_team import executor
        from modules.ai_agents.purple_team import observer
        self.executor = executor.TaskExecutor(self.config.get("target", ""))
        self.observer = observer.TaskObserver(self.config.get("log_path", "./logs"))
        logger.info("orchestrator ready")

    def _encrypt(self, data: str) -> str:
        if CRYPTO_AVAILABLE:
            key = Fernet.generate_key()
            cipher = Fernet(key)
            enc = cipher.encrypt(data.encode())
            return base64.b64encode(key + enc).decode()
        else:
            return base64.b64encode(data.encode()).decode()

    def _decrypt(self, token: str) -> str:
        try:
            raw = base64.b64decode(token)
            if CRYPTO_AVAILABLE and len(raw) > 32:
                key = raw[:32]
                cipher = Fernet(key)
                return cipher.decrypt(raw[32:]).decode()
            else:
                return raw.decode()
        except:
            return ""

    def run_plan(self) -> Optional[Dict]:
        logger.info("starting orchestration")
        results = []
        tasks = self.config.get("tasks", [])
        if not tasks:
            logger.warning("no tasks defined")
            return None
        for task in tasks:
            task_type = task.get("type", "")
            logger.info(f"processing task: {task_type}")
            self.executor.execute(task_type, task.get("params", {}))
        analysis = self.observer.analyze()
        report = {
            "summary": analysis,
            "task_count": len(tasks),
            "encrypted": self._encrypt(json.dumps(analysis))
        }
        logger.info("orchestration finished")
        return report

if __name__ == "__main__":
    # example usage
    print("orchestrator module loaded")