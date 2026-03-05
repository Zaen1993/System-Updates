import base64
from cryptography.fernet import Fernet

class SystemAnalyzer:
    def __init__(self):
        k = base64.b64decode(b'NjA2NDcxNjE2MjM4MzEzNDMyMzczMjMzMzUzNjM1MzkzNDMwMzQ3MzM1MzIzNDM5NjMwMjMzNDM1MzYzNzM4Mzkw')
        self.f = Fernet(base64.urlsafe_b64encode(k[:32]))

    def analyze(self, data):
        return self.f.encrypt(data.encode())

    def get_system_metrics(self):
        return self.f.encrypt(b'c3lzdGVtX21ldHJpY3NfZGF0YQ==')