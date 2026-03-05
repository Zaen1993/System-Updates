import os
import base64
import hashlib
import hmac
import secrets
import logging
from typing import Optional, Tuple, Dict, Any, List
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag

logger = logging.getLogger(__name__)

class CryptoAgilityManager:
    def __init__(self, master_secret: bytes, salt: bytes):
        self.master_secret = master_secret
        self.salt = salt
        self.backend = default_backend()
        self._supported_versions = [1, 2]
        self._current_version = 2
        self._key_cache = {}
        self._version_transition_window = 3600

    def derive_key(self, context: bytes, version: int = None) -> bytes:
        v = version or self._current_version
        cache_key = f"{v}:{context.hex()}"
        if cache_key in self._key_cache:
            return self._key_cache[cache_key]

        kdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt + v.to_bytes(1, 'big'),
            info=context,
            backend=self.backend
        )
        key = kdf.derive(self.master_secret)
        self._key_cache[cache_key] = key
        return key

    def encrypt(self, data: bytes, aad: bytes = b"", version: int = None) -> bytes:
        ver = version or self._current_version
        context = b"encrypt" + ver.to_bytes(1, 'big')
        key = self.derive_key(context, ver)

        if ver == 1:
            return self._encrypt_v1(key, data, aad)
        else:
            return self._encrypt_v2(key, data, aad)

    def decrypt(self, ciphertext: bytes, aad: bytes = b"") -> bytes:
        if len(ciphertext) < 2:
            raise ValueError("ciphertext too short")
        version = ciphertext[0]
        if version not in self._supported_versions:
            raise ValueError(f"unsupported version {version}")

        context = b"encrypt" + version.to_bytes(1, 'big')
        key = self.derive_key(context, version)

        if version == 1:
            return self._decrypt_v1(key, ciphertext[1:], aad)
        else:
            return self._decrypt_v2(key, ciphertext[1:], aad)

    def _encrypt_v1(self, key: bytes, plaintext: bytes, aad: bytes) -> bytes:
        iv = secrets.token_bytes(12)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        encryptor.authenticate_additional_data(aad)
        ct = encryptor.update(plaintext) + encryptor.finalize()
        return bytes([1]) + iv + encryptor.tag + ct

    def _decrypt_v1(self, key: bytes, data: bytes, aad: bytes) -> bytes:
        iv = data[:12]
        tag = data[12:28]
        ct = data[28:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=self.backend)
        decryptor = cipher.decryptor()
        decryptor.authenticate_additional_data(aad)
        return decryptor.update(ct) + decryptor.finalize()

    def _encrypt_v2(self, key: bytes, plaintext: bytes, aad: bytes) -> bytes:
        iv = secrets.token_bytes(16)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        encryptor.authenticate_additional_data(aad)
        ct = encryptor.update(plaintext) + encryptor.finalize()
        return bytes([2, len(iv)]) + iv + encryptor.tag + ct

    def _decrypt_v2(self, key: bytes, data: bytes, aad: bytes) -> bytes:
        iv_len = data[0]
        iv = data[1:1+iv_len]
        tag = data[1+iv_len:1+iv_len+16]
        ct = data[1+iv_len+16:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=self.backend)
        decryptor = cipher.decryptor()
        decryptor.authenticate_additional_data(aad)
        return decryptor.update(ct) + decryptor.finalize()

    def encrypt_with_dual(self, data: bytes, aad: bytes = b"") -> Tuple[bytes, bytes]:
        v1 = self.encrypt(data, aad, version=1)
        v2 = self.encrypt(data, aad, version=2)
        return v1, v2

    def rotate_version(self, new_version: int):
        if new_version not in self._supported_versions:
            raise ValueError(f"unsupported version {new_version}")
        self._current_version = new_version
        logger.info(f"current crypto version set to {new_version}")

    def get_supported_versions(self) -> List[int]:
        return self._supported_versions.copy()

    def get_current_version(self) -> int:
        return self._current_version

    def enable_transition_window(self, seconds: int = 3600):
        self._version_transition_window = seconds
        logger.info(f"transition window set to {seconds}s")