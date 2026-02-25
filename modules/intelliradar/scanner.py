#!/usr/bin/env python3
import sys
import json
import requests
import base64
import hashlib
import random
from bs4 import BeautifulSoup

class IntRad:
    def __init__(self):
        self.nr = "aHR0cHM6Ly9yZWdpc3RyeS5ucG1qcy5vcmcvLXYxL3NlYXJjaA=="
        self.pr = "aHR0cHM6Ly9weXBpLm9yZy9zaW1wbGUv"
        self._s = bytearray(random.getrandbits(8) for _ in range(32))

    def _h(self, d):
        return hashlib.sha256(d.encode() + self._s).hexdigest()

    def _b64e(self, b):
        return base64.b64encode(b).decode()

    def _b64d(self, s):
        return base64.b64decode(s)

    def scn(self, pkg):
        try:
            u = f"https://api.npmjs.org/package/{pkg}"
            r = requests.get(u, timeout=10)
            if r.status_code == 200:
                return r.json()
            return {"e": f"HTTP{r.status_code}"}
        except Exception as e:
            return {"e": str(e)}

    def scp(self, pkg):
        try:
            u = f"https://pypi.org/pypi/{pkg}/json"
            r = requests.get(u, timeout=10)
            if r.status_code == 200:
                return r.json()
            return {"e": f"HTTP{r.status_code}"}
        except Exception as e:
            return {"e": str(e)}

    def srcn(self, limit=10):
        try:
            u = self._b64d(self.nr).decode()
            params = {"text": "bootstrap", "size": limit}
            r = requests.get(u, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                return [p["package"]["name"] for p in data.get("objects", [])]
            return []
        except:
            return []

    def srcp(self, limit=10):
        try:
            u = self._b64d(self.pr).decode()
            r = requests.get(u, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                pkgs = [a.text for a in soup.find_all("a")][:limit]
                return pkgs
            return []
        except:
            return []

    def hys(self, data, query):
        # simple haystack simulation
        res = []
        for d in data:
            if query in d:
                res.append(d)
        return res

    def scnrc(self):
        threats = []
        npm = self.srcn(5)
        pypi = self.srcp(5)
        for p in npm:
            threats.append({"s": "npm", "p": p, "i": self.scn(p)})
        for p in pypi:
            threats.append({"s": "pypi", "p": p, "i": self.scp(p)})
        return threats

    def r(self, pkg):
        n = self.scn(pkg)
        p = self.scp(pkg)
        return {"npm": n, "pypi": p}

    def _mix(self, d):
        return self._h(json.dumps(d))

if __name__ == "__main__":
    ir = IntRad()
    if len(sys.argv) > 1:
        p = sys.argv[1]
        res = ir.r(p)
        print(json.dumps(res, indent=2))
    else:
        recent = ir.scnrc()
        print(json.dumps(recent, indent=2))