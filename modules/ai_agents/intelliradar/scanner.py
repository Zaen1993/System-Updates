import logging
import socket
import ipaddress
import json
from typing import List, Dict, Optional
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class IntelliRadarScanner:
    def __init__(self, target_range: str, encryption_key: Optional[bytes] = None):
        self.target_range = target_range
        self.encryption_key = encryption_key
        self.cipher = Fernet(encryption_key) if encryption_key else None

    def _encrypt_data(self, data: Dict) -> Optional[bytes]:
        if self.cipher:
            try:
                return self.cipher.encrypt(json.dumps(data).encode())
            except Exception as e:
                logger.error(f"Encryption failed: {e}")
        return None

    def arp_scan(self) -> List[Dict[str, str]]:
        try:
            from scapy.all import ARP, Ether, srp
        except ImportError:
            logger.error("scapy not installed")
            return []

        logger.info(f"Starting ARP scan on {self.target_range}")
        try:
            arp = ARP(pdst=self.target_range)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether / arp
            result = srp(packet, timeout=3, verbose=0)[0]
            devices = [{"ip": rcv.psrc, "mac": rcv.hwsrc} for _, rcv in result]
            logger.info(f"Found {len(devices)} devices")
            return devices
        except Exception as e:
            logger.error(f"ARP scan failed: {e}")
            return []

    def port_scan(self, ip: str, ports: List[int] = None) -> List[int]:
        if ports is None:
            ports = [22, 80, 443, 445, 3389, 8080, 8443, 3306, 5432, 27017]
        open_ports = []
        logger.info(f"Scanning ports on {ip}")
        for port in ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.3)
                result = s.connect_ex((ip, port))
                if result == 0:
                    open_ports.append(port)
                s.close()
            except Exception:
                continue
        return open_ports

    def scan_network(self) -> List[Dict]:
        devices = self.arp_scan()
        for dev in devices:
            dev["open_ports"] = self.port_scan(dev["ip"])
        return devices

    def get_encrypted_results(self) -> Optional[bytes]:
        data = {"target": self.target_range, "results": self.scan_network()}
        return self._encrypt_data(data)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scanner = IntelliRadarScanner("192.168.1.0/24")
    results = scanner.scan_network()
    print(json.dumps(results, indent=2))