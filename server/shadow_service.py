import os
import socket
import threading
import json
import logging
import base64
from typing import Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from load_balancer import process_task
from error_tracker import ErrorTracker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MASTER_SECRET_B64 = os.environ.get('MASTER_SECRET_B64')
if not MASTER_SECRET_B64:
    raise ValueError("MASTER_SECRET_B64 is required")
MASTER_SECRET = base64.b64decode(MASTER_SECRET_B64)

SALT = os.environ.get('SALT')
if not SALT:
    raise ValueError("SALT is required")
SALT = SALT.encode()

HOST = '0.0.0.0'
PORT = int(os.environ.get('PORT', 10000))

error_tracker = ErrorTracker()

def derive_key(device_id: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT + device_id.encode(),
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(MASTER_SECRET)

def decrypt_packet(key: bytes, ciphertext: bytes) -> bytes:
    iv = ciphertext[:12]
    tag = ciphertext[12:28]
    ct = ciphertext[28:]
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ct) + decryptor.finalize()

def encrypt_packet(key: bytes, plaintext: bytes) -> bytes:
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ct = encryptor.update(plaintext) + encryptor.finalize()
    return iv + encryptor.tag + ct

def handle_client(conn: socket.socket, addr: tuple):
    logger.info(f"Connected by {addr}")
    device_id = None
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            if not device_id:
                try:
                    first_packet = json.loads(data.decode())
                    device_id = first_packet.get('device_id')
                    if not device_id:
                        raise ValueError("Missing device_id")
                    key = derive_key(device_id)
                    logger.info(f"Device {device_id} authenticated")
                    ack = encrypt_packet(key, json.dumps({"status": "auth_ok"}).encode())
                    conn.sendall(ack)
                except Exception as e:
                    logger.error(f"Auth error from {addr}: {e}")
                    error_tracker.log_error("unknown", "AUTH_FAIL", str(e), module="shadow_service")
                    break
            else:
                key = derive_key(device_id)
                try:
                    decrypted = decrypt_packet(key, data)
                    request = json.loads(decrypted.decode())
                    logger.debug(f"Request from {device_id}: {request}")
                    task_type = request.get('type')
                    task_data = request.get('data')
                    if task_type:
                        result = process_task.delay(task_type, task_data).get(timeout=30)
                    else:
                        result = {"status": "error", "message": "no type"}
                    response = encrypt_packet(key, json.dumps(result).encode())
                    conn.sendall(response)
                except Exception as e:
                    logger.error(f"Processing error from {device_id}: {e}")
                    error_tracker.log_error(device_id, "PROCESS_ERR", str(e), module="shadow_service")
    except Exception as e:
        logger.error(f"Connection error with {addr}: {e}")
        error_tracker.log_error(device_id or "unknown", "CONN_ERR", str(e), module="shadow_service")
    finally:
        conn.close()
        logger.info(f"Connection closed for {addr}")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        logger.info(f"Shadow Service listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            client_thread.start()

if __name__ == '__main__':
    start_server()