import os
import json
import logging
import hashlib
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime

import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class TargetProfiler:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.cve_cache = {}
        self._setup_encryption()

    def _setup_encryption(self):
        master_secret = os.environ.get("MASTER_SECRET_B64")
        if master_secret:
            secret = base64.b64decode(master_secret)
            salt = os.environ.get("SALT", "default_salt").encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000
            )
            key = base64.urlsafe_b64encode(kdf.derive(secret))
            self.cipher = Fernet(key)
        else:
            self.cipher = None

    def _encrypt_data(self, data: Dict) -> str:
        if not self.cipher:
            return json.dumps(data)
        serialized = json.dumps(data, sort_keys=True).encode()
        encrypted = self.cipher.encrypt(serialized)
        return base64.b64encode(encrypted).decode()

    def _decrypt_data(self, encrypted: str) -> Dict:
        if not self.cipher:
            return json.loads(encrypted)
        decrypted = self.cipher.decrypt(base64.b64decode(encrypted))
        return json.loads(decrypted.decode())

    def analyze_scan(self, scan_data: Dict) -> Dict[str, Any]:
        """
        Analyze raw scan data and produce a structured target profile.
        """
        logger.info("Analyzing scan data...")
        profile = {
            "target_id": self._generate_target_id(scan_data),
            "os": self._detect_os(scan_data),
            "services": self._extract_services(scan_data),
            "vulnerabilities": [],
            "recommendations": [],
            "timestamp": datetime.utcnow().isoformat()
        }

        # Enrich with CVE matching
        profile["vulnerabilities"] = self._match_cves(profile["services"])
        profile["recommendations"] = self._generate_recommendations(profile)
        return profile

    def _generate_target_id(self, data: Dict) -> str:
        unique = str(data.get("target_ip", "")) + str(data.get("hostname", "")) + str(datetime.utcnow().timestamp())
        return hashlib.sha256(unique.encode()).hexdigest()[:16]

    def _detect_os(self, data: Dict) -> str:
        """
        Simple OS fingerprinting based on common indicators.
        """
        banners = data.get("banners", [])
        for b in banners:
            if "Linux" in b:
                return "linux"
            if "Windows" in b:
                return "windows"
            if "Darwin" in b or "BSD" in b:
                return "bsd"
        return "unknown"

    def _extract_services(self, data: Dict) -> List[Dict]:
        """
        Extract service information from port scan data.
        """
        services = []
        for port_info in data.get("ports", []):
            service = {
                "port": port_info.get("port"),
                "protocol": port_info.get("protocol", "tcp"),
                "name": port_info.get("service", "unknown"),
                "version": port_info.get("version", ""),
                "banner": port_info.get("banner", "")
            }
            services.append(service)
        return services

    def _match_cves(self, services: List[Dict]) -> List[Dict]:
        """
        Match service versions against a local or remote CVE database.
        """
        vulnerabilities = []
        for svc in services:
            if svc["version"]:
                # Example: query a CVE API (simplified)
                # In practice, you'd use a local database or call a service.
                cves = self._query_cve_database(svc["name"], svc["version"])
                if cves:
                    vulnerabilities.append({
                        "service": svc["name"],
                        "version": svc["version"],
                        "cves": cves
                    })
        return vulnerabilities

    def _query_cve_database(self, service: str, version: str) -> List[str]:
        """
        Placeholder for CVE lookup.
        """
        # Simulate some known CVEs
        known = {
            ("openssh", "7.4"): ["CVE-2018-15473", "CVE-2016-6210"],
            ("apache", "2.4.41"): ["CVE-2021-41773", "CVE-2021-42013"],
            ("nginx", "1.18.0"): ["CVE-2021-23017"]
        }
        key = (service.lower(), version)
        return known.get(key, [])

    def _generate_recommendations(self, profile: Dict) -> List[str]:
        """
        Generate attack recommendations based on the profile.
        """
        recs = []
        if profile["os"] == "windows":
            recs.append("consider SMB exploits (EternalBlue)")
        elif profile["os"] == "linux":
            recs.append("check for misconfigured sudo or kernel exploits")

        for vuln in profile["vulnerabilities"]:
            for cve in vuln["cves"]:
                recs.append(f"exploit {cve} targeting {vuln['service']}")
        return recs

    def save_profile(self, profile: Dict, output_path: str):
        """
        Save the profile (optionally encrypted) to a file.
        """
        encrypted = self._encrypt_data(profile)
        with open(output_path, "w") as f:
            f.write(encrypted)
        logger.info(f"Profile saved to {output_path} (encrypted)")

    def load_profile(self, input_path: str) -> Dict:
        """
        Load and decrypt a profile from file.
        """
        with open(input_path, "r") as f:
            encrypted = f.read()
        return self._decrypt_data(encrypted)

if __name__ == "__main__":
    # Example usage
    profiler = TargetProfiler()
    sample_scan = {
        "target_ip": "192.168.1.100",
        "hostname": "test.local",
        "banners": ["Linux ubuntu 5.4.0", "Apache/2.4.41"],
        "ports": [
            {"port": 22, "protocol": "tcp", "service": "openssh", "version": "7.4", "banner": "SSH-2.0-OpenSSH_7.4"},
            {"port": 80, "protocol": "tcp", "service": "apache", "version": "2.4.41", "banner": "Apache/2.4.41 (Ubuntu)"}
        ]
    }
    profile = profiler.analyze_scan(sample_scan)
    print(json.dumps(profile, indent=2))
    profiler.save_profile(profile, "target_profile.dat")