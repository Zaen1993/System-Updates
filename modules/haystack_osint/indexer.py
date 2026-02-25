#!/usr/bin/env python3
import json
import time
import hashlib
import base64
import random
from cryptography.fernet import Fernet

class HaystackIndexer:
    def __init__(self):
        self._s = bytearray(random.getrandbits(8) for _ in range(32))
        self._k = Fernet.generate_key()
        self._f = Fernet(self._k)
        self._idx = {}
        self._rev = {}

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

    def add(self, doc_id, content):
        self._idx[doc_id] = content
        words = set(content.split())
        for w in words:
            if w not in self._rev:
                self._rev[w] = []
            self._rev[w].append(doc_id)

    def build(self, docs):
        for doc_id, content in docs.items():
            self.add(doc_id, content)

    def search(self, term):
        return self._rev.get(term, [])

    def save(self):
        return self._e(json.dumps({"idx": self._idx, "rev": self._rev}).encode())

    def load(self, enc):
        data = json.loads(self._d(enc).decode())
        self._idx = data["idx"]
        self._rev = data["rev"]

if __name__ == "__main__":
    hi = HaystackIndexer()
    docs = {"doc1": "apple banana", "doc2": "apple pie", "doc3": "banana split"}
    hi.build(docs)
    print("search 'apple':", hi.search("apple"))
    saved = hi.save()
    print("saved index:", saved)
    hi2 = HaystackIndexer()
    hi2.load(saved)
    print("after load search 'banana':", hi2.search("banana"))