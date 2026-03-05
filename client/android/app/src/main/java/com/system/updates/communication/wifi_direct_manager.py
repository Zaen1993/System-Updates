import subprocess
import time
import re
import logging
import threading
import json
import socket
import os
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class WiFiDirectManager:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.interface = self.config.get("interface", "wlan0")
        self.peers = {}
        self.running = False
        self.p2p_group = None
        self.ip_address = None
        self.scan_thread = None
        self._check_dependencies()

    def _check_dependencies(self):
        try:
            subprocess.run(["iw", "--version"], capture_output=True)
        except FileNotFoundError:
            logger.warning("iw not found")

    def start(self):
        self.running = True
        self._enable_p2p()
        self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.scan_thread.start()
        logger.info("WiFiDirectManager started")

    def stop(self):
        self.running = False
        self._disable_p2p()
        logger.info("WiFiDirectManager stopped")

    def _enable_p2p(self):
        try:
            subprocess.run(["sudo", "ifconfig", self.interface, "up"])
            subprocess.run(["sudo", "iw", "dev", self.interface, "set", "type", "p2p_go"])
        except Exception as e:
            logger.error(f"Failed to enable P2P: {e}")

    def _disable_p2p(self):
        try:
            subprocess.run(["sudo", "iw", "dev", self.interface, "set", "type", "managed"])
        except Exception as e:
            logger.error(f"Failed to disable P2P: {e}")

    def _scan_loop(self):
        while self.running:
            try:
                result = subprocess.run(["sudo", "iw", "dev", self.interface, "scan"], capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    self._parse_scan(result.stdout)
            except Exception as e:
                logger.error(f"Scan error: {e}")
            time.sleep(10)

    def _parse_scan(self, scan_output):
        bssids = re.findall(r"BSS ([0-9a-f:]{17})", scan_output)
        for bssid in bssids:
            self.peers[bssid] = {"bssid": bssid, "last_seen": time.time()}

    def scan(self) -> List[Dict]:
        return [{"bssid": b, "last_seen": info["last_seen"]} for b, info in self.peers.items()]

    def connect(self, peer_bssid: str) -> Optional[str]:
        try:
            cmd = ["sudo", "wpa_cli", "p2p_connect", peer_bssid]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                time.sleep(3)
                return self._get_ip()
        except Exception as e:
            logger.error(f"Connect failed: {e}")
        return None

    def _get_ip(self) -> Optional[str]:
        try:
            result = subprocess.run(["hostname", "-I"], capture_output=True, text=True)
            ips = result.stdout.strip().split()
            return ips[0] if ips else None
        except:
            return None

    def send(self, target_ip: str, data: bytes) -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((target_ip, 12345))
            s.send(data)
            s.close()
            return True
        except Exception as e:
            logger.error(f"Send via TCP failed: {e}")
            return False

    def broadcast(self, data: bytes) -> bool:
        success = False
        for peer in self.peers:
            if self.send(peer, data):
                success = True
        return success

    def receive(self, timeout: int = 5) -> Optional[Dict]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", 12345))
            s.settimeout(timeout)
            s.listen(1)
            conn, addr = s.accept()
            data = conn.recv(4096)
            conn.close()
            s.close()
            return {"from": addr[0], "data": data}
        except socket.timeout:
            return None
        except Exception as e:
            logger.error(f"Receive error: {e}")
            return None

    def get_signal_quality(self) -> int:
        return 80

    def status(self) -> dict:
        return {"running": self.running, "interface": self.interface, "peers": len(self.peers)}

    def start_discover(self):
        logger.info("Starting Wi-Fi Direct discovery...")
        try:
            subprocess.run(["wpa_cli", "-i", self.interface, "p2p_find"], check=True)
            logger.info("Discovery initiated.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to initiate discovery: {e}")

    def connect_to_node(self, peer_address: str):
        logger.info(f"Connecting to {peer_address} via Wi-Fi Direct...")
        try:
            subprocess.run(["wpa_cli", "-i", self.interface, "p2p_connect", peer_address, "pbc"], check=True)
            logger.info("Connection request sent.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to connect: {e}")

    def send_file(self, peer_address: str, file_path: str):
        logger.info(f"Sending file {file_path} to {peer_address}")