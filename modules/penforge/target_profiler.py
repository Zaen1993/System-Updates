#!/usr/bin/env python3
import json
import time
import random
import hashlib
import base64
import socket
import requests
from cryptography.fernet import Fernet

class TargetProfiler:
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

    def resolve(self, host):
        try:
            return socket.gethostbyname(host)
        except:
            return None

    def scan_port(self, ip, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            r = s.connect_ex((ip, port))
            s.close()
            return r == 0
        except:
            return False

    def http_fingerprint(self, url):
        try:
            r = requests.get(url, timeout=5)
            return {
                "code": r.status_code,
                "server": r.headers.get("server", ""),
                "title": "not parsed",
                "cookies": len(r.cookies)
            }
        except:
            return None

    def profile(self, target):
        ip = self.resolve(target) if not target.replace('.','').isdigit() else target
        if not ip:
            return {"error": "resolution failed"}
        ports = [21,22,23,25,80,443,445,8080,8443,3306,3389]
        open_ports = []
        for p in ports:
            if self.scan_port(ip, p):
                open_ports.append(p)
        services = {}
        if 80 in open_ports:
            services["http"] = self.http_fingerprint(f"http://{ip}")
        if 443 in open_ports:
            services["https"] = self.http_fingerprint(f"https://{ip}")
        if 22 in open_ports:
            services["ssh"] = "sshd"
        if 21 in open_ports:
            services["ftp"] = "ftp"
        if 3306 in open_ports:
            services["mysql"] = "mysql"
        result = {
            "ip": ip,
            "open_ports": open_ports,
            "services": services,
            "timestamp": time.time(),
            "id": self._h(ip)
        }
        return result

    def encrypt_profile(self, profile):
        return self._e(json.dumps(profile).encode())

if __name__ == "__main__":
    import sys
    p = TargetProfiler()
    if len(sys.argv) > 1:
        prof = p.profile(sys.argv[1])
        print(json.dumps(prof, indent=2))
        enc = p.encrypt_profile(prof)
        print("encrypted:", enc)
    else:
        print("usage: target_profiler.py <target>")