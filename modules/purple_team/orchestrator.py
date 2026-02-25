#!/usr/bin/env python3
import json
import time
import random
import hashlib
import base64
import threading
from cryptography.fernet import Fernet

class Orch:
    def __init__(self):
        self._s = bytearray(random.getrandbits(8) for _ in range(32))
        self._k = Fernet.generate_key()
        self._f = Fernet(self._k)
        self._a = []
        self._q = []
        self._l = threading.Lock()
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

    def reg(self, n, t):
        aid = self._h(n + str(t) + str(time.time()))
        with self._l:
            self._a.append({"id": aid, "n": n, "t": t, "ts": time.time()})
        return aid

    def task(self, aid, cmd):
        tid = self._h(aid + cmd + str(time.time()))
        with self._l:
            self._q.append({"id": tid, "a": aid, "c": cmd, "ts": time.time(), "st": 0})
        return tid

    def next(self):
        with self._l:
            for t in self._q:
                if t["st"] == 0:
                    t["st"] = 1
                    return t
        return None

    def done(self, tid, res):
        with self._l:
            for t in self._q:
                if t["id"] == tid:
                    t["st"] = 2
                    t["r"] = res
                    return True
        return False

    def res(self, aid=None):
        with self._l:
            if aid:
                return [t for t in self._q if t["a"] == aid and t["st"] == 2]
            return [t for t in self._q if t["st"] == 2]

    def stat(self):
        with self._l:
            return {"a": len(self._a), "q": len(self._q), "c": self._c}

    def run(self, src):
        self._c += 1
        return self._e(json.dumps({"s": "ok", "i": self._h(src)}).encode())

if __name__ == "__main__":
    o = Orch()
    a1 = o.reg("recon", "scan")
    a2 = o.reg("exploit", "cve")
    t1 = o.task(a1, "nmap 192.168.1.1")
    t2 = o.task(a2, "CVE-2026-22769")
    print(o.stat())
    n = o.next()
    if n:
        print("next:", n)
        o.done(n["id"], "done")
    print(o.res())