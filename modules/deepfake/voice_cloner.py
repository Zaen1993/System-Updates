#!/usr/bin/env python3
import json
import time
import random
import hashlib
import base64
from cryptography.fernet import Fernet

class VoiceCloner:
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

    def clone(self, audio, text):
        cid = self._h(audio + text + str(time.time()))
        return self._e(json.dumps({"id": cid, "audio": audio, "text": text}).encode())

    def synthesize(self, clone_id, phrase):
        return self._e(json.dumps({"clone_id": clone_id, "phrase": phrase, "ts": time.time()}).encode())

if __name__ == "__main__":
    vc = VoiceCloner()
    c = vc.clone("sample.wav", "Hello world")
    print(c)
    s = vc.synthesize(json.loads(vc._d(c).decode())["id"], "New phrase")
    print(s)