import os
import logging
from PIL import Image
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

class SecureMediaManager:
    def __init__(self, encryption_key: bytes):
        self.aesgcm = AESGCM(encryption_key)

    def remove_exif(self, image_path: str) -> bool:
        try:
            with Image.open(image_path) as img:
                data = list(img.getdata())
                img_without_exif = Image.new(img.mode, img.size)
                img_without_exif.putdata(data)
                img_without_exif.save(image_path)
            return True
        except Exception as e:
            logger.error(f"remove_exif failed: {e}")
            return False

    def encrypt_media(self, file_path: str) -> str | None:
        try:
            if not os.path.exists(file_path):
                return None
            with open(file_path, 'rb') as f:
                data = f.read()
            nonce = os.urandom(12)
            ciphertext = self.aesgcm.encrypt(nonce, data, None)
            encrypted_path = f"{file_path}.enc"
            with open(encrypted_path, 'wb') as f:
                f.write(nonce + ciphertext)
            return encrypted_path
        except Exception as e:
            logger.error(f"encrypt_media failed: {e}")
            return None

    def secure_cleanup(self, file_path: str) -> None:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"secure_cleanup failed: {e}")

    def process_and_protect(self, image_path: str) -> str | None:
        if not os.path.exists(image_path):
            return None
        if self.remove_exif(image_path):
            enc_path = self.encrypt_media(image_path)
            if enc_path:
                self.secure_cleanup(image_path)
                return enc_path
        return None
