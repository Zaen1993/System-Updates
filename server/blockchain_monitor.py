import time
import json
import hashlib
import base64
import random
from web3 import Web3
from cryptography.fernet import Fernet

class BCM:
    def __init__(self, ep="https://mainnet.infura.io/v3/YOUR_KEY"):
        self.w3 = Web3(Web3.HTTPProvider(ep))
        self._k = Fernet.generate_key()
        self._f = Fernet(self._k)
        self._s = bytearray(random.getrandbits(8) for _ in range(32))
        self._w = []

    def _h(self, d):
        return hashlib.sha256(str(d).encode() + self._s).hexdigest()

    def _b(self, d):
        return base64.b64encode(d).decode()

    def _ub(self, s):
        return base64.b64decode(s)

    def _x(self, b, k):
        return bytes([_a ^ _b for _a, _b in zip(b, k * (len(b)//len(k)+1))])

    def _mk(self):
        return bytearray(random.getrandbits(8) for _ in range(32))

    def _enc(self, d):
        k = self._mk()
        x = self._x(d, k)
        e = self._f.encrypt(x)
        return self._b(e + k)

    def _dec(self, s):
        d = self._ub(s)
        e = d[:-32]
        k = d[-32:]
        x = self._f.decrypt(e)
        return self._x(x, k)

    def w(self, addr, sec=60):
        while True:
            try:
                b = self.w3.eth.block_number
                if len(self._w) == 0:
                    self._w.append(b)
                else:
                    last = self._w[-1]
                    for nb in range(last+1, b+1):
                        block = self.w3.eth.get_block(nb, full_transactions=True)
                        for tx in block.transactions:
                            if tx.to and tx.to.lower() == addr.lower():
                                inp = tx.input
                                if inp and inp != "0x" and len(inp) > 10:
                                    raw = bytes.fromhex(inp[2:])
                                    try:
                                        dec = self._dec(raw)
                                        msg = dec.decode()
                                        print(f"BCM: cmd from {tx.hash.hex()} -> {msg}")
                                    except:
                                        pass
                    self._w.append(b)
            except Exception as e:
                print(f"BCM err: {e}")
            time.sleep(sec)

    def r(self, tx_hash):
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

    def _fake(self):
        return self._h(str(time.time()))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        addr = sys.argv[1]
        mon = BCM()
        mon.w(addr)
    else:
        print("usage: python blockchain_monitor.py <contract_address>")