import logging
import random
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AdvisorAgent:
    def __init__(self, error_tracker=None):
        self.error_tracker = error_tracker
        self.alternatives = {
            "network_scan": ["ping_sweep", "dns_enumeration", "arp_scan"],
            "data_exfiltration": ["smtp_tunnel", "dns_tunnel", "https_post"],
            "persistence": ["cron_job", "systemd_service", "bashrc_injection"],
            "privilege_escalation": ["cve_2022_0847", "sudo_bypass", "polkit_exploit"],
            "lateral_movement": ["ssh_key_theft", "wmi_exec", "ps_remoting"],
            "default": ["retry_delayed", "use_fallback_channel", "simplify_command"]
        }

    def suggest_alternative(self, failed_command_type: str, error_code: Optional[str] = None) -> str:
        logger.info(f"Advisor: analyzing failure type {failed_command_type} (code: {error_code})")
        if error_code and error_code == "PERMISSION_DENIED":
            return "escalate_first"
        if error_code and error_code == "NETWORK_ERROR":
            return "switch_channel"
        alternatives = self.alternatives.get(failed_command_type, self.alternatives["default"])
        suggestion = random.choice(alternatives)
        logger.info(f"Advisor: suggesting {suggestion}")
        return suggestion

    def provide_strategic_advice(self, current_status: Dict[str, Any]) -> str:
        if current_status.get("detection_risk", 0) > 70:
            return "hibernate"
        if current_status.get("target_value", 0) < 30:
            return "abort_and_clean"
        return "proceed_normal"