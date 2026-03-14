import os
import logging
import random

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, cache_dir: str, max_size_mb: int = 50):
        self.cache_dir = cache_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.sensitive_extensions = ['.log', '.json', '.txt', '.db']

    def get_dir_size(self, path: str) -> int:
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total_size += os.path.getsize(fp)
            return total_size
        except Exception as e:
            logger.error(f"get_dir_size failed: {e}")
            return 0

    def secure_delete(self, file_path: str, passes: int = 1) -> None:
        try:
            if not os.path.exists(file_path):
                return
            length = os.path.getsize(file_path)
            with open(file_path, "ba+", buffering=0) as f:
                for _ in range(passes):
                    f.seek(0)
                    f.write(os.urandom(length))
            os.remove(file_path)
            logger.info(f"Securely deleted: {os.path.basename(file_path)}")
        except Exception as e:
            logger.error(f"secure_delete failed for {file_path}: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)

    def auto_cleanup(self) -> None:
        current_size = self.get_dir_size(self.cache_dir)
        if current_size > self.max_size_bytes:
            logger.info(f"Cache size {current_size} exceeded limit. Cleaning...")
            try:
                for dirpath, dirnames, filenames in os.walk(self.cache_dir):
                    for f in filenames:
                        full = os.path.join(dirpath, f)
                        if any(full.endswith(ext) for ext in self.sensitive_extensions):
                            self.secure_delete(full)
                        else:
                            os.remove(full)
            except Exception as e:
                logger.error(f"auto_cleanup failed: {e}")

    def get_cache_report(self) -> dict:
        size_bytes = self.get_dir_size(self.cache_dir)
        return {
            "cache_dir": self.cache_dir,
            "current_size_mb": round(size_bytes / (1024 * 1024), 2),
            "limit_mb": self.max_size_bytes / (1024 * 1024),
            "is_over_limit": size_bytes > self.max_size_bytes
        }
