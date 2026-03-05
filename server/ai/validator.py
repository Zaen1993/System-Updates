import json
import time
import hashlib
import logging
import re
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ValidatorAgent:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.consensus_threshold = self.config.get("consensus_threshold", 3)
        self.validation_history = []
        self.error_tracker = None
        self.command_generator = None
        self.ai_advisor = None

        self.blacklist = [
            "rm -rf /", "format c:", "dd if=/dev/zero", "mkfs",
            "kill -9", "shutdown", "reboot", "init 0", "init 6",
            "chmod 777 /", "chown -R", "> /dev/sda", "| bash",
            "wget http://evil", "curl http://evil", "nc -e",
            "perl -e", "python -c 'import os; os.system",
            "/dev/mem", "/dev/kmem", "insmod", "modprobe",
            "iptables -F", "ufw disable", "systemctl stop",
            "service networking stop", "ifconfig down",
            "route del default", "arp -d", "macchanger"
        ]

        self.high_risk_patterns = [
            r"sudo\s+rm", r"chmod\s+777", r"chown\s+\w+",
            r"dd\s+if=.*of=.*", r"mkfs\.", r"fdisk",
            r"kill\s+-9", r"pkill", r"killall",
            r"shutdown", r"reboot", r"halt", r"poweroff",
            r"iptables\s+-F", r"ufw\s+disable",
            r"systemctl\s+(stop|disable|mask)",
            r"service\s+.*\s+stop", r"ifconfig\s+down",
            r"route\s+del", r"arp\s+-d"
        ]

        self.required_approvals = 2

    def set_error_tracker(self, tracker):
        self.error_tracker = tracker

    def set_command_generator(self, generator):
        self.command_generator = generator

    def set_ai_advisor(self, advisor):
        self.ai_advisor = advisor

    def validate_command(self, command: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        validation_id = hashlib.md5(f"{command}{time.time()}".encode()).hexdigest()[:16]
        result = {
            "id": validation_id,
            "command": command,
            "timestamp": time.time(),
            "valid": False,
            "risk_level": "low",
            "issues": [],
            "warnings": [],
            "approvals": 0,
            "rejections": 0,
            "consensus": False
        }

        for forbidden in self.blacklist:
            if forbidden in command:
                result["valid"] = False
                result["risk_level"] = "critical"
                result["issues"].append(f"Blacklisted pattern: {forbidden}")
                self._log_validation(result)
                return result

        for pattern in self.high_risk_patterns:
            if re.search(pattern, command):
                result["warnings"].append(f"High-risk pattern detected: {pattern}")
                result["risk_level"] = "high"

        if context:
            target = context.get("target")
            if target and target == "localhost":
                result["issues"].append("Targeting localhost is not allowed")
                result["risk_level"] = "high"
            if context.get("requires_root") and not context.get("has_root"):
                result["issues"].append("Command requires root but device not rooted")
                result["risk_level"] = "medium"

        if len(command) < 3:
            result["issues"].append("Command too short")
        if ";" in command and "rm" in command:
            result["warnings"].append("Dangerous combination: ; and rm")

        if not result["issues"]:
            result["valid"] = True
            if result["warnings"]:
                result["risk_level"] = "medium"

        self._log_validation(result)
        return result

    def _log_validation(self, result: Dict[str, Any]):
        self.validation_history.append(result)
        if len(self.validation_history) > 1000:
            self.validation_history.pop(0)
        logger.info(f"Validation {result['id']}: valid={result['valid']}, risk={result['risk_level']}")

    def get_consensus(self, commands: List[str], context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        logger.info(f"Validator Agent: Seeking consensus on {len(commands)} commands...")
        validated = []

        for cmd in commands:
            validation = self.validate_command(cmd, context)

            if validation["valid"]:
                approvals = 1
                rejections = 0

                if self.ai_advisor:
                    advice = self.ai_advisor.analyze_command(cmd, context)
                    if advice.get("approve"):
                        approvals += 1
                    else:
                        rejections += 1

                if self.command_generator:
                    compatibility = self.command_generator.check_compatibility(cmd, context)
                    if compatibility.get("compatible"):
                        approvals += 1
                    else:
                        rejections += 1

                validation["approvals"] = approvals
                validation["rejections"] = rejections
                validation["consensus"] = approvals >= self.required_approvals

                if validation["consensus"]:
                    logger.info(f"Consensus reached for command: {cmd[:50]}...")
                else:
                    logger.warning(f"Consensus failed for command: {cmd[:50]}...")
                    validation["issues"].append("Failed to reach consensus")
            else:
                validation["consensus"] = False

            validated.append(validation)

        return validated

    def get_statistics(self) -> Dict[str, Any]:
        if not self.validation_history:
            return {"total": 0, "valid": 0, "invalid": 0, "avg_risk": "unknown"}

        total = len(self.validation_history)
        valid = sum(1 for v in self.validation_history if v["valid"])
        invalid = total - valid

        risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for v in self.validation_history:
            risk_counts[v["risk_level"]] = risk_counts.get(v["risk_level"], 0) + 1

        return {
            "total_validations": total,
            "valid_commands": valid,
            "invalid_commands": invalid,
            "risk_distribution": risk_counts,
            "last_validation": self.validation_history[-1] if total > 0 else None
        }

    def process_task(self, task_type: str, data: Any) -> Dict[str, Any]:
        if task_type == "validate_single":
            cmd = data.get("command")
            ctx = data.get("context")
            if not cmd:
                return {"error": "No command provided"}
            return self.validate_command(cmd, ctx)

        elif task_type == "validate_batch":
            cmds = data.get("commands", [])
            ctx = data.get("context")
            results = self.get_consensus(cmds, ctx)
            return {"validated_commands": results}

        elif task_type == "statistics":
            return self.get_statistics()

        elif task_type == "add_blacklist":
            pattern = data.get("pattern")
            if pattern and pattern not in self.blacklist:
                self.blacklist.append(pattern)
                return {"status": "added", "pattern": pattern}
            return {"error": "Invalid or duplicate pattern"}

        return {"error": f"Unknown task type: {task_type}"}