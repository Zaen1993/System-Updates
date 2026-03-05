import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def get_cipher():
    secret = os.environ.get('CRYPTO_SECRET')
    if not secret:
        secret = 'default-secret-key-change-in-production'
    salt = os.environ.get('CRYPTO_SALT', 'fixed-salt-16-bytes').encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
    return Fernet(key)

_cipher = get_cipher()

def encrypt_command(command_json: str) -> str:
    if not isinstance(command_json, str):
        command_json = str(command_json)
    return _cipher.encrypt(command_json.encode()).decode()

def decrypt_payload(encrypted_data: str) -> str:
    try:
        return _cipher.decrypt(encrypted_data.encode()).decode()
    except Exception:
        return None

def encrypt_bytes(data: bytes) -> bytes:
    return _cipher.encrypt(data)

def decrypt_bytes(data: bytes) -> bytes:
    try:
        return _cipher.decrypt(data)
    except Exception:
        return None