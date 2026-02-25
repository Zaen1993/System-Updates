#!/usr/bin/env python3
import json
import time
import random
import hashlib
import base64
from cryptography.fernet import Fernet

class DeepFakeFactory:
    def __init__(self):
        self._s = bytearray(random.getrandbits(8) for _ in range(32))
        self._k = Fernet.generate_key()
        self._f = Fernet(self._k)

    def _h(self, d):
        return hashlib.sha256(str(d).encode() + self._s).hexdigest()

    def _b64e(self, d):
        return base64.b64encode(d).decode()

    def _b64d(self, s):
        return base64.b64decode(s)

    def _x(self, b):
        return bytes([a ^ b for a, b in zip(b, self._s * (len(b)//32+1))])

    def _e(self, d):
        e = self._f.encrypt(d)
        return self._b64e(self._x(e))

    def _d(self, s):
        d = self._x(self._b64d(s))
        return self._f.decrypt(d)

    def generate_face(self, source, target):
        fid = self._h(source + target + str(time.time()))
        return self._e(json.dumps({"id": fid, "source": source, "target": target}).encode())

    def swap_face(self, video, face):
        return self._e(json.dumps({"video": video, "face": face, "ts": time.time()}).encode())

if __name__ == "__main__":
    df = DeepFakeFactory()
    f = df.generate_face("person_a.jpg", "person_b.jpg")
    print(f)
    print(df._d(f).decode())