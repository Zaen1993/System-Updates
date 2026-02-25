#!/usr/bin/env python3
import json
import time
import random
import hashlib
import base64
import threading
import queue
import requests
from cryptography.fernet import Fernet

class MatrixBridge:
    def __init__(self, homeserver="https://matrix.org", user=None, pwd=None):
        self.hs = homeserver
        self.user = user
        self.pwd = pwd
        self.token = None
        self.room_id = None
        self._s = bytearray(random.getrandbits(8) for _ in range(32))
        self._k = Fernet.generate_key()
        self._f = Fernet(self._k)
        self._q = queue.Queue()
        self._running = True
        self._listener = None

    def _h(self, d):
        return hashlib.sha256(str(d).encode() + self._s).hexdigest()

    def _b64e(self, d):
        return base64.b64encode(d).decode()

    def _b64d(self, s):
        return base64.b64decode(s)

    def _x(self, b):
        return bytes([a ^ b for a, b in zip(b, self._s * (len(b)//32+1))])

    def _e(self, d):
        e = self._f.encrypt(d)
        return self._b64e(self._x(e))

    def _d(self, s):
        d = self._x(self._b64d(s))
        return self._f.decrypt(d)

    def login(self):
        if not self.user or not self.pwd:
            self.token = "dummy_token"
            return True
        try:
            r = requests.post(f"{self.hs}/_matrix/client/r0/login", json={
                "type": "m.login.password",
                "user": self.user,
                "password": self.pwd
            })
            if r.status_code == 200:
                data = r.json()
                self.token = data["access_token"]
                return True
        except:
            pass
        return False

    def create_room(self, name, encrypted=True):
        if not self.token:
            return None
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "name": name,
            "preset": "private_chat" if encrypted else "public_chat",
            "initial_state": []
        }
        if encrypted:
            payload["initial_state"].append({
                "type": "m.room.encryption",
                "content": {"algorithm": "m.megolm.v1.aes-sha2"}
            })
        try:
            r = requests.post(f"{self.hs}/_matrix/client/r0/createRoom", headers=headers, json=payload)
            if r.status_code == 200:
                data = r.json()
                self.room_id = data["room_id"]
                return self.room_id
        except:
            pass
        return None

    def join_room(self, room_id):
        if not self.token:
            return False
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            r = requests.post(f"{self.hs}/_matrix/client/r0/rooms/{room_id}/join", headers=headers)
            return r.status_code == 200
        except:
            return False

    def send_message(self, msg):
        if not self.token or not self.room_id:
            return False
        encrypted = self._e(msg.encode())
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        payload = {
            "msgtype": "m.text",
            "body": encrypted
        }
        try:
            r = requests.put(f"{self.hs}/_matrix/client/r0/rooms/{self.room_id}/send/m.room.message/{int(time.time()*1000)}", headers=headers, json=payload)
            return r.status_code == 200
        except:
            return False

    def listen(self, callback=None):
        if not self.token or not self.room_id:
            return
        def _l():
            since = None
            while self._running:
                headers = {"Authorization": f"Bearer {self.token}"}
                params = {"timeout": 30000}
                if since:
                    params["since"] = since
                try:
                    r = requests.get(f"{self.hs}/_matrix/client/r0/sync", headers=headers, params=params, timeout=35)
                    if r.status_code == 200:
                        data = r.json()
                        since = data.get("next_batch")
                        rooms = data.get("rooms", {}).get("join", {})
                        if self.room_id in rooms:
                            events = rooms[self.room_id].get("timeline", {}).get("events", [])
                            for ev in events:
                                if ev["type"] == "m.room.message":
                                    body = ev["content"].get("body", "")
                                    try:
                                        dec = self._d(body).decode()
                                        if callback:
                                            callback(dec)
                                        else:
                                            self._q.put(dec)
                                    except:
                                        pass
                except:
                    time.sleep(5)
        self._listener = threading.Thread(target=_l, daemon=True)
        self._listener.start()

    def get_message(self, timeout=1):
        try:
            return self._q.get(timeout=timeout)
        except:
            return None

    def stop(self):
        self._running = False
        if self._listener:
            self._listener.join(timeout=2)

    def _fake(self):
        return self._h(str(time.time()))

if __name__ == "__main__":
    m = MatrixBridge(user="@test:matrix.org", pwd="pass")
    if m.login():
        rid = m.create_room("c2channel")
        if rid:
            m.listen(print)
            m.send_message("hello")
            time.sleep(10)
            m.stop()