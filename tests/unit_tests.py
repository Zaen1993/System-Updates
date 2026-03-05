import os
import sys
import unittest
import tempfile
import sqlite3
import base64

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))

from security_shield import CryptoManager
from crypto_agility_manager import CryptoAgilityManager
from error_tracker import ErrorTracker
from command_obfuscator import AIObfuscator

MASTER_SECRET = base64.b64decode(b'bWFzdGVyX3NlY3JldF8zMl9ieXRlX2Jhc2U2NA==')
SALT = b'salt_16_bytes_example'

class TestCrypto(unittest.TestCase):
    def setUp(self):
        self.crypto = CryptoManager(MASTER_SECRET, SALT)
        self.agile = CryptoAgilityManager(MASTER_SECRET, SALT)
        self.device_id = 'test_device_001'

    def test_key_derivation(self):
        key = self.crypto.derive_device_key(self.device_id)
        self.assertEqual(len(key), 32)

    def test_encrypt_decrypt_packet(self):
        key = self.crypto.derive_device_key(self.device_id)
        plain = b'example payload'
        aad = b'aad_data'
        encrypted = self.crypto.encrypt_packet(key, plain, aad)
        decrypted = self.crypto.decrypt_packet(key, encrypted, aad)
        self.assertEqual(plain, decrypted)

    def test_agile_encrypt_decrypt(self):
        data = b'important data'
        ctx = b'context'
        key = self.agile.derive_key(ctx)
        enc = self.agile.encrypt(data)
        dec = self.agile.decrypt(enc)
        self.assertEqual(data, dec)

    def test_agile_dual_encrypt(self):
        data = b'test'
        v1, v2 = self.agile.encrypt_with_dual(data)
        dec1 = self.agile.decrypt(v1)
        dec2 = self.agile.decrypt(v2)
        self.assertEqual(dec1, data)
        self.assertEqual(dec2, data)

class TestObfuscator(unittest.TestCase):
    def setUp(self):
        self.obf = AIObfuscator()

    def test_obfuscate_deobfuscate(self):
        cmd = 'status'
        obf = self.obf.obfuscate_command(cmd)
        deobf = self.obf.deobfuscate_command(obf)
        self.assertEqual(cmd, deobf)

    def test_mutate_patterns(self):
        old = self.obf.patterns.copy()
        self.obf.mutate_patterns()
        self.assertNotEqual(old, self.obf.patterns)

class TestErrorTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = ErrorTracker()

    def test_log_and_retrieve(self):
        eid = self.tracker.log_error('dev1', 'ERR001', 'test error', 'mod', 'cmd', 'trace')
        errors = self.tracker.get_errors(device_id='dev1')
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['error_code'], 'ERR001')
        self.assertEqual(errors[0]['resolved'], False)

    def test_mark_resolved(self):
        eid = self.tracker.log_error('dev1', 'ERR002', 'msg')
        ok = self.tracker.mark_resolved(eid, 'manual')
        self.assertTrue(ok)
        err = self.tracker.get_error(eid)
        self.assertTrue(err['resolved'])
        self.assertEqual(err['resolution_method'], 'manual')

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)')

    def tearDown(self):
        self.conn.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_insert_and_select(self):
        self.conn.execute('INSERT INTO test (value) VALUES (?)', ('hello',))
        cur = self.conn.cursor()
        cur.execute('SELECT value FROM test')
        row = cur.fetchone()
        self.assertEqual(row[0], 'hello')

class TestIntegrationPlaceholder(unittest.TestCase):
    def test_imports(self):
        try:
            import security_shield
            import crypto_agility_manager
            import error_tracker
            import command_obfuscator
        except ImportError as e:
            self.fail(f'import failed: {e}')

if __name__ == '__main__':
    unittest.main()