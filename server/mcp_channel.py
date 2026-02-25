import socket
import json
import time
import random
import hashlib
import base64
import threading

class MCP:
    def __init__(self, h='127.0.0.1', p=12346):
        self.h = h
        self.p = p
        self.s = None
        self.c = []
        self.l = threading.Lock()
        self._x = bytearray(random.getrandbits(8) for _ in range(32))

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

    def conn(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.h, self.p))
            return True
        except:
            return False

    def send(self, data):
        if not self.s:
            return False
        try:
            msg = json.dumps({'t':'d','d':self._b(self._e(data.encode()))})
            self.s.sendall(msg.encode() + b'\n')
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
                        j = json.loads(line)
                        if j.get('t') == 'd':
                            raw = self._ub(j['d'])
                            return self._d(raw).decode()
                    except:
                        pass
            return None
        except:
            return None

    def close(self):
        if self.s:
            self.s.close()
            self.s = None

    def _fake(self):
        return self._h(str(time.time()))

if __name__ == "__main__":
    m = MCP()
    if m.conn():
        m.send("test")
        r = m.recv()
        print(r)
        m.close()