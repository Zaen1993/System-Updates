import os
import logging
from typing import List, Dict, Any, Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class SupabaseSync:
    def __init__(self, node_index: str = "A"):
        self.url = os.environ.get(f"SUPABASE_URL_{node_index}")
        self.key = os.environ.get(f"SUPABASE_KEY_{node_index}")
        self.master_pass = os.environ.get("MASTER_PASSWORD")

        if not self.url or not self.key:
            logger.error(f"Supabase configuration for Node {node_index} is missing")
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")

        self.client: Client = create_client(self.url, self.key)

    def register_client(self, device_id: str, model: str, version: str):
        try:
            data = {
                "client_serial": device_id,
                "model_name": model,
                "android_version": version,
                "auth_token": self.master_pass,
                "last_seen": "now()"
            }
            self.client.table("client_info").upsert(data, on_conflict="client_serial").execute()
        except Exception as e:
            logger.error(f"Error registering client: {e}")

    def get_pending_tasks(self, device_id: str) -> List[Dict[str, Any]]:
        try:
            response = self.client.table('service_tasks') \
                .select('*') \
                .eq('device_id', device_id) \
                .eq('status', 'pending') \
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []

    def add_task(self, device_id: str, command: str, params: Dict = None) -> bool:
        try:
            task_data = {
                "device_id": device_id,
                "command_type": command,
                "params": params or {},
                "status": "pending",
                "created_at": "now()"
            }
            self.client.table('service_tasks').insert(task_data).execute()
            return True
        except Exception as e:
            logger.error(f"Error adding task: {e}")
            return False

    def update_task_status(self, task_id: int, status: str, result: Any = None):
        try:
            update_data = {'status': status}
            if result:
                update_data['result_data'] = result
            self.client.table('service_tasks') \
                .update(update_data) \
                .eq('id', task_id) \
                .execute()
        except Exception as e:
            logger.error(f"Error updating task: {e}")

    def get_notifications(self, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            response = self.client.table('notification_logs') \
                .select('*') \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching logs: {e}")
            return []