import os
import json
import base64
import logging
import time
from typing import Optional, Dict, Any, List, Union
import ipfshttpclient
from ipfshttpclient.exceptions import ErrorResponse, ConnectionError

logger = logging.getLogger(__name__)

class IPFSHandler:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.host = self.config.get("host", "/ip4/127.0.0.1/tcp/5001")
        self.timeout = self.config.get("timeout", 60)
        self.client = None
        self._connect()

    def _connect(self) -> bool:
        try:
            self.client = ipfshttpclient.connect(self.host, timeout=self.timeout)
            logger.info(f"Connected to IPFS node at {self.host}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to IPFS: {e}")
            return False

    def add(self, data: Union[str, bytes, dict], pin: bool = True, encrypt: bool = False, key: bytes = None) -> Optional[str]:
        try:
            if encrypt and key:
                if isinstance(data, dict):
                    data = json.dumps(data)
                if isinstance(data, str):
                    data = data.encode()
                from cryptography.fernet import Fernet
                cipher = Fernet(base64.urlsafe_b64encode(key[:32]))
                data = cipher.encrypt(data)
            res = self.client.add_json(data) if isinstance(data, (dict, list)) else self.client.add_str(data)
            cid = res if isinstance(res, str) else res.get('Hash', res)
            if pin and cid:
                self.client.pin.add(cid)
            logger.info(f"Added to IPFS: {cid}")
            return cid
        except Exception as e:
            logger.error(f"IPFS add failed: {e}")
            return None

    def cat(self, cid: str, decrypt: bool = False, key: bytes = None) -> Optional[Union[str, bytes]]:
        try:
            data = self.client.cat(cid)
            if decrypt and key:
                from cryptography.fernet import Fernet
                cipher = Fernet(base64.urlsafe_b64encode(key[:32]))
                data = cipher.decrypt(data)
            try:
                return json.loads(data.decode())
            except:
                return data.decode()
        except Exception as e:
            logger.error(f"IPFS cat failed for {cid}: {e}")
            return None

    def add_json(self, obj: dict, pin: bool = True, encrypt: bool = False, key: bytes = None) -> Optional[str]:
        return self.add(obj, pin, encrypt, key)

    def get_json(self, cid: str, decrypt: bool = False, key: bytes = None) -> Optional[dict]:
        return self.cat(cid, decrypt, key)

    def add_bytes(self, data: bytes, pin: bool = True, encrypt: bool = False, key: bytes = None) -> Optional[str]:
        return self.add(data, pin, encrypt, key)

    def get_bytes(self, cid: str, decrypt: bool = False, key: bytes = None) -> Optional[bytes]:
        try:
            return self.client.cat(cid)
        except Exception as e:
            logger.error(f"IPFS get_bytes failed for {cid}: {e}")
            return None

    def pin_add(self, cid: str) -> bool:
        try:
            self.client.pin.add(cid)
            return True
        except Exception as e:
            logger.error(f"Pin add failed: {e}")
            return False

    def pin_rm(self, cid: str) -> bool:
        try:
            self.client.pin.rm(cid)
            return True
        except Exception as e:
            logger.error(f"Pin rm failed: {e}")
            return False

    def pin_ls(self) -> List[str]:
        try:
            return list(self.client.pin.ls(type='recursive').keys())
        except Exception as e:
            logger.error(f"Pin ls failed: {e}")
            return []

    def ls(self, cid: str) -> List[Dict]:
        try:
            return self.client.ls(cid).get('Objects', [{}])[0].get('Links', [])
        except Exception as e:
            logger.error(f"IPFS ls failed: {e}")
            return []

    def resolve(self, cid: str) -> str:
        return f"https://ipfs.io/ipfs/{cid}"

    def store_command(self, device_id: str, command: Dict, encrypt: bool = True, key: bytes = None) -> Optional[str]:
        data = {
            "device_id": device_id,
            "command": command,
            "timestamp": time.time()
        }
        return self.add_json(data, pin=True, encrypt=encrypt, key=key)

    def retrieve_commands(self, device_id: str, max_age: float = 3600, decrypt: bool = True, key: bytes = None) -> List[Dict]:
        pins = self.pin_ls()
        results = []
        for cid in pins:
            try:
                data = self.get_json(cid, decrypt=decrypt, key=key)
                if data and data.get("device_id") == device_id:
                    ts = data.get("timestamp", 0)
                    if time.time() - ts <= max_age:
                        results.append(data)
            except:
                continue
        return results

    def publish_config(self, config: Dict, encrypt: bool = True, key: bytes = None) -> Optional[str]:
        return self.add_json(config, pin=True, encrypt=encrypt, key=key)

    def fetch_config(self, cid: str, decrypt: bool = True, key: bytes = None) -> Optional[Dict]:
        return self.get_json(cid, decrypt=decrypt, key=key)

    def status(self) -> Dict[str, Any]:
        return {
            "connected": self.client is not None,
            "host": self.host,
            "peer_id": self.client.id()['ID'] if self.client else None,
            "pins": len(self.pin_ls())
        }

    def close(self):
        if self.client:
            self.client.close()