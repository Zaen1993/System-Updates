import os
import json
import logging
import sqlite3
import hashlib
import base64
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

DB_NAME = os.environ.get('C2_DB_NAME', '../c2/c2_data.db')
ENCRYPTION_KEY = os.environ.get('LOCATION_ENCRYPTION_KEY', 'change-this-key-32-bytes-').encode()[:32]

def _encrypt(data: str) -> str:
    cipher = hashlib.sha256(ENCRYPTION_KEY).digest()
    encrypted = bytes([ord(c) ^ cipher[i % len(cipher)] for i, c in enumerate(data)])
    return base64.b64encode(encrypted).decode()

def _decrypt(data: str) -> str:
    raw = base64.b64decode(data)
    cipher = hashlib.sha256(ENCRYPTION_KEY).digest()
    decrypted = bytes([raw[i] ^ cipher[i % len(cipher)] for i in range(len(raw))])
    return decrypted.decode()

class LocationTracker:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS location_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    accuracy REAL,
                    speed REAL,
                    bearing REAL,
                    altitude REAL,
                    provider TEXT,
                    encrypted_data TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def record_location(self, device_id: str, lat: float, lon: float,
                        accuracy: float = None, speed: float = None,
                        bearing: float = None, altitude: float = None,
                        provider: str = 'gps') -> bool:
        try:
            metadata = {
                'accuracy': accuracy, 'speed': speed, 'bearing': bearing,
                'altitude': altitude, 'provider': provider
            }
            encrypted = _encrypt(json.dumps(metadata))
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute('''
                    INSERT INTO location_history
                    (device_id, latitude, longitude, accuracy, speed, bearing, altitude, provider, encrypted_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (device_id, lat, lon, accuracy, speed, bearing, altitude, provider, encrypted))
                conn.commit()
            logger.info(f"Location recorded for {device_id}: {lat},{lon}")
            return True
        except Exception as e:
            logger.error(f"Failed to record location: {e}")
            return False

    def get_history(self, device_id: str, limit: int = 100) -> List[Dict]:
        try:
            with sqlite3.connect(DB_NAME) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT latitude, longitude, accuracy, speed, bearing, altitude, provider, timestamp
                    FROM location_history
                    WHERE device_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (device_id, limit))
                rows = cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []

    def analyze_hotspots(self, device_id: str, radius_km: float = 1.0) -> List[Dict]:
        history = self.get_history(device_id, limit=500)
        if not history:
            return []
        # simple clustering: round coordinates to ~radius_km
        factor = 1.0 / (radius_km * 111.0)  # approx degrees per km
        clusters = {}
        for h in history:
            lat_round = round(h['latitude'] / factor) * factor
            lon_round = round(h['longitude'] / factor) * factor
            key = (lat_round, lon_round)
            if key not in clusters:
                clusters[key] = {'count': 0, 'entries': []}
            clusters[key]['count'] += 1
            clusters[key]['entries'].append(h)
        hotspots = [
            {'latitude': k[0], 'longitude': k[1], 'count': v['count'], 'samples': v['entries']}
            for k, v in clusters.items() if v['count'] > 2
        ]
        hotspots.sort(key=lambda x: -x['count'])
        return hotspots

    def is_in_geofence(self, device_id: str, center_lat: float, center_lon: float, radius_km: float) -> bool:
        history = self.get_history(device_id, limit=1)
        if not history:
            return False
        latest = history[0]
        from math import radians, sin, cos, sqrt, atan2
        R = 6371.0
        lat1, lon1 = radians(center_lat), radians(center_lon)
        lat2, lon2 = radians(latest['latitude']), radians(latest['longitude'])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        return distance <= radius_km

    def delete_old_records(self, days: int = 30) -> int:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.execute('DELETE FROM location_history WHERE timestamp < datetime("now", ?)', (f'-{days} days',))
            conn.commit()
            return cursor.rowcount