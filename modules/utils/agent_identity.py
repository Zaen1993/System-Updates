import uuid
import time
import json
import base64
import hashlib
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography not available, agent signing disabled")

class AgentIdentity:
    def __init__(self, name: str, role: str, ttl: int = 86400):
        self.id = str(uuid.uuid4())
        self.name = name
        self.role = role
        self.created_at = int(time.time())
        self.ttl = ttl
        self._private_key = None
        self._public_key = None
        if CRYPTO_AVAILABLE:
            self._generate_keypair()
        else:
            self._public_key = None
        logger.info(f"Agent {self.name} ({self.id}) created")

    def _generate_keypair(self):
        self._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self._public_key = self._private_key.public_key()

    def sign(self, data: bytes) -> Optional[str]:
        if not CRYPTO_AVAILABLE or not self._private_key:
            return None
        signature = self._private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode()

    def verify(self, data: bytes, signature_b64: str) -> bool:
        if not CRYPTO_AVAILABLE or not self._public_key:
            return False
        try:
            signature = base64.b64decode(signature_b64)
            self._public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    def get_public_key_pem(self) -> Optional[str]:
        if not CRYPTO_AVAILABLE or not self._public_key:
            return None
        pem = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode()

    def get_private_key_pem(self) -> Optional[str]:
        if not CRYPTO_AVAILABLE or not self._private_key:
            return None
        pem = self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        return pem.decode()

    def is_expired(self) -> bool:
        return int(time.time()) > self.created_at + self.ttl

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "created_at": self.created_at,
            "ttl": self.ttl,
            "public_key": self.get_public_key_pem(),
            "expired": self.is_expired()
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentIdentity":
        obj = cls(data["name"], data["role"], data.get("ttl", 86400))
        obj.id = data["id"]
        obj.created_at = data["created_at"]
        if CRYPTO_AVAILABLE and data.get("public_key"):
            try:
                obj._public_key = serialization.load_pem_public_key(
                    data["public_key"].encode(),
                    backend=default_backend()
                )
            except Exception as e:
                logger.error(f"Failed to load public key: {e}")
        return obj

    @classmethod
    def from_json(cls, json_str: str) -> "AgentIdentity":
        return cls.from_dict(json.loads(json_str))

    def __repr__(self):
        return f"<AgentIdentity id={self.id} name={self.name} role={self.role}>"

if __name__ == "__main__":
    ai = AgentIdentity("test-agent", "analyzer")
    print(ai.to_json())
    data = b"hello world"
    sig = ai.sign(data)
    print("Signature:", sig)
    print("Verified:", ai.verify(data, sig))