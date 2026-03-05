import json
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class PrivilegeEscalationHelper:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), 'vuln_db.json')
        self.vulnerability_db = self._load_db()

    def _load_db(self) -> Dict:
        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load vulnerability DB: {e}")
            return {
                "linux": {
                    "CVE-2021-3156": {"affected": ["5.4", "5.8"], "method": "sudo_heap_overflow"},
                    "CVE-2022-0847": {"affected": ["5.8", "5.16"], "method": "dirty_pipe"},
                },
                "android": {
                    "CVE-2020-0041": {"affected": ["10"], "method": "ashmem_slab_confusion"},
                }
            }

    def analyze_system(self, system_info: Dict) -> List[Dict]:
        results = []
        os_type = system_info.get("os", "linux").lower()
        kernel = system_info.get("kernel_version", "")
        os_ver = system_info.get("os_version", "")

        if os_type in self.vulnerability_db:
            for cve, details in self.vulnerability_db[os_type].items():
                for affected in details.get("affected", []):
                    if kernel.startswith(affected) or os_ver.startswith(affected):
                        results.append({
                            "cve": cve,
                            "method": details.get("method", "unknown"),
                            "confidence": 0.7 if affected in kernel else 0.5
                        })
        logger.info(f"Found {len(results)} potential privilege escalation vectors")
        return results

    def suggest_method(self, vuln: Dict) -> str:
        base = vuln.get("method", "generic")
        cve = vuln.get("cve", "unknown")
        return f"Try {base} exploit for {cve} (search in /modules/exploits/)"