import os
import logging
import shutil
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataCleaner:
    def __init__(self, target_dirs=None, days_old=30):
        self.target_dirs = target_dirs or []
        self.days_old = int(os.environ.get('CLEANER_DAYS_OLD', days_old))
        self.log_files = [
            '/var/log/syslog',
            '/var/log/auth.log',
            '/var/log/daemon.log',
            '/var/log/kern.log',
            '/tmp/debug.log'
        ]

    def clean_old_files(self):
        cutoff = datetime.now() - timedelta(days=self.days_old)
        for directory in self.target_dirs:
            if not os.path.exists(directory):
                continue
            for root, dirs, files in os.walk(directory):
                for name in files:
                    path = os.path.join(root, name)
                    try:
                        mtime = datetime.fromtimestamp(os.path.getmtime(path))
                        if mtime < cutoff:
                            os.remove(path)
                            logger.info(f"Deleted old file: {path}")
                    except Exception as e:
                        logger.error(f"Error deleting {path}: {e}")
                for name in dirs:
                    path = os.path.join(root, name)
                    try:
                        mtime = datetime.fromtimestamp(os.path.getmtime(path))
                        if mtime < cutoff:
                            shutil.rmtree(path)
                            logger.info(f"Deleted old directory: {path}")
                    except Exception as e:
                        logger.error(f"Error deleting {path}: {e}")

    def wipe_logs(self):
        for log in self.log_files:
            if os.path.exists(log):
                try:
                    with open(log, 'w') as f:
                        f.truncate(0)
                    logger.info(f"Cleared log: {log}")
                except Exception as e:
                    logger.error(f"Failed to clear {log}: {e}")

    def run(self, wipe_logs=True):
        logger.info("Starting data cleaner")
        self.clean_old_files()
        if wipe_logs:
            self.wipe_logs()
        logger.info("Data cleaner finished")

if __name__ == '__main__':
    cleaner = DataCleaner(target_dirs=['/tmp', '/var/tmp'])
    cleaner.run(wipe_logs=True)