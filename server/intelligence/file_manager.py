import os
import shutil
import logging
from datetime import datetime
from typing import Optional, List

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, base_storage: Optional[str] = None):
        self.base_storage = base_storage or os.environ.get('FILE_STORAGE_PATH', '/intelligence/data/')
        os.makedirs(self.base_storage, exist_ok=True)

    def organize_file(self, target_id: str, source_path: str, file_type: str) -> Optional[str]:
        logger.info(f"Organizing file {source_path} for target {target_id}")
        try:
            date_folder = datetime.now().strftime("%Y-%m-%d")
            target_dir = os.path.join(self.base_storage, target_id, date_folder, file_type)
            os.makedirs(target_dir, exist_ok=True)
            filename = os.path.basename(source_path)
            dest = os.path.join(target_dir, filename)
            shutil.move(source_path, dest)
            logger.info(f"File moved to {dest}")
            return dest
        except Exception as e:
            logger.error(f"Failed to organize file: {e}")
            return None

    def list_files(self, target_id: str, file_type: Optional[str] = None) -> List[str]:
        base = os.path.join(self.base_storage, target_id)
        if not os.path.exists(base):
            return []
        if file_type:
            pattern = os.path.join(base, '*', file_type, '*')
        else:
            pattern = os.path.join(base, '*', '*', '*')
        import glob
        return glob.glob(pattern, recursive=True)

    def delete_file(self, file_path: str) -> bool:
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                logger.info(f"Deleted {file_path}")
                return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
        return False

    def get_file_info(self, file_path: str) -> dict:
        try:
            stat = os.stat(file_path)
            return {
                'path': file_path,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get info for {file_path}: {e}")
            return {}