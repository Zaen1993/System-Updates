import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class SecureCallback:
    def __init__(self, secret_key: str, salt: str = "fixed_salt_123"):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        self.cipher = Fernet(key)
        self.shortcuts = {
            "process_file": "pf:",
            "send_to_admin": "sa:",
            "delete_cache": "dc:",
            "get_system_info": "gsi:",
            "capture_media": "cm:",
            "start_service": "ss:"
        }
        self.reverse_shortcuts = {v: k for k, v in self.shortcuts.items()}

    def _compress(self, text: str) -> str:
        for long, short in self.shortcuts.items():
            text = text.replace(long, short)
        return text

    def _decompress(self, text: str) -> str:
        for short, long in self.reverse_shortcuts.items():
            text = text.replace(short, long)
        return text

    def encrypt_data(self, plain_text: str) -> str:
        try:
            compressed = self._compress(plain_text)
            encrypted = self.cipher.encrypt(compressed.encode())
            return encrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return plain_text

    def decrypt_data(self, encrypted_text: str) -> str:
        try:
            decrypted = self.cipher.decrypt(encrypted_text.encode()).decode('utf-8')
            return self._decompress(decrypted)
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return ""

callback_handler = SecureCallback(secret_key="my_super_secret_key")
