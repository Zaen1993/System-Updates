import os
import math
import logging
from collections import Counter
from typing import Union, Dict, Any

logger = logging.getLogger(__name__)

class ShannonAnalyzer:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.logger = logger

    def calculate_entropy(self, data: bytes) -> float:
        if not data:
            return 0.0
        data_len = len(data)
        if data_len == 0:
            return 0.0
        frequencies = Counter(data)
        entropy = 0.0
        for count in frequencies.values():
            prob = count / data_len
            if prob > 0:
                entropy -= prob * math.log2(prob)
        return entropy

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        try:
            if not os.path.exists(file_path):
                return {"error": "file not found"}
            with open(file_path, 'rb') as f:
                data = f.read()
            entropy = self.calculate_entropy(data)
            threshold = self.config.get("entropy_threshold", 7.5)
            status = "encrypted" if entropy > threshold else "normal"
            return {"entropy": entropy, "status": status, "size": len(data)}
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {e}")
            return {"error": str(e)}

    def analyze_text(self, text: str) -> Dict[str, Any]:
        data = text.encode('utf-8')
        entropy = self.calculate_entropy(data)
        threshold = self.config.get("entropy_threshold", 7.5)
        status = "high_entropy" if entropy > threshold else "low_entropy"
        return {"entropy": entropy, "status": status, "length": len(data)}

if __name__ == "__main__":
    import json
    analyzer = ShannonAnalyzer()
    sample_data = os.urandom(1024)
    entropy = analyzer.calculate_entropy(sample_data)
    print(json.dumps({"sample_entropy": entropy}, indent=2))