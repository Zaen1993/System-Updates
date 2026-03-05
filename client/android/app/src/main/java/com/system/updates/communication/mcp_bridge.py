import os
import socket
import threading
import logging
import json
import base64
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class MCPBridge:
    def __init__(self, host: str = '0.0.0.0', port: int = 9000, use_encryption: bool = True):
        self.host = host
        self.port = port
        self.use_encryption = use_encryption
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        self.clients = []
        self.lock = threading.Lock()
        self.secret = os.environ.get('MCP_SECRET', 'default_mcp_secret').encode()
        self.crypto = None
        if use_encryption:
            try:
                from server.core.crypto_agility_manager import CryptoAgilityManager
                master_secret_b64 = os.environ.get('MASTER_SECRET_B64')
                salt = os.environ.get('SALT', '').encode()
                if master_secret_b64:
                    import base64
                    master_secret = base64.b64decode(master_secret_b64)
                    self.crypto = CryptoAgilityManager(master_secret, salt)
            except ImportError:
                logger.warning("Crypto module not available, encryption disabled")
                self.use_encryption = False

    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        logger.info(f"MCP Bridge listening on {self.host}:{self.port}")
        threading.Thread(target=self._accept_connections, daemon=True).start()

    def _accept_connections(self):
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                logger.info(f"Connection from {addr}")
                with self.lock:
                    self.clients.append(client_socket)
                threading.Thread(target=self._handle_client, args=(client_socket, addr), daemon=True).start()
            except Exception as e:
                logger.error(f"Accept error: {e}")

    def _handle_client(self, client_socket: socket.socket, addr):
        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break
                decrypted = self._decrypt(data)
                logger.debug(f"Received from {addr}: {decrypted}")
                response = self._process_message(decrypted)
                encrypted_response = self._encrypt(response)
                client_socket.sendall(encrypted_response)
        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            with self.lock:
                if client_socket in self.clients:
                    self.clients.remove(client_socket)
            client_socket.close()
            logger.info(f"Connection closed: {addr}")

    def _process_message(self, message: str) -> str:
        try:
            msg = json.loads(message)
            msg_type = msg.get('type', 'ping')
            if msg_type == 'ping':
                return json.dumps({'type': 'pong', 'status': 'ok'})
            elif msg_type == 'cmd':
                return json.dumps({'type': 'ack', 'cmd_id': msg.get('cmd_id'), 'status': 'received'})
            else:
                return json.dumps({'type': 'error', 'message': 'unknown type'})
        except json.JSONDecodeError:
            return json.dumps({'type': 'error', 'message': 'invalid json'})

    def _encrypt(self, data: str) -> bytes:
        if self.use_encryption and self.crypto:
            encrypted = self.crypto.encrypt(data.encode(), aad=b"mcp")
            return base64.b64encode(encrypted)
        else:
            encoded = data.encode()
            key = self.secret
            xored = bytes([encoded[i] ^ key[i % len(key)] for i in range(len(encoded))])
            return xored

    def _decrypt(self, data: bytes) -> str:
        if self.use_encryption and self.crypto:
            decoded = base64.b64decode(data)
            decrypted = self.crypto.decrypt(decoded, aad=b"mcp")
            return decrypted.decode()
        else:
            key = self.secret
            xored = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
            return xored.decode()

    def send_command(self, target_ip: str, target_port: int, command: Dict[str, Any]) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((target_ip, target_port))
            msg = json.dumps({'type': 'cmd', 'cmd': command})
            encrypted = self._encrypt(msg)
            sock.sendall(encrypted)
            response = sock.recv(4096)
            decrypted = self._decrypt(response)
            result = json.loads(decrypted)
            sock.close()
            return result.get('status') == 'ok' or result.get('type') == 'ack'
        except Exception as e:
            logger.error(f"Send command failed: {e}")
            return False

    def stop(self):
        self.running = False
        with self.lock:
            for c in self.clients:
                try:
                    c.close()
                except:
                    pass
            self.clients.clear()
        if self.server_socket:
            self.server_socket.close()
        logger.info("MCP Bridge stopped")

    def process_task(self, task_type: str, data: Any) -> Dict[str, Any]:
        if task_type == "start":
            self.start()
            return {"status": "started"}
        elif task_type == "stop":
            self.stop()
            return {"status": "stopped"}
        elif task_type == "send":
            ip = data.get("ip")
            port = data.get("port", self.port)
            cmd = data.get("command")
            success = self.send_command(ip, port, cmd)
            return {"success": success}
        return {"error": "unknown task"}

if __name__ == "__main__":
    bridge = MCPBridge()
    bridge.start()
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        bridge.stop()