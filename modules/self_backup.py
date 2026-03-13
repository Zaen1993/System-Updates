import os
import shutil
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SelfBackup:
    def __init__(self):
        base_path = os.environ.get('EXTERNAL_STORAGE', '/sdcard')
        self.base_backup_path = os.path.join(base_path, 'Download', 'SystemBackups')
        self._ensure_backup_directory()

    def _ensure_backup_directory(self):
        try:
            if not os.path.exists(self.base_backup_path):
                os.makedirs(self.base_backup_path, exist_ok=True)
                logger.info(f"Backup directory created at: {self.base_backup_path}")
        except Exception as e:
            logger.error(f"Failed to create backup directory: {e}")

    def create_backup(self, source_dir):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.zip"
            destination_path = os.path.join(self.base_backup_path, backup_filename)
            shutil.make_archive(destination_path.replace('.zip', ''), 'zip', source_dir)
            logger.info(f"Backup completed successfully: {destination_path}")
            return destination_path
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None

    def cleanup_old_backups(self, days=7):
        try:
            now = datetime.now().timestamp()
            for file in os.listdir(self.base_backup_path):
                file_path = os.path.join(self.base_backup_path, file)
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    if now - file_time > days * 86400:
                        os.remove(file_path)
                        logger.info(f"Removed old backup: {file}")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

if __name__ == "__main__":
    backup_manager = SelfBackup()
    backup_manager.create_backup(os.getcwd())
    backup_manager.cleanup_old_backups()
