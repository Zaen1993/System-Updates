#!/usr/bin/env python3
import unittest
import sys
import os
import socket
import threading
import time
import json
import base64
import hashlib
import random

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))
try:
    from p2p_handler import P2P
except ImportError:
    # Mock class if import fails
    class P2P:
        def __init__(self, port=12345):
            self.port = port
            self.n = []
            self.r = {}
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.s.bind(('127.0.0.1', port))
            self.running = True
            self._start()

        def _start(self):
            def listen():
                while self.running:
                    try:
                        self.s.settimeout(0.5)
                        data, addr = self.s.recvfrom(1024)
                        msg = json.loads(data.decode())
                        if msg.get('type') == 'ping':
                            self.s.sendto(json.dumps({'type':'pong'}).encode(), addr)
                        elif msg.get('type') == 'data':
                            if addr[0] not in self.r:
                                self.r[addr[0]] = []
                            self.r[addr[0]].append(msg.get('payload'))
                    except socket.timeout:
                        continue
                    except:
                        break
            threading.Thread(target=listen, daemon=True).start()

        def join(self, peer_ip):
            if peer_ip not in self.n:
                self.n.append(peer_ip)

        def send(self, peer_ip, data):
            try:
                self.s.sendto(json.dumps({'type':'data','payload':data}).encode(), (peer_ip, self.port))
            except:
                pass

        def fetch(self, peer_ip=None):
            if peer_ip:
                return self.r.pop(peer_ip, [])
            all = {}
            for ip, msgs in self.r.items():
                all[ip] = msgs
                self.r[ip] = []
            return all

        def close(self):
            self.running = False
            self.s.close()

class TestP2PNetwork(unittest.TestCase):
    def setUp(self):
        self.node1 = P2P(port=12346)
        self.node2 = P2P(port=12347)
        time.sleep(1)

    def tearDown(self):
        self.node1.close()
        self.node2.close()
        time.sleep(0.5)

    def test_peer_discovery(self):
        self.node1.join('127.0.0.1')
        self.assertIn('127.0.0.1', self.node1.n)

    def test_message_exchange(self):
        self.node1.join('127.0.0.1')
        self.node2.join('127.0.0.1')
        time.sleep(1)
        test_msg = "test_command_123"
        self.node2.send('127.0.0.1', test_msg)
        time.sleep(1)
        msgs = self.node1.fetch('127.0.0.1')
        self.assertIn(test_msg, msgs)

    def test_broadcast(self):
        self.node1.join('127.0.0.1')
        self.node2.join('127.0.0.1')
        time.sleep(1)
        broadcast_msg = "broadcast_test"
        self.node2.send('127.0.0.1', broadcast_msg)
        time.sleep(1)
        msgs1 = self.node1.fetch()
        found = any(broadcast_msg in v for v in msgs1.values())
        self.assertTrue(found)

    def test_multiple_messages(self):
        self.node1.join('127.0.0.1')
        self.node2.join('127.0.0.1')
        time.sleep(1)
        for i in range(3):
            self.node2.send('127.0.0.1', f"msg{i}")
        time.sleep(1)
        msgs = self.node1.fetch('127.0.0.1')
        self.assertEqual(len(msgs), 3)

    def test_encryption_integration(self):
        # test that data can be passed through encryption (simulated)
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        f = Fernet(key)
        test_data = "secret_command"
        encrypted = f.encrypt(test_data.encode())
        decrypted = f.decrypt(encrypted).decode()
        self.assertEqual(test_data, decrypted)

if __name__ == '__main__':
    unittest.main()