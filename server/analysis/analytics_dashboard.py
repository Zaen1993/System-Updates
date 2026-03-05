import os
import json
import time
import logging
from flask import Flask, render_template, jsonify, request
from functools import wraps
import sqlite3
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = os.environ.get('ANALYTICS_DB', '/data/analytics.db')
SECRET_KEY = os.environ.get('ANALYTICS_SECRET', 'change_this_secret_key')
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

app = Flask(__name__)
app.secret_key = SECRET_KEY

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if key and key == SECRET_KEY:
            return f(*args, **kwargs)
        return jsonify({"error": "unauthorized"}), 401
    return decorated

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP,
            ip TEXT,
            os_version TEXT,
            model TEXT,
            manufacturer TEXT,
            country TEXT,
            status TEXT DEFAULT 'active'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            event_type TEXT,
            event_data TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            command TEXT,
            status TEXT DEFAULT 'pending',
            result TEXT,
            sent_at TIMESTAMP,
            executed_at TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            cpu_usage REAL,
            memory_usage REAL,
            battery_level INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Database initialized")

threading.Thread(target=init_db, daemon=True).start()

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/devices')
@require_api_key
def get_devices():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM devices ORDER BY last_seen DESC')
    devices = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(devices)

@app.route('/api/device/<device_id>')
@require_api_key
def get_device(device_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM devices WHERE id = ?', (device_id,))
    device = cursor.fetchone()
    if not device:
        conn.close()
        return jsonify({"error": "device not found"}), 404
    device = dict(device)
    cursor.execute('SELECT * FROM events WHERE device_id = ? ORDER BY timestamp DESC LIMIT 50', (device_id,))
    events = [dict(row) for row in cursor.fetchall()]
    cursor.execute('SELECT * FROM stats WHERE device_id = ? ORDER BY timestamp DESC LIMIT 100', (device_id,))
    stats = [dict(row) for row in cursor.fetchall()]
    cursor.execute('SELECT * FROM commands WHERE device_id = ? ORDER BY sent_at DESC', (device_id,))
    commands = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({
        "device": device,
        "events": events,
        "stats": stats,
        "commands": commands
    })

@app.route('/api/events', methods=['POST'])
@require_api_key
def add_event():
    data = request.get_json()
    if not data or 'device_id' not in data or 'event_type' not in data:
        return jsonify({"error": "missing fields"}), 400
    device_id = data['device_id']
    event_type = data['event_type']
    event_data = json.dumps(data.get('event_data', {}))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO events (device_id, event_type, event_data)
        VALUES (?, ?, ?)
    ''', (device_id, event_type, event_data))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/api/stats', methods=['POST'])
@require_api_key
def add_stats():
    data = request.get_json()
    if not data or 'device_id' not in data:
        return jsonify({"error": "missing device_id"}), 400
    device_id = data['device_id']
    cpu = data.get('cpu_usage')
    mem = data.get('memory_usage')
    batt = data.get('battery_level')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO stats (device_id, cpu_usage, memory_usage, battery_level)
        VALUES (?, ?, ?, ?)
    ''', (device_id, cpu, mem, batt))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/api/commands/push', methods=['POST'])
@require_api_key
def push_command():
    data = request.get_json()
    if not data or 'device_id' not in data or 'command' not in data:
        return jsonify({"error": "missing fields"}), 400
    device_id = data['device_id']
    command = data['command']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO commands (device_id, command, sent_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    ''', (device_id, command))
    conn.commit()
    command_id = cursor.lastrowid
    conn.close()
    return jsonify({"status": "ok", "command_id": command_id})

@app.route('/api/commands/pull/<device_id>', methods=['GET'])
@require_api_key
def pull_commands(device_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, command FROM commands
        WHERE device_id = ? AND status = 'pending'
        ORDER BY sent_at ASC
    ''', (device_id,))
    commands = [dict(row) for row in cursor.fetchall()]
    for cmd in commands:
        cursor.execute('UPDATE commands SET status = 'sent' WHERE id = ?', (cmd['id'],))
    conn.commit()
    conn.close()
    return jsonify(commands)

@app.route('/api/commands/result', methods=['POST'])
@require_api_key
def command_result():
    data = request.get_json()
    if not data or 'command_id' not in data or 'result' not in data:
        return jsonify({"error": "missing fields"}), 400
    cmd_id = data['command_id']
    result = data['result']
    status = data.get('status', 'completed')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE commands SET status = ?, result = ?, executed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (status, result, cmd_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/api/summary')
@require_api_key
def get_summary():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM devices')
    total_devices = cursor.fetchone()['total']
    cursor.execute('SELECT COUNT(*) as active FROM devices WHERE status = 'active'')
    active_devices = cursor.fetchone()['active']
    cursor.execute('SELECT COUNT(*) as total FROM events WHERE timestamp > datetime('now', '-1 day')')
    events_24h = cursor.fetchone()['total']
    cursor.execute('SELECT COUNT(*) as pending FROM commands WHERE status = 'pending'')
    pending_commands = cursor.fetchone()['pending']
    conn.close()
    return jsonify({
        "total_devices": total_devices,
        "active_devices": active_devices,
        "events_24h": events_24h,
        "pending_commands": pending_commands,
        "timestamp": time.time()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=DEBUG)