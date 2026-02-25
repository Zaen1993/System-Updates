#!/usr/bin/env python3
import json
import time
import random
import hashlib
import base64
import requests
from cryptography.fernet import Fernet

class IPFSHandler:
    def __init__(self, gateway="http://localhost:5001", public_gateway="https://ipfs.io/ipfs/"):
        self.gateway = gateway
        self.pub_gateway = public_gateway
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

    def add(self, data):
        try:
            if isinstance(data, str):
                data = data.encode()
            files = {'file': data}
            r = requests.post(f"{self.gateway}/api/v0/add", files=files, timeout=30)
            if r.status_code == 200:
                resp = r.text.strip().split('\n')[-1]
                j = json.loads(resp)
                return j.get('Hash')
        except:
            pass
        return None

    def cat(self, cid):
        try:
            r = requests.post(f"{self.gateway}/api/v0/cat?arg={cid}", timeout=30)
            if r.status_code == 200:
                return r.content
        except:
            pass
        return None

    def add_encrypted(self, data):
        if isinstance(data, str):
            data = data.encode()
        enc = self._e(data)
        return self.add(enc)

    def cat_encrypted(self, cid):
        raw = self.cat(cid)
        if raw:
            try:
                dec = self._d(raw.decode())
                return dec
            except:
                pass
        return None

    def resolve(self, cid):
        return f"{self.pub_gateway}{cid}"

    def _fake(self):
        return self._h(str(time.time()))

if __name__ == "__main__":
    ipfs = IPFSHandler()
    test = "hello ipfs"
    cid = ipfs.add_encrypted(test)
    print("stored at:", cid)
    if cid:
        retrieved = ipfs.cat_encrypted(cid)
        print("retrieved:", retrieved)