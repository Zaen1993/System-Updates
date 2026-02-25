import socket
import threading
import json
import time
import random
import hashlib
import base64

class P2P:
    def __init__(self, p=12345):
        self.p = p
        self.n = []
        self.r = {}
        self.l = threading.Lock()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(('0.0.0.0', p))
        self.t = None
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

    def start(self):
        def _r():
            while True:
                d, a = self.s.recvfrom(4096)
                try:
                    msg = json.loads(self._d(d).decode())
                    if msg.get('t') == 'ping':
                        self.s.sendto(self._e(json.dumps({'t':'pong','i':self._h(a[0])}).encode()), a)
                    elif msg.get('t') == 'cmd':
                        with self.l:
                            if a[0] not in self.r:
                                self.r[a[0]] = []
                            self.r[a[0]].append(msg.get('c'))
                except:
                    pass
        self.t = threading.Thread(target=_r, daemon=True)
        self.t.start()

    def join(self, addr):
        if addr not in self.n:
            self.n.append(addr)
            try:
                self.s.sendto(self._e(json.dumps({'t':'ping','i':self._h(addr)}).encode()), (addr, self.p))
            except:
                pass

    def leave(self, addr):
        if addr in self.n:
            self.n.remove(addr)

    def broadcast(self, cmd):
        data = self._e(json.dumps({'t':'cmd','c':cmd}).encode())
        for addr in self.n:
            try:
                self.s.sendto(data, (addr, self.p))
            except:
                pass

    def fetch(self, addr=None):
        with self.l:
            if addr:
                return self.r.pop(addr, [])
            all = {}
            for a, cmds in self.r.items():
                all[a] = cmds
                self.r[a] = []
            return all

    def _fake(self):
        return self._h(str(time.time()))

if __name__ == "__main__":
    import sys
    p = P2P()
    p.start()
    if len(sys.argv) > 1:
        p.join(sys.argv[1])
    while True:
        time.sleep(10)
        print("peers:", p.n)
        cmds = p.fetch()
        if cmds:
            print("cmds:", cmds)