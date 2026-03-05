from flask import Flask, request, jsonify
from core.security_shield import SecurityShield
from core.crypto_agility_manager import CryptoAgilityManager
import json
import base64
import os

app = Flask(__name__)

master_secret = base64.b64decode(os.environ.get('MASTER_SECRET_B64', ''))
salt = os.environ.get('SALT', '').encode()
if not master_secret or not salt:
    raise ValueError("MASTER_SECRET_B64 and SALT must be set")

security_shield = SecurityShield(master_secret, salt)
crypto_manager = CryptoAgilityManager(master_secret, salt)

@app.route('/api/v1/sync', methods=['POST'])
def sync_endpoint():
    auth_header = request.headers.get('X-Service-Auth')
    if not security_shield.validate_device_session(auth_header):
        return jsonify({"error": "unauthorized"}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "invalid request"}), 400

        device_id = data.get('device_id')
        encrypted_payload = data.get('data')
        iv_b64 = data.get('iv')
        version = data.get('version', 2)

        if not device_id or not encrypted_payload or not iv_b64:
            return jsonify({"error": "missing fields"}), 400

        encrypted = base64.b64decode(encrypted_payload)
        iv = base64.b64decode(iv_b64)
        ciphertext = encrypted

        device_key = security_shield.crypto.derive_device_key(device_id, version=version)
        decrypted = crypto_manager.decrypt_data(ciphertext, aad=device_id.encode(), version=version)
        payload = json.loads(decrypted.decode())

        print(f"Received sync from {device_id}: {payload}")

        response_command = {
            "type": "heartbeat",
            "params": {"interval": 300}
        }

        response_bytes = json.dumps(response_command).encode()
        iv_out = os.urandom(12)
        encrypted_response = crypto_manager.encrypt_data(response_bytes, aad=device_id.encode(), version=version)
        encrypted_b64 = base64.b64encode(encrypted_response).decode()
        iv_out_b64 = base64.b64encode(iv_out).decode()

        return jsonify({
            "data": encrypted_b64,
            "iv": iv_out_b64,
            "version": version
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)