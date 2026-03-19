import threading
import time

class AutoCollector:
    def run(self):
        threading.Thread(target=self._collect).start()

    def _collect(self):
        while True:
            time.sleep(60)
