import os
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_TYPE = os.environ.get('DB_TYPE', 'sqlite').lower()
DB_NAME = os.environ.get('DB_NAME', '../c2/c2_data.db')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_DATABASE = os.environ.get('DB_DATABASE', 'c2db')

def get_db_connection():
    if DB_TYPE == 'sqlite':
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn
    elif DB_TYPE == 'postgresql':
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_DATABASE,
            cursor_factory=RealDictCursor
        )
        return conn
    else:
        raise ValueError(f"Unsupported DB_TYPE: {DB_TYPE}")

def fetch_location_data(device_id):
    query = """
        SELECT latitude, longitude, timestamp
        FROM location_logs
        WHERE device_id = %s
        ORDER BY timestamp
    """
    conn = get_db_connection()
    try:
        if DB_TYPE == 'sqlite':
            cursor = conn.execute(query, (device_id,))
            rows = cursor.fetchall()
            return [{'latitude': r['latitude'], 'longitude': r['longitude'], 'timestamp': r['timestamp']} for r in rows]
        else:
            with conn.cursor() as cur:
                cur.execute(query, (device_id,))
                rows = cur.fetchall()
                return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Database error: {e}")
        return []
    finally:
        conn.close()

def generate_location_heatmap(device_id):
    logger.info(f"Generating heatmap for device: {device_id}")
    data = fetch_location_data(device_id)
    if not data:
        logger.warning("No location data found.")
        return
    df = pd.DataFrame(data)
    if df.empty:
        return
    plt.figure(figsize=(10, 6))
    plt.hexbin(df['longitude'], df['latitude'], gridsize=30, cmap='inferno')
    plt.colorbar(label='Number of occurrences')
    plt.title(f'Location Heatmap - Device: {device_id}')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    filename = f"heatmap_{device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Heatmap saved: {filename}")

def generate_activity_timeline(device_id):
    logger.info(f"Generating activity timeline for device: {device_id}")
    data = fetch_location_data(device_id)
    if not data:
        return
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    daily_counts = df.resample('D').size()
    plt.figure(figsize=(12, 5))
    daily_counts.plot(kind='line', marker='o')
    plt.title(f'Daily Location Updates - Device: {device_id}')
    plt.xlabel('Date')
    plt.ylabel('Number of updates')
    plt.grid(True)
    filename = f"timeline_{device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Timeline saved: {filename}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: data_visualizer.py <device_id> [heatmap|timeline]")
        sys.exit(1)
    device = sys.argv[1]
    viz_type = sys.argv[2] if len(sys.argv) > 2 else 'heatmap'
    if viz_type == 'heatmap':
        generate_location_heatmap(device)
    elif viz_type == 'timeline':
        generate_activity_timeline(device)
    else:
        print(f"Unknown viz type: {viz_type}")