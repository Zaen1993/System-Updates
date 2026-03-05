import os
import json
import logging
import base64
import requests
import scapy.all as scapy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PurpleTeamRecon")

class ReconAgent:
    def __init__(self, network_range=None):
        self.network_range = network_range or "192.168.1.0/24"
        self.results = []

    def scan_network(self, timeout=2):
        try:
            arp = scapy.ARP(pdst=self.network_range)
            ether = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether / arp
            answered = scapy.srp(packet, timeout=timeout, verbose=False)[0]
            for element in answered:
                self.results.append({"ip": element[1].psrc, "mac": element[1].hwsrc})
            return self.results
        except Exception as e:
            logger.error(f"Scan error: {e}")
            return []

    def format_report(self):
        return json.dumps(self.results, indent=2)

    def send_encrypted(self, server_url, encryption_key):
        try:
            data = self.format_report().encode()
            # simple XOR obfuscation (for demo, replace with proper AES)
            key = encryption_key.encode()[:16]
            obfuscated = bytearray()
            for i, b in enumerate(data):
                obfuscated.append(b ^ key[i % len(key)])
            b64 = base64.b64encode(obfuscated).decode()
            response = requests.post(server_url, json={"payload": b64}, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False

if __name__ == "__main__":
    agent = ReconAgent()
    agent.scan_network()
    print(agent.format_report())