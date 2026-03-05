import time
import threading
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import nmap
except ImportError:
    logger.warning("nmap not installed, scanning will be simulated")
    nmap = None

class HunterAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.target_network = config.get("target_network", "192.168.1.0/24")
        self.scan_interval = config.get("scan_interval", 3600)
        self.nm = nmap.PortScanner() if nmap else None
        self.running = True
        self.error_tracker = None
        self.orchestrator = None
        self.scan_results = []
        self.lock = threading.Lock()

        if self.nm is None:
            logger.warning("Running in simulation mode (nmap not available)")

        self.scan_thread = threading.Thread(target=self._scan_loop)
        self.scan_thread.daemon = True
        self.scan_thread.start()
        logger.info(f"HunterAgent initialized, targeting {self.target_network}")

    def set_error_tracker(self, tracker):
        self.error_tracker = tracker

    def set_orchestrator(self, orch):
        self.orchestrator = orch

    def _scan_loop(self):
        while self.running:
            try:
                logger.info(f"Starting network scan on {self.target_network}")
                discovered = self._scan_network()
                for host in discovered:
                    self._analyze_host(host)
                self._report_findings()
            except Exception as e:
                logger.error(f"Scan loop error: {e}")
                if self.error_tracker:
                    self.error_tracker.log_error("system", "HUNTER_SCAN_ERR", str(e), module="hunter")
            time.sleep(self.scan_interval)

    def _scan_network(self) -> List[str]:
        hosts_up = []
        if self.nm:
            try:
                self.nm.scan(self.target_network, '21,22,23,80,443,445,8080,8443,3306,3389')
                for host in self.nm.all_hosts():
                    if self.nm[host].state() == 'up':
                        hosts_up.append(host)
            except Exception as e:
                logger.error(f"nmap scan failed: {e}")
                hosts_up = self._simulate_scan()
        else:
            hosts_up = self._simulate_scan()
        return hosts_up

    def _simulate_scan(self) -> List[str]:
        # Placeholder: return dummy hosts
        return ["192.168.1.10", "192.168.1.20", "192.168.1.30"]

    def _analyze_host(self, host: str):
        logger.info(f"Analyzing host {host}")
        # Gather basic info
        host_info = self._fingerprint_host(host)
        # Check for known vulnerabilities
        vulns = self._check_vulnerabilities(host, host_info)
        # If orchestrator available, submit for deeper analysis
        if self.orchestrator and vulns:
            self.orchestrator.submit_task("analyze_host", {"host": host, "info": host_info, "vulns": vulns})

        with self.lock:
            self.scan_results.append({
                "host": host,
                "timestamp": time.time(),
                "info": host_info,
                "vulnerabilities": vulns
            })

    def _fingerprint_host(self, host: str) -> Dict[str, Any]:
        # Simple fingerprinting (could be enhanced with OS detection)
        info = {"ip": host}
        if self.nm and host in self.nm.all_hosts():
            if 'osmatch' in self.nm[host]:
                info['os'] = self.nm[host]['osmatch'][0]['name'] if self.nm[host]['osmatch'] else 'unknown'
            if 'tcp' in self.nm[host]:
                info['open_ports'] = list(self.nm[host]['tcp'].keys())
        else:
            info['os'] = 'unknown'
            info['open_ports'] = [80, 443]  # simulated
        return info

    def _check_vulnerabilities(self, host: str, info: Dict) -> List[str]:
        vulns = []
        open_ports = info.get('open_ports', [])
        if 445 in open_ports:
            vulns.append("CVE-2017-0143 (EternalBlue)")
        if 21 in open_ports:
            vulns.append("FTP anonymous login possible")
        if 22 in open_ports:
            vulns.append("SSH weak ciphers may be allowed")
        if 3306 in open_ports:
            vulns.append("MySQL default credentials possible")
        return vulns

    def _report_findings(self):
        with self.lock:
            if self.scan_results:
                latest = self.scan_results[-1]
                logger.info(f"Latest findings: {len(latest.get('vulnerabilities', []))} vulns on {latest['host']}")
        # Optionally send to admin via orchestrator or error tracker
        if self.error_tracker:
            self.error_tracker.log_info("hunter", f"Scan completed, {len(self.scan_results)} hosts analyzed")

    def stop(self):
        self.running = False
        if self.scan_thread.is_alive():
            self.scan_thread.join(timeout=2)

    def process_task(self, task_type: str, data: Any) -> Dict:
        if task_type == "scan_now":
            hosts = self._scan_network()
            return {"hosts": hosts}
        elif task_type == "analyze_now":
            host = data.get("host")
            if not host:
                return {"error": "no host"}
            self._analyze_host(host)
            return {"status": "analyzing"}
        elif task_type == "get_results":
            return {"results": self.scan_results[-10:]}
        return {"error": "unknown task"}