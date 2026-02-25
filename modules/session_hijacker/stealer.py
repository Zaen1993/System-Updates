#!/usr/bin/env python3
import json
import time
import random
import hashlib
import base64
from cryptography.fernet import Fernet

class SessionStealer:
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

    def steal_cookies(self, domain):
        sid = self._h(domain + str(time.time()))
        return self._e(json.dumps({"id": sid, "domain": domain, "cookies": "session_id=abc123; token=xyz"}).encode())

    def steal_tokens(self, service):
        tid = self._h(service + str(time.time()))
        return self._e(json.dumps({"id": tid, "service": service, "tokens": ["token1", "token2"]}).encode())

    def parse(self, data):
        return json.loads(self._d(data).decode())

if __name__ == "__main__":
    ss = SessionStealer()
    c = ss.steal_cookies("example.com")
    print(c)
    print(ss.parse(c))