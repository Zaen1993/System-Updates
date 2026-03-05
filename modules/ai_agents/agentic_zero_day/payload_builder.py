import base64
from cryptography.fernet import Fernet

class PayloadBuilder:
    def __init__(self):
        k = base64.b64decode(b'NjA2NDcxNjE2MjM4MzEzNDMyMzczMjMzMzUzNjM1MzkzNDMwMzQ3MzM1MzIzNDM5NjMwMjMzNDM1MzYzNzM4Mzkw')
        self.f = Fernet(base64.urlsafe_b64encode(k[:32]))

    def build(self, data):
        return self.f.encrypt(data.encode())

    def get_config(self):
        return self.f.encrypt(b'c2VydmVyX2NvbmZpZ19kYXRh')