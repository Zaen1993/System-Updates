#!/usr/bin/env python3
import sys
import json
import base64
import hashlib
from cryptography.fernet import Fernet
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np

class SAn:
    def __init__(self, mn="microsoft/codebert-base"):
        self.tk = AutoTokenizer.from_pretrained(mn)
        self.md = AutoModelForSequenceClassification.from_pretrained(mn, num_labels=2)
        self.md.eval()
        self.k = Fernet.generate_key()
        self.f = Fernet(self.k)
        self.x = np.random.bytes(32)

    def _x(self, d):
        h = hashlib.sha256(d + self.x).digest()
        return base64.b64encode(h).decode()

    def az(self, cs):
        i = self.tk(cs, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            o = self.md(**i)
        p = torch.softmax(o.logits, dim=-1)
        r = {"v": bool(torch.argmax(p)), "c": float(p[0][1])}
        e = self.f.encrypt(json.dumps(r).encode())
        return self._x(e)

    def sc(self, ru):
        h = hashlib.md5(ru.encode()).hexdigest()
        return {"st": "sc", "id": h, "tk": self._x(b"git")}

    def _y(self, s):
        b = base64.b64decode(s.encode())
        return self.f.decrypt(b).decode()

if __name__ == "__main__":
    a = SAn()
    if len(sys.argv) > 1:
        t = sys.argv[1]
        if t.startswith("http"):
            r = a.sc(t)
            print(json.dumps(r))
        else:
            with open(t, 'r') as f:
                c = f.read()
            r = a.az(c)
            print(json.dumps({"result": r}))
    else:
        print("usage: analyzer.py <file|url>")