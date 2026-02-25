#!/usr/bin/env python3
import json
import time
import random
import hashlib
import base64
import requests
from cryptography.fernet import Fernet

class UncensoredAI:
    def __init__(self, api_key=None):
        self._s = bytearray(random.getrandbits(8) for _ in range(32))
        self._k = Fernet.generate_key()
        self._f = Fernet(self._k)
        self.api_key = api_key
        self._endpoints = [
            "https://dark-ai.example.com/api",
            "http://uncensored.local:8080/query",
            "https://gpt4all.example.org/ask"
        ]
        self._current_ep = 0

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

    def _rotate_endpoint(self):
        self._current_ep = (self._current_ep + 1) % len(self._endpoints)

    def ask(self, prompt, system=None):
        # simulate calling an uncensored AI API
        ep = self._endpoints[self._current_ep]
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "prompt": prompt,
            "system": system,
            "temperature": 0.8,
            "max_tokens": 500
        }
        try:
            # in a real implementation, you'd do requests.post(ep, json=payload, headers=headers)
            # here we simulate a response
            time.sleep(1)  # simulate network delay
            response = {
                "choices": [{
                    "text": f"Simulated uncensored response to: {prompt[:50]}...",
                    "finish_reason": "stop"
                }],
                "usage": {"total_tokens": random.randint(50,200)}
            }
            return response
        except Exception as e:
            self._rotate_endpoint()
            return {"error": str(e), "status": "failed"}

    def generate_malware_code(self, description):
        prompt = f"Write a simple {description} script that does the following: download a file from a URL and execute it. Provide only the code."
        resp = self.ask(prompt)
        if "choices" in resp:
            return resp["choices"][0]["text"]
        return None

    def generate_phishing_email(self, target_info):
        prompt = f"Write a convincing phishing email targeting {target_info.get('name','someone')} pretending to be from {target_info.get('company','a bank')}. Include a sense of urgency and a link to click."
        resp = self.ask(prompt)
        if "choices" in resp:
            return resp["choices"][0]["text"]
        return None

    def obfuscate_code(self, original_code):
        prompt = f"Obfuscate this code to avoid detection:\n{original_code}"
        resp = self.ask(prompt)
        if "choices" in resp:
            return resp["choices"][0]["text"]
        return None

    def encrypt_prompt(self, prompt):
        return self._e(prompt.encode())

    def decrypt_response(self, encrypted):
        return self._d(encrypted).decode()

    def _fake(self):
        return self._h(str(time.time()))

if __name__ == "__main__":
    ai = UncensoredAI()
    res = ai.ask("How to bypass security?")
    print(json.dumps(res, indent=2))
    code = ai.generate_malware_code("python reverse shell")
    print(code)