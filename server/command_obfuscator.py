#!/usr/bin/env python3
import random
import base64
import hashlib
import time

class AIObfuscator:
    def __init__(self):
        self.np=[
            "sys:opt_cache",
            "bg:sync_ok",
            "chk:upd",
            "bat:health",
            "proc:anlytics",
            "ref:cntnt",
            "val:crd",
            "sync:cfg",
            "mnt:routine",
            "tz:upd"
        ]
        self.seed=int(time.time())%1000
        self.pat=self._gen_pat()
    def _gen_pat(self):
        p=random.Random(self.seed)
        return [p.choice(['a','b','c','d','e','f'])+p.choice(['1','2','3','4','5']) for _ in range(10)]
    def _rot(self,s,n):
        return ''.join(chr((ord(c)-32+n)%95+32) for c in s)
    def obfuscate_command(self,cmd):
        n=random.choice(self.np)
        e=base64.b64encode(cmd.encode()).decode()
        r=random.randint(1,25)
        e=self._rot(e,r)
        return f"{n}|{r}|{e}"
    def deobfuscate_command(self,obf):
        try:
            p=obf.split('|')
            if len(p)==3:
                r=int(p[1]); e=self._rot(p[2],-r)
                return base64.b64decode(e).decode()
        except: pass
        return obf
    def mutate_pattern(self):
        self.seed=(self.seed+random.randint(1,100))%1000
        self.pat=self._gen_pat()