#!/usr/bin/env python3
import os
import base64
import hashlib
import hmac
import secrets
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
try:
    import liboqs
    OQ=True
except ImportError:
    OQ=False

class CryptoManager:
    def __init__(self,ms,slt):
        self.ms=ms; self.slt=slt; self.bk=default_backend()
        self.pq=OQ and os.environ.get('ENABLE_PQC','false').lower()=='true'
    def derive_device_key(self,did):
        k=PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=self.slt+did.encode(),iterations=100000,backend=self.bk)
        return k.derive(self.ms)
    def generate_ephemeral_keypair(self):
        if self.pq and OQ:
            km=liboqs.KeyEncapsulation('Kyber512')
            pk=km.generate_keypair()
            return km,pk
        pv=x25519.X25519PrivateKey.generate()
        pu=pv.public_key()
        return pv,pu
    def compute_shared_secret(self,pv,pub):
        if self.pq and OQ:
            ss=pv.decap_secret(pub)
        else:
            pu=x25519.X25519PublicKey.from_public_bytes(pub)
            ss=pv.exchange(pu)
        h=HKDF(algorithm=hashes.SHA256(),length=32,salt=self.slt,info=b"session-key",backend=self.bk)
        return h.derive(ss)
    def encrypt_packet(self,key,pt,aad=b""):
        iv=secrets.token_bytes(12)
        c=Cipher(algorithms.AES(key),modes.GCM(iv),backend=self.bk)
        e=c.encryptor()
        e.authenticate_additional_data(aad)
        ct=e.update(pt)+e.finalize()
        return iv+e.tag+ct
    def decrypt_packet(self,key,pkt,aad=b""):
        iv=pkt[:12]; tag=pkt[12:28]; ct=pkt[28:]
        c=Cipher(algorithms.AES(key),modes.GCM(iv,tag),backend=self.bk)
        d=c.decryptor()
        d.authenticate_additional_data(aad)
        return d.update(ct)+d.finalize()
    def encrypt_stored_key(self,km):
        wk=HKDF(algorithm=hashes.SHA256(),length=32,salt=self.slt,info=b"key-wrapping",backend=self.bk).derive(self.ms)
        iv=secrets.token_bytes(12)
        c=Cipher(algorithms.AES(wk),modes.GCM(iv),backend=self.bk)
        e=c.encryptor()
        ct=e.update(km)+e.finalize()
        return iv+e.tag+ct
    def decrypt_stored_key(self,ed):
        wk=HKDF(algorithm=hashes.SHA256(),length=32,salt=self.slt,info=b"key-wrapping",backend=self.bk).derive(self.ms)
        iv=ed[:12]; tag=ed[12:28]; ct=ed[28:]
        c=Cipher(algorithms.AES(wk),modes.GCM(iv,tag),backend=self.bk)
        d=c.decryptor()
        return d.update(ct)+d.finalize()
    def split_key(self,key):
        p1=secrets.token_bytes(16)
        p2=secrets.token_bytes(16)
        for i in range(16):
            p2[i]=(key[i]^p1[i]^key[i+16]).to_bytes(1,'big')[0]
        return p1,p2
    def merge_key(self,p1,p2):
        k=bytearray(32)
        for i in range(16):
            k[i]=p1[i]^p2[i]
        for i in range(16,32):
            k[i]=p2[i-16]^k[i-16]
        return bytes(k)
    def sign_hmac(self,key,msg):
        h=hmac.new(key,msg,hashlib.sha256)
        return h.hexdigest()
    def verify_hmac(self,key,msg,sig):
        return hmac.compare_digest(self.sign_hmac(key,msg),sig)