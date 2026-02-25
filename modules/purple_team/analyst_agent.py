#!/usr/bin/env python3
import json
import time
import random
import hashlib
import base64
from cryptography.fernet import Fernet

class AnalystAgent:
    def __init__(self, aid):
        self.id = aid
        self._s = bytearray(random.getrandbits(8) for _ in range(32))
        self._k = Fernet.generate_key()
        self._f = Fernet(self._k)
        self._d = []

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

    def analyze(self, data):
        try:
            j = json.loads(data) if isinstance(data, str) else data
            self._d.append(j)
            res = {"status": "analyzed", "count": len(self._d), "id": self._h(str(j))}
            return self._e(json.dumps(res).encode())
        except Exception as e:
            return self._e(json.dumps({"status": "error", "msg": str(e)}).encode())

    def summary(self):
        return {"entries": len(self._d), "latest": self._d[-1] if self._d else None}

if __name__ == "__main__":
    import sys
    a = AnalystAgent("analyst1")
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            res = a.analyze(f.read())
            print(a._d(res).decode())
    else:
        print(json.dumps(a.summary()))