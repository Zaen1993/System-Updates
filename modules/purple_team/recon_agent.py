#!/usr/bin/env python3
import json
import time
import random
import hashlib
import base64
import socket
import requests
from cryptography.fernet import Fernet

class ReconAgent:
    def __init__(self, aid):
        self.id = aid
        self._s = bytearray(random.getrandbits(8) for _ in range(32))
        self._k = Fernet.generate_key()
        self._f = Fernet(self._k)
        self._r = []

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

    def scan_port(self, host, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            r = s.connect_ex((host, port))
            s.close()
            return r == 0
        except:
            return False

    def scan_ports(self, host, ports=[21,22,23,25,80,443,445,8080,8443,3306,3389]):
        o = []
        for p in ports:
            if self.scan_port(host, p):
                o.append(p)
        return o

    def http_get(self, url):
        try:
            r = requests.get(url, timeout=5)
            return {"code": r.status_code, "len": len(r.text), "type": r.headers.get("content-type","")}
        except:
            return None

    def dns_lookup(self, domain):
        try:
            ip = socket.gethostbyname(domain)
            return ip
        except:
            return None

    def run(self, target):
        res = {}
        res["ip"] = self.dns_lookup(target) if not target.replace('.','').isdigit() else target
        res["ports"] = self.scan_ports(target)
        res["http"] = self.http_get(f"http://{target}") if 80 in res["ports"] else None
        res["https"] = self.http_get(f"https://{target}") if 443 in res["ports"] else None
        res["ts"] = time.time()
        res["id"] = self._h(target + str(res["ts"]))
        enc = self._e(json.dumps(res).encode())
        return enc

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        a = ReconAgent("recon1")
        r = a.run(sys.argv[1])
        print(a._d(r).decode())
    else:
        print("usage: recon_agent.py <target>")