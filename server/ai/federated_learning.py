import numpy as np
import logging

logger = logging.getLogger(__name__)

class FederatedLearningAgent:
    def __init__(self, model_initial_weights=None):
        if model_initial_weights is None:
            self.global_model_weights = np.random.randn(10)
        else:
            self.global_model_weights = model_initial_weights
        self.client_updates = []
        self.min_clients = 2

    def receive_client_update(self, client_weights):
        if not isinstance(client_weights, np.ndarray):
            logger.error("Invalid client weights type")
            return False
        self.client_updates.append(client_weights)
        logger.debug(f"Received update, total clients now: {len(self.client_updates)}")
        return True

    def aggregate_models(self):
        if len(self.client_updates) < self.min_clients:
            logger.info(f"Not enough clients: {len(self.client_updates)} < {self.min_clients}")
            return False
        try:
            new_weights = np.mean(self.client_updates, axis=0)
            self.global_model_weights = new_weights
            logger.info("Global model updated via federated averaging")
            self.client_updates = []
            return True
        except Exception as e:
            logger.error(f"Aggregation failed: {e}")
            return False

    def get_global_model(self):
        return self.global_model_weights.copy()

    def set_min_clients(self, n):
        self.min_clients = n