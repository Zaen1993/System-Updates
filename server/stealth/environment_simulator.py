import logging
import json
import time
import os
import subprocess
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class EnvironmentSimulator:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.simulation_id = None
        self.virtual_env = {}
        self.error_tracker = None
        self.docker_client = None
        self._init_docker()

    def _init_docker(self):
        try:
            import docker
            self.docker_client = docker.from_env()
        except ImportError:
            logger.warning("Docker not available, using lightweight simulation")
        except Exception as e:
            logger.error(f"Docker init failed: {e}")

    def set_error_tracker(self, tracker):
        self.error_tracker = tracker

    def simulate_device(self, device_profile: Dict[str, Any]) -> str:
        self.simulation_id = f"sim_{int(time.time())}_{device_profile.get('device_id', 'unknown')}"
        os_type = device_profile.get("os", "android")
        os_version = device_profile.get("os_version", "10")
        arch = device_profile.get("arch", "arm64")
        has_root = device_profile.get("has_root", False)

        self.virtual_env = {
            "id": self.simulation_id,
            "os": os_type,
            "version": os_version,
            "arch": arch,
            "root": has_root,
            "profile": device_profile,
            "status": "created"
        }

        if self.docker_client:
            self._create_docker_container(os_type, os_version)
        else:
            self._create_lightweight_sim()

        logger.info(f"Simulation environment created: {self.simulation_id}")
        return self.simulation_id

    def _create_docker_container(self, os_type: str, version: str):
        image_map = {
            "android": f"android:{version}",
            "linux": f"ubuntu:{version}",
            "windows": f"mcr.microsoft.com/windows:{version}"
        }
        image = image_map.get(os_type, "alpine:latest")
        try:
            container = self.docker_client.containers.run(
                image=image,
                command="sleep infinity",
                detach=True,
                remove=False,
                name=f"sim_{self.simulation_id}"
            )
            self.virtual_env["container"] = container.id
            self.virtual_env["type"] = "docker"
        except Exception as e:
            logger.error(f"Docker container creation failed: {e}")
            self._create_lightweight_sim()

    def _create_lightweight_sim(self):
        self.virtual_env["type"] = "lightweight"
        self.virtual_env["filesystem"] = self._mock_filesystem()
        self.virtual_env["processes"] = self._mock_processes()

    def _mock_filesystem(self) -> Dict:
        return {
            "/system": ["build.prop", "app"],
            "/data": ["data", "local/tmp"],
            "/sdcard": ["Download", "DCIM"]
        }

    def _mock_processes(self) -> list:
        return [
            {"pid": 1, "name": "init"},
            {"pid": 1000, "name": "system_server"}
        ]

    def test_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        if not self.virtual_env:
            return {"error": "No simulation active", "safe": False}

        cmd_type = command.get("type", "unknown")
        cmd_data = command.get("data", {})
        logger.info(f"Testing command {cmd_type} in {self.simulation_id}")

        result = self._run_in_sandbox(cmd_type, cmd_data)

        if result.get("detected"):
            logger.warning(f"Command detected by sandbox: {cmd_type}")
            return {"safe": False, "reason": "detected", "details": result}

        if result.get("failed"):
            logger.warning(f"Command failed in simulation: {cmd_type}")
            return {"safe": False, "reason": "failed", "details": result}

        return {"safe": True, "reason": "passed", "details": result}

    def _run_in_sandbox(self, cmd_type: str, cmd_data: Any) -> Dict:
        # Simulate antivirus detection
        if "root" in cmd_type and self.virtual_env.get("root", False):
            return {"detected": False, "output": "executed"}

        if self.virtual_env.get("type") == "docker" and "container" in self.virtual_env:
            return self._run_in_docker(cmd_type, cmd_data)

        # Lightweight simulation
        import random
        detection = random.random() < 0.1
        success = random.random() < 0.8
        return {
            "detected": detection,
            "failed": not success and not detection,
            "output": "simulated"
        }

    def _run_in_docker(self, cmd_type: str, cmd_data: Any) -> Dict:
        try:
            container_id = self.virtual_env.get("container")
            if not container_id:
                return {"detected": False, "failed": True}
            container = self.docker_client.containers.get(container_id)
            exec_result = container.exec_run(cmd_data.get("command", "echo test"))
            return {
                "detected": False,
                "failed": exec_result.exit_code != 0,
                "output": exec_result.output.decode('utf-8', errors='ignore')
            }
        except Exception as e:
            logger.error(f"Docker exec failed: {e}")
            return {"detected": False, "failed": True, "error": str(e)}

    def test_file(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {"safe": False, "reason": "file not found"}

        with open(file_path, 'rb') as f:
            data = f.read()[:4096]

        # Simple signature check (placeholder)
        signatures = [b"MZ", b"ELF", b"%PDF"]
        detected = any(sig in data for sig in signatures)
        return {"safe": not detected, "reason": "signature match" if detected else "clean"}

    def cleanup(self):
        if self.virtual_env.get("type") == "docker" and "container" in self.virtual_env:
            try:
                container = self.docker_client.containers.get(self.virtual_env["container"])
                container.stop()
                container.remove()
            except Exception as e:
                logger.error(f"Cleanup failed: {e}")
        self.virtual_env = {}
        logger.info(f"Simulation {self.simulation_id} cleaned up")

    def get_status(self) -> Dict:
        return {
            "active": bool(self.virtual_env),
            "simulation_id": self.simulation_id,
            "env_type": self.virtual_env.get("type", "none")
        }