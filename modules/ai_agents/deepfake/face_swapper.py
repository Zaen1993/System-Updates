import logging
import base64
import os
import cv2
import numpy as np
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from modules.ai_agents.deepfake import swap_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FaceSwapper")

class FaceSwapper:
    def __init__(self, model_path, encryption_key=None):
        logger.info("Loading face swap model...")
        self.model = swap_model.load_model(model_path)
        self.encryption_key = encryption_key if encryption_key else os.urandom(32)

    def _encrypt_image(self, image_data):
        iv = os.urandom(12)
        cipher = Cipher(algorithms.AES(self.encryption_key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(image_data) + encryptor.finalize()
        return iv + encryptor.tag + encrypted

    def _decrypt_image(self, encrypted_data):
        iv = encrypted_data[:12]
        tag = encrypted_data[12:28]
        ct = encrypted_data[28:]
        cipher = Cipher(algorithms.AES(self.encryption_key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ct) + decryptor.finalize()

    def swap_face(self, source_image_path, target_image_path, output_path, quality=95, encrypt_output=False):
        try:
            if not os.path.exists(source_image_path):
                logger.error(f"Source image not found: {source_image_path}")
                return False
            if not os.path.exists(target_image_path):
                logger.error(f"Target image not found: {target_image_path}")
                return False

            logger.info("Loading images...")
            source_img = cv2.imread(source_image_path, cv2.IMREAD_COLOR)
            target_img = cv2.imread(target_image_path, cv2.IMREAD_COLOR)

            if source_img is None or target_img is None:
                logger.error("Failed to load one or both images.")
                return False

            logger.info("Processing face swap...")
            result_img = self.model.process(source_img, target_img)

            if result_img is None:
                logger.error("Face swap model returned None.")
                return False

            logger.info("Encoding result image...")
            _, buffer = cv2.imencode('.jpg', result_img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])

            if encrypt_output:
                encrypted = self._encrypt_image(buffer.tobytes())
                with open(output_path, 'wb') as f:
                    f.write(encrypted)
                logger.info(f"Encrypted result saved to: {output_path}")
            else:
                with open(output_path, 'wb') as f:
                    f.write(buffer)
                logger.info(f"Result saved to: {output_path}")

            return True

        except Exception as e:
            logger.error(f"Error during face swap: {e}")
            return False

    def swap_face_from_bytes(self, source_bytes, target_bytes, encrypt_output=False):
        try:
            source_np = np.frombuffer(source_bytes, np.uint8)
            target_np = np.frombuffer(target_bytes, np.uint8)
            source_img = cv2.imdecode(source_np, cv2.IMREAD_COLOR)
            target_img = cv2.imdecode(target_np, cv2.IMREAD_COLOR)

            if source_img is None or target_img is None:
                logger.error("Failed to decode image bytes.")
                return None

            result_img = self.model.process(source_img, target_img)
            if result_img is None:
                logger.error("Face swap model returned None.")
                return None

            _, buffer = cv2.imencode('.jpg', result_img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            if encrypt_output:
                return self._encrypt_image(buffer.tobytes())
            else:
                return buffer.tobytes()

        except Exception as e:
            logger.error(f"Error during face swap from bytes: {e}")
            return None

if __name__ == "__main__":
    swapper = FaceSwapper(model_path="models/swap_model.h5")
    print("FaceSwapper agent initialized.")