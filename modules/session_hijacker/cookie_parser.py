#!/usr/bin/env python3
import json
import time
import random
import hashlib
import base64
from cryptography.fernet import Fernet

class CookieParser:
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

    def parse(self, raw):
        lines = raw.split('\n')
        cookies = {}
        for l in lines:
            if '=' in l:
                k, v = l.split('=', 1)
                cookies[k.strip()] = v.strip()
        return cookies

    def extract_names(self, raw):
        cookies = self.parse(raw)
        return list(cookies.keys())

    def extract_values(self, raw):
        cookies = self.parse(raw)
        return list(cookies.values())

    def to_json(self, raw):
        return json.dumps(self.parse(raw))

    def to_base64(self, raw):
        return base64.b64encode(raw.encode()).decode()

    def from_base64(self, b64):
        return base64.b64decode(b64).decode()

    def encrypt_cookies(self, raw):
        return self._e(raw.encode())

    def decrypt_cookies(self, enc):
        return self._d(enc).decode()

if __name__ == "__main__":
    cp = CookieParser()
    sample = "session=abc123; token=xyz789"
    print("parsed:", cp.parse(sample))
    print("json:", cp.to_json(sample))
    enc = cp.encrypt_cookies(sample)
    print("encrypted:", enc)
    dec = cp.decrypt_cookies(enc)
    print("decrypted:", dec)