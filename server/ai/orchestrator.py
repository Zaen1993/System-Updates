import json
import threading
import time
import logging
import queue
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class AIOrchestrator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agents = {}
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.consensus_threshold = config.get("consensus_threshold", 3)
        self.running = False
        self.lock = threading.Lock()
        self.agent_status = {}
        self.hunter = None
        self.analyzer = None
        self.generator = None
        self.validator = None
        self.error_tracker = None
        self.fallback_executor = None

    def set_error_tracker(self, tracker):
        self.error_tracker = tracker

    def set_fallback_executor(self, executor):
        self.fallback_executor = executor

    def register_agent(self, agent_name: str, agent_instance):
        with self.lock:
            self.agents[agent_name] = agent_instance
            self.agent_status[agent_name] = "idle"
            logger.info(f"Agent {agent_name} registered")

    def start(self):
        self.running = True
        threading.Thread(target=self._process_tasks, daemon=True).start()
        threading.Thread(target=self._process_results, daemon=True).start()
        logger.info("AI Orchestrator started")

    def stop(self):
        self.running = False
        logger.info("AI Orchestrator stopped")

    def submit_task(self, task_type: str, data: Any, source: str = "system"):
        task = {
            "id": f"{task_type}_{int(time.time()*1000)}_{hash(str(data))}",
            "type": task_type,
            "data": data,
            "source": source,
            "timestamp": time.time(),
            "status": "pending"
        }
        self.task_queue.put(task)
        logger.debug(f"Task {task['id']} of type {task_type} submitted")
        return task["id"]

    def _process_tasks(self):
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                self._dispatch_task(task)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing task: {e}")
                if self.error_tracker:
                    self.error_tracker.log_error("system", "ORCH_PROCESS_ERR", str(e), module="ai_orchestrator")

    def _dispatch_task(self, task: Dict):
        task_type = task["type"]
        data = task["data"]
        agent = None
        if task_type.startswith("hunt_"):
            agent = self.hunter
        elif task_type.startswith("analyze_"):
            agent = self.analyzer
        elif task_type.startswith("generate_"):
            agent = self.generator
        elif task_type.startswith("validate_"):
            agent = self.validator
        else:
            logger.warning(f"No agent for task type {task_type}")
            return

        if agent is None:
            logger.warning(f"Agent for {task_type} not available")
            return

        try:
            with self.lock:
                self.agent_status[agent.__class__.__name__] = "busy"
            result = agent.process_task(task_type, data)
            with self.lock:
                self.agent_status[agent.__class__.__name__] = "idle"
            task["result"] = result
            task["status"] = "completed"
            self.result_queue.put(task)
        except Exception as e:
            logger.error(f"Agent {agent.__class__.__name__} failed on task {task['id']}: {e}")
            task["status"] = "failed"
            task["error"] = str(e)
            self.result_queue.put(task)
            if self.error_tracker:
                self.error_tracker.log_error(
                    "system", "AGENT_EXEC_FAIL", str(e),
                    module=agent.__class__.__name__, command=task_type,
                    context={"task_id": task["id"]}
                )

    def _process_results(self):
        while self.running:
            try:
                result = self.result_queue.get(timeout=1)
                self._handle_result(result)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error handling result: {e}")

    def _handle_result(self, task: Dict):
        task_type = task["type"]
        if task["status"] == "completed":
            if task_type.startswith("hunt_"):
                if task["result"].get("anomaly"):
                    logger.info(f"Anomaly detected: {task['result']}")
                    self.submit_task("analyze_anomaly", task["result"], source=task["id"])
            elif task_type.startswith("analyze_"):
                if task["result"].get("confirmed_vulnerability"):
                    logger.info(f"Vulnerability confirmed: {task['result']}")
                    self.submit_task("generate_exploit", task["result"], source=task["id"])
            elif task_type.startswith("generate_"):
                if task["result"].get("exploit_code"):
                    logger.info(f"Exploit generated, submitting for validation")
                    self.submit_task("validate_exploit", task["result"], source=task["id"])
            elif task_type.startswith("validate_"):
                if self._check_consensus(task["result"]):
                    logger.info(f"Consensus reached for exploit: {task['result']}")
                    self._store_generated_command(task["result"])
        else:
            logger.warning(f"Task {task['id']} failed: {task.get('error')}")
            if self.fallback_executor and task.get("error"):
                self.fallback_executor.submit_failed_command(
                    device_id="system",
                    command_name=task_type,
                    command_params=task.get("data", {}),
                    error_message=task["error"],
                    error_code="TASK_FAIL"
                )

    def _check_consensus(self, result: Dict) -> bool:
        return result.get("consensus", False)

    def _store_generated_command(self, result: Dict):
        logger.info(f"Command stored: {result.get('command_name')}")

    def set_hunter(self, hunter):
        self.hunter = hunter

    def set_analyzer(self, analyzer):
        self.analyzer = analyzer

    def set_generator(self, generator):
        self.generator = generator

    def set_validator(self, validator):
        self.validator = validator

    def get_status(self) -> Dict:
        with self.lock:
            return {
                "agents": list(self.agents.keys()),
                "status": self.agent_status.copy(),
                "queue_size": self.task_queue.qsize()
            }