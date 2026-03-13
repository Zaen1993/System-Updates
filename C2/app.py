import time
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self, timeout_minutes=10):
        self.authenticated_admins = {}
        self.timeout_seconds = timeout_minutes * 60

    def authenticate_admin(self, chat_id):
        self.authenticated_admins[chat_id] = time.time()
        logger.info(f"Admin {chat_id} session started/refreshed.")

    def is_authenticated(self, chat_id):
        if chat_id not in self.authenticated_admins:
            return False
        last_activity = self.authenticated_admins[chat_id]
        if time.time() - last_activity > self.timeout_seconds:
            self.logout_admin(chat_id)
            logger.warning(f"Session expired for admin {chat_id}")
            return False
        self.authenticated_admins[chat_id] = time.time()
        return True

    def logout_admin(self, chat_id):
        if chat_id in self.authenticated_admins:
            del self.authenticated_admins[chat_id]
            logger.info(f"Admin {chat_id} logged out.")

session_manager = SessionManager(timeout_minutes=10)
