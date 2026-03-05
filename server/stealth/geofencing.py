import os
import json
import time
import ipaddress
import logging
from typing import Dict, Any, Optional, List
import requests

logger = logging.getLogger(__name__)

class Geofencing:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", False)
        self.default_action = self.config.get("default_action", "allow")
        self.blocked_countries = set(self.config.get("blocked_countries", []))
        self.blocked_ips = [ipaddress.ip_network(cidr) for cidr in self.config.get("blocked_ips", [])]
        self.cache = {}
        self.cache_ttl = self.config.get("cache_ttl", 3600)

    def check_ip(self, ip_str: str) -> Dict[str, Any]:
        now = time.time()
        if ip_str in self.cache:
            entry = self.cache[ip_str]
            if now - entry["timestamp"] < self.cache_ttl:
                return entry["result"]
        try:
            ip = ipaddress.ip_address(ip_str)
            for net in self.blocked_ips:
                if ip in net:
                    result = {"action": "block", "reason": f"IP in blocked range {net}"}
                    self.cache[ip_str] = {"timestamp": now, "result": result}
                    return result
            country = self._get_country(ip_str)
            if country in self.blocked_countries:
                result = {"action": "block", "reason": f"Country {country} blocked"}
                self.cache[ip_str] = {"timestamp": now, "result": result}
                return result
            result = {"action": self.default_action, "reason": "allowed by default"}
            self.cache[ip_str] = {"timestamp": now, "result": result}
            return result
        except Exception as e:
            logger.error(f"Geofencing check failed for {ip_str}: {e}")
            return {"action": "allow", "reason": "check_failed"}

    def _get_country(self, ip_str: str) -> Optional[str]:
        try:
            resp = requests.get(f"http://ip-api.com/json/{ip_str}", timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("countryCode")
        except Exception as e:
            logger.debug(f"Country lookup failed: {e}")
        return None

    def should_block(self, ip_str: str) -> bool:
        if not self.enabled:
            return False
        result = self.check_ip(ip_str)
        return result["action"] == "block"

    def filter_devices(self, devices: List[Dict]) -> List[Dict]:
        if not self.enabled:
            return devices
        filtered = []
        for dev in devices:
            ip = dev.get("ip_address")
            if ip and self.should_block(ip):
                logger.info(f"Blocked device {dev.get('client_serial')} due to geofencing")
                continue
            filtered.append(dev)
        return filtered

    def add_blocked_country(self, country_code: str):
        self.blocked_countries.add(country_code.upper())

    def remove_blocked_country(self, country_code: str):
        self.blocked_countries.discard(country_code.upper())

    def add_blocked_ip_range(self, cidr: str):
        try:
            net = ipaddress.ip_network(cidr)
            self.blocked_ips.append(net)
        except Exception as e:
            logger.error(f"Invalid CIDR {cidr}: {e}")

    def get_status(self) -> Dict:
        return {
            "enabled": self.enabled,
            "default_action": self.default_action,
            "blocked_countries": list(self.blocked_countries),
            "blocked_ip_ranges": [str(net) for net in self.blocked_ips],
            "cache_size": len(self.cache)
        }

    def process_task(self, task_type: str, data: Any) -> Dict:
        if task_type == "check":
            ip = data.get("ip")
            if not ip:
                return {"error": "no ip"}
            return self.check_ip(ip)
        elif task_type == "should_block":
            ip = data.get("ip")
            if not ip:
                return {"error": "no ip"}
            return {"block": self.should_block(ip)}
        elif task_type == "filter_devices":
            devices = data.get("devices", [])
            return {"filtered": self.filter_devices(devices)}
        elif task_type == "status":
            return self.get_status()
        elif task_type == "add_country":
            cc = data.get("country_code")
            if cc:
                self.add_blocked_country(cc)
            return {"status": "ok"}
        elif task_type == "remove_country":
            cc = data.get("country_code")
            if cc:
                self.remove_blocked_country(cc)
            return {"status": "ok"}
        return {"error": "unknown task"}