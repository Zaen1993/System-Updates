import os
import base64
import hashlib
import hmac
import secrets
import logging
import json
from typing import Optional, Tuple, Dict, Any
from flask import request, abort
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag

logger = logging.getLogger(__name__)

class CryptoManager:
    def __init__(self, master_secret: bytes, salt: bytes):
        self.master_secret = master_secret
        self.salt = salt
        self.backend = default_backend()
        self._key_cache = {}
        self._supported_versions = [1, 2]
        self._current_version = 2

    def derive_device_key(self, device_id: str, version: int = None) -> bytes:
        cache_key = f"{device_id}_{version or self._current_version}"
        if cache_key in self._key_cache:
            return self._key_cache[cache_key]

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt + device_id.encode() + str(version or self._current_version).encode(),
            iterations=100000,
            backend=self.backend
        )
        key = kdf.derive(self.master_secret)
        self._key_cache[cache_key] = key
        return key

    def generate_ephemeral_keypair(self) -> Tuple:
        private_key = x25519.X25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key

    def compute_shared_secret(self, private_key, peer_public_bytes: bytes) -> bytes:
        peer_public = x25519.X25519PublicKey.from_public_bytes(peer_public_bytes)
        shared = private_key.exchange(peer_public)
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            info=b"session-key",
            backend=self.backend
        )
        return hkdf.derive(shared)

    def encrypt_packet(self, key: bytes, plaintext: bytes, aad: bytes = b"", version: int = None) -> bytes:
        ver = version or self._current_version
        if ver == 1:
            return self._encrypt_v1(key, plaintext, aad)
        else:
            return self._encrypt_v2(key, plaintext, aad)

    def decrypt_packet(self, key: bytes, ciphertext: bytes, aad: bytes = b"") -> bytes:
        if len(ciphertext) < 2:
            raise ValueError("Ciphertext too short")
        version = ciphertext[0]
        if version == 1:
            return self._decrypt_v1(key, ciphertext[1:], aad)
        elif version == 2:
            return self._decrypt_v2(key, ciphertext[1:], aad)
        else:
            raise ValueError(f"Unsupported version {version}")

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

    def encrypt_stored_key(self, key_material: bytes) -> bytes:
        wrap_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            info=b"key-wrapping",
            backend=self.backend
        ).derive(self.master_secret)
        iv = secrets.token_bytes(12)
        cipher = Cipher(algorithms.AES(wrap_key), modes.GCM(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        ct = encryptor.update(key_material) + encryptor.finalize()
        return iv + encryptor.tag + ct

    def decrypt_stored_key(self, encrypted: bytes) -> bytes:
        wrap_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            info=b"key-wrapping",
            backend=self.backend
        ).derive(self.master_secret)
        iv = encrypted[:12]
        tag = encrypted[12:28]
        ct = encrypted[28:]
        cipher = Cipher(algorithms.AES(wrap_key), modes.GCM(iv, tag), backend=self.backend)
        decryptor = cipher.decryptor()
        return decryptor.update(ct) + decryptor.finalize()

    def sign_hmac(self, key: bytes, message: bytes) -> str:
        h = hmac.new(key, message, hashlib.sha256)
        return h.hexdigest()

    def verify_hmac(self, key: bytes, message: bytes, signature: str) -> bool:
        expected = self.sign_hmac(key, message)
        return hmac.compare_digest(expected, signature)

    def rotate_master_key(self, new_master: bytes):
        self.master_secret = new_master
        self._key_cache.clear()
        logger.info("Master key rotated")

    def get_supported_versions(self) -> list:
        return self._supported_versions

    def set_current_version(self, version: int):
        if version in self._supported_versions:
            self._current_version = version
            logger.info(f"Current crypto version set to {version}")
        else:
            raise ValueError(f"Unsupported version {version}")


class SecurityShield:
    def __init__(self, master_secret: bytes, salt: bytes):
        self.crypto = CryptoManager(master_secret, salt)
        self.secret_key = os.environ.get('ACCESS_KEY', 'default_secret_key').encode()
        self.malicious_patterns = [
            "DROP TABLE", "SELECT * FROM", "system(", "eval(", "exec(",
            "rm -rf", "wget", "curl", "chmod", "chown", "sudo"
        ]

    def secure_outgoing_data(self, data: dict, device_id: str) -> str:
        """Encrypt data for a specific device and return base64 string."""
        device_key = self.crypto.derive_device_key(device_id)
        json_data = json.dumps(data).encode()
        encrypted = self.crypto.encrypt_packet(device_key, json_data)
        return base64.b64encode(encrypted).decode()

    def process_incoming_data(self, encrypted_data: str, device_id: str) -> dict:
        """Decrypt data from a device and return original dict."""
        device_key = self.crypto.derive_device_key(device_id)
        raw = base64.b64decode(encrypted_data)
        decrypted = self.crypto.decrypt_packet(device_key, raw)
        return json.loads(decrypted.decode())

    def validate_device_session(self, token: str) -> bool:
        """Validate a JWT token (placeholder)."""
        try:
            import jwt
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return True
        except Exception:
            return False

    # ----- New methods from user request -----
    def verify_integrity(self, data: str, received_checksum: str) -> bool:
        """Verify data integrity using SHA-256."""
        computed = hashlib.sha256(data.encode('utf-8')).hexdigest()
        return computed == received_checksum

    def filter_request(self):
        """Filter incoming HTTP requests for security."""
        auth_header = request.headers.get('X-Auth-Token')
        if not auth_header or auth_header != self.secret_key.decode():
            abort(403)

        if request.is_json:
            data = request.get_json()
            if self._contains_malicious_content(data):
                abort(400)

    def _contains_malicious_content(self, data: Any) -> bool:
        """Check for malicious patterns in data."""
        data_str = json.dumps(data)
        for pattern in self.malicious_patterns:
            if pattern in data_str:
                return True
        return False