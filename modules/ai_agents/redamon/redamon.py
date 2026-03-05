import os
import sys
import time
import json
import logging
import hashlib
import threading
import requests
import psutil
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("rda")

class rda:
    def __init__(self, cfg=None):
        self.cfg = cfg or {}
        self.interval = self.cfg.get("interval", 30)
        self.api_url = self.cfg.get("api_url", os.environ.get("RDA_API_URL", "http://localhost:8080/api/alert"))
        self.api_key = self.cfg.get("api_key", os.environ.get("RDA_API_KEY", ""))
        self.bp = {}
        self.fw = {}
        self.nl = []
        self.running = True
        self._load_baseline()

    def _load_baseline(self):
        try:
            with open("baseline.json", "r") as f:
                self.bp = json.load(f)
        except:
            self.bp = {"processes": {}, "files": {}, "connections": []}
            self._save_baseline()

    def _save_baseline(self):
        with open("baseline.json", "w") as f:
            json.dump(self.bp, f, indent=2)

    def _hash_file(self, path):
        try:
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    h.update(chunk)
            return h.hexdigest()
        except:
            return None

    def _scan_processes(self):
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'username', 'create_time']):
            try:
                pinfo = p.info
                procs.append({
                    "pid": pinfo['pid'],
                    "name": pinfo['name'],
                    "exe": pinfo['exe'],
                    "cmd": " ".join(pinfo['cmdline']) if pinfo['cmdline'] else "",
                    "user": pinfo['username'],
                    "start": pinfo['create_time']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return procs

    def _scan_connections(self):
        conns = []
        for c in psutil.net_connections(kind='inet'):
            if c.status == 'ESTABLISHED' and c.raddr:
                conns.append({
                    "laddr": f"{c.laddr.ip}:{c.laddr.port}",
                    "raddr": f"{c.raddr.ip}:{c.raddr.port}",
                    "pid": c.pid,
                    "status": c.status
                })
        return conns

    def _scan_files(self, paths=None):
        if paths is None:
            paths = ['/etc/passwd', '/etc/shadow', '/etc/hosts', '/var/log/auth.log']
        files = {}
        for p in paths:
            if os.path.exists(p):
                files[p] = self._hash_file(p)
        return files

    def _check_anomalies(self):
        alerts = []

        # process monitoring
        cur_procs = self._scan_processes()
        cur_proc_names = [p['name'] for p in cur_procs]
        sus_names = ['nc', 'ncat', 'netcat', 'mimikatz', 'wireshark', 'tcpdump', 'nmap', 'hydra', 'john', 'sqlmap']
        for p in cur_procs:
            if p['name'] and any(s in p['name'].lower() for s in sus_names):
                alerts.append({"type": "suspicious_process", "details": p})

        # connection monitoring
        cur_conns = self._scan_connections()
        for c in cur_conns:
            if c['raddr'].startswith(('10.', '192.168.', '172.16.')):
                pass
            elif c['raddr'].startswith(('8.8.8.8', '1.1.1.1')):
                pass
            else:
                alerts.append({"type": "unusual_connection", "details": c})

        # file integrity
        cur_files = self._scan_files()
        for f, h in cur_files.items():
            if f in self.bp.get('files', {}):
                if self.bp['files'][f] != h:
                    alerts.append({"type": "file_modified", "details": {"file": f, "old_hash": self.bp['files'][f], "new_hash": h}})
            else:
                self.bp['files'][f] = h

        return alerts

    def _send_alert(self, alert):
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            resp = requests.post(self.api_url, json=alert, headers=headers, timeout=5)
            if resp.status_code >= 300:
                logger.warning(f"alert send failed: {resp.status_code}")
        except Exception as e:
            logger.error(f"alert send exception: {e}")

    def run(self):
        logger.info("rda started")
        while self.running:
            try:
                alerts = self._check_anomalies()
                for a in alerts:
                    logger.warning(f"anomaly: {a}")
                    self._send_alert(a)
                self._save_baseline()
                time.sleep(self.interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"check loop error: {e}")
                time.sleep(self.interval)
        logger.info("rda stopped")

    def stop(self):
        self.running = False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--api-url", default=os.environ.get("RDA_API_URL", "http://localhost:8080/api/alert"))
    parser.add_argument("--api-key", default=os.environ.get("RDA_API_KEY", ""))
    args = parser.parse_args()
    cfg = {"interval": args.interval, "api_url": args.api_url, "api_key": args.api_key}
    d = rda(cfg)
    d.run()