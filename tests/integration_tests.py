#!/usr/bin/env python3
import unittest
import json
import requests
import time
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))
from shadow_service import app

class TestIntegration(unittest.TestCase):
    BASE_URL = "http://localhost:10000/v16"

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_register(self):
        payload = {
            "device_id": "test_device_001",
            "public_key": "dGVzdF9wdWJsaWNfa2V5"
        }
        response = self.app.post('/v16/register', json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("server_public_key", data)
        self.assertIn("key_expiry", data)

    def test_pull_no_auth(self):
        response = self.app.get('/v16/pull')
        self.assertEqual(response.status_code, 401)

    def test_push_no_auth(self):
        response = self.app.post('/v16/push', json={"payload": "test"})
        self.assertEqual(response.status_code, 401)

    def test_config_no_auth(self):
        response = self.app.get('/v16/config')
        self.assertEqual(response.status_code, 401)

    def test_api_clients_no_auth(self):
        response = self.app.get('/api/clients')
        self.assertEqual(response.status_code, 401)

    def test_api_command_no_auth(self):
        response = self.app.post('/api/command', json={})
        self.assertEqual(response.status_code, 401)

    def test_api_results_no_auth(self):
        response = self.app.get('/api/results')
        self.assertEqual(response.status_code, 401)

if __name__ == "__main__":
    unittest.main()