import os
import json
import base64
import logging
from flask import Flask, request, jsonify
from security_shield import SecurityShield
from db_manager import save_data, get_pending_commands
from command_retry_queue import CommandRetryQueue
from fallback_executor import FallbackExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

master_secret_b64 = os.environ.get('MASTER_SECRET_B64')
if not master_secret_b64:
    raise ValueError("MASTER_SECRET_B64 required")
master_secret = base64.b64decode(master_secret_b64)
salt = os.environ.get('SALT')
if not salt:
    raise ValueError("SALT required")
salt = salt.encode()

shield = SecurityShield(master_secret, salt)
retry_queue = CommandRetryQueue()
fallback = FallbackExecutor()

@app.route('/api/v1/collect', methods=['POST'])
def collect_data():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "invalid json"}), 400
        device_id = data.get('device_id')
        encrypted_payload = data.get('payload')
        if not device_id or not encrypted_payload:
            return jsonify({"error": "missing fields"}), 400
        device_key = shield.crypto.derive_device_key(device_id)
        raw = base64.b64decode(encrypted_payload)
        decrypted = shield.crypto.decrypt_packet(device_key, raw)
        payload_str = decrypted.decode('utf-8')
        save_data(device_id, payload_str)
        logger.info(f"Data received from {device_id}")
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.exception("collect_data error")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/commands/<device_id>', methods=['GET'])
def get_commands(device_id):
    try:
        commands = get_pending_commands(device_id)
        device_key = shield.crypto.derive_device_key(device_id)
        encrypted = shield.crypto.encrypt_packet(device_key, json.dumps(commands).encode())
        return jsonify({"commands": base64.b64encode(encrypted).decode()}), 200
    except Exception as e:
        logger.exception("get_commands error")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/commands/push', methods=['POST'])
def push_command():
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        command = data.get('command')
        if not device_id or not command:
            return jsonify({"error": "missing fields"}), 400
        save_command(device_id, command)
        return jsonify({"status": "queued"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)