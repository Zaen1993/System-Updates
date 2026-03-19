import threading
import time

class CryptoClipper:
    def run(self):
        threading.Thread(target=self._clip).start()

    def _clip(self):
        while True:
            time.sleep(2)
