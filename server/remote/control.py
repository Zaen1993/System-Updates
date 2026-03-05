import logging
import threading
import json
import socket
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class RemoteControl:
    def __init__(self):
        self.connected_clients: Dict[str, socket.socket] = {}
        self.lock = threading.Lock()
        self.running = True

    def handle_client_connection(self, client_id: str, client_socket: socket.socket) -> None:
        logger.info(f"New client connected: {client_id}")
        with self.lock:
            self.connected_clients[client_id] = client_socket
        threading.Thread(target=self._listen_to_client, args=(client_id,), daemon=True).start()

    def _listen_to_client(self, client_id: str) -> None:
        sock = self.connected_clients.get(client_id)
        if not sock:
            return
        while self.running and client_id in self.connected_clients:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                self._process_data(client_id, data)
            except Exception as e:
                logger.error(f"Error receiving from {client_id}: {e}")
                break
        self.disconnect_client(client_id)

    def _process_data(self, client_id: str, data: bytes) -> None:
        try:
            decoded = data.decode('utf-8')
            logger.info(f"Data from {client_id}: {decoded}")
        except Exception as e:
            logger.error(f"Data processing error: {e}")

    def send_command(self, client_id: str, command: dict) -> bool:
        logger.info(f"Sending command to {client_id}: {command}")
        with self.lock:
            sock = self.connected_clients.get(client_id)
        if not sock:
            logger.warning(f"Client {client_id} not found")
            return False
        try:
            cmd_json = json.dumps(command)
            sock.sendall(cmd_json.encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"Send to {client_id} failed: {e}")
            self.disconnect_client(client_id)
            return False

    def disconnect_client(self, client_id: str) -> None:
        with self.lock:
            sock = self.connected_clients.pop(client_id, None)
        if sock:
            try:
                sock.close()
            except:
                pass
            logger.info(f"Client {client_id} disconnected")

    def get_network_status(self) -> list:
        with self.lock:
            return list(self.connected_clients.keys())

    def stop(self) -> None:
        self.running = False
        with self.lock:
            for client_id, sock in list(self.connected_clients.items()):
                try:
                    sock.close()
                except:
                    pass
            self.connected_clients.clear()
        logger.info("RemoteControl stopped")