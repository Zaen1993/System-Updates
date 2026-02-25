import os
import random
import hashlib
import base64
import time
import json

class PMG:
    def __init__(self):
        self._s = bytearray(random.getrandbits(8) for _ in range(32))
        self._c = 0

    def _h(self, d):
        return hashlib.sha256(str(d).encode() + self._s).hexdigest()

    def _b(self, d):
        return base64.b64encode(d).decode()

    def _ub(self, s):
        return base64.b64decode(s)

    def _x(self, b):
        return bytes([a ^ b for a, b in zip(b, self._s * (len(b)//32+1))])

    def _r(self, l=16):
        return bytearray(random.getrandbits(8) for _ in range(l))

    def new_pkg(self, old):
        # generate new package name from old
        h = hashlib.md5(old.encode()).digest()
        p1 = base64.b32encode(h).decode().lower().replace('=', '')
        return f"com.{p1[:8]}.{p1[8:16]}"

    def new_cert(self):
        # dummy cert generation
        return self._h(str(time.time()))

    def mutate(self, code):
        # simple code obfuscation (placeholder)
        lines = code.split('\n')
        new_lines = []
        for l in lines:
            if 'class ' in l:
                parts = l.split(' ')
                if len(parts) > 1:
                    parts[1] = '_' + self._h(parts[1])[:8]
                    l = ' '.join(parts)
            if 'def ' in l:
                parts = l.split(' ')
                if len(parts) > 1:
                    parts[1] = '_' + self._h(parts[1])[:8]
                    l = ' '.join(parts)
            new_lines.append(l)
        return '\n'.join(new_lines)

    def gen(self, src, dst):
        # generate mutated copy
        with open(src, 'r') as f:
            code = f.read()
        mutated = self.mutate(code)
        with open(dst, 'w') as f:
            f.write(mutated)
        return self._h(dst)

    def _fake(self):
        return self._h(str(self._c))

if __name__ == "__main__":
    p = PMG()
    print(p.new_pkg("com.system.updates"))
    print(p.gen("sample.py", "sample_mutated.py"))