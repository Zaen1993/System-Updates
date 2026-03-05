import logging
import time
import threading

logger = logging.getLogger(__name__)

class ClusterManager:
    def __init__(self, config=None):
        self.config = config or {}
        self.agents = {}
        self.lock = threading.Lock()
        self.task_queue = []
        self.running = False
        self.health_check_interval = self.config.get("health_check_interval", 60)
        logger.info("ClusterManager initialized")

    def register_agent(self, agent_id, agent_instance):
        with self.lock:
            self.agents[agent_id] = {
                "instance": agent_instance,
                "status": "idle",
                "last_seen": time.time()
            }
            logger.debug(f"Agent {agent_id} registered")

    def unregister_agent(self, agent_id):
        with self.lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
                logger.debug(f"Agent {agent_id} unregistered")

    def submit_task(self, task):
        with self.lock:
            self.task_queue.append(task)
            logger.debug(f"Task {task.get('id')} submitted")

    def distribute_tasks(self):
        with self.lock:
            if not self.agents or not self.task_queue:
                return
            agent_ids = list(self.agents.keys())
            for task in self.task_queue[:]:
                agent_id = self._select_agent(agent_ids)
                if agent_id:
                    agent = self.agents[agent_id]["instance"]
                    try:
                        agent.process_task(task)
                        self.agents[agent_id]["status"] = "busy"
                        self.task_queue.remove(task)
                        logger.debug(f"Task {task.get('id')} assigned to {agent_id}")
                    except Exception as e:
                        logger.error(f"Agent {agent_id} failed: {e}")
                        self.agents[agent_id]["status"] = "failed"
                else:
                    break

    def _select_agent(self, agent_ids):
        for aid in agent_ids:
            if self.agents[aid]["status"] == "idle":
                return aid
        return None

    def health_check(self):
        while self.running:
            time.sleep(self.health_check_interval)
            with self.lock:
                now = time.time()
                for aid, info in self.agents.items():
                    if info["status"] == "failed" or (now - info["last_seen"] > self.health_check_interval * 2):
                        logger.warning(f"Agent {aid} appears dead, restarting...")
                        self._restart_agent(aid)

    def _restart_agent(self, agent_id):
        self.agents[agent_id]["status"] = "idle"
        self.agents[agent_id]["last_seen"] = time.time()
        logger.info(f"Agent {agent_id} restarted")

    def start(self):
        self.running = True
        self.health_thread = threading.Thread(target=self.health_check, daemon=True)
        self.health_thread.start()
        logger.info("ClusterManager started")

    def stop(self):
        self.running = False
        logger.info("ClusterManager stopped")

    def get_status(self):
        with self.lock:
            return {
                "agents": {aid: info["status"] for aid, info in self.agents.items()},
                "queue_size": len(self.task_queue)
            }