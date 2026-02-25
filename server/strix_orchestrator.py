import json
import random
import hashlib
import base64
import time
import threading

class StrOrc:
    def __init__(self):
        self._s = bytearray(random.getrandbits(8) for _ in range(32))
        self._q = []
        self._l = threading.Lock()
        self._c = 0

    def _h(self, d):
        return hashlib.sha256(str(d).encode() + self._s).hexdigest()

    def _b64e(self, b):
        return base64.b64encode(b).decode()

    def _b64d(self, s):
        return base64.b64decode(s)

    def _m(self, x):
        return (x * 0x9E3779B9) & 0xFFFFFFFF

    def add(self, task):
        tid = self._h(str(task) + str(time.time()))
        with self._l:
            self._q.append({"id": tid, "t": task, "ts": time.time(), "st": 0})
        return tid

    def status(self, tid):
        with self._l:
            for item in self._q:
                if item["id"] == tid:
                    return item
        return None

    def next(self):
        with self._l:
            for item in self._q:
                if item["st"] == 0:
                    item["st"] = 1
                    return item
        return None

    def done(self, tid, result):
        with self._l:
            for item in self._q:
                if item["id"] == tid:
                    item["st"] = 2
                    item["r"] = result
                    return True
        return False

    def prune(self, age=3600):
        now = time.time()
        with self._l:
            self._q = [x for x in self._q if now - x["ts"] < age]

    def stats(self):
        with self._l:
            total = len(self._q)
            pend = sum(1 for x in self._q if x["st"] == 0)
            act = sum(1 for x in self._q if x["st"] == 1)
            done = sum(1 for x in self._q if x["st"] == 2)
        return {"t": total, "p": pend, "a": act, "d": done}

    def serialize(self):
        with self._l:
            return json.dumps(self._q, default=str)

    def _mix(self, a, b):
        return [ (x + y) // 2 for x, y in zip(a, b) ]

    def _shuffle(self, seq):
        r = random.Random(self._h(str(seq)))
        shuffled = seq[:]
        r.shuffle(shuffled)
        return shuffled

    def route(self, tasks):
        return self._shuffle(tasks)

    def _x(self, b):
        return self._b64e(b)

    def _y(self, s):
        return self._b64d(s)

if __name__ == "__main__":
    o = StrOrc()
    t1 = o.add({"type": "scan", "target": "192.168.1.1"})
    t2 = o.add({"type": "exploit", "target": "10.0.0.2"})
    print(o.stats())
    n = o.next()
    if n:
        print("next:", n)
        o.done(n["id"], {"success": True})
    print(o.stats())
    print(o.serialize())