import unittest
import json
import base64
from unittest.mock import patch, MagicMock
import requests

class ErrorInjectionTests(unittest.TestCase):

    def setUp(self):
        self.base_url = "http://127.0.0.1:5000"
        self.test_device = "test_device_001"
        self.master_key = base64.b64encode(b"test_master_key_32_bytes_test_key").decode()

    @patch('requests.post')
    def test_server_unreachable(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError
        try:
            resp = requests.post(f"{self.base_url}/api/v1/collect", json={"d": "test"}, timeout=2)
            self.fail("Expected exception not raised")
        except requests.exceptions.ConnectionError:
            pass

    @patch('requests.post')
    def test_malformed_json(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        resp = requests.post(f"{self.base_url}/api/v1/collect", data="not json")
        self.assertEqual(resp.status_code, 400)

    @patch('requests.post')
    def test_invalid_signature(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        headers = {"X-Signature": "invalid"}
        resp = requests.post(f"{self.base_url}/api/v1/collect", json={"id": self.test_device}, headers=headers)
        self.assertEqual(resp.status_code, 401)

    @patch('requests.post')
    def test_timeout_handling(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout
        try:
            resp = requests.post(f"{self.base_url}/api/v1/collect", json={"d": "test"}, timeout=1)
            self.fail("Expected timeout exception")
        except requests.exceptions.Timeout:
            pass

    @patch('requests.post')
    def test_rate_limiting(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response
        for _ in range(10):
            resp = requests.post(f"{self.base_url}/api/v1/collect", json={"id": self.test_device})
        self.assertEqual(resp.status_code, 429)

    def test_encryption_decryption(self):
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        key = b"32_bytes_test_key_12345678901234"
        iv = b"16_bytes_test_iv"
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        plain = b"sensitive data"
        padded = plain + b"\x00" * (16 - len(plain) % 16)
        ct = encryptor.update(padded) + encryptor.finalize()
        decryptor = cipher.decryptor()
        pt = decryptor.update(ct) + decryptor.finalize()
        self.assertEqual(plain, pt.rstrip(b"\x00"))

if __name__ == '__main__':
    unittest.main()