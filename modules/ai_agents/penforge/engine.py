import logging
import threading
from modules.ai_agents.penforge import orchestrator
from modules.ai_agents.penforge import report_generator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PenForgeEngine")

class PenForgeEngine:
    def __init__(self, target_config):
        self.target_config = target_config
        self.orchestrator = orchestrator.AgentOrchestrator(target_config)
        self.reporter = report_generator.ReportGenerator()
        self.is_running = False

    def start_campaign(self):
        if self.is_running:
            logger.warning("Campaign already running.")
            return
        logger.info(f"Starting PenForge campaign on target: {self.target_config['domain']}...")
        self.is_running = True
        campaign_thread = threading.Thread(target=self._run_engine)
        campaign_thread.start()

    def _run_engine(self):
        try:
            raw_findings = self.orchestrator.execute_scan()
            report_path = self.reporter.generate(raw_findings)
            logger.info(f"Campaign finished. Report generated at: {report_path}")
            self.is_running = False
        except Exception as e:
            logger.error(f"Critical error in PenForge engine: {e}")
            self.is_running = False

if __name__ == "__main__":
    target = {"domain": "example.com", "scan_intensity": "high"}
    engine = PenForgeEngine(target)
    print("PenForgeEngine initialized.")