#!/usr/bin/env python3
import json
import time
import hashlib
import base64
import random
from cryptography.fernet import Fernet

class HaystackSearcher:
    def __init__(self):
        self._s = bytearray(random.getrandbits(8) for _ in range(32))
        self._k = Fernet.generate_key()
        self._f = Fernet(self._k)
        self._idx = {}

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

    def index(self, docs):
        for i, doc in enumerate(docs):
            doc_id = self._h(doc)
            self._idx[doc_id] = doc
        return list(self._idx.keys())

    def search(self, query, top_k=5):
        results = []
        for doc_id, doc in self._idx.items():
            if query in doc:
                results.append((doc_id, doc))
        return results[:top_k]

    def encrypt_index(self):
        return self._e(json.dumps(self._idx).encode())

    def load_index(self, enc):
        self._idx = json.loads(self._d(enc).decode())

if __name__ == "__main__":
    hs = HaystackSearcher()
    docs = ["apple banana", "apple pie", "banana split", "cherry pie"]
    print("indexing...")
    ids = hs.index(docs)
    print("indexed ids:", ids)
    print("search 'apple':", hs.search("apple"))
    enc = hs.encrypt_index()
    print("encrypted index:", enc)
    hs2 = HaystackSearcher()
    hs2.load_index(enc)
    print("search after load:", hs2.search("pie"))