import json
import logging
import hashlib
import base64
from typing import Dict, Any, Optional
import pandas as pd
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

class AnalystAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.data = None
        self._secret = hashlib.sha256(str(id(self)).encode()).digest()

    def load_data(self, source: str, format: str = 'csv') -> bool:
        try:
            if format == 'csv':
                self.data = pd.read_csv(source)
            elif format == 'json':
                self.data = pd.read_json(source)
            else:
                return False
            return True
        except Exception as e:
            logger.error(f"load_data error: {e}")
            return False

    def analyze(self) -> Dict[str, Any]:
        if self.data is None or self.data.empty:
            return {"status": "no_data"}
        try:
            features = self.data.select_dtypes(include=[float, int])
            if features.shape[1] == 0:
                return {"status": "no_numeric_features"}
            predictions = self.model.fit_predict(features)
            anomalies = (predictions == -1).sum()
            return {
                "status": "ok",
                "anomalies": int(anomalies),
                "total": len(features)
            }
        except Exception as e:
            logger.error(f"analyze error: {e}")
            return {"status": "error", "message": str(e)}

    def _xor(self, data: bytes) -> bytes:
        key = self._secret
        return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

    def encrypt_report(self, report: Dict) -> str:
        plain = json.dumps(report).encode()
        encrypted = self._xor(plain)
        return base64.b64encode(encrypted).decode()

    def decrypt_report(self, encrypted: str) -> Dict:
        raw = base64.b64decode(encrypted)
        decrypted = self._xor(raw)
        return json.loads(decrypted.decode())

    def process_task(self, task_type: str, data: Any) -> Dict:
        if task_type == "analyze":
            return self.analyze()
        elif task_type == "load":
            success = self.load_data(data.get("source"), data.get("format", "csv"))
            return {"success": success}
        elif task_type == "encrypt":
            return {"encrypted": self.encrypt_report(data)}
        elif task_type == "decrypt":
            return self.decrypt_report(data)
        return {"error": "unknown_task"}