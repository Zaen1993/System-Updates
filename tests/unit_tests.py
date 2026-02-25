#!/usr/bin/env python3
import unittest
import os
import sys
import tempfile
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))
from crypto_utils import CryptoManager
from command_obfuscator import AIObfuscator

class TestCryptoUtils(unittest.TestCase):
    def setUp(self):
        self.master = os.urandom(32)
        self.salt = os.urandom(16)
        self.crypto = CryptoManager(self.master, self.salt)

    def test_key_derivation(self):
        device_id = "test_device"
        key = self.crypto.derive_device_key(device_id)
        self.assertEqual(len(key), 32)

    def test_encrypt_decrypt_packet(self):
        key = os.urandom(32)
        plaintext = b"test data"
        aad = b"additional"
        encrypted = self.crypto.encrypt_packet(key, plaintext, aad)
        decrypted = self.crypto.decrypt_packet(key, encrypted, aad)
        self.assertEqual(plaintext, decrypted)

    def test_stored_key_encryption(self):
        key_material = os.urandom(32)
        encrypted = self.crypto.encrypt_stored_key(key_material)
        decrypted = self.crypto.decrypt_stored_key(encrypted)
        self.assertEqual(key_material, decrypted)

class TestObfuscator(unittest.TestCase):
    def setUp(self):
        self.obf = AIObfuscator()

    def test_obfuscate_deobfuscate(self):
        cmd = "test command"
        obf = self.obf.obfuscate_command(cmd)
        deobf = self.obf.deobfuscate_command(obf)
        self.assertEqual(cmd, deobf)

if __name__ == "__main__":
    unittest.main()