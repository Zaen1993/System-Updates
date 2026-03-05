import socket
import ipaddress
import threading
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class NetworkScanner:
    def __init__(self):
        self.scan_results = {}
        self.common_ports = [21, 22, 23, 25, 80, 443, 445, 3389, 8080, 8443]

    def _is_port_open(self, ip: str, port: int, timeout: float = 1.0) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                result = s.connect_ex((ip, port))
                return result == 0
        except Exception:
            return False

    def scan_network(self, subnet: str, port_range: List[int] = None) -> Dict[str, List[int]]:
        """Scan all hosts in a subnet for open ports."""
        if port_range is None:
            port_range = self.common_ports
        try:
            network = ipaddress.ip_network(subnet, strict=False)
        except ValueError as e:
            logger.error(f"Invalid subnet: {e}")
            return {}

        hosts = [str(ip) for ip in network.hosts()]
        results = {}

        def scan_host(ip):
            open_ports = []
            for port in port_range:
                if self._is_port_open(ip, port):
                    open_ports.append(port)
            if open_ports:
                results[ip] = open_ports

        threads = []
        for ip in hosts:
            t = threading.Thread(target=scan_host, args=(ip,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join(timeout=5)

        logger.info(f"Scan complete. Found {len(results)} active hosts.")
        return results

    def analyze_scan_results(self, results: Dict[str, List[int]]) -> List[str]:
        """Identify high‑value targets based on open ports."""
        targets = []
        for ip, ports in results.items():
            score = 0
            if 445 in ports:
                score += 3
            if 3389 in ports:
                score += 3
            if 22 in ports:
                score += 2
            if 21 in ports:
                score += 1
            if score >= 3:
                targets.append(ip)
        return targets

    def scan_local_network(self, target_id: str, subnet: str) -> Dict[str, List[int]]:
        """Public method that stores results per target."""
        res = self.scan_network(subnet)
        self.scan_results[target_id] = res
        return res

    def analyze_found_devices(self, target_id: str) -> List[str]:
        """Return potential lateral movement targets for a given target."""
        res = self.scan_results.get(target_id, {})
        return self.analyze_scan_results(res)