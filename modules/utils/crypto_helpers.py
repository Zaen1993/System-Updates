import os
import base64
import hashlib
import hmac
import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag

logger = logging.getLogger(__name__)

class CryptoHelpers:
    def __init__(self, master_key_b64: str = None, salt: bytes = None):
        self.backend = default_backend()
        if master_key_b64:
            self.master_key = base64.b64decode(master_key_b64)
        else:
            env_key = os.environ.get('MASTER_KEY')
            if env_key:
                self.master_key = base64.b64decode(env_key)
            else:
                self.master_key = os.urandom(32)
                logger.warning("No MASTER_KEY set, using random key (insecure)")
        self.salt = salt or os.environ.get('SALT', 'fixed_salt_16bytes').encode()
        self._supported_versions = [1]

    def derive_key(self, context: bytes, length: int = 32) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=length,
            salt=self.salt + context,
            iterations=100000,
            backend=self.backend
        )
        return kdf.derive(self.master_key)

    def encrypt(self, data: bytes, aad: bytes = b"", context: bytes = b"encrypt") -> bytes:
        key = self.derive_key(context)
        iv = os.urandom(12)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        encryptor.authenticate_additional_data(aad)
        ct = encryptor.update(data) + encryptor.finalize()
        return bytes([1]) + iv + encryptor.tag + ct

    def decrypt(self, ciphertext: bytes, aad: bytes = b"", context: bytes = b"encrypt") -> bytes:
        if len(ciphertext) < 2:
            raise ValueError("ciphertext too short")
        version = ciphertext[0]
        if version != 1:
            raise ValueError(f"unsupported version {version}")
        key = self.derive_key(context)
        iv = ciphertext[1:13]
        tag = ciphertext[13:29]
        ct = ciphertext[29:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=self.backend)
        decryptor = cipher.decryptor()
        decryptor.authenticate_additional_data(aad)
        return decryptor.update(ct) + decryptor.finalize()

    def encrypt_data(self, data: str, aad: str = "") -> str:
        encrypted = self.encrypt(data.encode(), aad.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt_data(self, encrypted_b64: str, aad: str = "") -> str:
        raw = base64.b64decode(encrypted_b64)
        decrypted = self.decrypt(raw, aad.encode())
        return decrypted.decode()

    def sign_hmac(self, key_context: bytes, message: bytes) -> str:
        key = self.derive_key(key_context, length=32)
        h = hmac.new(key, message, hashlib.sha256)
        return h.hexdigest()

    def verify_hmac(self, key_context: bytes, message: bytes, signature: str) -> bool:
        expected = self.sign_hmac(key_context, message)
        return hmac.compare_digest(expected, signature)

    def hash_password(self, password: str) -> str:
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        key = kdf.derive(password.encode())
        return base64.b64encode(salt + key).decode()

    def verify_password(self, password: str, hashed: str) -> bool:
        data = base64.b64decode(hashed)
        salt = data[:16]
        key = data[16:]
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        new_key = kdf.derive(password.encode())
        return hmac.compare_digest(key, new_key)