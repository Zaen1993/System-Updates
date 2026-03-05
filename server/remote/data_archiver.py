import os
import tarfile
import shutil
import base64
import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

class DataArchiver:
    def __init__(self, staging_dir="/tmp/staging", archive_dir="/tmp/archives", key=None):
        self.staging_dir = staging_dir
        self.archive_dir = archive_dir
        os.makedirs(self.staging_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)
        if key is None:
            key = os.environ.get('MASTER_KEY', 'defaultkey12345678').encode()[:32]
        self.key = key.ljust(32, b'\0')[:32]

    def _encrypt_file(self, file_path):
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(128).padder()
        with open(file_path, 'rb') as f:
            data = f.read()
        padded = padder.update(data) + padder.finalize()
        encrypted = encryptor.update(padded) + encryptor.finalize()
        enc_path = file_path + '.enc'
        with open(enc_path, 'wb') as f:
            f.write(iv + encrypted)
        os.remove(file_path)
        return enc_path

    def archive_target(self, target_id):
        src = os.path.join(self.staging_dir, target_id)
        if not os.path.isdir(src):
            logger.warning(f"Staging area for {target_id} not found")
            return None
        archive_name = f"{target_id}_{int(time.time())}.tar.gz"
        archive_path = os.path.join(self.archive_dir, archive_name)
        try:
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(src, arcname=target_id)
            enc_path = self._encrypt_file(archive_path)
            shutil.rmtree(src)
            logger.info(f"Archived and encrypted {target_id}")
            return enc_path
        except Exception as e:
            logger.error(f"Archive failed: {e}")
            return None