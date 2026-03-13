import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoadBalancer:
    def __init__(self, nodes=None):
        self.nodes = nodes or []
        logger.info("Temporary LoadBalancer initialized (Dummy Mode).")

    def balance(self, request):
        logger.info("LoadBalancer.balance() called in dummy mode.")
        return request

    def get_health_status(self):
        return {"status": "online", "mode": "dummy"}

def initialize_balancer():
    return LoadBalancer()
