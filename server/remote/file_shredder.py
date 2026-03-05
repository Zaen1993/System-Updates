import os
import logging
import base64

logger = logging.getLogger(__name__)

class FileShredder:
    def __init__(self):
        self.passes = 3

    def shred_file(self, target_client_id: str, file_path: str, passes: int = None) -> bool:
        if passes is None:
            passes = self.passes
        logger.info(f"Shredding {file_path} on client {target_client_id} with {passes} passes")
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                return False
            size = os.path.getsize(file_path)
            with open(file_path, 'r+b') as f:
                for _ in range(passes):
                    f.seek(0)
                    f.write(os.urandom(size))
                    f.flush()
                    os.fsync(f.fileno())
            os.remove(file_path)
            logger.info(f"File {file_path} shredded and deleted")
            return True
        except Exception as e:
            logger.error(f"Shred failed: {e}")
            return False