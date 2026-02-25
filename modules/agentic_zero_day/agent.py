#!/usr/bin/env python3
import sys
import json
import base64
import hashlib
import requests
import time
import random
from cryptography.fernet import Fernet

class ZA:
    def __init__(self):
        self._s = bytearray(random.getrandbits(8) for _ in range(32))
        self._k = Fernet.generate_key()
        self._f = Fernet(self._k)
        self._q = []
        self._c = 0

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

    def add(self, t):
        i = self._h(str(t) + str(time.time()))
        self._q.append({"id": i, "t": t, "ts": time.time()})
        return i

    def run(self, src):
        try:
            if src.startswith("http"):
                r = requests.get(src, timeout=10)
                c = r.text
            else:
                with open(src, 'r') as f:
                    c = f.read()
            a = self._e(c.encode())
            self._c += 1
            return {"s": "ok", "d": a, "i": self._h(src)}
        except Exception as e:
            return {"s": "err", "e": str(e)}

    def stat(self):
        return {"q": len(self._q), "c": self._c}

if __name__ == "__main__":
    z = ZA()
    if len(sys.argv) > 1:
        res = z.run(sys.argv[1])
        print(json.dumps(res))
    else:
        print(json.dumps(z.stat()))