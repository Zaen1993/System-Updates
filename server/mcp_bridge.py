import socket
import json
import time
import random
import hashlib
import base64
import threading

class MCPB:
    def __init__(self, h='127.0.0.1', p=12347):
        self.h = h
        self.p = p
        self.s = None
        self._x = bytearray(random.getrandbits(8) for _ in range(32))
        self._c = []

    def _h(self, d):
        return hashlib.sha256(str(d).encode() + self._x).hexdigest()

    def _b(self, d):
        return base64.b64encode(d).decode()

    def _ub(self, s):
        return base64.b64decode(s)

    def _e(self, d):
        return bytes([a ^ b for a, b in zip(d, self._x * (len(d)//32+1))])

    def _d(self, d):
        return self._e(d)

    def _l(self, msg):
        return self._b(self._e(json.dumps(msg).encode()))

    def _u(self, data):
        return json.loads(self._d(self._ub(data)).decode())

    def conn(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.h, self.p))
            return True
        except:
            return False

    def send(self, cmd, pld=None):
        if not self.s:
            return False
        msg = {'c': cmd, 'p': pld, 't': time.time(), 'h': self._h(cmd+str(pld))}
        try:
            self.s.sendall(self._l(msg).encode() + b'\n')
            return True
        except:
            return False

    def recv(self):
        if not self.s:
            return None
        try:
            d = self.s.recv(4096)
            if not d:
                return None
            for line in d.split(b'\n'):
                if line:
                    try:
                        return self._u(line)
                    except:
                        pass
            return None
        except:
            return None

    def ch_open(self, id, type='ws'):
        self._c.append({'id': id, 't': type, 's': None})

    def ch_send(self, id, data):
        for ch in self._c:
            if ch['id'] == id:
                if ch['s']:
                    try:
                        ch['s'].sendall(data)
                        return True
                    except:
                        return False
        return False

    def close(self):
        if self.s:
            self.s.close()
            self.s = None

    def _fake(self):
        return self._h(str(time.time()))

if __name__ == "__main__":
    b = MCPB()
    if b.conn():
        b.send("ping", {"data": "test"})
        r = b.recv()
        print(r)
        b.close()