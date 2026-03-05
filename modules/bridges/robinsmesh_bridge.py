import json
import logging
from typing import Dict, Any, Optional

from server.crypto_agility_manager import CryptoAgilityManager
from server.mesh_network_manager import MeshNetworkManager
from server.error_tracker import ErrorTracker

logger = logging.getLogger(__name__)

class RobinsMeshBridge:
    def __init__(self, node_id: str, config: Dict[str, Any]):
        self.node_id = node_id
        self.crypto = CryptoAgilityManager(
            config.get('master_secret', b''),
            config.get('salt', b'')
        )
        self.mesh = MeshNetworkManager(config.get('mesh_config', {}))
        self.error_tracker = ErrorTracker(config.get('error_config', {}))
        self.shared_key = config.get('shared_key')

    def process_data(self, target_node: str, data: Any) -> bool:
        try:
            logger.info(f"Processing data from {self.node_id} to {target_node}")
            payload = json.dumps(data)
            encrypted = self.crypto.encrypt_data(payload.encode(), aad=target_node.encode())
            success = self.mesh.send_data(target_node, encrypted)
            return success
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            self.error_tracker.log_error(self.node_id, 'BRIDGE_ERROR', str(e))
            return False

    def receive_data(self, timeout: int = 5) -> Optional[Dict]:
        try:
            raw = self.mesh.receive_data(timeout=timeout)
            if not raw:
                return None
            decrypted = self.crypto.decrypt_data(raw['data'], aad=raw['source'].encode())
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error(f"Receive failed: {e}")
            self.error_tracker.log_error(self.node_id, 'RECEIVE_ERROR', str(e))
            return None

if __name__ == '__main__':
    config = {
        'master_secret': b'some_secret',
        'salt': b'some_salt',
        'shared_key': b'shared_key',
        'mesh_config': {},
        'error_config': {}
    }
    bridge = RobinsMeshBridge('node_1', config)
    bridge.process_data('node_2', {'action': 'ping'})