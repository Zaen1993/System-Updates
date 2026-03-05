import os
import json
import base64
import logging
from typing import List, Dict, Any, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import importlib.util

logger = logging.getLogger(__name__)

class MoltSkillsFactory:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._master_key = self._load_master_key()
        self._salt = self.config.get('salt', b'moltskills_salt').encode()
        self._agents = []
        self._agent_types = {
            'analyst': 'modules.ai_agents.ai_supply_chain.analyst_agent',
            'negotiator': 'modules.ai_agents.ai_supply_chain.negotiator_agent',
            'logistics': 'modules.ai_agents.ai_supply_chain.logistics_agent'
        }

    def _load_master_key(self) -> bytes:
        key_b64 = os.environ.get('MASTER_SECRET_B64')
        if not key_b64:
            raise ValueError('MASTER_SECRET_B64 environment variable required')
        return base64.b64decode(key_b64)

    def _derive_key(self, context: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(self._master_key + context)

    def _encrypt(self, data: bytes, context: bytes) -> bytes:
        key = self._derive_key(context)
        iv = os.urandom(12)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ct = encryptor.update(data) + encryptor.finalize()
        return iv + encryptor.tag + ct

    def _decrypt(self, enc_data: bytes, context: bytes) -> bytes:
        key = self._derive_key(context)
        iv = enc_data[:12]
        tag = enc_data[12:28]
        ct = enc_data[28:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ct) + decryptor.finalize()

    def _import_agent_class(self, module_path: str, class_name: str) -> Optional[type]:
        try:
            spec = importlib.util.find_spec(module_path)
            if spec is None:
                return None
            module = importlib.import_module(module_path)
            return getattr(module, class_name, None)
        except Exception as e:
            logger.error(f'Import failed {module_path}.{class_name}: {e}')
            return None

    def create_agent(self, agent_type: str, agent_name: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        logger.info(f'Creating agent: {agent_type}/{agent_name}')
        module_path = self._agent_types.get(agent_type)
        if not module_path:
            logger.error(f'Unknown agent type: {agent_type}')
            return None

        class_name = {
            'analyst': 'SupplyChainAnalyst',
            'negotiator': 'NegotiatorAgent',
            'logistics': 'LogisticsPlanner'
        }.get(agent_type)

        agent_class = self._import_agent_class(module_path, class_name)
        if agent_class is None:
            logger.error(f'Agent class {class_name} not found')
            return None

        try:
            agent_instance = agent_class(agent_name, **(params or {}))
            agent_id = base64.b64encode(os.urandom(16)).decode()[:24]
            agent_record = {
                'id': agent_id,
                'type': agent_type,
                'name': agent_name,
                'instance': agent_instance,
                'created': int(time.time())
            }
            self._agents.append(agent_record)
            encrypted_id = self._encrypt(agent_id.encode(), f'agent_{agent_name}'.encode())
            return {
                'agent_id': agent_id,
                'encrypted': base64.b64encode(encrypted_id).decode(),
                'type': agent_type,
                'name': agent_name
            }
        except Exception as e:
            logger.error(f'Agent creation failed: {e}')
            return None

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        for agent in self._agents:
            if agent['id'] == agent_id:
                return agent
        return None

    def list_agents(self) -> List[Dict[str, Any]]:
        return [{'id': a['id'], 'type': a['type'], 'name': a['name'], 'created': a['created']} for a in self._agents]

    def call_agent_method(self, agent_id: str, method: str, args: List = None, kwargs: Dict = None) -> Any:
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f'Agent {agent_id} not found')
        instance = agent['instance']
        if not hasattr(instance, method):
            raise AttributeError(f'Method {method} not found on agent {agent_id}')
        func = getattr(instance, method)
        return func(*(args or []), **(kwargs or {}))

    def save_state(self) -> bytes:
        state = [{'id': a['id'], 'type': a['type'], 'name': a['name'], 'created': a['created']} for a in self._agents]
        return self._encrypt(json.dumps(state).encode(), b'factory_state')

    def load_state(self, encrypted_state: bytes) -> bool:
        try:
            data = self._decrypt(encrypted_state, b'factory_state')
            state = json.loads(data.decode())
            self._agents = []
            for s in state:
                self.create_agent(s['type'], s['name'])
            return True
        except Exception as e:
            logger.error(f'State load failed: {e}')
            return False

if __name__ == '__main__':
    import time
    factory = MoltSkillsFactory()
    a1 = factory.create_agent('analyst', 'Analyst_01')
    a2 = factory.create_agent('negotiator', 'Negotiator_01')
    print(f'Active agents: {len(factory.list_agents())}')