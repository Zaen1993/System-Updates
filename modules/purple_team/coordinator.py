#!/usr/bin/env python3
import json
import time
import random
import hashlib
import base64
import threading
from cryptography.fernet import Fernet

class Coordinator:
    def __init__(self):
        self._s = bytearray(random.getrandbits(8) for _ in range(32))
        self._k = Fernet.generate_key()
        self._f = Fernet(self._k)
        self._a = {}
        self._q = []
        self._l = threading.Lock()

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

    def register(self, n, t):
        with self._l:
            aid = self._h(n + str(t) + str(time.time()))
            self._a[aid] = {"name": n, "type": t, "ts": time.time()}
            return aid

    def unregister(self, aid):
        with self._l:
            if aid in self._a:
                del self._a[aid]
                return True
            return False

    def task(self, aid, cmd):
        with self._l:
            tid = self._h(aid + cmd + str(time.time()))
            self._q.append({"id": tid, "aid": aid, "cmd": cmd, "ts": time.time(), "st": 0})
            return tid

    def next_task(self, aid=None):
        with self._l:
            for t in self._q:
                if t["st"] == 0:
                    if aid is None or t["aid"] == aid:
                        t["st"] = 1
                        return t
            return None

    def complete_task(self, tid, res):
        with self._l:
            for t in self._q:
                if t["id"] == tid:
                    t["st"] = 2
                    t["res"] = res
                    return True
            return False

    def agent_list(self):
        with self._l:
            return list(self._a.keys())

    def stats(self):
        with self._l:
            total = len(self._q)
            pending = sum(1 for t in self._q if t["st"] == 0)
            active = sum(1 for t in self._q if t["st"] == 1)
            done = sum(1 for t in self._q if t["st"] == 2)
            return {"agents": len(self._a), "tasks": total, "pending": pending, "active": active, "done": done}

if __name__ == "__main__":
    c = Coordinator()
    a1 = c.register("recon1", "recon")
    a2 = c.register("exploit1", "exploit")
    t1 = c.task(a1, "scan 192.168.1.1")
    t2 = c.task(a2, "CVE-2026-22769")
    print(c.stats())
    nt = c.next_task()
    if nt:
        print("next:", nt)
        c.complete_task(nt["id"], "done")
    print(c.stats())