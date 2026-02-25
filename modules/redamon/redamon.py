#!/usr/bin/env python3
import os
import sys
import json
import time
import requests
import socket
import base64
import hashlib
from concurrent.futures import ThreadPoolExecutor

class Rdm:
    def __init__(self, tg):
        self.tg = tg
        self.op = []
        self.sv = {}
        self._x = bytearray(os.urandom(32))

    def _h(self, d):
        return hashlib.sha256(d.encode() + self._x).hexdigest()

    def sc(self, pt=[21,22,23,25,80,443,445,8080,8443,3306,3389]):
        def ck(p):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            r = s.connect_ex((self.tg, p))
            s.close()
            if r == 0:
                self.op.append(p)
        with ThreadPoolExecutor(max_workers=20) as ex:
            ex.map(ck, pt)
        return self.op

    def fp(self):
        for p in self.op:
            try:
                if p == 80 or p == 443:
                    u = f"http{'s' if p==443 else ''}://{self.tg}:{p}"
                    r = requests.get(u, timeout=5)
                    self.sv[p] = r.headers.get('server', 'uk')
                elif p == 21:
                    self.sv[p] = "FTP"
                elif p == 22:
                    self.sv[p] = "SSH"
                elif p == 25:
                    self.sv[p] = "SMTP"
                elif p == 445:
                    self.sv[p] = "SMB"
                elif p == 3306:
                    self.sv[p] = "MySQL"
                elif p == 3389:
                    self.sv[p] = "RDP"
                else:
                    self.sv[p] = "uk"
            except:
                self.sv[p] = "uk"
        return self.sv

    def ep(self):
        # placeholder for AI-driven exploitation
        # would normally call external AI model
        return {"rec": "analyze manually"}

    def run(self):
        print(f"[*] scanning {self.tg}")
        self.sc()
        print(f"[+] open: {self.op}")
        self.fp()
        print(f"[+] services: {self.sv}")
        adv = self.ep()
        print(f"[*] advice: {adv}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: redamon.py <target_ip>")
        sys.exit(1)
    r = Rdm(sys.argv[1])
    r.run()