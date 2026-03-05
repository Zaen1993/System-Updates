import os
import shutil
import json
import base64
import logging
import hashlib
import threading
import time
from datetime import datetime
from typing import List, Dict, Optional, Any

try:
    from cryptography.fernet import Fernet
    import requests
except ImportError:
    pass

logger = logging.getLogger("SelfBackup")

class SelfBackupAgent:
    def __init__(self, backup_dir: str = "/tmp/.sys_backup", storage_locations: List[str] = None):
        self.backup_dir = backup_dir
        self.storage_locations = storage_locations or []
        self.encryption_key = self._load_or_create_key()
        self.cipher = Fernet(self.encryption_key) if self.encryption_key else None
        self.running = False
        self.thread = None

    def _load_or_create_key(self) -> Optional[bytes]:
        key_path = os.path.join(self.backup_dir, ".key")
        try:
            if os.path.exists(key_path):
                with open(key_path, "rb") as f:
                    return f.read()
            else:
                key = Fernet.generate_key()
                os.makedirs(self.backup_dir, exist_ok=True)
                with open(key_path, "wb") as f:
                    f.write(key)
                return key
        except Exception:
            return None

    def _encrypt_data(self, data: bytes) -> Optional[bytes]:
        if self.cipher:
            try:
                return self.cipher.encrypt(data)
            except Exception:
                return None
        return data

    def _decrypt_data(self, data: bytes) -> Optional[bytes]:
        if self.cipher:
            try:
                return self.cipher.decrypt(data)
            except Exception:
                return None
        return data

    def create_backup(self, data_path: str, include_metadata: bool = True) -> Optional[str]:
        logger.info(f"Initiating backup for: {data_path}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.tar.gz"
        backup_path = os.path.join(self.backup_dir, backup_name)

        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            shutil.make_archive(backup_path.replace('.tar.gz', ''), 'gztar', data_path)
            logger.info(f"Backup created: {backup_path}")

            if include_metadata:
                self._save_metadata(backup_path, data_path, timestamp)

            self._distribute_backup(backup_path)
            return backup_path
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None

    def _save_metadata(self, backup_path: str, source_path: str, timestamp: str):
        meta = {
            "backup": os.path.basename(backup_path),
            "source": source_path,
            "timestamp": timestamp,
            "size_bytes": os.path.getsize(backup_path) if os.path.exists(backup_path) else 0,
            "hash": self._calculate_hash(backup_path)
        }
        meta_path = backup_path + ".meta"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        logger.debug(f"Metadata saved: {meta_path}")

    def _calculate_hash(self, file_path: str) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _distribute_backup(self, backup_path: str):
        logger.info("Distributing backup to secure locations...")
        if not os.path.exists(backup_path):
            logger.error("Backup file missing, cannot distribute.")
            return

        for location in self.storage_locations:
            try:
                self._upload_to_location(backup_path, location)
                logger.info(f"Uploaded to {location}")
            except Exception as e:
                logger.error(f"Failed to upload to {location}: {e}")

    def _upload_to_location(self, file_path: str, location: str):
        if location.startswith("ftp://"):
            self._upload_ftp(file_path, location)
        elif location.startswith("s3://"):
            self._upload_s3(file_path, location)
        elif location.startswith("http://") or location.startswith("https://"):
            self._upload_http(file_path, location)
        else:
            shutil.copy2(file_path, location)

    def _upload_ftp(self, file_path: str, url: str):
        try:
            from ftplib import FTP
            parts = url.replace("ftp://", "").split("/")
            host = parts[0]
            remote_path = "/" + "/".join(parts[1:]) if len(parts) > 1 else "/"
            ftp = FTP(host)
            ftp.login()
            with open(file_path, "rb") as f:
                ftp.storbinary(f"STOR {remote_path}", f)
            ftp.quit()
        except ImportError:
            logger.warning("FTP module not available")

    def _upload_s3(self, file_path: str, url: str):
        try:
            import boto3
            parts = url.replace("s3://", "").split("/")
            bucket = parts[0]
            key = "/".join(parts[1:]) if len(parts) > 1 else os.path.basename(file_path)
            s3 = boto3.client('s3')
            with open(file_path, "rb") as f:
                s3.upload_fileobj(f, bucket, key)
        except ImportError:
            logger.warning("boto3 not available")

    def _upload_http(self, file_path: str, url: str):
        with open(file_path, "rb") as f:
            files = {'file': f}
            requests.post(url, files=files, timeout=30)

    def schedule_periodic_backup(self, interval_seconds: int = 3600, data_path: str = "/server/data"):
        def backup_loop():
            self.running = True
            while self.running:
                self.create_backup(data_path)
                time.sleep(interval_seconds)

        self.thread = threading.Thread(target=backup_loop, daemon=True)
        self.thread.start()
        logger.info(f"Periodic backup scheduled every {interval_seconds}s")

    def stop_periodic_backup(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            logger.info("Periodic backup stopped")

    def restore_backup(self, backup_path: str, restore_to: str) -> bool:
        if not os.path.exists(backup_path):
            logger.error(f"Backup not found: {backup_path}")
            return False
        try:
            shutil.unpack_archive(backup_path, restore_to)
            logger.info(f"Restored {backup_path} to {restore_to}")
            return True
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        backups = []
        if not os.path.exists(self.backup_dir):
            return backups
        for fname in os.listdir(self.backup_dir):
            if fname.endswith(".tar.gz"):
                full = os.path.join(self.backup_dir, fname)
                meta_path = full + ".meta"
                if os.path.exists(meta_path):
                    with open(meta_path) as f:
                        meta = json.load(f)
                else:
                    meta = {"size_bytes": os.path.getsize(full), "hash": self._calculate_hash(full)}
                backups.append({
                    "name": fname,
                    "path": full,
                    "size": os.path.getsize(full),
                    "created": datetime.fromtimestamp(os.path.getctime(full)).isoformat(),
                    "metadata": meta
                })
        return sorted(backups, key=lambda x: x["created"], reverse=True)

    def process_task(self, task_type: str, data: Any) -> Dict:
        if task_type == "create":
            path = data.get("path")
            incl_meta = data.get("include_metadata", True)
            result = self.create_backup(path, incl_meta)
            return {"backup_path": result} if result else {"error": "backup failed"}
        elif task_type == "restore":
            backup = data.get("backup")
            target = data.get("target")
            ok = self.restore_backup(backup, target)
            return {"success": ok}
        elif task_type == "list":
            return {"backups": self.list_backups()}
        elif task_type == "schedule":
            interval = data.get("interval", 3600)
            path = data.get("path", "/server/data")
            self.schedule_periodic_backup(interval, path)
            return {"scheduled": True}
        elif task_type == "stop":
            self.stop_periodic_backup()
            return {"stopped": True}
        return {"error": "unknown task"}

if __name__ == "__main__":
    # مثال للتشغيل المستقل
    agent = SelfBackupAgent(storage_locations=["/mnt/backup", "ftp://backup.example.com/"])
    agent.create_backup("/server/data")
    print("Backup created.")