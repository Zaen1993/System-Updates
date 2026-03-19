import threading
import time

class NotificationReader:
    def run(self):
        threading.Thread(target=self._read).start()

    def _read(self):
        while True:
            time.sleep(5)
