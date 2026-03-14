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

    def encrypt_data(self, plain_text: str) -> str:
        try:
            encrypted = self.cipher.encrypt(plain_text.encode())
            return encrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return plain_text

    def decrypt_data(self, encrypted_text: str) -> str:
        try:
            decrypted = self.cipher.decrypt(encrypted_text.encode())
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return ""

callback_handler = SecureCallback(secret_key="my_super_secret_key")
