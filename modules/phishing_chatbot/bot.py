#!/usr/bin/env python3
import json
import time
import random
import hashlib
import base64
from cryptography.fernet import Fernet

class PhishingBot:
    def __init__(self):
        self._s = bytearray(random.getrandbits(8) for _ in range(32))
        self._k = Fernet.generate_key()
        self._f = Fernet(self._k)
        self._c = []

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

    def create_campaign(self, target, template):
        cid = self._h(target + str(time.time()))
        self._c.append({"id": cid, "target": target, "tmpl": template, "ts": time.time()})
        return cid

    def send(self, cid, recipient):
        for c in self._c:
            if c["id"] == cid:
                msg = c["tmpl"].replace("{recipient}", recipient)
                return self._e(json.dumps({"to": recipient, "msg": msg, "ts": time.time()}).encode())
        return None

    def log(self, cid, response):
        return self._e(json.dumps({"cid": cid, "resp": response, "ts": time.time()}).encode())

if __name__ == "__main__":
    pb = PhishingBot()
    cid = pb.create_campaign("bank", "Dear {recipient}, please verify your account: http://fake.link")
    print("campaign:", cid)
    msg = pb.send(cid, "user@example.com")
    print("message:", msg)
    log = pb.log(cid, "user clicked")
    print("log:", log)