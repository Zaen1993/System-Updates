import json
import random
import hashlib
import base64

class GLR:
    def __init__(self):
        self.s = bytearray(random.getrandbits(8) for _ in range(32))
        self.h = {}

    def _h(self, d):
        return hashlib.sha256(str(d).encode() + self.s).hexdigest()

    def _m(self, a, b):
        return [[sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]

    def _n(self, m):
        return [i for i in range(len(m)) if all(m[i][j] == max(col) for j, col in enumerate(zip(*m)))]

    def e(self, ctx):
        r = random.randint(1000, 9999)
        return self._h(r)

    def p(self, hist):
        if not hist:
            return {"s": "i", "p": 0.5}
        w = [h["w"] for h in hist if "w" in h]
        if not w:
            return {"s": "r", "p": 0.5}
        avg = sum(w) / len(w)
        nxt = avg + random.uniform(-0.1, 0.1)
        return {"s": "p", "p": max(0, min(1, nxt))}

    def a(self, data):
        k = self._h(data)
        self.h[k] = data
        return k

    def r(self, key):
        return self.h.get(key, None)

    def _x(self, b):
        return base64.b64encode(b).decode()

    def _y(self, s):
        return base64.b64decode(s)

    def z(self, mtx):
        flat = [item for sublist in mtx for item in sublist]
        h = hashlib.sha256(str(flat).encode()).digest()
        return self._x(h)

    def _t(self, n):
        return [[random.random() for _ in range(n)] for _ in range(n)]

    def w(self, dim):
        mat = self._t(dim)
        dom = self._n(mat)
        return {"mat": self.z(mat), "dom": dom}

    def s(self, a, b):
        mix = [(x + y) / 2 for x, y in zip(a, b)]
        return mix