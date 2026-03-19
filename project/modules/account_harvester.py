import threading
import time

class AccountHarvester:
    def run(self):
        threading.Thread(target=self._harvest).start()

    def _harvest(self):
        while True:
            time.sleep(120)
