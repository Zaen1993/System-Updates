import os
import json
import base64
import logging
import random
import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhishingBot:
    def __init__(self, config_path=None):
        self.config = self._load_config(config_path)
        self.key = self._derive_key()
        self.cipher = Fernet(self.key)
        self.scenarios = self._load_scenarios()
        self.conversation_log = []

    def _load_config(self, path):
        default = {
            "scenario_file": "scenarios.json",
            "log_encrypted": True,
            "callback_url": os.environ.get("PHISHING_CALLBACK_URL", ""),
            "user_agent": "Mozilla/5.0"
        }
        if path and os.path.exists(path):
            with open(path, 'r') as f:
                loaded = json.load(f)
                default.update(loaded)
        return default

    def _derive_key(self):
        password = os.environ.get("PHISHING_SECRET", "default_secret_change_me").encode()
        salt = os.environ.get("PHISHING_SALT", "salt_123").encode()
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        return base64.urlsafe_b64encode(kdf.derive(password))

    def _load_scenarios(self):
        try:
            with open(self.config["scenario_file"], 'r') as f:
                return json.load(f)
        except:
            return {
                "default": [
                    "Your account requires verification. Click here: {link}",
                    "Urgent security update: {link}",
                    "You have a new message. Read it: {link}"
                ]
            }

    def _generate_link(self, scenario):
        base = self.config.get("callback_url", "https://example.com")
        token = base64.urlsafe_b64encode(os.urandom(16)).decode().rstrip("=")
        return f"{base}/track?t={token}"

    def respond(self, user_input, scenario="default"):
        if scenario not in self.scenarios:
            scenario = "default"
        templates = self.scenarios[scenario]
        template = random.choice(templates)
        link = self._generate_link(scenario)
        response = template.format(link=link)
        self._log_interaction(user_input, response)
        return response

    def _log_interaction(self, user_msg, bot_msg):
        entry = {
            "user": user_msg,
            "bot": bot_msg,
            "timestamp": __import__("time").time()
        }
        self.conversation_log.append(entry)
        if self.config.get("log_encrypted", True):
            encrypted = self.cipher.encrypt(json.dumps(entry).encode())
            logger.info(f"LOG: {base64.b64encode(encrypted).decode()}")
        else:
            logger.info(f"LOG: {entry}")

    def encrypt_payload(self, data):
        return self.cipher.encrypt(json.dumps(data).encode())

    def decrypt_payload(self, enc_data):
        return json.loads(self.cipher.decrypt(enc_data).decode())

if __name__ == "__main__":
    bot = PhishingBot()
    print(bot.respond("Hello"))